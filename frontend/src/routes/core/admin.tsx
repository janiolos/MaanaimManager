import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Users, Calendar, Building, Settings, Shield, ArrowLeft, Plus, Trash2, Edit2, Check, X, KeyRound, Lock, Database } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useAdminUsers,
  useAdminGrupos,
  useCriarUser,
  useAtualizarUser,
  useDeletarUser,
  useResetPasswordUser,
  useEventos,
  useCentrosCusto,
} from "@/routes/core/hooks";
import { api } from "@/lib/api";
import type { User } from "@/routes/core/types";
import { STATUS_EVENTO_LABELS } from "@/routes/core/types";
import { cn } from "@/lib/utils";
import { PermissoesTab } from "./permissoes-tab";
import { BaseDeDadosTab } from "./base-de-dados-tab";

type Aba = "usuarios" | "eventos" | "centros" | "config" | "permissoes" | "base-de-dados";

export function AdminPage() {
  const [aba, setAba] = useState<Aba>("usuarios");

  const abas: { key: Aba; label: string; icon: React.ReactNode }[] = [
    { key: "usuarios", label: "Usuários", icon: <Users className="h-4 w-4" /> },
    { key: "permissoes", label: "Permissões", icon: <Lock className="h-4 w-4" /> },
    { key: "eventos", label: "Eventos", icon: <Calendar className="h-4 w-4" /> },
    { key: "centros", label: "Centros de Custo", icon: <Building className="h-4 w-4" /> },
    { key: "base-de-dados", label: "Base de Dados", icon: <Database className="h-4 w-4" /> },
    { key: "config", label: "Configurações", icon: <Settings className="h-4 w-4" /> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => window.history.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-mm-accent" />
          <h1 className="text-2xl font-bold tracking-tight">Administração do Sistema</h1>
        </div>
      </div>

      <div className="flex gap-1 border-b border-border pb-1 overflow-x-auto">
        {abas.map((a) => (
          <button
            key={a.key}
            onClick={() => setAba(a.key)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              aba === a.key
                ? "bg-mm-accent text-white"
                : "text-mm-muted hover:text-foreground hover:bg-muted/50"
            )}
          >
            {a.icon}
            {a.label}
          </button>
        ))}
      </div>

      {aba === "usuarios" && <UsuariosTab />}
      {aba === "permissoes" && <PermissoesTab />}
      {aba === "eventos" && <EventosTab />}
      {aba === "centros" && <CentrosTab />}
      {aba === "base-de-dados" && <BaseDeDadosTab />}
      {aba === "config" && <ConfigTab />}
    </div>
  );
}

/* ====================================================================== */
/* USUÁRIOS                                                               */
/* ====================================================================== */

