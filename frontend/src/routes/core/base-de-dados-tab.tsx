import { useState } from "react";
import { toast } from "sonner";
import { Plus, Trash2, Edit2, Check, X, Search, ChevronLeft, ChevronRight, ShoppingCart, Store, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { cn, formatBRL, formatDateTime } from "@/lib/utils";
import type { CentroCusto, CategoriaFinanceira, ContaCaixa, Fornecedor } from "@/routes/core/types";
import {
  useAdminCentrosCusto,
  useCriarCentroCusto,
  useAtualizarCentroCusto,
  useDeletarCentroCusto,
  useAdminCategorias,
  useCriarCategoria,
  useAtualizarCategoria,
  useDeletarCategoria,
  useAdminContas,
  useCriarConta,
  useAtualizarConta,
  useDeletarConta,
  useAdminFornecedores,
  useCriarFornecedor,
  useAtualizarFornecedor,
  useDeletarFornecedor,
  useAdminLocaisVenda,
  useCriarLocalVenda,
  useAtualizarLocalVenda,
  useAdminFamilias,
  useCriarFamilia,
  useDeletarFamilia,
  useAuditLogs,
  useOrdensCompra,
} from "@/routes/core/hooks";

type SubAba = "centros" | "categorias" | "contas" | "fornecedores" | "locais" | "auditoria" | "ordens";

export function BaseDeDadosTab() {
  const [subAba, setSubAba] = useState<SubAba>("centros");

  const subAbas: { key: SubAba; label: string; icon: React.ReactNode }[] = [
    { key: "centros", label: "Centros de Custo", icon: <FileText className="h-3.5 w-3.5" /> },
    { key: "categorias", label: "Categorias Financeiras", icon: <FileText className="h-3.5 w-3.5" /> },
    { key: "contas", label: "Contas Caixa", icon: <FileText className="h-3.5 w-3.5" /> },
    { key: "fornecedores", label: "Fornecedores", icon: <FileText className="h-3.5 w-3.5" /> },
    { key: "locais", label: "Locais de Venda", icon: <Store className="h-3.5 w-3.5" /> },
    { key: "ordens", label: "Pedidos de Compra", icon: <ShoppingCart className="h-3.5 w-3.5" /> },
    { key: "auditoria", label: "Auditoria", icon: <Search className="h-3.5 w-3.5" /> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-1 border-b border-border pb-1 overflow-x-auto">
        {subAbas.map((a) => (
          <button
            key={a.key}
            onClick={() => setSubAba(a.key)}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t-md transition-colors whitespace-nowrap",
              subAba === a.key
                ? "bg-mm-accent text-white"
                : "text-mm-muted hover:text-foreground hover:bg-muted/50"
            )}
          >
            {a.icon}
            {a.label}
          </button>
        ))}
      </div>

      {subAba === "centros" && <CentrosCrud />}
      {subAba === "categorias" && <CategoriasCrud />}
      {subAba === "contas" && <ContasCrud />}
      {subAba === "fornecedores" && <FornecedoresCrud />}
      {subAba === "locais" && <LocaisVendaCrud />}
      {subAba === "ordens" && <OrdensCompraCrud />}
      {subAba === "auditoria" && <AuditoriaCrud />}
    </div>
  );
}

/* ====================================================================== */
/* CENTROS DE CUSTO                                                       */
/* ====================================================================== */

