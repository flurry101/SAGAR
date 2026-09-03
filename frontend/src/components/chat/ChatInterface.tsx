import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../state/appStore';
import { tripApi } from '../../api/tripApi';
import { MessageBubble } from './MessageBubble';
import { ClarificationPrompt } from './ClarificationPrompt';
import { TripConfirmation } from '../trip/TripConfirmation';
import { AssessmentProgress } from '../trip/AssessmentProgress';
import { TripContext } from '../../types/trip';
import { Send, Navigation, Anchor, RefreshCw, AlertCircle, ShieldAlert } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';
import { motion } from 'framer-motion';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

export const ChatInterface: React.FC = () => {
  const { t } = useLingui();
  const {
    chatHistory,
    addChatMessage,
    setActiveAssessment,
    setCurrentView,
    userVessel,
    selectedLanguage,
    sessionId,
    threadId,
  } = useAppStore();

  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [needsClarification, setNeedsClarification] = useState(false);
  const [clarificationFields, setClarificationFields] = useState<any[]>([]);
  const [pendingConfirmation, setPendingConfirmation] = useState<Partial<TripContext> | null>(null);
  const [isAssessingSteps, setIsAssessingSteps] = useState(false);
  const [cachedResponse, setCachedResponse] = useState<any>(null);
  const [graphTimer, setGraphTimer] = useState<number>(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sampleInputs = [
    t`Leave at 5 AM from Mangalore to nearest PFZ and return by 2 PM`,
    t`Planning trip from Malpe at 6 AM, 4 hours fishing, return at 4 PM`,
    t`Departure 5 AM from Mangalore, return 6 PM with mechanized trawler (missing beam example)`
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, loading, pendingConfirmation, isAssessingSteps]);

  // Graph execution timer simulation
  useEffect(() => {
    let interval: any;
    if (loading) {
      setGraphTimer(0);
      interval = setInterval(() => {
        setGraphTimer((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSendMessage = async (textToSend?: string) => {
    const messageText = textToSend || inputMessage.trim();
    if (!messageText || loading) return;

    if (needsClarification) {
      handleClarificationResponse(messageText);
      setInputMessage('');
      return;
    }

    setPendingConfirmation(null);
    setIsAssessingSteps(false);

    // Add User Message
    addChatMessage({ sender: 'user', text: messageText });
    setInputMessage('');
    setLoading(true);

    try {
      const response = await tripApi.assessTrip({
        message: messageText,
        thread_id: threadId,
        session_id: sessionId,
        language: selectedLanguage,
        vessel_profile: userVessel || undefined,
      });

      if (response.status === 'needs_clarification') {
        setNeedsClarification(true);
        setClarificationFields(response.data?.task_plan?.missing_fields || []);
        const question = response.data?.task_plan?.clarification_question || 'I need a few missing parameters to safely evaluate your voyage:';
        addChatMessage({
          sender: 'sagar',
          text: question,
          isClarification: true,
        });
      } else if (response.status === 'insufficient_information') {
        setActiveAssessment(response);
        addChatMessage({
          sender: 'sagar',
          text: sanitizeSagarText(response.data?.recommendation_text) || t`Unable to assess safety due to missing vessel or trip parameters.`,
        });
        setCurrentView('advisory');
      } else if (response.data?.workflow_status === 'KNOWLEDGE_RESPONSE') {
        addChatMessage({
          sender: 'sagar',
          text: response.data?.advisory?.recommendation_text || 'This is a knowledge question. Use the ORCA Copilot for detailed answers.',
        });
      } else if (response.status === 'success') {
        setCachedResponse(response);
        const tripContext = response.data?.trip_context || {
          origin: 'Mangalore Port',
          destination_type: 'NEAREST_PFZ',
          departure_time_iso: '2026-08-30T05:00:00+05:30',
          expected_return_time_iso: '2026-08-30T14:00:00+05:30',
        };
        setPendingConfirmation(tripContext);
        addChatMessage({
          sender: 'sagar',
          text: t`I have extracted your 4D voyage schedule. Please review the departure, destination, and return timing below before beginning safety assessment.`,
        });
      } else if (response.status === 'error') {
        addChatMessage({
          sender: 'sagar',
          text: t`Assessment error: ${response.error?.message || 'Failed to complete safety assessment.'}`,
        });
      }
    } catch (err: any) {
      addChatMessage({
        sender: 'sagar',
        text: t`Network error encountered while connecting to SAGAR decision-support service.`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClarificationResponse = async (answerText: string) => {
    addChatMessage({ sender: 'user', text: answerText });
    setNeedsClarification(false);
    setLoading(true);

    try {
      const response = await tripApi.continueTrip({
        session_id: sessionId,
        message: answerText,
      });

      if (response.data?.workflow_status === 'KNOWLEDGE_RESPONSE') {
        addChatMessage({
          sender: 'sagar',
          text: response.data?.advisory?.recommendation_text || 'This is a knowledge question. Use the ORCA Copilot for detailed answers.',
        });
      } else if (response.status === 'success') {
        setCachedResponse(response);
        const tripContext = response.data?.trip_context || {
          origin: 'Mangalore Port',
          destination_type: 'NEAREST_PFZ',
          departure_time_iso: '2026-08-30T05:00:00+05:30',
          expected_return_time_iso: '2026-08-30T14:00:00+05:30',
        };
        setPendingConfirmation(tripContext);
        addChatMessage({
          sender: 'sagar',
          text: t`Missing details received. Please review your trip summary before starting safety evaluation.`,
        });
      } else if (response.status === 'needs_clarification') {
        setNeedsClarification(true);
        setClarificationFields(response.data?.task_plan?.missing_fields || []);
        const question = response.data?.task_plan?.clarification_question || 'I need a few missing parameters to safely evaluate your voyage:';
        addChatMessage({
          sender: 'sagar',
          text: question,
          isClarification: true,
        });
      } else if (response.status === 'insufficient_information') {
        setActiveAssessment(response);
        addChatMessage({
          sender: 'sagar',
          text: sanitizeSagarText(response.data?.recommendation_text) || 'Unable to assess safety due to missing vessel or trip parameters.',
        });
        setCurrentView('advisory');
      } else if (response.status === 'error') {
        addChatMessage({
          sender: 'sagar',
          text: `Assessment error: ${response.error?.message || 'Failed to complete safety assessment.'}`,
        });
      }
    } catch (err) {
      addChatMessage({
        sender: 'sagar',
        text: t`Failed to process clarification response.`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmTrip = () => {
    setPendingConfirmation(null);
    setIsAssessingSteps(true);
  };

  const handleProgressComplete = () => {
    if (cachedResponse) {
      setActiveAssessment(cachedResponse);
      const cat = cachedResponse.data?.advisory?.advisory_category || t`Assessment complete`;
      const text = sanitizeSagarText(cachedResponse.data?.advisory?.recommendation_text) || '';
      addChatMessage({
        sender: 'sagar',
        text: t`Analysis complete [${cat}]: ${text}`,
      });
      setCurrentView('advisory');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] max-w-4xl mx-auto px-4 py-3">
      {/* Header Info Bar */}
      <div className="bg-white border border-sagar-border rounded-2xl p-4 mb-3 flex items-center justify-between shadow-soft-sm">
        <div className="flex items-center gap-3">
          <img
            src="/sagar-logo.png"
            alt="SAGAR Logo"
            className="w-10 h-10 object-contain rounded-full shadow-soft-sm shrink-0"
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm sm:text-base font-bold text-sagar-navy"><Trans>SAGAR Spatio-Temporal Voyage Planner</Trans></h1>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-sagar-powder text-sky-800 border border-sky-200">
                <Trans>4D Safety Evaluation</Trans>
              </span>
            </div>
            <p className="text-xs text-slate-500">
              <Trans>Natural language voyage planning with vessel stability limits</Trans>
            </p>
          </div>
        </div>

        <button
          onClick={() => handleSendMessage(sampleInputs[0])}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sagar-canvasAlt hover:bg-sagar-powder text-sky-800 text-xs font-bold border border-sagar-border transition-colors touch-target"
        >
          <Navigation className="w-3.5 h-3.5" />
          <span><Trans>Quick Sample</Trans></span>
        </button>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-3.5 scrollbar-thin">
        {chatHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold shadow-soft-sm">
              <Navigation className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-sagar-navy mb-1"><Trans>Plan Your Voyage Safely</Trans></h2>
              <p className="text-xs max-w-md text-slate-600 leading-relaxed">
                <Trans>Specify your departure time, origin harbor, operational area, and expected return time. SAGAR evaluates sea state forecasts, geofencing, and capsize stability limits across every phase of your journey.</Trans>
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="w-full max-w-lg space-y-2.5 pt-2">
              <span className="text-[11px] font-extrabold text-slate-600 uppercase tracking-wider block text-left">
                <Trans>Sample Voyage Inquiries:</Trans>
              </span>
              <div className="space-y-2">
                {sampleInputs.map((sample, idx) => (
                  <motion.button
                    key={idx}
                    whileHover={{ y: -2, scale: 1.01 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSendMessage(sample)}
                    className="w-full text-left text-xs sm:text-sm bg-white hover:bg-sagar-powder/40 border border-sagar-border hover:border-sky-300 p-3.5 sm:p-4 rounded-2xl text-sagar-navy transition-all shadow-soft-sm touch-target font-semibold leading-relaxed cursor-pointer block break-words"
                  >
                    "{sample}"
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          chatHistory.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}

        {loading && (
          <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-sagar-border my-2 text-sagar-navy text-xs shadow-soft-sm">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-4 h-4 text-sky-600 animate-spin shrink-0" />
              <div>
                <span className="font-bold block"><Trans>SAGAR Decision Pipeline is executing...</Trans></span>
                <span className="text-[11px] text-slate-500">
                  <Trans>Retrieving marine sea-state forecasts & spatial geofences</Trans>
                </span>
              </div>
            </div>
            <span className="text-xs font-mono text-sky-800 font-bold bg-sagar-powder px-2.5 py-1 rounded-lg border border-sky-200">
              {graphTimer}s
            </span>
          </div>
        )}

        {needsClarification && (
          <ClarificationPrompt
            onProvideInfo={handleClarificationResponse}
            missingFields={clarificationFields}
          />
        )}

        {/* Stage 4: Trip Confirmation Review Card */}
        {pendingConfirmation && !isAssessingSteps && (
          <TripConfirmation
            tripContext={pendingConfirmation}
            vesselProfile={userVessel}
            onConfirm={handleConfirmTrip}
            onCancel={() => setPendingConfirmation(null)}
          />
        )}

        {/* Stage 5: Step-by-Step Progress Checklist */}
        {isAssessingSteps && (
          <AssessmentProgress onComplete={handleProgressComplete} />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="mt-2 pt-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex gap-2 bg-white border border-sagar-border focus-within:border-sky-500 rounded-2xl p-2 shadow-soft-md"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={t`Type your voyage details (e.g. Leave Mangalore 5 AM, return 2 PM)...`}
            className="flex-1 bg-transparent px-3.5 py-2.5 text-xs sm:text-sm text-sagar-navy placeholder-slate-400 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-4 sm:px-6 py-2.5 rounded-xl text-xs sm:text-sm flex items-center gap-2 disabled:opacity-40 transition-all shadow-soft-sm shrink-0 touch-target"
          >
            <span><Trans>Assess Voyage</Trans></span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
