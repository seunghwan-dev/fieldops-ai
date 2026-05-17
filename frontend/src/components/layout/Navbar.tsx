import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Upload, Search, Zap, Moon, Sun, Wifi, WifiOff, Globe } from 'lucide-react';
import { useApp } from '../../contexts/AppContext';

export default function Navbar() {
  const { isDemo, language, setLanguage, t } = useApp();

  const tabs = [
    { to: '/knowledge', label: t.nav.knowledge, icon: Upload },
    { to: '/search', label: t.nav.search, icon: Search },
    { to: '/fusion', label: t.nav.fusion, icon: Zap },
  ];

  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('fieldops-dark') === 'true';
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('fieldops-dark', String(dark));
  }, [dark]);

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <NavLink to="/knowledge" className="text-lg font-bold text-gray-900 dark:text-white mr-8">
          FieldOps-AI
        </NavLink>

        <div className="flex items-center gap-1">
          {tabs.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`
              }
            >
              <Icon size={16} />
              <span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setLanguage(language === 'en' ? 'ja' : 'en')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                       text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Toggle language"
          >
            <Globe size={14} />
            <span>{language === 'en' ? 'EN' : 'JA'}</span>
          </button>

          <span
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              isDemo
                ? 'bg-amber-500/15 text-amber-500 border-amber-500/20'
                : 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20'
            }`}
          >
            {isDemo ? <WifiOff size={13} /> : <Wifi size={13} />}
            <span>{isDemo ? 'DEMO' : 'LIVE'}</span>
            <span
              className={`w-2 h-2 rounded-full ${
                isDemo ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'
              }`}
            />
          </span>

          <button
            onClick={() => setDark(!dark)}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Toggle dark mode"
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>
    </nav>
  );
}