function CentrosCrud() {
  const { data: items, isLoading } = useAdminCentrosCusto();
  const criar = useCriarCentroCusto();
  const atualizar = useAtualizarCentroCusto();
  const deletar = useDeletarCentroCusto();

  const [modoAdd, setModoAdd] = useState(false);
  const [novo, setNovo] = useState({ nome: "", codigo: "", ativo: true });
  const [editando, setEditando] = useState<number | null>(null);
  const [editPayload, setEditPayload] = useState<Partial<CentroCusto>>({});

  const handleCriar = async () => {
    if (!novo.nome.trim() || !novo.codigo.trim()) return toast.error("Nome e código são obrigatórios");
    try {
      await criar.mutateAsync(novo);
      setModoAdd(false);
      setNovo({ nome: "", codigo: "", ativo: true });
      toast.success("Centro de custo criado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar");
    }
  };

  const handleDeletar = async (id: number) => {
    if (!confirm("Excluir este centro de custo?")) return;
    try {
      await deletar.mutateAsync(id);
      toast.success("Excluído");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao excluir");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
          {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
          {modoAdd ? "Cancelar" : "Novo Centro"}
        </Button>
      </div>
      {modoAdd && (
        <Card>
          <CardHeader><CardTitle className="text-base">Novo Centro de Custo</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="space-y-1"><Label className="text-xs">Nome *</Label><Input value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} /></div>
            <div className="space-y-1"><Label className="text-xs">Código *</Label><Input value={novo.codigo} onChange={(e) => setNovo({ ...novo, codigo: e.target.value })} /></div>
            <div className="flex items-center gap-2 pt-5">
              <input type="checkbox" checked={novo.ativo} onChange={(e) => setNovo({ ...novo, ativo: e.target.checked })} />
              <Label className="text-sm">Ativo</Label>
            </div>
            <div className="md:col-span-3"><Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white"><Plus className="h-4 w-4 mr-1" /> Criar</Button></div>
          </CardContent>
        </Card>
      )}
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="space-y-2">
        {!isLoading && (items?.length ?? 0) === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-mm-muted">
              Nenhum fornecedor encontrado.
            </CardContent>
          </Card>
        )}
        {items?.map((item) => (
          <Card key={item.id} className={cn(!item.ativo && "opacity-60")}>
            <CardContent className="py-3">
              {editando === item.id ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                  <div><Label className="text-xs">Nome</Label><Input value={editPayload.nome ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, nome: e.target.value }))} /></div>
                  <div><Label className="text-xs">Código</Label><Input value={editPayload.codigo ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, codigo: e.target.value }))} /></div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={editPayload.ativo ?? false} onChange={(e) => setEditPayload((p) => ({ ...p, ativo: e.target.checked }))} />
                    <Label className="text-sm">Ativo</Label>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost" onClick={async () => { try { await atualizar.mutateAsync({ id: item.id, payload: editPayload }); setEditando(null); toast.success("Atualizado"); } catch (err: any) { toast.error(err?.response?.data?.detail || "Erro"); } }}><Check className="h-4 w-4 text-emerald-600" /></Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditando(null)}><X className="h-4 w-4 text-destructive" /></Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-1 text-sm flex-1">
                    <div><p className="text-xs text-mm-muted">Nome</p><p className="font-medium">{item.nome}</p></div>
                    <div><p className="text-xs text-mm-muted">Código</p><p>{item.codigo}</p></div>
                    <div><p className="text-xs text-mm-muted">Status</p><p className={cn(!item.ativo && "text-destructive")}>{item.ativo ? "Ativo" : "Inativo"}</p></div>
                  </div>
                  <div className="flex gap-1 ml-4">
                    <Button size="sm" variant="ghost" onClick={() => { setEditando(item.id); setEditPayload({ nome: item.nome, codigo: item.codigo, ativo: item.ativo }); }}><Edit2 className="h-4 w-4" /></Button>
                    <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDeletar(item.id)} disabled={deletar.isPending}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* CATEGORIAS FINANCEIRAS                                                 */
/* ====================================================================== */

