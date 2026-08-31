import { create } from 'zustand';
import { APIResponse } from '../types/api';
import { mockAdapter } from '../api/mock/mockAdapter';
import { sanitizeSagarText } from '../utils/brand';

export type AppView = 'landing' | 'chat' | 'advisory' | 'vessel' | 'knowledge' | 'history' | 'auth';
export type AppLanguage = 'en' | 'hi' | 'ta' | 'te' | 'kn' | 'ml' | 'bn' | 'mr' | 'gu' | 'pa' | 'or';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'sagar';
  text: string;
  timestamp: string;
  missingFields?: any[];
  isClarification?: boolean;
}

export interface HistoricalAssessment {
  id: string;
  timestamp: string;
  origin: string;
  destination: string;
  departureTime: string;
  returnTime: string;
  riskLevel: string;
  advisoryText: string;
  assessmentData: APIResponse;
}

interface AppState {
  currentView: AppView;
  selectedLanguage: AppLanguage;
  selectedScenarioId: string;
  activeAssessment: APIResponse | null;
  selectedRouteCandidateId: string | null;
  chatHistory: ChatMessage[];
  assessmentHistory: HistoricalAssessment[];
  isOffline: boolean;
  selectedWaypointIndex: number | null;
  userVessel: any | null;
  isAuthenticated: boolean;
  userProfile: { name: string; port: string; email?: string; userId?: string } | null;
  supabaseToken: string | null;

  // Actions
  setCurrentView: (view: AppView) => void;
  setLanguage: (lang: AppLanguage) => void;
  setScenario: (scenarioId: string) => void;
  setActiveAssessment: (assessment: APIResponse | null) => void;
  setSelectedRouteCandidateId: (routeId: string | null) => void;
  addChatMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  clearChatHistory: () => void;
  addToHistory: (assessment: APIResponse) => void;
  clearHistory: () => void;
  setIsOffline: (offline: boolean) => void;
  setSelectedWaypointIndex: (idx: number | null) => void;
  setUserVessel: (vessel: any) => void;
  setAuthenticated: (
    auth: boolean,
    profile?: { name: string; port: string; email?: string; userId?: string },
    token?: string | null
  ) => void;
}

const loadStoredHistory = (): HistoricalAssessment[] => {
  try {
    const saved = localStorage.getItem('sagar_assessment_history');
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

const saveStoredHistory = (history: HistoricalAssessment[]) => {
  try {
    localStorage.setItem('sagar_assessment_history', JSON.stringify(history));
  } catch {
    // ignore
  }
};

export const useAppStore = create<AppState>((set, get) => ({
  currentView: 'landing',
  selectedLanguage: 'en',
  selectedScenarioId: 'SCENARIO_3_SEVERE_RETURN',
  activeAssessment: null,
  selectedRouteCandidateId: null,
  chatHistory: [],
  assessmentHistory: loadStoredHistory(),
  isOffline: typeof navigator !== 'undefined' ? !navigator.onLine : false,
  selectedWaypointIndex: null,
  userVessel: {
    vessel_id: 'vessel-trawler-45',
    vessel_type: 'Mechanized Trawler',
    beam_width_m: 4.5,
    length_m: 14.5,
    cruising_speed_kmh: 15.0,
    registration_number: 'IND-KA-04-MM-8821',
    home_port: 'Mangalore Old Port'
  },
  isAuthenticated: true,
  userProfile: { name: 'Fisher Ravi Kumar', port: 'Mangalore Old Port', email: 'ravi.kumar@sagar.marine' },
  supabaseToken: null,

  setCurrentView: (view) => set({ currentView: view }),
  setLanguage: (lang) => set({ selectedLanguage: lang }),
  setScenario: (scenarioId) => {
    mockAdapter.setActiveScenario(scenarioId);
    set({ selectedScenarioId: scenarioId });
  },
  setActiveAssessment: (assessment) => {
    const defaultRoute = assessment?.data?.route_candidates?.[0]?.route_id || null;
    set({ activeAssessment: assessment, selectedRouteCandidateId: defaultRoute });
    if (assessment && assessment.status === 'success') {
      get().addToHistory(assessment);
    }
  },
  setSelectedRouteCandidateId: (routeId) => set({ selectedRouteCandidateId: routeId }),
  addChatMessage: (msg) =>
    set((state) => ({
      chatHistory: [
        ...state.chatHistory,
        {
          ...msg,
          text: sanitizeSagarText(msg.text),
          id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ],
    })),
  clearChatHistory: () => set({ chatHistory: [] }),
  addToHistory: (assessment) => {
    const data = assessment.data;
    if (!data) return;

    const newEntry: HistoricalAssessment = {
      id: data.trip_id || `hist-${Date.now()}`,
      timestamp: new Date().toISOString(),
      origin: data.trip_context?.origin || 'Mangalore Port',
      destination: data.trip_context?.destination_type === 'NEAREST_PFZ' ? 'Nearest PFZ' : 'Target Fishing Ground',
      departureTime: data.trip_context?.departure_time_iso || new Date().toISOString(),
      returnTime: data.trip_context?.expected_return_time_iso || new Date().toISOString(),
      riskLevel: data.overall_risk_level || data.risk_evidence?.overall_risk_level || 'SAFE',
      advisoryText: sanitizeSagarText(data.advisory?.recommendation_text) || 'Assessment completed.',
      assessmentData: assessment,
    };

    set((state) => {
      const filtered = state.assessmentHistory.filter((h) => h.id !== newEntry.id);
      const updated = [newEntry, ...filtered].slice(0, 20);
      saveStoredHistory(updated);
      return { assessmentHistory: updated };
    });
  },
  clearHistory: () => {
    saveStoredHistory([]);
    set({ assessmentHistory: [] });
  },
  setIsOffline: (offline) => set({ isOffline: offline }),
  setSelectedWaypointIndex: (idx) => set({ selectedWaypointIndex: idx }),
  setUserVessel: (vessel) => set({ userVessel: vessel }),
  setAuthenticated: (auth, profile, token) =>
    set({
      isAuthenticated: auth,
      userProfile: profile || null,
      supabaseToken: token || null,
    }),
}));
