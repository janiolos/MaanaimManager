import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Group {
  id: number;
  name: string;
}

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_superuser: boolean;
  is_staff: boolean;
  groups: Group[];
  scopes: string[];
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  hasScope: (scope: string) => boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      setAccessToken: (token) => set({ accessToken: token }),
      setUser: (user) => set({ user }),
      hasScope: (scope) => {
        const u = get().user;
        if (!u) return false;
        if (u.is_superuser) return true;
        return u.scopes.includes(scope);
      },
      login: (token, user) => set({ accessToken: token, user }),
      logout: () => set({ user: null, accessToken: null }),
    }),
    {
      // accessToken em memória? Persistente por enquanto para sobreviver a reload;
      // em produção mudar para não persistir o access (só o refresh via cookie).
      name: "maanaim-auth",
      partialize: (s) => ({ user: s.user, accessToken: s.accessToken }),
    },
  ),
);