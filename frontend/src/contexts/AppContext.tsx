// WHY: Auto-detect backend connectivity. DEMO mode when Docker is down.
//      Language state for i18n (EN/JA). Persisted in localStorage.
// INTERVIEW: "Same Context API pattern as P1 — design system consistency."

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { translations, type Language, type Translations } from '../i18n/translations';

interface AppState {
  isDemo: boolean;
  serverStatus: 'checking' | 'connected' | 'disconnected';
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const AppContext = createContext<AppState>({
  isDemo: true,
  serverStatus: 'checking',
  language: 'en',
  setLanguage: () => {},
  t: translations.en,
});

export function useApp() {
  return useContext(AppContext);
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [isDemo, setIsDemo] = useState(true);
  const [serverStatus, setServerStatus] = useState<AppState['serverStatus']>('checking');
  const [language, setLanguageState] = useState<Language>(
    () => (localStorage.getItem('fieldops-lang') as Language) || 'en'
  );

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('fieldops-lang', lang);
  };

  const t = translations[language];

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/health', { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          setIsDemo(false);
          setServerStatus('connected');
        } else {
          setIsDemo(true);
          setServerStatus('disconnected');
        }
      } catch {
        setIsDemo(true);
        setServerStatus('disconnected');
      }
    };
    check();
  }, []);

  return (
    <AppContext.Provider value={{ isDemo, serverStatus, language, setLanguage, t }}>
      {children}
    </AppContext.Provider>
  );
}
