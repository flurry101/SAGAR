import { createClient, SupabaseClient, Session } from '@supabase/supabase-js';
import { useAppStore } from '../state/appStore';
import { userApi } from './userApi';

const SUPABASE_URL =
  import.meta.env.VITE_SUPABASE_URL ||
  import.meta.env.NEXT_PUBLIC_SUPABASE_URL ||
  '';

const SUPABASE_ANON_KEY =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  '';

export const isSupabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
      },
    })
  : null;

export async function getSupabaseAccessToken(): Promise<string | null> {
  if (!supabase) return null;
  try {
    const { data } = await supabase.auth.getSession();
    return data?.session?.access_token || null;
  } catch (err) {
    console.warn('Failed to retrieve Supabase session token:', err);
    return null;
  }
}

/**
 * Initialise a Supabase auth-state listener.
 *
 * Handles the redirect-back from Google OAuth via Supabase:
 *  - On SIGNED_IN → updates Zustand store, syncs user to backend DB
 *  - On SIGNED_OUT → clears Zustand store
 *
 * Returns an unsubscribe function (or null if Supabase is not configured).
 */
export function initAuthListener(): (() => void) | null {
  if (!supabase) return null;

  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    async (event, session) => {
      const store = useAppStore.getState();

      if ((event === 'SIGNED_IN' || event === 'INITIAL_SESSION') && session) {
        const user = session.user;
        const meta = user.user_metadata || {};

        store.setAuthenticated(
          true,
          {
            name: meta.name || meta.full_name || user.email?.split('@')[0] || '',
            port: meta.home_port || '',
            email: user.email || '',
            userId: user.id,
          },
          session.access_token
        );

        // Sync with backend — create user record if it doesn't exist yet
        try {
          await userApi.createUser({
            name: meta.name || meta.full_name || undefined,
            preferred_language: store.selectedLanguage,
          });
        } catch (syncErr: any) {
          // 400 = user already exists — that's fine
          if (syncErr?.status !== 400) {
            console.warn('Backend user sync note:', syncErr);
          }
        }

        // Navigate to the main app view
        if (store.currentView === 'auth') {
          store.setCurrentView('chat');
        }
      }

      if (event === 'SIGNED_OUT') {
        store.setAuthenticated(false, undefined, null);
      }
    }
  );

  return () => subscription.unsubscribe();
}
