import {
  AlertTriangle,
  Boxes,
  Package,
  ShoppingCart,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useInventoryDashboard } from "@/routes/inventory/hooks";
import { formatBRL } from "@/lib/utils";

export function InventoryDashboardPage() {
  const { data, isLoading } = useInventoryDashboard();
  if (isLoading) return <p className="text-mm-muted">Carregando dashboard...</p>;
  if (!data) return null;

  const cards = [
    {
      title: "Produtos ativos",
      value: String(data.produtos_ativos),
      hint: `${data.total_produtos} totais`,
      icon: Package,
      to: "/inventory/produtos",
    },
    {
      title: "Estoque baixo",
      value: String(data.estoque_baixo),
      hint: `${data.estoque_reabastecer} p/ reabastecer`,
      icon: AlertTriangle,
      to: "/inventory/produtos",
      variant: "text-destructive",
    },
    {
      title: "Valor em estoque",
      value: formatBRL(data.valor_total_estoque),
      hint: "média ponderada",
      icon: TrendingUp,
      to: "/inventory/produtos",
    },
    {
      title: "Requisições abertas",
      value: String(data.requisicoes_abertas),
      icon: Boxes,
      to: "/inventory/requisicoes",
    },
    {
      title: "Cotações abertas",
      value: String(data.cotacoes_abertas),
      icon: ShoppingCart,
      to: "/inventory/cotacoes",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Estoque</h1>
          <p className="text-sm text-mm-muted">Visão geral do inventário</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/inventory/produtos"
            className="px-3 py-2 rounded border border-input hover:bg-accent text-sm"
          >
            Produtos
          </Link>
          <Link
            to="/inventory/requisicoes"
            className="px-3 py-2 rounded border border-input hover:bg-accent text-sm"
          >
            Requisições
          </Link>
          <Link
            to="/inventory/cotacoes"
            className="px-3 py-2 rounded border border-input hover:bg-accent text-sm"
          >
            Cotações
          </Link>
          <Link
            to="/inventory/fornecedores"
            className="px-3 py-2 rounded border border-input hover:bg-accent text-sm"
          >
            Fornecedores
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
        {cards.map((c) => (
          <Card key={c.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-mm-muted">{c.title}</CardTitle>
              <c.icon className={`size-5 ${c.variant ?? "text-mm-accent"}`} />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${c.variant ?? ""}`}>{c.value}</div>
              {c.hint && <p className="text-xs text-mm-muted mt-1">{c.hint}</p>}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}