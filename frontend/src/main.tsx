import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { I18nProvider } from '@lingui/react';
import { i18n, dynamicActivate, detectInitialLocale } from './i18n/lingui';
import App from './App.tsx';
import './index.css';

const Root: React.FC = () => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const initLocale = detectInitialLocale();
    dynamicActivate(initLocale).finally(() => {
      setReady(true);
    });
  }, []);

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-sagar-canvas text-sagar-navy">
        <div className="flex flex-col items-center gap-3">
          <img src="/sagar-logo.png" alt="SAGAR" className="w-14 h-14 object-contain animate-pulse" />
          <div className="w-6 h-6 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-bold text-slate-500">Initializing SAGAR Multi-Language...</p>
        </div>
      </div>
    );
  }

  return (
    <I18nProvider i18n={i18n}>
      <App />
    </I18nProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
);
