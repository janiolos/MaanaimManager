import { LogOut, Menu, Settings, X, Shield, HelpCircle } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { useEventoStore } from "@/stores/evento-store";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { HelpModal } from "./help-modal";

interface ModuleLink {
  to: string;
  label: string;
  requiredScope: string;
  emoji: string;
}

const MODULES: ModuleLink[] = [
  { to: "/", label: "Início", requiredScope: "core:read", emoji: "🏠" },
  { to: "/core/eventos", label: "Eventos", requiredScope: "core:read", emoji: "📅" },
  { to: "/finance/dashboard", label: "Financeiro", requiredScope: "finance:read", emoji: "💰" },
  { to: "/inventory", label: "Estoque", requiredScope: "inventory:read", emoji: "📦" },
  { to: "/lodging", label: "Hospedagem", requiredScope: "lodging:read", emoji: "🏨" },
  { to: "/pos", label: "PDV", requiredScope: "core:read", emoji: "🛒" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuthStore();
  const { evento } = useEventoStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  const visibleModules = MODULES.filter((m) => user?.is_superuser || user?.scopes.includes(m.requiredScope));

  async function handleLogout() {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore
    }
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col bg-mm-soft">
      <header className="bg-mm-primary text-white shadow-mm sticky top-0 z-30">
        <div className="container flex items-center justify-between h-14">
          <div className="flex items-center gap-4">
            <button
              type="button"
              className="md:hidden p-2"
              onClick={() => setOpen((v) => !v)}
              aria-label="Menu"
            >
              {open ? <X size={20} /> : <Menu size={20} />}
            </button>
            <Link to="/" className="flex items-center gap-2 font-semibold font-display">
              <span className="grid place-items-center h-8 w-8 rounded bg-mm-accent text-white font-bold">
                M
              </span>
              <span className="hidden sm:inline">Maanaim Manager</span>
            </Link>
          </div>

          <nav className="hidden md:flex items-center gap-1">
            {visibleModules.map((m) => {
              const isActive = m.to === "/" ? location.pathname === "/" : location.pathname.startsWith(m.to);
              return (
                <Link
                  key={m.to}
                  to={m.to}
                  className={cn(
                    "px-3 py-2 rounded text-sm font-medium text-white/80 hover:text-white hover:bg-white/10",
                    isActive && "bg-white/15 text-white",
                  )}
                >
                  <span aria-hidden> {m.emoji}</span> {m.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3">
            {evento && (
              <Badge variant="success" className="hidden sm:inline-flex">
                {evento.nome}
              </Badge>
            )}
            <span className="hidden sm:inline text-sm text-white/70">
              {user?.first_name || user?.username}
            </span>
            {(user?.is_superuser || user?.scopes.includes("admin:write")) && (
              <Link to="/admin">
                <Button variant="ghost" size="icon" aria-label="Administração">
                  <Shield size={18} />
                </Button>
              </Link>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setHelpOpen(true)}
              aria-label="Ajuda do Sistema"
              title="Ajuda do Sistema"
            >
              <HelpCircle size={18} />
            </Button>
            <Link to="/configuracoes">
              <Button variant="ghost" size="icon" aria-label="Configurações">
                <Settings size={18} />
              </Button>
            </Link>
            <Button variant="ghost" size="icon" onClick={handleLogout} aria-label="Sair">
              <LogOut size={18} />
            </Button>
          </div>
        </div>

        {open && (
          <nav className="md:hidden border-t border-white/10 bg-mm-primary-dark">
            {visibleModules.map((m) => {
              const isActive = m.to === "/" ? location.pathname === "/" : location.pathname.startsWith(m.to);
              return (
                <Link
                  key={m.to}
                  to={m.to}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "block px-4 py-3 text-sm border-b border-white/5",
                    isActive ? "bg-white/10 text-white font-semibold" : "text-white/90 hover:bg-white/10"
                  )}
                >
                  <span aria-hidden className="mr-1.5">{m.emoji}</span> {m.label}
                </Link>
              );
            })}
          </nav>
        )}
      </header>

      <main className="container py-6 flex-1">{children}</main>

      <footer className="border-t bg-mm-card py-3 text-center text-xs text-mm-muted">
        Maanaim Manager · FastAPI + React · v0.1
      </footer>

      <HelpModal isOpen={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  );
}