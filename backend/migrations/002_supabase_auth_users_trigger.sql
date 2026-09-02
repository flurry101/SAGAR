-- =============================================================================
-- Migration 002: Automatic User Profile Sync Trigger for Supabase Auth
-- =============================================================================
-- When users sign in via Google OAuth or Email/Password in Supabase, Supabase Auth
-- registers them inside the `auth.users` system schema.
-- This trigger automatically inserts or updates the corresponding row in `public.users`.

-- 1. Create the sync function
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.users (
        supabase_uid,
        email,
        name,
        preferred_language,
        home_port,
        created_at,
        updated_at
    )
    VALUES (
        new.id::text,
        COALESCE(new.email, ''),
        COALESCE(
            new.raw_user_meta_data->>'name',
            new.raw_user_meta_data->>'full_name',
            new.raw_user_meta_data->>'user_name',
            split_part(COALESCE(new.email, ''), '@', 1)
        ),
        COALESCE(new.raw_user_meta_data->>'preferred_language', 'en'),
        COALESCE(new.raw_user_meta_data->>'home_port', ''),
        NOW(),
        NOW()
    )
    ON CONFLICT (supabase_uid) DO UPDATE
    SET
        email = EXCLUDED.email,
        name = CASE 
            WHEN public.users.name IS NULL OR public.users.name = '' 
            THEN EXCLUDED.name 
            ELSE public.users.name 
        END,
        preferred_language = CASE 
            WHEN public.users.preferred_language IS NULL OR public.users.preferred_language = 'en'
            THEN EXCLUDED.preferred_language 
            ELSE public.users.preferred_language 
        END,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Bind the trigger to Supabase auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

-- 3. Backfill any existing users already registered in auth.users
INSERT INTO public.users (
    supabase_uid,
    email,
    name,
    preferred_language,
    home_port,
    created_at,
    updated_at
)
SELECT
    u.id::text,
    COALESCE(u.email, ''),
    COALESCE(
        u.raw_user_meta_data->>'name',
        u.raw_user_meta_data->>'full_name',
        split_part(COALESCE(u.email, ''), '@', 1)
    ),
    COALESCE(u.raw_user_meta_data->>'preferred_language', 'en'),
    COALESCE(u.raw_user_meta_data->>'home_port', ''),
    u.created_at,
    NOW()
FROM auth.users u
ON CONFLICT (supabase_uid) DO NOTHING;

