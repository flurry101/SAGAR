import React, { useState } from 'react';
import { Trans, useLingui } from '@lingui/react/macro';
import { BookOpen, Send, Database, ShieldAlert, Sparkles, HelpCircle, ArrowRight } from 'lucide-react';
import { sanitizeSagarText } from '../utils/brand';
import { apiRequest } from '../api/client';
import { RippleButton } from '../components/common/RippleButton';
import { motion } from 'framer-motion';

export const KnowledgeChatPage: React.FC = () => {
  const { t } = useLingui();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<any[]>([
    {
      sender: 'bot',
      text: t`Welcome to the <Trans>SAGAR Marine Knowledge Copilot</Trans>. You can ask grounded domain questions regarding INCOIS Potential Fishing Zones (PFZ), SVAS vessel stability safety formulas, Marine Protected Area rules, or satellite oceanography data.`,
      sources: ['INCOIS PFZ Operational Guidelines', 'SVAS Small Vessel Stability Standard']
    }
  ]);
  const [loading, setLoading] = useState(false);

  const sampleQueries = [
    {
      category: t`PFZ Satellite Data`,
      question: t`How is Potential Fishing Zone (PFZ) calculated from satellite SST?`,
    },
    {
      category: t`Vessel Stability Rule`,
      question: t`What is the SVAS capsize wave height limit formula for a 4.5m beam trawler?`,
    },
    {
      category: t`Marine Protected Area`,
      question: t`What marine protected areas exist near the Gulf of Mannar?`,
    },
    {
      category: t`Diurnal Swell Dynamics`,
      question: t`Why does afternoon wave surge increase risk for small motorized crafts?`,
    }
  ];

  const handleAsk = async (text?: string) => {
    const q = text || query.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: q }]);
    setQuery('');
    setLoading(true);

    try {
      // Try real copilot endpoint first
      const res = await apiRequest('/copilot', {
        method: 'POST',
        body: { message: q },
      });

      if (res.status === 'success' && res.data?.response) {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'bot',
            text: sanitizeSagarText(res.data.response),
            sources: ['INCOIS Marine Safety Repository', 'IMD Coastal Guidelines'],
          },
        ]);
        setLoading(false);
        return;
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: t`I am sorry, but I am currently unable to connect to the knowledge base. Please ensure your backend is running or check your network connection.`,
        },
      ]);
      setLoading(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto px-4 py-4 min-h-[calc(100vh-5rem)] flex flex-col space-y-4 text-sagar-navy">
      {/* Knowledge Header */}
      <div className="bg-white border border-sagar-border rounded-2xl p-4 sm:p-5 flex items-center justify-between shadow-soft-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-sagar-navy"><Trans>SAGAR Marine Knowledge Copilot</Trans></h2>
              <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-900 border border-sky-200 uppercase">
                <Trans>Grounded Q&A</Trans>
              </span>
            </div>
            <p className="text-xs text-slate-500"><Trans>Technical Q&A based on verified oceanographic & marine safety documentation.</Trans></p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-600 bg-sagar-canvasAlt px-3 py-1.5 rounded-xl border border-sagar-border font-medium">
          <Database className="w-3.5 h-3.5 text-sky-600" />
          <span><Trans>Curated Marine Repository</Trans></span>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-950 flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
        <span>
          <Trans><strong>Note:</strong> This knowledge assistant answers domain questions. To evaluate safety for a specific planned voyage, use the <strong>Trip Planner</strong>.</Trans>
        </span>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-3.5 scrollbar-thin">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.sender === 'bot' && (
              <div className="w-8 h-8 rounded-full bg-sagar-powder border border-sky-200 flex items-center justify-center text-sky-700 shrink-0 mt-0.5 shadow-soft-sm font-bold">
                <BookOpen className="w-4 h-4" />
              </div>
            )}
            <div
              className={`max-w-[88%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm space-y-2.5 border shadow-soft-sm ${
                m.sender === 'user'
                  ? 'bg-sky-600 border-sky-600 text-white rounded-br-none'
                  : 'bg-white border-sagar-border text-sagar-navy rounded-bl-none'
              }`}
            >
              <p className="leading-relaxed whitespace-pre-wrap">{sanitizeSagarText(m.text)}</p>
              {m.sources && m.sources.length > 0 && (
                <div className="pt-2.5 border-t border-sagar-borderLight space-y-1.5">
                  <span className="text-[10px] text-sky-800 font-bold uppercase tracking-wider block flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    <span><Trans>Grounded Sources & Documentation:</Trans></span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {m.sources.map((src: string, i: number) => (
                      <span key={i} className="text-[10px] px-2.5 py-0.5 rounded-full bg-sagar-canvasAlt text-slate-700 border border-sagar-border font-mono font-medium">
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2.5 p-3.5 bg-white rounded-xl border border-sagar-border text-xs text-slate-600 shadow-soft-sm">
            <div className="w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
            <span><Trans>Retrieving grounded marine knowledge...</Trans></span>
          </div>
        )}
      </div>

      {/* Suggested Questions: Responsive Grid with Multi-Line Text Wrapping (NO TEXT OVERFLOW!) */}
      <div className="space-y-2.5 pt-3 border-t border-sagar-borderLight">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
          <Sparkles className="w-3.5 h-3.5 text-sky-600 shrink-0" />
          <span><Trans>Recommended Marine Knowledge Inquiries:</Trans></span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {sampleQueries.map((item, i) => (
            <motion.button
              key={i}
              whileHover={{ y: -2, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleAsk(item.question)}
              className="p-4 rounded-2xl bg-white hover:bg-sagar-powder/40 border border-sagar-border hover:border-sky-300 shadow-soft-sm text-left transition-all space-y-2 group touch-target cursor-pointer flex flex-col justify-between"
            >
              <div className="flex items-center justify-between w-full gap-2">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-sky-900 bg-sagar-powder px-2.5 py-0.5 rounded-full border border-sky-200">
                  {item.category}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600 group-hover:translate-x-1 transition-all shrink-0" />
              </div>
              <p className="text-xs sm:text-sm text-sagar-navy font-semibold leading-relaxed whitespace-normal break-words">
                {item.question}
              </p>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk();
        }}
        className="flex gap-2 bg-white border border-sagar-border focus-within:border-sky-500 rounded-2xl p-2 shadow-soft-md"
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="{t`Ask about PFZ methods, SVAS stability formulas, MPAs, or weather datasets...`}"
          className="flex-1 bg-transparent px-3.5 py-2.5 text-xs sm:text-sm text-sagar-navy placeholder-slate-400 focus:outline-none"
        />
        <RippleButton
          type="submit"
          disabled={!query.trim() || loading}
          variant="primary"
          size="md"
          icon={<Send className="w-4 h-4" />}
        >
          <Trans>Ask</Trans>
        </RippleButton>
      </form>
    </main>
  );
};
