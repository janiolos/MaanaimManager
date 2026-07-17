import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Printer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useOfficialReport } from "@/routes/finance/hooks";
import { useEventoStore } from "@/stores/evento-store";
import { cn, formatBRL, formatDate } from "@/lib/utils";

export function OficialPage() {
  const location = useLocation();
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");

  const { data, isLoading } = useOfficialReport(dataInicio || undefined, dataFim || undefined);
  const { evento } = useEventoStore();

  const formattedPeriod = () => {
    if (dataInicio && dataFim) {
      return `PERÍODO: ${formatDate(dataInicio)} A ${formatDate(dataFim)}`;
    } else if (dataInicio) {
      return `A PARTIR DE: ${formatDate(dataInicio)}`;
    } else if (dataFim) {
      return `ATÉ: ${formatDate(dataFim)}`;
    }
    return "SELECIONE EVENTO E DATA";
  };

  return (
    <div className="space-y-6">
      <style>{`
        .relatorio-pdf {
          background: #fff;
          padding: 24px;
          border: 1px solid #e5e7eb;
          color: #111827;
        }
        .relatorio-header {
          text-align: center;
          margin-bottom: 16px;
        }
        .relatorio-header h1 {
          font-size: 18px;
          margin: 0;
          font-weight: bold;
        }
        .relatorio-header h2 {
          font-size: 16px;
          margin: 6px 0 0;
          font-weight: bold;
        }
        .relatorio-header .sub {
          font-size: 12px;
          margin-top: 4px;
          color: #4b5563;
        }
        .relatorio-section {
          margin-top: 16px;
          border-top: 2px solid #111827;
          padding-top: 8px;
        }
        .relatorio-section .titulo {
          text-align: center;
          font-weight: bold;
          font-size: 13px;
          margin-bottom: 6px;
        }
        .relatorio-section table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        .relatorio-section th,
        .relatorio-section td {
          border: 1px solid #9ca3af;
          padding: 6px 8px;
          color: #111827 !important;
        }
        .relatorio-section th {
          font-weight: bold;
          background-color: #f3f4f6;
        }
        .resultado {
          margin-top: 12px;
          border: 2px solid #111827;
          padding: 8px;
          text-align: right;
          font-size: 13px;
          font-weight: bold;
        }
        .assinaturas {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 24px;
          margin-top: 48px;
          text-align: center;
          font-size: 10px;
        }
        .assinaturas span {
          display: block;
          border-top: 1px solid #9ca3af;
          padding-top: 6px;
          font-weight: bold;
        }

        @media print {
          body * {
            visibility: hidden;
          }
          .relatorio-pdf, .relatorio-pdf * {
            visibility: visible;
          }
          .relatorio-pdf {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            border: none;
            padding: 0;
            margin: 0;
          }
        }
      `}</style>

      <div className="flex items-center justify-between gap-3 no-print">
        <div>
          <h1 className="text-2xl font-semibold font-display">Relatório Oficial</h1>
          <p className="text-sm text-mm-muted">Formato oficial de prestação de contas</p>
        </div>
        <Button variant="outline" onClick={() => window.print()}>
          <Printer className="mr-2" size={16} /> Imprimir / Salvar PDF
        </Button>
      </div>

      <div className="flex border-b border-mm-border mb-4 no-print">
        <Link to="/finance/dashboard" className={cn("px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200", location.pathname === "/finance/dashboard" ? "border-primary text-primary font-semibold" : "border-transparent text-mm-muted hover:text-foreground")}>Painel Geral</Link>
        <Link to="/finance" className={cn("px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200", location.pathname === "/finance" ? "border-primary text-primary font-semibold" : "border-transparent text-mm-muted hover:text-foreground")}>Lançamentos</Link>
        <Link to="/finance/relatorios" className={cn("px-4 py-2 border-b-2 font-medium text-sm transition-all duration-200", location.pathname.startsWith("/finance/relatorios") ? "border-primary text-primary font-semibold" : "border-transparent text-mm-muted hover:text-foreground")}>Relatórios</Link>
      </div>

      <Card className="no-print">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1.5"><Label>Data início</Label><Input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Data fim</Label><Input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} /></div>
          </div>
        </CardContent>
      </Card>

      {isLoading && <p className="text-mm-muted text-sm no-print">Carregando...</p>}

      {data && (
        <div className="relatorio-pdf shadow-sm max-w-4xl mx-auto">
          <div className="relatorio-header">
            <h1>RELATÓRIO PDF</h1>
            <h2>{evento?.nome || "Todos os Eventos"}</h2>
            <div className="sub">{formattedPeriod()}</div>
          </div>

          <div className="relatorio-section">
            <div className="titulo">RECEITAS</div>
            <table>
              <thead>
                <tr>
                  <th>Descrição</th>
                  <th className="text-right" style={{ width: "150px" }}>Valores (R$)</th>
                </tr>
              </thead>
              <tbody>
                {data.receitas.length > 0 ? (
                  data.receitas.map((r) => (
                    <tr key={r.id}>
                      <td>{r.descricao}</td>
                      <td className="text-right font-mono">{formatBRL(r.valor)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={2} className="text-center py-4 text-gray-500">Sem registros</td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="font-bold bg-gray-50">
                  <td className="font-bold">TOTAL DAS RECEITAS</td>
                  <td className="text-right font-mono text-green-600">{formatBRL(data.total_receitas)}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="relatorio-section">
            <div className="titulo">DESPESAS GERAIS</div>
            <table>
              <thead>
                <tr>
                  <th>Descrição</th>
                  <th className="text-right" style={{ width: "150px" }}>Valores (R$)</th>
                </tr>
              </thead>
              <tbody>
                {data.despesas.length > 0 ? (
                  data.despesas.map((r) => (
                    <tr key={r.id}>
                      <td>{r.descricao}</td>
                      <td className="text-right font-mono">{formatBRL(r.valor)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={2} className="text-center py-4 text-gray-500">Sem registros</td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="font-bold bg-gray-50">
                  <td className="font-bold">TOTAL DE DESPESAS</td>
                  <td className="text-right font-mono text-rose-600">{formatBRL(data.total_despesas)}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="resultado">
            <div>
              RESULTADO (RECEITA - DESPESAS): <span className={Number(data.saldo) >= 0 ? "text-green-600" : "text-rose-600"}>{formatBRL(data.saldo)}</span>
            </div>
          </div>

          <div className="assinaturas">
            <div>
              <span>COORDENADOR DO MAANAIM</span>
            </div>
            <div>
              <span>CONSELHO FISCAL</span>
            </div>
            <div>
              <span>COMISSÃO DO MAANAIM</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
