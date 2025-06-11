from typing import List, Optional, Dict, Any
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate

from ..models.youtube import YouTubeVideo, TranscriptResponse

class RAGService:
    def __init__(self):
        """Initialize the RAG service with LangChain components."""
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        self.vector_store = None
        self.qa_chain = None
        
    def chunking(self, document: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Split document text into chunks for processing.
        
        Args:
            document: The text content to be chunked
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects with chunked text
        """
        if not document or not document.strip():
            return []
            
        text_chunks = self.text_splitter.split_text(document)
        
        documents = []
        for i, chunk in enumerate(text_chunks):
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({
                "chunk_id": i,
                "chunk_size": len(chunk)
            })
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
            
        return documents

    def embedding(self, documents: List[Document]) -> List[Document]:
        """
        Create embeddings for document chunks.
        Note: LangChain handles embeddings internally when adding to vector store.
        This method validates and returns documents ready for vector storage.
        
        Args:
            documents: List of Document objects to embed
            
        Returns:
            List of validated Document objects
        """
        if not documents:
            return []
            
        # Validate documents have content
        valid_documents = [doc for doc in documents if doc.page_content.strip()]
        
        return valid_documents

    def vector_store(self, documents: List[Document], collection_name: str = "podcast_search") -> Chroma:
        """
        Store document embeddings in a vector database.
        
        Args:
            documents: List of Document objects to store
            collection_name: Name for the vector store collection
            
        Returns:
            Chroma vector store instance
        """
        if not documents:
            raise ValueError("No documents provided for vector storage")
            
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory="./chroma_db"
        )
        
        self._setup_qa_chain()
        
        return self.vector_store
    
    def _setup_qa_chain(self):
        """Setup the QA chain for querying the vector store."""
        if not self.vector_store:
            return
            
        prompt_template = """You are an AI assistant helping users find information from podcast and video transcripts. 
        Use the following context to answer the question. If you cannot find the answer in the context, say so clearly.
        
        Context: {context}
        
        Question: {question}
        
        Answer: """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            question: The question to ask
            
        Returns:
            Dictionary containing answer and source documents
        """
        if not self.qa_chain:
            raise ValueError("Vector store not initialized. Call vector_store() first.")
            
        result = self.qa_chain({"query": question})
        
        return {
            "answer": result["result"],
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result["source_documents"]
            ]
        }
    
    def add_youtube_video(self, video: YouTubeVideo, transcript: str) -> bool:
        """
        Process a YouTube video and add it to the vector store.
        
        Args:
            video: YouTubeVideo object with metadata
            transcript: Video transcript text
            
        Returns:
            True if successfully processed
        """
        try:
            metadata = {
                "video_id": video.id,
                "title": video.title,
                "uploader": video.uploader,
                "duration": video.duration,
                "url": video.url,
                "upload_date": video.upload_date,
                "source_type": "youtube_video"
            }
            
            chunks = self.chunking(transcript, metadata)
            embedded_docs = self.embedding(chunks)
            
            if embedded_docs:
                if self.vector_store is None:
                    # Create new vector store
                    self.vector_store(embedded_docs)
                else:
                    # Add to existing vector store
                    self.vector_store.add_documents(embedded_docs)
                    
                return True
            return False
            
        except Exception as e:
            print(f"Error processing YouTube video: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Perform similarity search without LLM processing.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        if not self.vector_store:
            return []
            
        docs = self.vector_store.similarity_search(query, k=k)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]
