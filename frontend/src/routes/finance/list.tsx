import { useQuery } from "@tanstack/react-query";
import { Plus, Search, Trash2, Pencil, Paperclip } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { formatBRL, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import {
  FORMA_PAGAMENTO_LABELS,
  TIPO_LABELS,
  type PaginatedLancamentos,
} from "@/routes/finance/types";
import { useCategorias } from "@/routes/finance/hooks";

export function FinanceListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [tipo, setTipo] = useState<"RECEITA" | "DESPESA" | "">("");
  const [categoriaId, setCategoriaId] = useState<string>("");
  const [descricao, setDescricao] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const { data: categorias } = useCategorias();

  const { data, isLoading, refetch, isFetching } = useQuery<PaginatedLancamentos>({
    queryKey: ["finance", "lancamentos", { tipo, categoriaId, page, pageSize }],
    queryFn: async () => {
      const { data } = await api.get<PaginatedLancamentos>("/finance/lancamentos", {
        params: {
          tipo: tipo || undefined,
          categoria_id: categoriaId || undefined,
          page,
          page_size: pageSize,
        },
      });
      return data;
    },
    placeholderData: (prev) => prev,
  });

  async function excluir(id: number, descricao: string) {
    if (!confirm(`Excluir lançamento "${descricao}"?`)) return;
    try {
      await api.delete(`/finance/lancamentos/${id}`);
      toast.success("Lançamento excluído");
      refetch();
    } catch {
      toast.error("Falha ao excluir");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Financeiro</h1>
          <p className="text-sm text-mm-muted">Lançamentos por evento</p>
        </div>
        <Button asChild>
          <Link to="/finance/novo">
            <Plus className="mr-2" size={16} /> Novo lançamento
          </Link>
        </Button>
      </div>

      {/* Module Navigation Tabs */}
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

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Search size={16} /> Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="tipo">Tipo</Label>
              <select
                id="tipo"
                value={tipo}
                onChange={(e) => {
                  setTipo(e.target.value as "RECEITA" | "DESPESA" | "");
                  setPage(1);
                }}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos</option>
                <option value="RECEITA">Receita</option>
                <option value="DESPESA">Despesa</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="categoria">Categoria</Label>
              <select
                id="categoria"
                value={categoriaId}
                onChange={(e) => {
                  setCategoriaId(e.target.value);
                  setPage(1);
                }}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todas</option>
                {categorias?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome} ({TIPO_LABELS[c.tipo]})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="descricao">Descrição</Label>
              <Input
                id="descricao"
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="busca textual (em breve)"
                disabled
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setTipo("");
                setCategoriaId("");
                setPage(1);
              }}
            >
              Limpar
            </Button>
            <Button size="sm" onClick={() => refetch()} disabled={isFetching}>
              Atualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabela */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-mm-muted">
                <tr>
                  <th className="px-4 py-3">Data</th>
                  <th className="px-4 py-3">Descrição</th>
                  <th className="px-4 py-3">Categoria</th>
                  <th className="px-4 py-3">Forma</th>
                  <th className="px-4 py-3">Valor</th>
                  <th className="px-4 py-3">Ações</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-mm-muted">
                      Carregando...
                    </td>
                  </tr>
                ) : data && data.items.length > 0 ? (
                  data.items.map((l) => {
                    const cat = categorias?.find((c) => c.id === l.categoria_id);
                    const variant = l.tipo === "RECEITA" ? "success" : "destructive";
                    return (
                      <tr key={l.id} className="border-t hover:bg-muted/30">
                        <td className="px-4 py-3 whitespace-nowrap">{formatDate(l.data)}</td>
                        <td className="px-4 py-3">
                          <div className="flex flex-col">
                            <span className="font-medium">{l.descricao}</span>
                            {l.pessoa && (
                              <span className="text-xs text-mm-muted">{l.pessoa}</span>
                            )}
                            {l.anexos && l.anexos.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {l.anexos.map((a) => (
                                  <a
                                    key={a.id}
                                    href={`/media/${a.arquivo}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-1 text-[11px] text-mm-primary hover:underline bg-mm-primary/5 hover:bg-mm-primary/10 px-1.5 py-0.5 rounded border border-mm-primary/10 transition-colors"
                                    title={a.descricao}
                                  >
                                    <Paperclip size={10} />
                                    <span className="max-w-[120px] truncate">{a.descricao}</span>
                                  </a>
                                ))}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {cat ? (
                            <Badge variant={variant}>
                              {cat.nome}
                            </Badge>
                          ) : (
                            <Badge variant="outline"># {l.categoria_id}</Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {FORMA_PAGAMENTO_LABELS[l.forma_pagamento] ?? l.forma_pagamento}
                        </td>
                        <td className="px-4 py-3 font-mono whitespace-nowrap">
                          <span className={l.tipo === "RECEITA" ? "text-mm-accent" : "text-destructive"}>
                            {l.tipo === "DESPESA" ? "-" : "+"} {formatBRL(l.valor)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label="Editar"
                              onClick={() => navigate(`/finance/${l.id}/editar`)}
                              title="Editar Lançamento"
                            >
                              <Pencil size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label="Adicionar comprovante"
                              title="Adicionar comprovante/nota"
                              onClick={() => {
                                const input = document.createElement("input");
                                input.type = "file";
                                input.accept = "image/*,application/pdf";
                                input.onchange = async (e) => {
                                  const files = (e.target as HTMLInputElement).files;
                                  if (!files || files.length === 0) return;
                                  const file = files[0];
                                  const formData = new FormData();
                                  formData.append("file", file);
                                  formData.append("descricao", file.name);

                                  const toastId = toast.loading("Enviando comprovante...");
                                  try {
                                    await api.post(`/finance/lancamentos/${l.id}/anexos`, formData, {
                                      headers: { "Content-Type": "multipart/form-data" },
                                    });
                                    toast.success("Comprovante adicionado!", { id: toastId });
                                    refetch();
                                  } catch (err: any) {
                                    const errMsg = err?.response?.data?.detail || "Falha ao enviar comprovante.";
                                    toast.error(errMsg, { id: toastId });
                                  }
                                };
                                input.click();
                              }}
                            >
                              <Paperclip size={16} className="text-mm-muted hover:text-mm-primary" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label="Excluir"
                              onClick={() => excluir(l.id, l.descricao)}
                              title="Excluir Lançamento"
                            >
                              <Trash2 size={16} className="text-destructive" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-mm-muted">
                      Nenhum lançamento neste evento.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Paginação */}
          {data && data.total > pageSize && (
            <div className="flex items-center justify-between border-t px-4 py-3 text-sm">
              <span className="text-mm-muted">
                {data.items.length} de {data.total} · pág. {data.page}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page * pageSize >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Próxima
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}