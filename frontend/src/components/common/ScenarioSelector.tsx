import React from 'react';
import { useAppStore } from '../../state/appStore';
import { DEMO_SCENARIOS } from '../../api/mock/scenarios';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export const ScenarioSelector: React.FC = () => {
  const { selectedScenarioId, setScenario, setActiveAssessment } = useAppStore();

  const handleSelectScenario = (id: string) => {
    setScenario(id);
    const mockData = DEMO_SCENARIOS[id]?.mockResponse;
    if (mockData) {
      setActiveAssessment(mockData);
    }
  };

  // Scenario buttons replace real assessments with fixture data. They must not
  // be offered when the application is configured for the live backend.
  if (import.meta.env.VITE_USE_MOCK_API === 'false') return null;

  return (
    <div className="bg-sagar-canvasAlt/90 backdrop-blur-md border-y border-sagar-borderLight px-4 py-2.5 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-2.5">
        <div className="flex items-center gap-2 text-sky-900 font-extrabold shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-sky-600" />
          <span>Operational Scenario Testbed:</span>
        </div>
        <div className="flex flex-wrap items-center gap-2 max-w-full">
          {Object.values(DEMO_SCENARIOS).map((sc) => {
            const isSelected = sc.id === selectedScenarioId;
            return (
              <motion.button
                key={sc.id}
                whileHover={{ y: -1, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleSelectScenario(sc.id)}
                title={sc.description}
                className={`px-3.5 py-1.5 rounded-full text-[11px] font-bold transition-all border cursor-pointer ${
                  isSelected
                    ? 'bg-sky-600 text-white border-sky-600 shadow-soft-sm'
                    : 'bg-white text-sagar-navy border-sagar-border hover:bg-sagar-powder/60 shadow-soft-xs'
                }`}
              >
                {sc.badge}
              </motion.button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
