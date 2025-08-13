import os
import asyncio
import re
import tldextract
from typing import List, Dict, Any, Optional
import requests
from sentence_transformers import SentenceTransformer
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except Exception:
    CrossEncoder = None
    CROSS_ENCODER_AVAILABLE = False
from playwright.async_api import async_playwright
import base64
from datetime import datetime
import numpy as np
from bs4 import BeautifulSoup
import json
import hashlib
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


class VerificationService:
    def __init__(self):
        self.use_llm_planner = os.getenv("VERIFICATION_USE_LLM_PLANNER", "true").lower() == "true"
        try:
            self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        except Exception:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        if CROSS_ENCODER_AVAILABLE:
            try:
                self.nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-base')
            except Exception:
                self.nli_model = None
        else:
            self.nli_model = None
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception:
                self.openai_client = None
        else:
            self.openai_client = None
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        os.makedirs("screenshots", exist_ok=True)

    async def get_or_create_page(self):
        if self._page is not None:
            return self._page
        
        self._playwright = await async_playwright().start()
        headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
        slow_mo = int(os.getenv("PLAYWRIGHT_SLOWMO_MS", "0") or "0")
        
        self._browser = await self._playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        self._page = await self._context.new_page()
        return self._page

    def extract_entities(self, claim_text: str) -> List[str]:
        entities = []
        words = claim_text.split()
        
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                name_parts = [word]
                j = i + 1
                while j < len(words) and j < i + 3 and words[j][0].isupper():
                    name_parts.append(words[j])
                    j += 1
                if len(name_parts) >= 2:
                    entities.append(" ".join(name_parts))
                elif len(word) > 3:
                    entities.append(word)
        
        words_clean = re.findall(r'\b[a-zA-Z]{4,}\b', claim_text)
        for word in words_clean:
            if word.lower() not in ['good', 'bad', 'very', 'much', 'most', 'some', 'many', 'this', 'that', 'they', 'them', 'have', 'been', 'will', 'from', 'with']:
                entities.append(word.lower())
                
        return list(set(entities))

    def build_llm_plan(self, claim_text: str) -> Optional[Dict[str, Any]]:
        if not (self.use_llm_planner and self.openai_client):
            return None
        system = (
            "You are a retrieval planner. Given a user claim, output ONLY JSON with keys: "
            "site_filters (list of 'site:domain' strings for trustworthy sources, 0-20), "
            "query_variants (list of 3-12 concise queries)."
        )
        user = f"Claim: {claim_text}"
        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.0,
                max_tokens=400
            )
            content = resp.choices[0].message.content.strip()
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1 and end > start:
                content = content[start:end+1]
            plan = json.loads(content)
            queries = plan.get('query_variants')
            if not isinstance(queries, list):
                return None
            return plan
        except Exception:
            return None

    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        candidates = []
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, region="wt-wt", safesearch="off"))
            
            for r in results:
                url = r.get("href") or r.get("url", "")
                title = r.get("title", "")
                body = r.get("body", "")
                
                if url and not self.is_search_page(url):
                    candidates.append({
                        "url": url,
                        "title": title,
                        "summary": body,
                        "source": "web"
                    })
        except Exception:
            pass
        
        return candidates[:max_results]

    def is_search_page(self, url: str) -> bool:
        search_indicators = [
            '/search?', '/search/', '?q=', '?query=', 
            'site-search', 'search-results', '/find?'
        ]
        return any(indicator in url.lower() for indicator in search_indicators)

    def score_relevance(self, candidate: Dict[str, Any], entities: List[str]) -> float:
        text = f"{candidate.get('title', '')} {candidate.get('summary', '')}".lower()
        
        entity_score = 0
        for entity in entities:
            if entity.lower() in text:
                entity_score += 1
        entity_score = entity_score / max(len(entities), 1)
        
        if self.is_search_page(candidate.get('url', '')):
            return 0.0
            
        return entity_score

    def _screenshot_name(self, url: str, claim_text: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = tldextract.extract(url).registered_domain or "site"
        csum = hashlib.md5(claim_text.encode()).hexdigest()[:8]
        return f"{ts}_{domain}_{csum}.png"

    async def _highlight_and_screenshot(self, page, target_text: str, url: str, claim_text: str) -> Optional[str]:
        try:
            text = normalize_whitespace(target_text)
            script = f"""
            const t = `{text}`.trim();
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            const nodes = [];
            let n; while (n = walker.nextNode()) {{ if (n.nodeValue.trim().length > 0) nodes.push(n); }}
            const find = (needle) => {{
              for (const node of nodes) {{
                const idx = node.nodeValue.toLowerCase().indexOf(needle.toLowerCase());
                if (idx !== -1) {{
                  const before = node.nodeValue.slice(0, idx);
                  const mid = node.nodeValue.slice(idx, idx + needle.length);
                  const after = node.nodeValue.slice(idx + needle.length);
                  const span = document.createElement('span');
                  span.style.backgroundColor = '#fff59d';
                  span.style.outline = '2px solid #ef5350';
                  span.style.padding = '2px';
                  span.textContent = mid;
                  const p = node.parentNode;
                  p.insertBefore(document.createTextNode(before), node);
                  p.insertBefore(span, node);
                  p.insertBefore(document.createTextNode(after), node);
                  p.removeChild(node);
                  span.scrollIntoView({ behavior: 'instant', block: 'center' });
                  return true;
                }}
              }}
              return false;
            }};
            let ok = find(t);
            if (!ok) {{
              const parts = t.split(' ').filter(w => w.length > 3).slice(0, 6);
              for (const p of parts) {{ if (find(p)) {{ ok = true; break; }} }}
            }}
            ok;
            """
            await page.evaluate(script)
            await asyncio.sleep(0.2)
            name = self._screenshot_name(url, claim_text)
            path = os.path.join("screenshots", name)
            await page.screenshot(path=path, full_page=False, quality=90)
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return None

    async def extract_content(self, page, claim_embedding: List[float], claim_text: str) -> Dict[str, Any]:
        try:
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(1)
            
            content_selectors = [
                'p', 'article p', 'div.content p', 'div.article-body p',
                'div.story-body p', 'div.entry-content p', '.mw-parser-output p'
            ]
            
            all_texts = []
            for selector in content_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for elem in elements[:50]:
                        text = await elem.text_content()
                        text = normalize_whitespace(text)
                        if len(text) >= 30:
                            all_texts.append(text)
                except Exception:
                    continue
            
            if not all_texts:
                body_text = await page.locator('body').text_content()
                sentences = re.split(r'[.!?]+', body_text)
                all_texts = [normalize_whitespace(s) for s in sentences if len(s.strip()) >= 30][:20]
            
            if not all_texts:
                return {
                    "snippet": "No content found",
                    "similarity": 0.0,
                    "screenshot_b64": None,
                    "url_with_text_fragment": page.url
                }
            
            text_embeddings = self.embedding_model.encode(all_texts).tolist()
            similarities = [self.cosine_similarity(claim_embedding, emb) for emb in text_embeddings]
            
            best_idx = max(range(len(similarities)), key=lambda i: similarities[i])
            best_text = all_texts[best_idx]
            best_similarity = similarities[best_idx]
            
            text_fragment = self.create_text_fragment_url(page.url, best_text)
            screenshot_b64 = await self._highlight_and_screenshot(page, best_text, page.url, claim_text)
            return {
                "snippet": best_text,
                "similarity": float(best_similarity),
                "screenshot_b64": screenshot_b64,
                "url_with_text_fragment": text_fragment
            }
            
        except Exception:
            return {
                "snippet": "No content found",
                "similarity": 0.0,
                "screenshot_b64": None,
                "url_with_text_fragment": page.url
            }

    def create_text_fragment_url(self, url: str, text: str) -> str:
        try:
            clean_text = re.sub(r'[^\w\s]', '', text)
            words = clean_text.split()[:10]
            fragment = '%20'.join(words)
            base_url = url.split('#')[0]
            return f"{base_url}#:~:text={fragment}"
        except Exception:
            return url

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        va = np.array(a)
        vb = np.array(b)
        norm_a = np.linalg.norm(va)
        norm_b = np.linalg.norm(vb)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(va, vb) / (norm_a * norm_b))

    def softmax(self, x: List[float]) -> List[float]:
        arr = np.array(x)
        arr = arr - np.max(arr)
        exp = np.exp(arr)
        return (exp / np.sum(exp)).tolist()

    def extract_content_http(self, url: str, claim_embedding: List[float]) -> Dict[str, Any]:
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            if resp.status_code >= 400 or not resp.text:
                return {
                    "snippet": "No content found",
                    "similarity": 0.0,
                    "screenshot_b64": None,
                    "url_with_text_fragment": url
                }
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = [normalize_whitespace(p.get_text(" ")) for p in soup.find_all("p")]
            texts = [t for t in paragraphs if len(t) >= 30]
            if not texts:
                return {
                    "snippet": "No content found",
                    "similarity": 0.0,
                    "screenshot_b64": None,
                    "url_with_text_fragment": url
                }
            text_embeddings = self.embedding_model.encode(texts).tolist()
            sims = [self.cosine_similarity(claim_embedding, emb) for emb in text_embeddings]
            idx = int(np.argmax(sims))
            best_text = texts[idx]
            best_sim = float(sims[idx])
            text_fragment = self.create_text_fragment_url(url, best_text)
            return {
                "snippet": best_text,
                "similarity": best_sim,
                "screenshot_b64": None,
                "url_with_text_fragment": text_fragment
            }
        except Exception:
            return {
                "snippet": "No content found",
                "similarity": 0.0,
                "screenshot_b64": None,
                "url_with_text_fragment": url
            }

    async def verify_claim(self, claim_text: str, max_sources: int = 1) -> Dict[str, Any]:
        claim = normalize_whitespace(claim_text)
        entities = self.extract_entities(claim)
        
        if not entities:
            entities = [claim]
        
        plan = self.build_llm_plan(claim)
        if plan:
            site_filters = [s for s in plan.get('site_filters', []) if isinstance(s, str) and s.startswith('site:')][:20]
            queries = plan.get('query_variants', [])
            queries.append(claim)
        else:
            site_filters = []
            queries = [claim]
        
        all_candidates = []
        search_queries = list(dict.fromkeys(
            [q.strip() for q in queries if q.strip()] +
            [f"{q} {sf}" for q in queries for sf in site_filters]
        ))[:20]
        
        for query in search_queries:
            candidates = await asyncio.get_running_loop().run_in_executor(
                None, self.search_web, query, 5
            )
            all_candidates.extend(candidates)
            await asyncio.sleep(0.2)
        
        seen_urls = set()
        scored_candidates = []
        for candidate in all_candidates:
            url = candidate['url']
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            score = self.score_relevance(candidate, entities)
            if score > 0.1:
                candidate['relevance_score'] = score
                scored_candidates.append(candidate)
        
        scored_candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        if not scored_candidates:
            return {
                "verdict": "Unclear", 
                "confidence": 0.0,
                "sources": []
            }
        
        claim_embedding = self.embedding_model.encode([claim]).tolist()[0]
        sources = []
        
        page = await self.get_or_create_page()
        
        for candidate in scored_candidates[:max_sources]:
            try:
                url = candidate['url']
                if page:
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    content_result = await self.extract_content(page, claim_embedding, claim)
                    title = await page.title()
                else:
                    content_result = self.extract_content_http(url, claim_embedding)
                    title = candidate.get('title', '')
                
                parsed_url = tldextract.extract(url)
                domain = parsed_url.registered_domain
                
                source = {
                    "url": url,
                    "domain": domain,
                    "title": normalize_whitespace(title),
                    "published_at": None,
                    "snippet": content_result["snippet"],
                    "screenshot_b64": content_result.get("screenshot_b64"),
                    "url_with_text_fragment": content_result["url_with_text_fragment"],
                    "similarity": content_result["similarity"],
                    "entailment_score": None
                }
                
                if self.nli_model and source["snippet"] and len(source["snippet"]) > 20:
                    try:
                        scores = self.nli_model.predict([(claim, source["snippet"])])[0]
                        probs = self.softmax(scores)
                        entail_prob = float(probs[-1])
                        source["entailment_score"] = entail_prob
                    except Exception:
                        pass
                
                sources.append(source)
                
            except Exception:
                continue
        
        if not sources:
            return {
                "verdict": "Unclear",
                "confidence": 0.0, 
                "sources": []
            }
        
        avg_similarity = sum(s["similarity"] for s in sources) / len(sources)
        entail_scores = [s["entailment_score"] for s in sources if s.get("entailment_score") is not None]
        max_entail = max(entail_scores) if entail_scores else 0.0
        
        confidence = min(0.98, max(0.0, 0.7 * max_entail + 0.3 * avg_similarity))
        
        if max_entail >= 0.65 and avg_similarity >= 0.3:
            verdict = "Supported"
        elif avg_similarity < 0.2 and max_entail < 0.4:
            verdict = "Contradicted"
        else:
            verdict = "Unclear"
        
        return {
            "verdict": verdict,
            "confidence": float(confidence),
            "sources": sources
        }