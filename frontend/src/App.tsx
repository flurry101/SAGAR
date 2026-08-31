import React from 'react';
import { useAppStore } from './state/appStore';
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
import { motion, AnimatePresence } from 'framer-motion';

export function App() {
  const { currentView } = useAppStore();

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
    </div>
  );
}

export default App;
