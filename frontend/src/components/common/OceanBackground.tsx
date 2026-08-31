import React from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';

export const OceanBackground: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();
  const { scrollY } = useScroll();

  // Scroll parallax for ambient ocean glows
  const yGlow1 = useTransform(scrollY, [0, 1200], [0, 100]);
  const yGlow2 = useTransform(scrollY, [0, 1200], [0, -80]);
  const yGlow3 = useTransform(scrollY, [0, 1200], [0, 120]);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 select-none opacity-60" aria-hidden="true">
      {/* Soft Pastel Radial Glows with Scroll Drift */}
      <motion.div
        style={{ y: shouldReduceMotion ? 0 : yGlow1 }}
        className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-sagar-powder/50 blur-3xl"
      />
      <motion.div
        style={{ y: shouldReduceMotion ? 0 : yGlow2 }}
        className="absolute top-1/3 -left-32 w-80 h-80 rounded-full bg-sagar-seafoam/40 blur-3xl"
      />
      <motion.div
        style={{ y: shouldReduceMotion ? 0 : yGlow3 }}
        className="absolute -bottom-20 right-1/4 w-96 h-96 rounded-full bg-sagar-aqua/40 blur-3xl"
      />

      {/* Floating Subtle Marine Current Paths */}
      {!shouldReduceMotion && (
        <svg
          className="absolute inset-0 w-full h-full stroke-sky-300/30 fill-none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <motion.path
            d="M -100,200 C 300,100 600,350 1200,180 C 1500,100 1800,280 2100,200"
            strokeWidth="1.5"
            strokeDasharray="8 12"
            animate={{
              d: [
                "M -100,200 C 300,100 600,350 1200,180 C 1500,100 1800,280 2100,200",
                "M -100,220 C 320,130 580,320 1220,200 C 1480,120 1820,260 2100,220",
                "M -100,200 C 300,100 600,350 1200,180 C 1500,100 1800,280 2100,200",
              ],
            }}
            transition={{ duration: 24, repeat: Infinity, ease: 'easeInOut' }}
          />

          <motion.path
            d="M -100,600 C 400,500 800,720 1300,580 C 1700,480 1900,640 2200,590"
            strokeWidth="1"
            strokeDasharray="6 10"
            animate={{
              d: [
                "M -100,600 C 400,500 800,720 1300,580 C 1700,480 1900,640 2200,590",
                "M -100,580 C 380,530 820,690 1280,600 C 1720,500 1880,620 2200,570",
                "M -100,600 C 400,500 800,720 1300,580 C 1700,480 1900,640 2200,590",
              ],
            }}
            transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut' }}
          />
        </svg>
      )}
    </div>
  );
};
