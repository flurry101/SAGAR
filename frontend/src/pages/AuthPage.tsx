import React, { useState } from 'react';
import { useAppStore } from '../state/appStore';
import { supabase, isSupabaseConfigured } from '../api/supabaseClient';
import { API_BASE_URL } from '../api/client';
import { userApi } from '../api/userApi';
import { User, Mail, Lock, ArrowRight, ShieldCheck, LogOut, AlertCircle, Anchor } from 'lucide-react';
import { motion } from 'framer-motion';

/** Inline Google "G" logo SVG — avoids external dependency */
const GoogleLogo: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
  </svg>
);

export const AuthPage: React.FC = () => {
  const { isAuthenticated, userProfile, setAuthenticated, setCurrentView, selectedLanguage } = useAppStore();
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('ops.sagar@marine.mission');
  const [password, setPassword] = useState('sagar12345');
  const [name, setName] = useState(userProfile?.name || 'Marine Operator');
  const [port, setHomePort] = useState(userProfile?.port || 'Mangalore Port');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // ── Google OAuth ───────────────────────────────────────────────────
  const handleGoogleSignIn = async () => {
    setLoading(true);
    setErrorMessage(null);
    setStatusMessage(null);

    try {
      if (isSupabaseConfigured && supabase) {
        // Preferred path: Supabase handles the full OAuth redirect flow
        const { error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: {
            redirectTo: window.location.origin,
          },
        });
        if (error) throw error;
        // Supabase will redirect away; the auth listener in App.tsx
        // handles the session when the user comes back.
        return;
      }

      // Fallback: redirect to backend OAuth endpoint
      window.location.href = `${API_BASE_URL}/login/google`;
    } catch (err: any) {
      setErrorMessage(err.message || 'Google sign-in failed.');
      setLoading(false);
    }
  };

  // ── Email / password auth ──────────────────────────────────────────
  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);
    setStatusMessage(null);

    try {
      if (isSupabaseConfigured && supabase) {
        if (authMode === 'signup') {
          const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
              data: {
                name,
                home_port: port,
                preferred_language: selectedLanguage,
              },
            },
          });
          if (error) throw error;

          const sessionToken = data.session?.access_token || null;
          setAuthenticated(
            true,
            { name, port, email, userId: data.user?.id },
            sessionToken
          );

          // Sync with backend API
          try {
            await userApi.createUser({
              name,
              home_port: port,
              preferred_language: selectedLanguage,
            });
          } catch (syncErr) {
            console.warn('Backend user sync note:', syncErr);
          }

          setStatusMessage('Account created and synced successfully!');
          setTimeout(() => setCurrentView('chat'), 1000);
        } else {
          // Sign In
          const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
          });
          if (error) throw error;

          const sessionToken = data.session?.access_token || null;
          setAuthenticated(
            true,
            { name: data.user?.user_metadata?.name || name, port: data.user?.user_metadata?.home_port || port, email, userId: data.user?.id },
            sessionToken
          );

          // Fetch profile from backend
          try {
            const meRes = await userApi.getCurrentUser();
            if (meRes.status === 'success' && meRes.data) {
              setAuthenticated(true, {
                name: meRes.data.name || name,
                port: meRes.data.home_port || port,
                email: meRes.data.email || email,
                userId: meRes.data.user_id,
              }, sessionToken);
            }
          } catch (meErr) {
            console.warn('Backend user/me note:', meErr);
          }

          setStatusMessage('Signed in successfully!');
          setTimeout(() => setCurrentView('chat'), 800);
        }
      } else {
        // Explicitly reject unauthenticated demo logins; require a configured auth provider.
        setAuthenticated(false, undefined, null);
        setErrorMessage('Authentication is not configured for this deployment. Configure Supabase or Google OAuth before signing in.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    if (supabase) {
      await supabase.auth.signOut().catch(() => {});
    }
    setAuthenticated(false, undefined, null);
    setStatusMessage('You have been signed out.');
  };

  return (
    <main className="max-w-md mx-auto px-4 py-8 text-sagar-navy">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white border border-sagar-border rounded-2xl p-6 sm:p-8 shadow-soft-md space-y-5"
      >
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-sagar-powder text-sky-700 flex items-center justify-center mx-auto font-bold shadow-soft-sm">
            <User className="w-6 h-6" />
          </div>
          <h1 className="text-lg sm:text-xl font-bold text-sagar-navy">Operator Identity & Authentication</h1>
          <p className="text-xs text-slate-500">
            Authenticate to sync your vessel profile and voyage safety records across maritime operations.
          </p>
        </div>

        {/* Current status card when logged in */}
        {isAuthenticated && userProfile ? (
          <div className="space-y-4">
            <div className="p-4 bg-sagar-canvasAlt border border-sagar-borderLight rounded-xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-emerald-700 font-bold flex items-center gap-1.5 text-sm">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Currently Signed In</span>
                </span>
                <button
                  onClick={handleSignOut}
                  className="text-xs text-rose-700 hover:text-rose-900 font-bold flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors touch-target"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
              <div className="text-slate-700 space-y-1 pt-1 border-t border-sagar-borderLight">
                <div>Name: <strong className="text-sagar-navy">{userProfile.name}</strong></div>
                <div>Base Harbor: <strong className="text-sagar-navy">{userProfile.port}</strong></div>
                {userProfile.email && <div>Email: <span className="text-slate-600 font-mono">{userProfile.email}</span></div>}
              </div>
            </div>

            <div className="pt-2 border-t border-sagar-border space-y-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-2">Quick Navigation</span>
              <button
                type="button"
                onClick={() => setCurrentView('chat')}
                className="w-full py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-soft-sm flex items-center justify-between transition-all touch-target cursor-pointer"
              >
                <span>Go to Trip Planner</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setCurrentView('vessel')}
                  className="py-2.5 px-3 rounded-xl bg-white hover:bg-sagar-canvasAlt text-sagar-navy font-bold text-xs border border-sagar-border flex items-center justify-center gap-2 transition-all touch-target cursor-pointer shadow-soft-sm"
                >
                  <Anchor className="w-3.5 h-3.5 text-sky-600" />
                  <span>Vessel Profile</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentView('history')}
                  className="py-2.5 px-3 rounded-xl bg-white hover:bg-sagar-canvasAlt text-sagar-navy font-bold text-xs border border-sagar-border flex items-center justify-center gap-2 transition-all touch-target cursor-pointer shadow-soft-sm"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
                  <span>Voyage History</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* ── Google Sign‑in Button ─────────────────────────────────── */}
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 py-3 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 shadow-soft-sm text-sm font-semibold text-slate-700 transition-all disabled:opacity-50 touch-target cursor-pointer"
            >
              <GoogleLogo className="w-5 h-5" />
              <span>Sign in with Google</span>
            </button>

            {/* ── OR divider ────────────────────────────────────────────── */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-sagar-border" />
              <span className="text-[11px] text-slate-400 font-bold uppercase tracking-wider">or</span>
              <div className="flex-1 h-px bg-sagar-border" />
            </div>

            {/* Tab Selection */}
            <div className="grid grid-cols-2 gap-2 bg-sagar-canvasAlt p-1 rounded-xl border border-sagar-borderLight text-xs">
              <button
                type="button"
                onClick={() => setAuthMode('signin')}
                className={`py-2 rounded-lg font-bold transition-colors touch-target ${
                  authMode === 'signin'
                    ? 'bg-white text-sky-900 shadow-soft-sm border border-sagar-border/60'
                    : 'text-slate-500 hover:text-sagar-navy'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setAuthMode('signup')}
                className={`py-2 rounded-lg font-bold transition-colors touch-target ${
                  authMode === 'signup'
                    ? 'bg-white text-sky-900 shadow-soft-sm border border-sagar-border/60'
                    : 'text-slate-500 hover:text-sagar-navy'
                }`}
              >
                Register / Sign Up
              </button>
            </div>

            <form onSubmit={handleEmailAuth} className="space-y-3.5 text-xs">
              {authMode === 'signup' && (
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Operator Full Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-white border border-sagar-border rounded-xl px-3.5 py-2.5 text-sagar-navy focus:border-sky-500 focus:outline-none"
                  />
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Base Port / Home Harbor</label>
                <input
                  type="text"
                  required
                  value={port}
                  onChange={(e) => setHomePort(e.target.value)}
                  className="w-full bg-white border border-sagar-border rounded-xl px-3.5 py-2.5 text-sagar-navy focus:border-sky-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1 flex items-center gap-1">
                  <Mail className="w-3.5 h-3.5 text-sky-600" />
                  <span>Email Address</span>
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-sagar-border rounded-xl px-3.5 py-2.5 text-sagar-navy focus:border-sky-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1 flex items-center gap-1">
                  <Lock className="w-3.5 h-3.5 text-sky-600" />
                  <span>Password</span>
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-sagar-border rounded-xl px-3.5 py-2.5 text-sagar-navy focus:border-sky-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold text-xs shadow-soft-sm flex items-center justify-center gap-2 transition-all mt-2 touch-target"
              >
                <span>
                  {loading
                    ? 'Authenticating...'
                    : authMode === 'signup'
                    ? 'Create Account & Sync Profile'
                    : 'Sign In to SAGAR'}
                </span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </>
        )}
      </motion.div>
    </main>
  );
};
