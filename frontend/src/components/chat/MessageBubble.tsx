import React from 'react';
import { ChatMessage } from '../../state/appStore';
import { User, Anchor } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';
import { motion } from 'framer-motion';

interface Props {
  message: ChatMessage;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-sagar-powder border border-sky-200 flex items-center justify-center text-sky-700 shrink-0 mt-0.5 shadow-soft-sm">
          <Anchor className="w-4 h-4" />
        </div>
      )}

      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm space-y-1.5 shadow-soft-sm border ${
          isUser
            ? 'bg-sky-600 border-sky-600 text-white rounded-br-none'
            : 'bg-white border-sagar-border text-sagar-navy rounded-bl-none'
        }`}
      >
        <div className="flex items-center justify-between gap-4 text-[10px] font-medium">
          <span className={`font-bold ${isUser ? 'text-sky-100' : 'text-sky-800'}`}>
            {isUser ? 'You' : 'SAGAR Safety Decision Support'}
          </span>
          <span className={`font-mono ${isUser ? 'text-sky-200' : 'text-slate-500'}`}>{message.timestamp}</span>
        </div>

        <p className="leading-relaxed whitespace-pre-wrap font-normal">{sanitizeSagarText(message.text)}</p>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-sagar-navy text-white flex items-center justify-center shrink-0 mt-0.5 shadow-soft-sm">
          <User className="w-4 h-4" />
        </div>
      )}
    </motion.div>
  );
};
