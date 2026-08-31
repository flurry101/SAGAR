import React from 'react';
import { ChatInterface } from '../components/chat/ChatInterface';
import { ScenarioSelector } from '../components/common/ScenarioSelector';

export const TripPlannerPage: React.FC = () => {
  return (
    <div className="space-y-2">
      <ScenarioSelector />
      <TripPlannerPageContent />
    </div>
  );
};

const TripPlannerPageContent: React.FC = () => {
  return (
    <main className="py-2">
      <ChatInterface />
    </main>
  );
};
