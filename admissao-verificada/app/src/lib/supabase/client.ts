"use client";

import { createBrowserClient } from "@supabase/ssr";

// Cliente Supabase para uso no navegador (componentes client).
export function createSupabaseBrowserClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
