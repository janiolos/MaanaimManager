import { BarChart3, DollarSign, PiggyBank, ScrollText } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const reports = [
  {
    path: "/finance/relatorios/dre",
    icon: BarChart3,
    title: "DRE",
    desc: "Demonstrativo do Resultado do Exercício",
  },
  {
    path: "/finance/relatorios/fluxo-caixa",
    icon: DollarSign,
    title: "Fluxo de Caixa",
    desc: "Movimentação diária com saldo acumulado",
  },
  {
    path: "/finance/relatorios/conciliacao",
    icon: PiggyBank,
    title: "Conciliação",
    desc: "Receitas e despesas por forma de pagamento",
  },
  {
    path: "/finance/relatorios/oficial",
    icon: ScrollText,
    title: "Relatório Oficial",
    desc: "Listagem completa para impressão",
  },
];

export function ReportsIndexPage() {
  const location = useLocation();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold font-display">Relatórios Financeiros</h1>
        <p className="text-sm text-mm-muted">Selecione o tipo de relatório desejado</p>
      </div>

      <div className="flex border-b border-mm-border mb-4">
        <Link
          to="/finance/dashboard"
          className={cn(
            "px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200",
            location.pathname === "/finance/dashboard"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-mm-muted hover:text-foreground"
          )}
        >
          Painel Geral
        </Link>
        <Link
          to="/finance"
          className={cn(
            "px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200",
            location.pathname === "/finance"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-mm-muted hover:text-foreground"
          )}
        >
          Lançamentos
        </Link>
        <Link
          to="/finance/relatorios"
          className={cn(
            "px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200",
            location.pathname.startsWith("/finance/relatorios")
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-mm-muted hover:text-foreground"
          )}
        >
          Relatórios
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {reports.map((r) => (
          <Link key={r.path} to={r.path}>
            <Card className="hover:border-mm-accent hover:shadow-mm-md transition-all duration-200 cursor-pointer">
              <CardHeader className="flex flex-row items-start gap-4">
                <div className="p-2 bg-mm-accent/10 rounded-lg">
                  <r.icon className="size-6 text-mm-accent" />
                </div>
                <div>
                  <CardTitle className="text-base">{r.title}</CardTitle>
                  <p className="text-sm text-mm-muted mt-1">{r.desc}</p>
                </div>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
