import React, { useState } from 'react';
import { VesselForm } from '../components/vessel/VesselForm';
import { OperatorProfileForm } from '../components/profile/OperatorProfileForm';
import { User, Ship } from 'lucide-react';

export const VesselProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'operator' | 'vessel'>('operator');

  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Profile Navigation Tabs */}
      <div className="flex justify-center">
        <div className="inline-flex bg-sagar-canvasAlt p-1.5 rounded-2xl border border-sagar-borderLight shadow-soft-sm">
          <button
            type="button"
            onClick={() => setActiveTab('operator')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all cursor-pointer ${
              activeTab === 'operator'
                ? 'bg-white text-sky-900 shadow-soft-sm border border-sagar-border/60'
                : 'text-slate-500 hover:text-sagar-navy'
            }`}
          >
            <User className="w-4 h-4 text-sky-600" />
            <span>Operator Identity</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('vessel')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all cursor-pointer ${
              activeTab === 'vessel'
                ? 'bg-white text-sky-900 shadow-soft-sm border border-sagar-border/60'
                : 'text-slate-500 hover:text-sagar-navy'
            }`}
          >
            <Ship className="w-4 h-4 text-sky-600" />
            <span>Vessel Specifications</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'operator' ? <OperatorProfileForm /> : <VesselForm />}
      </div>
    </main>
  );
};

