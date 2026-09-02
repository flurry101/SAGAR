import React, { useState } from 'react';
import { useAppStore } from '../state/appStore';
import { supabase, isSupabaseConfigured } from '../api/supabaseClient';
import { API_BASE_URL } from '../api/client';
import { Anchor, ArrowRight, ShieldCheck, Mail, Lock, User, CheckCircle2 } from 'lucide-react';
import { RippleButton } from '../components/common/RippleButton';
import { useLingui } from '@lingui/react/macro';
import { Trans } from '@lingui/react/macro';

export const AuthPage: React.FC = () => {
  const { setCurrentView } = useAppStore();
  const { t } = useLingui();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supabase) {
      setError('Supabase is not configured.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName } }
        });
        if (error) throw error;
      }
      setCurrentView('landing');
    } catch (err: any) {
      setError(err.message || 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    window.location.href = `${API_BASE_URL}/login/google`;
  };

  return (
    <div className="min-h-screen bg-sagar-canvas flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-soft-xl border border-sagar-border overflow-hidden">
        
        {/* Header Section */}
        <div className="bg-sagar-navy p-8 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <img src="/sagar-logo.png" alt="" className="w-32 h-32 object-contain" />
          </div>
          
          <div className="relative z-10 flex flex-col items-center gap-4">
            <img
              src="/sagar-logo.png"
              alt="SAGAR Logo"
              className="w-16 h-16 object-contain rounded-full shadow-soft-lg ring-4 ring-white/20 bg-sky-950/40 p-0.5"
            />
            
            <div className="space-y-1">
              <h2 className="text-2xl font-black text-white tracking-wide">
                <Trans>SAGAR Identity</Trans>
              </h2>
              <p className="text-sky-200 text-sm font-medium">
                <Trans>Secure Coastal Decision Support Access</Trans>
              </p>
            </div>
          </div>
        </div>

        {/* Form Section */}
        <div className="p-8 space-y-6">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-xl font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleAuth} className="space-y-4">
            {!isLogin && (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider ml-1">
                  <Trans>Full Name</Trans>
                </label>
                <div className="relative">
                  <User className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={t`Enter your full name`}
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-sky-500 focus:ring-2 focus:ring-sky-200 transition-all outline-none"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider ml-1">
                <Trans>Email Address</Trans>
              </label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t`marine.operator@example.com`}
                  className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-sky-500 focus:ring-2 focus:ring-sky-200 transition-all outline-none"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider ml-1">
                <Trans>Password</Trans>
              </label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-sky-500 focus:ring-2 focus:ring-sky-200 transition-all outline-none"
                />
              </div>
            </div>

            <RippleButton
              variant="primary"
              size="lg"
              className="w-full mt-2"
              iconRight={<ArrowRight className="w-4 h-4" />}
            >
              {isLogin ? <Trans>Sign In to SAGAR</Trans> : <Trans>Create Account</Trans>}
            </RippleButton>
          </form>

          <div className="flex items-center gap-3">
            <div className="h-px bg-slate-200 flex-1"></div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider"><Trans>OR</Trans></span>
            <div className="h-px bg-slate-200 flex-1"></div>
          </div>

          <button
            onClick={handleGoogleSignIn}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-white border-2 border-slate-200 hover:border-slate-300 rounded-xl text-sm font-bold text-slate-700 transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <Trans>Continue with Google</Trans>
          </button>

          <div className="text-center pt-2">
            <button 
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm font-bold text-sky-600 hover:text-sky-700 transition-colors"
            >
              {isLogin ? <Trans>Need an account? Sign up</Trans> : <Trans>Already have an account? Sign in</Trans>}
            </button>
          </div>
        </div>
      </div>
      
      {/* Footer Trust Markers */}
      <div className="mt-8 flex gap-6 text-xs font-bold text-slate-500 uppercase tracking-widest">
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          <Trans>Tier 1 Data</Trans>
        </div>
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          <Trans>SVAS Compliant</Trans>
        </div>
      </div>
    </div>
  );
};
