import React, { useState } from 'react';
import { useAppStore } from '../state/appStore';
import { supabase, isSupabaseConfigured } from '../api/supabaseClient';
import { userApi } from '../api/userApi';
import { User, Mail, Lock, ArrowRight, ShieldCheck, LogOut, AlertCircle, Anchor } from 'lucide-react';
import { motion } from 'framer-motion';

export const AuthPage: React.FC = () => {
  const { isAuthenticated, userProfile, setAuthenticated, setCurrentView, selectedLanguage } = useAppStore();
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('fisher.ravi@sagar.marine');
  const [password, setPassword] = useState('sagar12345');
  const [name, setName] = useState(userProfile?.name || 'Fisher Ravi Kumar');
  const [port, setHomePort] = useState(userProfile?.port || 'Mangalore Old Port');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

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
        // Safe offline / demo auth simulation
        setAuthenticated(
          true,
          { name, port, email, userId: 'user-demo-001' },
          'mock-jwt-token-demo'
        );
        setStatusMessage('Signed in in local operational demo mode.');
        setTimeout(() => setCurrentView('chat'), 800);
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
          <h1 className="text-lg sm:text-xl font-bold text-sagar-navy">Fisherman Identity & Authentication</h1>
          <p className="text-xs text-slate-500">
            Authenticate to sync your registered vessel profile and past voyage safety records.
          </p>
        </div>

        {/* Current status card */}
        {isAuthenticated && userProfile && (
          <div className="p-3.5 bg-sagar-canvasAlt border border-sagar-borderLight rounded-xl space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-emerald-700 font-bold flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                <span>Currently Signed In</span>
              </span>
              <button
                onClick={handleSignOut}
                className="text-[11px] text-rose-700 hover:text-rose-900 font-bold flex items-center gap-1 touch-target"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
            <div className="text-slate-700 space-y-0.5">
              <div>Name: <strong className="text-sagar-navy">{userProfile.name}</strong></div>
              <div>Base Harbor: <strong className="text-sagar-navy">{userProfile.port}</strong></div>
              {userProfile.email && <div>Email: <span className="text-slate-500 font-mono">{userProfile.email}</span></div>}
            </div>
          </div>
        )}

        {/* Status / Error Messages */}
        {errorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-300 rounded-xl text-rose-950 text-xs flex items-center gap-2 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-700 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {statusMessage && (
          <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-emerald-950 text-xs flex items-center gap-2 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}

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
              <label className="font-semibold text-slate-700 block mb-1">Fisher Full Name</label>
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
      </motion.div>
    </main>
  );
};
