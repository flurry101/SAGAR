import React, { useEffect } from 'react';
import { useAppStore } from './state/appStore';
import { initAuthListener } from './api/supabaseClient';
import { userApi } from './api/userApi';
import { API_BASE_URL } from './api/client';
import { Header } from './components/layout/Header';
import { OfflineBanner } from './components/layout/OfflineBanner';
import { OceanBackground } from './components/common/OceanBackground';
import { LandingPage } from './pages/LandingPage';
import { TripPlannerPage } from './pages/TripPlannerPage';
import { AdvisoryPage } from './pages/AdvisoryPage';
import { VesselProfilePage } from './pages/VesselProfilePage';
import { KnowledgeChatPage } from './pages/KnowledgeChatPage';
import { AssessmentHistoryPage } from './pages/AssessmentHistoryPage';
import { AuthPage } from './pages/AuthPage';
import { VoiceWidget } from './components/VoiceAssistant/VoiceWidget';
import { SosEmergencyModal } from './components/common/SosEmergencyModal';
import { motion, AnimatePresence } from 'framer-motion';

export function App() {
  const { currentView, setAuthenticated, setCurrentView, isSosModalOpen, setSosModalOpen } = useAppStore();

  // ── Handle backend OAuth redirect using a one-time auth code exchange ─
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const authCode = params.get('auth_code');
    const authError = params.get('auth_error');

    if (authError) {
      console.error('OAuth error:', authError);
      window.history.replaceState({}, '', window.location.pathname);
      return;
    }

    if (!authCode) {
      return;
    }

    let cancelled = false;

    const exchangeCode = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/exchange`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: authCode }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data?.detail || 'Authentication exchange failed');
        }

        const authToken = data?.auth_token;
        const authName = data?.auth_name || '';
        const authEmail = data?.auth_email || '';
        const authUserId = data?.auth_user_id || '';

        if (!authToken) {
          throw new Error('No authenticated session token returned by the server');
        }

        if (cancelled) return;

        setAuthenticated(
          true,
          { name: authName, port: '', email: authEmail, userId: authUserId },
          authToken
        );
        setCurrentView('chat');

        const meRes: any = await userApi.getCurrentUser();
        if (!cancelled && meRes?.status === 'success' && meRes.data) {
          setAuthenticated(
            true,
            {
              name: meRes.data.name || authName,
              port: meRes.data.home_port || '',
              email: meRes.data.email || authEmail,
              userId: meRes.data.user_id || authUserId,
            },
            authToken
          );
        }
      } catch (error: any) {
        console.error('OAuth code exchange failed:', error);
        if (!cancelled) {
          setAuthenticated(false, undefined, null);
        }
      } finally {
        if (!cancelled) {
          window.history.replaceState({}, '', window.location.pathname);
        }
      }
    };

    exchangeCode();
    return () => {
      cancelled = true;
    };
  }, [setAuthenticated, setCurrentView]);

  // ── Supabase auth-state listener (handles Supabase OAuth redirect) ─
  useEffect(() => {
    const unsubscribe = initAuthListener();
    return () => {
      unsubscribe?.();
    };
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingPage />;
      case 'chat':
        return <TripPlannerPage />;
      case 'advisory':
        return <AdvisoryPage />;
      case 'vessel':
        return <VesselProfilePage />;
      case 'knowledge':
        return <KnowledgeChatPage />;
      case 'history':
        return <AssessmentHistoryPage />;
      case 'auth':
        return <AuthPage />;
      default:
        return <LandingPage />;
    }
  };

  return (
    <div className="relative min-h-screen max-w-full overflow-x-clip bg-sagar-canvas text-sagar-textDark flex flex-col font-sans selection:bg-sky-200 selection:text-sky-950">
      <OceanBackground />
      <OfflineBanner />
      <Header />
      <main className="relative z-10 flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </main>
      <VoiceWidget />
      <SosEmergencyModal
        isOpen={isSosModalOpen}
        onClose={() => setSosModalOpen(false)}
      />
    </div>
  );
}

export default App;