function CategoriasCrud() {
  const { data: items, isLoading } = useAdminCategorias();
  const criar = useCriarCategoria();
  const atualizar = useAtualizarCategoria();
  const deletar = useDeletarCategoria();

  const [modoAdd, setModoAdd] = useState(false);
  const [novo, setNovo] = useState<{ nome: string; tipo: "RECEITA" | "DESPESA" }>({ nome: "", tipo: "DESPESA" });
  const [editando, setEditando] = useState<number | null>(null);
  const [editPayload, setEditPayload] = useState<Partial<CategoriaFinanceira>>({});

  const handleCriar = async () => {
    if (!novo.nome.trim()) return toast.error("Nome é obrigatório");
    try {
      await criar.mutateAsync(novo);
      setModoAdd(false);
      setNovo({ nome: "", tipo: "DESPESA" });
      toast.success("Categoria criada");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar");
    }
  };

  const handleDeletar = async (id: number) => {
    if (!confirm("Excluir esta categoria?")) return;
    try {
      await deletar.mutateAsync(id);
      toast.success("Excluída");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao excluir");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
          {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
          {modoAdd ? "Cancelar" : "Nova Categoria"}
        </Button>
      </div>
      {modoAdd && (
        <Card>
          <CardHeader><CardTitle className="text-base">Nova Categoria Financeira</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="space-y-1"><Label className="text-xs">Nome *</Label><Input value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} /></div>
            <div className="space-y-1"><Label className="text-xs">Tipo</Label>
              <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={novo.tipo} onChange={(e) => setNovo({ ...novo, tipo: e.target.value as "RECEITA" | "DESPESA" })}>
                <option value="RECEITA">RECEITA</option>
                <option value="DESPESA">DESPESA</option>
              </select>
            </div>
            <div className="md:col-span-3"><Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white"><Plus className="h-4 w-4 mr-1" /> Criar</Button></div>
          </CardContent>
        </Card>
      )}
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="space-y-2">
        {items?.map((item) => (
          <Card key={item.id}>
            <CardContent className="py-3">
              {editando === item.id ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                  <div><Label className="text-xs">Nome</Label><Input value={editPayload.nome ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, nome: e.target.value }))} /></div>
                  <div><Label className="text-xs">Tipo</Label>
                    <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={editPayload.tipo ?? item.tipo} onChange={(e) => setEditPayload((p) => ({ ...p, tipo: e.target.value as "RECEITA" | "DESPESA" }))}>
                      <option value="RECEITA">RECEITA</option>
                      <option value="DESPESA">DESPESA</option>
                    </select>
                  </div>
                  <div className="flex gap-2 md:col-span-2">
                    <Button size="sm" variant="ghost" onClick={async () => { try { await atualizar.mutateAsync({ id: item.id, payload: editPayload }); setEditando(null); toast.success("Atualizado"); } catch (err: any) { toast.error(err?.response?.data?.detail || "Erro"); } }}><Check className="h-4 w-4 text-emerald-600" /></Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditando(null)}><X className="h-4 w-4 text-destructive" /></Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-1 text-sm flex-1">
                    <div><p className="text-xs text-mm-muted">Nome</p><p className="font-medium">{item.nome}</p></div>
                    <div><p className="text-xs text-mm-muted">Tipo</p><p className={cn(item.tipo === "RECEITA" ? "text-emerald-600" : "text-destructive")}>{item.tipo}</p></div>
                  </div>
                  <div className="flex gap-1 ml-4">
                    <Button size="sm" variant="ghost" onClick={() => { setEditando(item.id); setEditPayload({ nome: item.nome, tipo: item.tipo }); }}><Edit2 className="h-4 w-4" /></Button>
                    <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDeletar(item.id)} disabled={deletar.isPending}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* CONTAS CAIXA                                                           */
/* ====================================================================== */

function ContasCrud() {
  const { data: items, isLoading } = useAdminContas();
  const criar = useCriarConta();
  const atualizar = useAtualizarConta();
  const deletar = useDeletarConta();

  const [modoAdd, setModoAdd] = useState(false);
  const [novo, setNovo] = useState({ nome: "", ativo: true });
  const [editando, setEditando] = useState<number | null>(null);
  const [editPayload, setEditPayload] = useState<Partial<ContaCaixa>>({});

  const handleCriar = async () => {
    if (!novo.nome.trim()) return toast.error("Nome é obrigatório");
    try {
      await criar.mutateAsync(novo);
      setModoAdd(false);
      setNovo({ nome: "", ativo: true });
      toast.success("Conta criada");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar");
    }
  };

  const handleDeletar = async (id: number) => {
    if (!confirm("Excluir esta conta?")) return;
    try {
      await deletar.mutateAsync(id);
      toast.success("Excluída");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao excluir");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
          {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
          {modoAdd ? "Cancelar" : "Nova Conta"}
        </Button>
      </div>
      {modoAdd && (
        <Card>
          <CardHeader><CardTitle className="text-base">Nova Conta Caixa</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="space-y-1"><Label className="text-xs">Nome *</Label><Input value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} /></div>
            <div className="flex items-center gap-2 pt-5">
              <input type="checkbox" checked={novo.ativo} onChange={(e) => setNovo({ ...novo, ativo: e.target.checked })} />
              <Label className="text-sm">Ativo</Label>
            </div>
            <div className="md:col-span-3"><Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white"><Plus className="h-4 w-4 mr-1" /> Criar</Button></div>
          </CardContent>
        </Card>
      )}
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="space-y-2">
        {items?.map((item) => (
          <Card key={item.id} className={cn(!item.ativo && "opacity-60")}>
            <CardContent className="py-3">
              {editando === item.id ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                  <div><Label className="text-xs">Nome</Label><Input value={editPayload.nome ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, nome: e.target.value }))} /></div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={editPayload.ativo ?? false} onChange={(e) => setEditPayload((p) => ({ ...p, ativo: e.target.checked }))} />
                    <Label className="text-sm">Ativo</Label>
                  </div>
                  <div className="flex gap-2 md:col-span-2">
                    <Button size="sm" variant="ghost" onClick={async () => { try { await atualizar.mutateAsync({ id: item.id, payload: editPayload }); setEditando(null); toast.success("Atualizado"); } catch (err: any) { toast.error(err?.response?.data?.detail || "Erro"); } }}><Check className="h-4 w-4 text-emerald-600" /></Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditando(null)}><X className="h-4 w-4 text-destructive" /></Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-1 text-sm flex-1">
                    <div><p className="text-xs text-mm-muted">Nome</p><p className="font-medium">{item.nome}</p></div>
                    <div><p className="text-xs text-mm-muted">Status</p><p className={cn(!item.ativo && "text-destructive")}>{item.ativo ? "Ativo" : "Inativo"}</p></div>
                  </div>
                  <div className="flex gap-1 ml-4">
                    <Button size="sm" variant="ghost" onClick={() => { setEditando(item.id); setEditPayload({ nome: item.nome, ativo: item.ativo }); }}><Edit2 className="h-4 w-4" /></Button>
                    <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDeletar(item.id)} disabled={deletar.isPending}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* FORNECEDORES                                                           */
/* ====================================================================== */

function FornecedoresCrud() {
  const { data: items, isLoading } = useAdminFornecedores();
  const criar = useCriarFornecedor();
  const atualizar = useAtualizarFornecedor();
  const deletar = useDeletarFornecedor();

  const [modoAdd, setModoAdd] = useState(false);
  const [novo, setNovo] = useState({ nome: "", documento: "", contato: "", telefone: "", email: "", ativo: true });
  const [editando, setEditando] = useState<number | null>(null);
  const [editPayload, setEditPayload] = useState<Partial<Omit<Fornecedor, "id" | "criado_em">>>({});

  const handleCriar = async () => {
    if (!novo.nome.trim()) return toast.error("Nome é obrigatório");
    try {
      await criar.mutateAsync(novo);
      setModoAdd(false);
      setNovo({ nome: "", documento: "", contato: "", telefone: "", email: "", ativo: true });
      toast.success("Fornecedor criado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar");
    }
  };

  const handleDeletar = async (id: number) => {
    if (!confirm("Excluir este fornecedor?")) return;
    try {
      await deletar.mutateAsync(id);
      toast.success("Excluído");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao excluir");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
          {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
          {modoAdd ? "Cancelar" : "Novo Fornecedor"}
        </Button>
      </div>
      {modoAdd && (
        <Card>
          <CardHeader><CardTitle className="text-base">Novo Fornecedor</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="space-y-1"><Label className="text-xs">Nome *</Label><Input value={novo.nome} onChange={(e) => setNovo({ ...novo, nome: e.target.value })} /></div>
            <div className="space-y-1"><Label className="text-xs">Documento</Label><Input value={novo.documento} onChange={(e) => setNovo({ ...novo, documento: e.target.value })} /></div>
            <div className="space-y-1"><Label className="text-xs">Contato</Label><Input value={novo.contato} onChange={(e) => setNovo({ ...novo, contato: e.target.value })} /></div>
            <div className="space-y-1"><Label className="text-xs">Telefone</Label><Input value={novo.telefone} onChange={(e) => setNovo({ ...novo, telefone: e.target.value })} /></div>
            <div className="space-y-1"><Label className="text-xs">Email</Label><Input type="email" value={novo.email} onChange={(e) => setNovo({ ...novo, email: e.target.value })} /></div>
            <div className="flex items-center gap-2 pt-5">
              <input type="checkbox" checked={novo.ativo} onChange={(e) => setNovo({ ...novo, ativo: e.target.checked })} />
              <Label className="text-sm">Ativo</Label>
            </div>
            <div className="md:col-span-3"><Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white"><Plus className="h-4 w-4 mr-1" /> Criar</Button></div>
          </CardContent>
        </Card>
      )}
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="space-y-2">
        {items?.map((item) => (
          <Card key={item.id} className={cn(!item.ativo && "opacity-60")}>
            <CardContent className="py-3">
              {editando === item.id ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                  <div><Label className="text-xs">Nome</Label><Input value={editPayload.nome ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, nome: e.target.value }))} /></div>
                  <div><Label className="text-xs">Documento</Label><Input value={editPayload.documento ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, documento: e.target.value }))} /></div>
                  <div><Label className="text-xs">Contato</Label><Input value={editPayload.contato ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, contato: e.target.value }))} /></div>
                  <div><Label className="text-xs">Telefone</Label><Input value={editPayload.telefone ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, telefone: e.target.value }))} /></div>
                  <div><Label className="text-xs">Email</Label><Input value={editPayload.email ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, email: e.target.value }))} /></div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={editPayload.ativo ?? false} onChange={(e) => setEditPayload((p) => ({ ...p, ativo: e.target.checked }))} />
                    <Label className="text-sm">Ativo</Label>
                  </div>
                  <div className="flex gap-2 md:col-span-2">
                    <Button size="sm" variant="ghost" onClick={async () => { try { await atualizar.mutateAsync({ id: item.id, payload: editPayload }); setEditando(null); toast.success("Atualizado"); } catch (err: any) { toast.error(err?.response?.data?.detail || "Erro"); } }}><Check className="h-4 w-4 text-emerald-600" /></Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditando(null)}><X className="h-4 w-4 text-destructive" /></Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-x-6 gap-y-1 text-sm flex-1">
                    <div><p className="text-xs text-mm-muted">Nome</p><p className="font-medium">{item.nome}</p></div>
                    <div><p className="text-xs text-mm-muted">Documento</p><p>{item.documento || "—"}</p></div>
                    <div><p className="text-xs text-mm-muted">Contato</p><p>{item.contato || "—"}</p></div>
                    <div><p className="text-xs text-mm-muted">Telefone</p><p>{item.telefone || "—"}</p></div>
                    <div><p className="text-xs text-mm-muted">Status</p><p className={cn(!item.ativo && "text-destructive")}>{item.ativo ? "Ativo" : "Inativo"}</p></div>
                  </div>
                  <div className="flex gap-1 ml-4">
                    <Button size="sm" variant="ghost" onClick={() => { setEditando(item.id); setEditPayload({ nome: item.nome, documento: item.documento, contato: item.contato, telefone: item.telefone, email: item.email, ativo: item.ativo }); }}><Edit2 className="h-4 w-4" /></Button>
                    <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDeletar(item.id)} disabled={deletar.isPending}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* LOCAIS DE VENDA                                                        */
