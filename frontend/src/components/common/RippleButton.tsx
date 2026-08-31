import React, { useState } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface RippleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

interface Ripple {
  x: number;
  y: number;
  id: number;
}

export const RippleButton: React.FC<RippleButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon,
  iconRight,
  children,
  className = '',
  onClick,
  disabled,
  ...props
}) => {
  const [ripples, setRipples] = useState<Ripple[]>([]);

  const handlePointerDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const newRipple = { x, y, id: Date.now() };

    setRipples((prev) => [...prev.slice(-3), newRipple]);
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
    }, 600);
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return 'bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-500 hover:to-sky-600 text-white shadow-soft-md hover:shadow-soft-lg border border-sky-500/30';
      case 'secondary':
        return 'bg-white hover:bg-sagar-powder/60 text-sagar-navy border border-sagar-border hover:border-sky-300 shadow-soft-sm hover:shadow-soft-md';
      case 'outline':
        return 'bg-transparent hover:bg-sagar-powder/40 text-sky-800 border border-sky-300 hover:border-sky-400';
      case 'danger':
        return 'bg-rose-600 hover:bg-rose-500 text-white shadow-soft-sm hover:shadow-soft-md border border-rose-500';
      case 'ghost':
        return 'bg-transparent hover:bg-sagar-canvasAlt text-slate-700 hover:text-sagar-navy';
      default:
        return 'bg-sky-600 text-white';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-xs rounded-lg gap-1.5';
      case 'lg':
        return 'px-6 py-3.5 text-sm sm:text-base rounded-2xl gap-3 font-extrabold';
      case 'md':
      default:
        return 'px-4 sm:px-5 py-2.5 sm:py-3 text-xs sm:text-sm rounded-xl gap-2 font-bold';
    }
  };

  return (
    <motion.button
      whileHover={disabled ? undefined : { y: -2, scale: 1.015 }}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 450, damping: 25 }}
      onMouseDown={handlePointerDown}
      onClick={onClick}
      disabled={disabled}
      className={`relative overflow-hidden inline-flex items-center justify-center font-sans transition-colors cursor-pointer select-none touch-target ${getVariantStyles()} ${getSizeStyles()} ${
        disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''
      } ${className}`}
      {...(props as any)}
    >
      {/* Dynamic Water Ripple Animation */}
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="absolute rounded-full bg-white/30 pointer-events-none animate-ping"
          style={{
            left: ripple.x - 20,
            top: ripple.y - 20,
            width: 40,
            height: 40,
          }}
        />
      ))}

      {icon && <span className="shrink-0 transition-transform group-hover:scale-110">{icon}</span>}
      <span className="relative z-10 leading-none">{children}</span>
      {iconRight && <span className="shrink-0 transition-transform group-hover:translate-x-0.5">{iconRight}</span>}
    </motion.button>
  );
};
