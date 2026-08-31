import React from 'react';
import { VesselForm } from '../components/vessel/VesselForm';

export const VesselProfilePage: React.FC = () => {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <VesselForm />
    </main>
  );
};