function UsuariosTab() {
  const { data: users, isLoading } = useAdminUsers();
  const { data: grupos } = useAdminGrupos();
  const criar = useCriarUser();
  const atualizar = useAtualizarUser();
  const deletar = useDeletarUser();
  const resetSenha = useResetPasswordUser();

  const [modoAdd, setModoAdd] = useState(false);
  const [novo, setNovo] = useState({
    username: "",
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    is_active: true,
    is_superuser: false,
    is_staff: false,
    group_ids: [] as number[],
  });

  const [editando, setEditando] = useState<number | null>(null);
  const [editPayload, setEditPayload] = useState<Partial<User & { group_ids?: number[] }>>({});
  const [resetando, setResetando] = useState<number | null>(null);
  const [novaSenha, setNovaSenha] = useState("");

  const handleCriar = async () => {
    if (!novo.username.trim() || !novo.password) {
      return toast.error("Username e senha são obrigatórios");
    }
    try {
      await criar.mutateAsync(novo);
      setModoAdd(false);
      setNovo({ username: "", first_name: "", last_name: "", email: "", password: "", is_active: true, is_superuser: false, is_staff: false, group_ids: [] });
      toast.success("Usuário criado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar usuário");
    }
  };

  const handleDeletar = async (id: number) => {
    if (!confirm("Desativar este usuário?")) return;
    try {
      await deletar.mutateAsync(id);
      toast.success("Usuário desativado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao desativar");
    }
  };

  const iniciarEdicao = (u: User) => {
    setEditando(u.id);
    setEditPayload({
      first_name: u.first_name,
      last_name: u.last_name,
      email: u.email,
      is_active: u.is_active,
      is_superuser: u.is_superuser,
      is_staff: u.is_staff,
      group_ids: u.groups.map((g) => g.id),
    });
  };

  const salvarEdicao = async (id: number) => {
    try {
      await atualizar.mutateAsync({ id, payload: editPayload });
      setEditando(null);
      toast.success("Usuário atualizado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao atualizar");
    }
  };

  const handleResetSenha = async (id: number) => {
    if (!novaSenha || novaSenha.length < 6) {
      return toast.error("Senha deve ter pelo menos 6 caracteres");
    }
    try {
      await resetSenha.mutateAsync({ id, password: novaSenha });
      setResetando(null);
      setNovaSenha("");
      toast.success("Senha redefinida");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao redefinir senha");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
          {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
          {modoAdd ? "Cancelar" : "Novo Usuário"}
        </Button>
      </div>

      {modoAdd && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Novo Usuário</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Username *</Label>
              <Input value={novo.username} onChange={(e) => setNovo({ ...novo, username: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Nome</Label>
              <Input value={novo.first_name} onChange={(e) => setNovo({ ...novo, first_name: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Sobrenome</Label>
              <Input value={novo.last_name} onChange={(e) => setNovo({ ...novo, last_name: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Email</Label>
              <Input type="email" value={novo.email} onChange={(e) => setNovo({ ...novo, email: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Senha *</Label>
              <Input type="password" value={novo.password} onChange={(e) => setNovo({ ...novo, password: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Grupos</Label>
              <select
                multiple
                className="flex h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={novo.group_ids.map(String)}
                onChange={(e) => {
                  const opts = Array.from(e.target.selectedOptions).map((o) => Number(o.value));
                  setNovo({ ...novo, group_ids: opts });
                }}
              >
                {grupos?.map((g) => (
                  <option key={g.id} value={g.id}>{g.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-4 md:col-span-3">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={novo.is_active} onChange={(e) => setNovo({ ...novo, is_active: e.target.checked })} />
                Ativo
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={novo.is_superuser} onChange={(e) => setNovo({ ...novo, is_superuser: e.target.checked })} />
                Superusuário
              </label>
            </div>
            <div className="md:col-span-3">
              <Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white">
                <Plus className="h-4 w-4 mr-1" /> Criar Usuário
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      <div className="space-y-2">
        {users?.map((u) => (
          <Card key={u.id} className={cn(!u.is_active && "opacity-60")}>
            <CardContent className="py-3">
              {editando === u.id ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                  <div>
                    <Label className="text-xs">Nome</Label>
                    <Input value={editPayload.first_name ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, first_name: e.target.value }))} />
                  </div>
                  <div>
                    <Label className="text-xs">Sobrenome</Label>
                    <Input value={editPayload.last_name ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, last_name: e.target.value }))} />
                  </div>
                  <div>
                    <Label className="text-xs">Email</Label>
                    <Input value={editPayload.email ?? ""} onChange={(e) => setEditPayload((p) => ({ ...p, email: e.target.value }))} />
                  </div>
                  <div>
                    <Label className="text-xs">Grupos</Label>
                    <select
                      multiple
                      className="flex h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={(editPayload.group_ids ?? []).map(String)}
                      onChange={(e) => {
                        const opts = Array.from(e.target.selectedOptions).map((o) => Number(o.value));
                        setEditPayload((p) => ({ ...p, group_ids: opts }));
                      }}
                    >
                      {grupos?.map((g) => (
                        <option key={g.id} value={g.id}>{g.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-4 md:col-span-4">
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={editPayload.is_active ?? false} onChange={(e) => setEditPayload((p) => ({ ...p, is_active: e.target.checked }))} />
                      Ativo
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={editPayload.is_superuser ?? false} onChange={(e) => setEditPayload((p) => ({ ...p, is_superuser: e.target.checked }))} />
                      Superusuário
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={editPayload.is_staff ?? false} onChange={(e) => setEditPayload((p) => ({ ...p, is_staff: e.target.checked }))} />
                      Staff
                    </label>
                  </div>
                  <div className="flex gap-2 md:col-span-4">
                    <Button size="sm" variant="ghost" onClick={() => salvarEdicao(u.id)}>
                      <Check className="h-4 w-4 text-emerald-600" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditando(null)}>
                      <X className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-x-6 gap-y-1 text-sm flex-1">
                    <div>
                      <p className="text-xs text-mm-muted">Username</p>
                      <p className="font-medium">{u.username}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Nome</p>
                      <p>{u.first_name} {u.last_name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Email</p>
                      <p>{u.email || "—"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Grupos</p>
                      <p>{u.groups.map((g) => g.name).join(", ") || "—"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Status</p>
                      <div className="flex gap-1">
                        {!u.is_active && <span className="text-destructive text-xs">Inativo</span>}
                        {u.is_superuser && <span className="text-mm-accent text-xs font-medium">Admin</span>}
                        {u.is_staff && <span className="text-blue-600 text-xs">Staff</span>}
                        {u.is_active && !u.is_superuser && !u.is_staff && <span className="text-xs text-mm-muted">Ativo</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1 ml-4">
                    <Button size="sm" variant="ghost" onClick={() => iniciarEdicao(u)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setResetando(resetando === u.id ? null : u.id)}
                    >
                      <KeyRound className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive"
                      onClick={() => handleDeletar(u.id)}
                      disabled={deletar.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
              {resetando === u.id && (
                <div className="mt-3 flex gap-2 items-end border-t pt-3">
                  <div className="flex-1">
                    <Label className="text-xs">Nova Senha</Label>
                    <Input type="password" value={novaSenha} onChange={(e) => setNovaSenha(e.target.value)} />
                  </div>
                  <Button size="sm" onClick={() => handleResetSenha(u.id)} disabled={resetSenha.isPending}>
                    Redefinir
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setResetando(null)}>
                    <X className="h-4 w-4" />
                  </Button>
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
/* EVENTOS                                                                 */
/* ====================================================================== */

function EventosTab() {
  const { data: eventos, isLoading } = useEventos(true);
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" onClick={() => navigate("/core/eventos/novo")}>
          <Plus className="h-4 w-4 mr-1" /> Novo Evento
        </Button>
      </div>
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="space-y-2">
        {eventos?.map((ev) => (
          <Card key={ev.id}>
            <CardContent className="py-3">
              <div className="flex items-center justify-between">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-sm flex-1">
                  <div>
                    <p className="text-xs text-mm-muted">Nome</p>
                    <p className="font-medium">{ev.nome}</p>
                  </div>
                  <div>
                    <p className="text-xs text-mm-muted">Período</p>
                    <p>
                      {new Date(ev.data_inicio).toLocaleDateString("pt-BR")} →{" "}
                      {new Date(ev.data_fim).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-mm-muted">Status</p>
                    <p>{STATUS_EVENTO_LABELS[ev.status] || ev.status}</p>
                  </div>
                  <div>
                    <p className="text-xs text-mm-muted">Situação</p>
                    <p className={cn(ev.fechado && "text-destructive")}>
                      {ev.fechado ? "Encerrado" : "Aberto"}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1 ml-4">
                  <Button size="sm" variant="ghost" onClick={() => navigate(`/core/eventos/${ev.id}/editar`)}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  {!ev.fechado && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive"
                      onClick={async () => {
                        if (!confirm(`Encerrar o evento "${ev.nome}"?`)) return;
                        try {
                          await api.post(`/core/eventos/${ev.id}/encerrar`);
                          toast.success("Evento encerrado");
                        } catch (err: any) {
                          toast.error(err?.response?.data?.detail || "Erro ao encerrar");
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* CENTROS DE CUSTO                                                        */
/* ====================================================================== */

function CentrosTab() {
  const { data: centros, isLoading } = useCentrosCusto();

  return (
    <div className="space-y-4">
      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {centros?.map((c) => (
          <Card key={c.id}>
            <CardContent className="py-4">
              <p className="font-medium">{c.nome}</p>
              <p className="text-xs text-mm-muted">Código: {c.codigo}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ====================================================================== */
/* CONFIGURAÇÕES                                                           */
/* ====================================================================== */

function ConfigTab() {
  const navigate = useNavigate();

  return (
    <div className="space-y-4 max-w-xl">
      <Card className="cursor-pointer hover:bg-muted/50" onClick={() => navigate("/configuracoes")}>
        <CardContent className="py-4 flex items-center justify-between">
          <div>
            <p className="font-medium">Configurações do Sistema</p>
            <p className="text-xs text-mm-muted">Nome, rótulos, módulos ativos</p>
          </div>
          <Settings className="h-5 w-5 text-mm-muted" />
        </CardContent>
      </Card>
    </div>
  );
}