/* ====================================================================== */

function LocaisVendaCrud() {
  const { data: items, isLoading } = useAdminLocaisVenda();
  const criar = useCriarLocalVenda();
  const atualizar = useAtualizarLocalVenda();

  const [modoAdd, setModoAdd] = useState(false);
  const [novoNome, setNovoNome] = useState("");
  const [localFamilias, setLocalFamilias] = useState<number | null>(null);

  const handleCriar = async () => {
    if (!novoNome.trim()) return toast.error("Nome é obrigatório");
    try {
      await criar.mutateAsync({ nome: novoNome.trim() });
      setModoAdd(false);
      setNovoNome("");
      toast.success("Local criado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar");
    }
  };

  const toggleAtivo = async (id: number, ativo: boolean) => {
    try {
      await atualizar.mutateAsync({ id, payload: { ativo } });
      toast.success(ativo ? "Ativado" : "Desativado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
          {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
          {modoAdd ? "Cancelar" : "Novo Local"}
        </Button>
      </div>

      {modoAdd && (
        <Card>
          <CardHeader><CardTitle className="text-base">Novo Local de Venda</CardTitle></CardHeader>
          <CardContent className="flex gap-2 max-w-md">
            <Input placeholder="Nome do local (ex: Cantina)" value={novoNome} onChange={(e) => setNovoNome(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleCriar()} />
            <Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white">
              <Plus className="h-4 w-4 mr-1" /> Criar
            </Button>
          </CardContent>
        </Card>
      )}

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      {localFamilias !== null ? (
        <FamiliasSubTab localId={localFamilias} onVoltar={() => setLocalFamilias(null)} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {items?.map((item) => (
            <Card key={item.id} className={cn(!item.ativo && "opacity-60")}>
              <CardContent className="py-4">
                <div className="flex items-center gap-2">
                  <Store className="h-4 w-4 text-mm-muted" />
                  <p className="font-medium">{item.nome}</p>
                </div>
                <div className="mt-2 text-xs text-mm-muted space-y-1">
                  <p>Escopo: global/perene</p>
                  <p className="flex items-center gap-2">
                    Status:{" "}
                    <button
                      onClick={() => toggleAtivo(item.id, !item.ativo)}
                      className={cn("text-xs px-2 py-0.5 rounded-full border", item.ativo ? "border-emerald-300 text-emerald-600" : "border-destructive/30 text-destructive")}
                    >
                      {item.ativo ? "Ativo" : "Inativo"}
                    </button>
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t flex gap-2">
                  <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => setLocalFamilias(item.id)}>
                    Famílias
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ====================================================================== */
/* FAMÍLIAS (sub-aberta do Local de Venda)                                */
/* ====================================================================== */

function FamiliasSubTab({ localId, onVoltar }: { localId: number; onVoltar: () => void }) {
  const { data: items, isLoading } = useAdminFamilias(localId);
  const criar = useCriarFamilia();
  const deletar = useDeletarFamilia();

  const [novoNome, setNovoNome] = useState("");

  const handleCriar = async () => {
    if (!novoNome.trim()) return toast.error("Nome é obrigatório");
    try {
      await criar.mutateAsync({ localId, nome: novoNome.trim() });
      setNovoNome("");
      toast.success("Família criada");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar");
    }
  };

  const handleDeletar = async (familiaId: number) => {
    if (!confirm("Excluir esta família?")) return;
    try {
      await deletar.mutateAsync({ localId, familiaId });
      toast.success("Excluída");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao excluir");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button size="sm" variant="ghost" onClick={onVoltar}>
          <ChevronLeft className="h-4 w-4 mr-1" /> Voltar
        </Button>
        <h3 className="text-lg font-semibold">Famílias do Local #{localId}</h3>
      </div>

      <div className="flex gap-2 max-w-md">
        <Input placeholder="Nome da família" value={novoNome} onChange={(e) => setNovoNome(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleCriar()} />
        <Button size="sm" onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white">
          <Plus className="h-4 w-4 mr-1" /> Adicionar
        </Button>
      </div>

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
        {items?.map((f: any) => (
          <Card key={f.id}>
            <CardContent className="py-3 flex items-center justify-between">
              <span className="font-medium text-sm">{f.nome}</span>
              <Button size="sm" variant="ghost" className="text-destructive h-7 w-7 p-0" onClick={() => handleDeletar(f.id)} disabled={deletar.isPending}>
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </CardContent>
          </Card>
        ))}
        {items?.length === 0 && !isLoading && (
          <p className="text-sm text-mm-muted col-span-full text-center py-8">Nenhuma família cadastrada.</p>
        )}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* AUDITORIA                                                              */
/* ====================================================================== */

function AuditoriaCrud() {
  const [page, setPage] = useState(1);
  const [methodFilter, setMethodFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const pageSize = 50;

  const filters: Record<string, any> = { page, page_size: pageSize };
  if (methodFilter) filters.method = methodFilter;
  if (statusFilter) filters.status_code = Number(statusFilter);

  const { data, isLoading } = useAuditLogs(filters);

  return (
    <div className="space-y-4">
      <div className="flex gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs">Método</Label>
          <select
            className="flex h-9 w-28 rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={methodFilter}
            onChange={(e) => { setMethodFilter(e.target.value); setPage(1); }}
          >
            <option value="">Todos</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PATCH">PATCH</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Status</Label>
          <select
            className="flex h-9 w-28 rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          >
            <option value="">Todos</option>
            <option value="200">200 OK</option>
            <option value="201">201 Criado</option>
            <option value="204">204 Sucesso</option>
            <option value="400">400 Erro</option>
            <option value="401">401 Não auth</option>
            <option value="403">403 Proibido</option>
            <option value="404">404 Não encontrado</option>
            <option value="422">422 Validação</option>
            <option value="500">500 Erro</option>
          </select>
        </div>
      </div>

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      <div className="space-y-1">
        {data?.items.map((log) => (
          <Card key={log.id} className="py-0">
            <CardContent className="py-2">
              <div className="flex items-center gap-3 text-sm">
                <Badge
                  className={cn(
                    "text-[10px] font-mono",
                    log.method === "GET" && "bg-blue-100 text-blue-700",
                    log.method === "POST" && "bg-emerald-100 text-emerald-700",
                    log.method === "PATCH" && "bg-amber-100 text-amber-700",
                    log.method === "DELETE" && "bg-red-100 text-red-700",
                  )}
                >
                  {log.method}
                </Badge>
                <Badge
                  variant={log.status_code >= 400 ? "destructive" : "secondary"}
                  className="text-[10px] font-mono"
                >
                  {log.status_code}
                </Badge>
                <span className="text-xs text-mm-muted font-mono flex-1 truncate max-w-[400px]">
                  {log.path}
                </span>
                <span className="text-xs text-mm-muted whitespace-nowrap">
                  {log.user_name || "—"}
                </span>
                <span className="text-[10px] text-mm-muted whitespace-nowrap">
                  {formatDateTime(log.created_at)}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {data && data.total > pageSize && (
        <div className="flex items-center justify-center gap-4">
          <Button
            size="sm"
            variant="outline"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft className="h-4 w-4" /> Anterior
          </Button>
          <span className="text-sm text-mm-muted">
            Página {data.page} de {Math.ceil(data.total / pageSize)}
          </span>
          <Button
            size="sm"
            variant="outline"
            disabled={page >= Math.ceil(data.total / pageSize)}
            onClick={() => setPage((p) => p + 1)}
          >
            Próximo <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

/* ====================================================================== */
/* PEDIDOS DE COMPRA                                                      */
/* ====================================================================== */

function OrdensCompraCrud() {
  const [page, setPage] = useState(1);
  const pageSize = 50;
  const { data, isLoading } = useOrdensCompra(page, pageSize);

  const statusLabel: Record<string, string> = {
    PENDENTE: "Pendente",
    ENVIADA: "Enviada",
    FALHA: "Falha",
  };

  const statusColor: Record<string, string> = {
    PENDENTE: "text-amber-600 bg-amber-50",
    ENVIADA: "text-emerald-600 bg-emerald-50",
    FALHA: "text-destructive bg-destructive/10",
  };

  return (
    <div className="space-y-4">
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-xs text-mm-muted">
              <th className="text-left py-2 px-2 font-medium">N°</th>
              <th className="text-left py-2 px-2 font-medium">Fornecedor</th>
              <th className="text-left py-2 px-2 font-medium">Cotação</th>
              <th className="text-right py-2 px-2 font-medium">Valor Total</th>
              <th className="text-left py-2 px-2 font-medium">Status</th>
              <th className="text-left py-2 px-2 font-medium">Criado por</th>
              <th className="text-left py-2 px-2 font-medium">Data</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((oc) => (
              <tr key={oc.id} className="border-b hover:bg-muted/30">
                <td className="py-2 px-2 font-medium">{oc.numero}</td>
                <td className="py-2 px-2">{oc.fornecedor_nome}</td>
                <td className="py-2 px-2 text-mm-muted">#{oc.cotacao_id}</td>
                <td className="py-2 px-2 text-right font-mono">{formatBRL(oc.valor_total)}</td>
                <td className="py-2 px-2">
                  <span className={cn("text-xs px-2 py-0.5 rounded-full", statusColor[oc.status_envio] || "")}>
                    {statusLabel[oc.status_envio] || oc.status_envio}
                  </span>
                </td>
                <td className="py-2 px-2 text-mm-muted">{oc.criado_por_nome}</td>
                <td className="py-2 px-2 text-mm-muted text-xs">{formatDateTime(oc.criado_em)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.total > pageSize && (
        <div className="flex items-center justify-center gap-4">
          <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft className="h-4 w-4" /> Anterior
          </Button>
          <span className="text-sm text-mm-muted">
            Página {data.page} de {Math.ceil(data.total / pageSize)}
          </span>
          <Button size="sm" variant="outline" disabled={page >= Math.ceil(data.total / pageSize)} onClick={() => setPage((p) => p + 1)}>
            Próximo <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
