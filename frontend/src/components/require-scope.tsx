import { useAuthStore } from "@/stores/auth-store";

interface Props {
  scope: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/** Bloqueia children se o usuário não possuir o scope. Equivale a @user_passes_test. */
export function RequireScope({ scope, children, fallback = null }: Props) {
  const hasScope = useAuthStore((s) => s.hasScope(scope));
  if (!hasScope) return <>{fallback}</>;
  return <>{children}</>;
}