import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useUIState, useUIActions } from '@/store/useStore';
import { Button } from '@/components/ui/Button';
import { 
  Search,
  Home,
  BookOpen,
  Menu,
  X,
  Headphones
} from 'lucide-react';
import { clsx } from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  title = 'PodSearch AI'
}) => {
  const pathname = usePathname();
  const ui = useUIState();
  const { setSidebarOpen } = useUIActions();

  const navigation = [
    { name: 'Home', href: '/', icon: Home, current: pathname === '/' },
    { name: 'Search', href: '/search', icon: Search, current: pathname === '/search' },
    { name: 'Saved', href: '/saved', icon: BookOpen, current: pathname === '/saved' },
  ];


  return (
    <div className={clsx('min-h-screen bg-gray-50', ui.theme === 'dark' && 'dark')}>
      <div className={clsx(
        'fixed inset-0 z-50 lg:hidden',
        ui.sidebarOpen ? 'block' : 'hidden'
      )}>
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-72 flex-col bg-white shadow-2xl">
          <div className="flex h-20 items-center justify-between px-6 border-b border-gray-100">
            <div className="flex items-center">
              <div className="bg-primary-100 p-2 rounded-xl mr-3">
                <Headphones className="h-6 w-6 text-primary-600" />
              </div>
              <span className="text-xl font-bold text-gray-900">PodSearch</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="rounded-xl p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <nav className="flex-1 space-y-2 px-4 py-6">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  'group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all',
                  item.current
                    ? 'bg-primary-600 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                )}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon
                  className={clsx(
                    'mr-3 h-5 w-5',
                    item.current
                      ? 'text-white'
                      : 'text-gray-500 group-hover:text-gray-700'
                  )}
                />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-72 lg:flex-col">
        <div className="flex flex-grow flex-col overflow-y-auto bg-white border-r border-gray-200 shadow-sm">
          <div className="flex h-20 items-center px-6 border-b border-gray-100">
            <div className="bg-primary-100 p-2 rounded-xl mr-3">
              <Headphones className="h-6 w-6 text-primary-600" />
            </div>
            <span className="text-xl font-bold text-gray-900">PodSearch</span>
          </div>
          <nav className="flex-1 space-y-2 px-4 py-6">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  'group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all',
                  item.current
                    ? 'bg-primary-600 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <item.icon
                  className={clsx(
                    'mr-3 h-5 w-5',
                    item.current
                      ? 'text-white'
                      : 'text-gray-500 group-hover:text-gray-700'
                  )}
                />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      <div className="lg:pl-72 flex flex-col flex-1">
        <div className="sticky top-0 z-40 flex h-16 bg-white/80 backdrop-blur-lg border-b border-gray-200">
          <button
            type="button"
            className="px-4 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="flex flex-1 justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex flex-1 items-center">
              <h1 className="text-xl font-bold text-gray-900">{title}</h1>
            </div>
          </div>
        </div>

        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}; 