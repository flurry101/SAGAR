import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { APIResponse } from '../types/api';
import { mockAdapter } from '../api/mock/mockAdapter';
import { sanitizeSagarText } from '../utils/brand';
import { SupportedLocale, dynamicActivate, detectInitialLocale } from '../i18n/lingui';

export type AppView = 'landing' | 'chat' | 'conditions' | 'advisory' | 'vessel' | 'knowledge' | 'history' | 'auth';
export type AppLanguage = SupportedLocale;

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
  userProfile: { name: string; port: string; email?: string; userId?: string; preferred_language?: AppLanguage } | null;
  supabaseToken: string | null;
  isSosModalOpen: boolean;
  sessionId: string;
  threadId: string;

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
  setSosModalOpen: (open: boolean) => void;
  setAuthenticated: (
    auth: boolean,
    profile?: { name: string; port: string; email?: string; userId?: string; preferred_language?: AppLanguage },
    token?: string | null
  ) => void;
  setSessionId: (id: string) => void;
  setThreadId: (id: string) => void;
  voiceQuery: string | null;
  setVoiceQuery: (query: string | null) => void;
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

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      currentView: 'landing',
      selectedLanguage: detectInitialLocale(),
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
        home_port: 'Unspecified'
      },
      isAuthenticated: false,
      userProfile: null,
      supabaseToken: null,
      isSosModalOpen: false,
      sessionId: `sess-${Date.now()}`,
      threadId: `thread-${Date.now()}`,
      voiceQuery: null,

      setCurrentView: (view) => set({ currentView: view }),
      setVoiceQuery: (query) => set({ voiceQuery: query }),
      setLanguage: (lang) => {
        dynamicActivate(lang);
        set((state) => ({
          selectedLanguage: lang,
          userProfile: state.userProfile ? { ...state.userProfile, preferred_language: lang } : null,
        }));
      },
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
          origin: data.trip_context?.origin || 'Unknown',
          destination: data.trip_context?.destination_name || 'Unknown',
          departureTime: data.trip_context?.departure_time_iso || new Date().toISOString(),
          returnTime: data.trip_context?.expected_return_time_iso || data.trip_context?.return_time_iso || new Date().toISOString(),
          riskLevel: data.overall_risk_level || data.risk_evidence?.overall_risk_level || 'UNKNOWN',
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
      setSosModalOpen: (open) => set({ isSosModalOpen: open }),
      setAuthenticated: (auth, profile, token) => {
        if (profile?.preferred_language) {
          dynamicActivate(profile.preferred_language);
        }
        set({
          isAuthenticated: auth,
          userProfile: profile || null,
          selectedLanguage: profile?.preferred_language || get().selectedLanguage,
          supabaseToken: token || null,
        });
      },
      setSessionId: (id) => set({ sessionId: id }),
      setThreadId: (id) => set({ threadId: id }),
    }),
    {
      name: 'sagar_app_store',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        userProfile: state.userProfile,
        supabaseToken: state.supabaseToken,
        currentView: state.currentView,
        userVessel: state.userVessel,
        sessionId: state.sessionId,
        threadId: state.threadId,
      }),
    }
  )
);
