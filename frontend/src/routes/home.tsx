import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RequireScope } from "@/components/require-scope";
import { useAuthStore } from "@/stores/auth-store";
import { useEventoStore } from "@/stores/evento-store";
import { Button } from "@/components/ui/button";

interface ModuleTile {
  to: string;
  title: string;
  desc: string;
  emoji: string;
  scope: string;
}

const TILES: ModuleTile[] = [
  { to: "/core/eventos", title: "Eventos", desc: "Ciclos e calendário", emoji: "📅", scope: "core:read" },
  { to: "/finance/dashboard", title: "Financeiro", desc: "Receitas, despesas e relatórios", emoji: "💰", scope: "finance:read" },
  { to: "/inventory", title: "Estoque", desc: "Produtos, requisições, cotações", emoji: "📦", scope: "inventory:read" },
  { to: "/lodging", title: "Hospedagem", desc: "Chalés, reservas, mapa", emoji: "🏨", scope: "lodging:read" },
  { to: "/pos", title: "PDV", desc: "Vendas e check-out", emoji: "🛒", scope: "core:read" },
];

export function HomePage() {
  const { user } = useAuthStore();
  const { evento } = useEventoStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold font-display">
          Olá, {user?.first_name || user?.username} 👋
        </h1>
        <p className="text-sm text-mm-muted">
          {evento ? (
            <>
              Evento atual: <strong>{evento.nome}</strong> · {" "}
              <Link to="/selecionar-evento" className="text-mm-accent underline">
                trocar
              </Link>
            </>
          ) : (
            <>
              Nenhum evento selecionado.{" "}
              <Link to="/selecionar-evento" className="text-mm-accent underline">
                escolher evento
              </Link>
            </>
          )}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {TILES.map((tile) => (
          <RequireScope key={tile.to} scope={tile.scope}>
            <Card className="transition-shadow hover:shadow-mm-lg">
              <CardHeader className="flex-row items-start gap-4 space-y-0">
                <div className="text-3xl">{tile.emoji}</div>
                <div className="flex-1">
                  <CardTitle className="text-lg">{tile.title}</CardTitle>
                  <CardDescription>{tile.desc}</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <Button asChild variant="outline" className="w-full">
                  <Link to={tile.to}>Abrir módulo</Link>
                </Button>
              </CardContent>
            </Card>
          </RequireScope>
        ))}
      </div>
    </div>
  );
}