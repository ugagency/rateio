import { cookies } from "next/headers";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

type CookieParaDefinir = { name: string; value: string; options: CookieOptions };

// Cliente Supabase para uso server-side (route handlers, server components).
// Usa a sessão do operador (cookies), então a RLS por claim associacao_id
// (ADR-002 C2) é aplicada automaticamente.
export async function createSupabaseServerClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(toSet: CookieParaDefinir[]) {
          try {
            toSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // chamado de um server component; ignorável quando há middleware
            // cuidando do refresh da sessão.
          }
        },
      },
    },
  );
}

// Cliente com service_role para operações privilegiadas (upload de vistoria,
// finalização). Nunca importar em código que roda no cliente.
import { createClient } from "@supabase/supabase-js";

export function createSupabaseServiceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false } },
  );
}
