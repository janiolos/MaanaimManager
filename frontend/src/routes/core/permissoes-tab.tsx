import { useState } from "react";
import { toast } from "sonner";
import { Shield, Plus, Trash2, Check, X, ChevronDown, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Permission, Role } from "@/routes/core/types";
import {
  useAdminUsers,
  usePermissions,
  useRoles,
  useUserPermissions,
  useAddUserPermission,
  useRemoveUserPermission,
  useAddUserRole,
  useRemoveUserRole,
  useSyncRolePermissions,
} from "@/routes/core/hooks";
export function PermissoesTab() {
  const { data: users, isLoading: usersLoading } = useAdminUsers();
  const { data: permissions } = usePermissions();
  const { data: roles } = useRoles();

  const [expandedUser, setExpandedUser] = useState<number | null>(null);
  const [abaSecundaria, setAbaSecundaria] = useState<"usuarios" | "roles">("usuarios");
  const [editandoRole, setEditandoRole] = useState<number | null>(null);
  const [rolePermsSelecionadas, setRolePermsSelecionadas] = useState<number[]>([]);

  const addPerm = useAddUserPermission();
  const removePerm = useRemoveUserPermission();
  const addRole = useAddUserRole();
  const removeRole = useRemoveUserRole();
  const syncRole = useSyncRolePermissions();

  const handleToggleRoleEdit = (role: Role) => {
    if (editandoRole === role.id) {
      setEditandoRole(null);
      return;
    }
    setEditandoRole(role.id);
    setRolePermsSelecionadas(role.permissions?.map((p) => p.id) ?? []);
  };

  const handleSalvarRole = async (roleId: number) => {
    try {
      await syncRole.mutateAsync({ roleId, permissionIds: rolePermsSelecionadas });
      setEditandoRole(null);
      toast.success("Papel atualizado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao atualizar papel");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-1 border-b border-border pb-1">
        {[
          { key: "usuarios" as const, label: "Por Usuário" },
          { key: "roles" as const, label: "Papéis (Roles)" },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setAbaSecundaria(t.key)}
            className={cn(
              "px-3 py-1.5 text-sm font-medium rounded-t-md transition-colors",
              abaSecundaria === t.key
                ? "bg-mm-accent text-white"
                : "text-mm-muted hover:text-foreground hover:bg-muted/50"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ========== POR USUÁRIO ========== */}
      {abaSecundaria === "usuarios" && (
        <div className="space-y-2">
          {usersLoading && <p className="text-sm text-mm-muted">Carregando usuários...</p>}
          {users?.map((u) => (
            <Card key={u.id} className={cn(!u.is_active && "opacity-60")}>
              <CardContent className="py-3">
                <div
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setExpandedUser(expandedUser === u.id ? null : u.id)}
                >
                  <div className="flex items-center gap-2">
                    {expandedUser === u.id ? (
                      <ChevronDown className="h-4 w-4 text-mm-muted" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-mm-muted" />
                    )}
                    <span className="font-medium">{u.first_name} {u.last_name}</span>
                    <span className="text-xs text-mm-muted">({u.username})</span>
                    {u.is_superuser && <Badge className="bg-mm-accent text-white text-[10px]">Admin</Badge>}
                  </div>
                  <UserScopesBadge userId={u.id} />
                </div>

                {expandedUser === u.id && (
                  <div className="mt-3 pt-3 border-t space-y-4">
                    <UserPermissionsEditor
                      userId={u.id}
                      permissions={permissions ?? []}
                      roles={roles ?? []}
                      addPerm={addPerm}
                      removePerm={removePerm}
                      addRole={addRole}
                      removeRole={removeRole}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ========== PAPÉIS ========== */}
      {abaSecundaria === "roles" && (
        <div className="space-y-3">
          {roles?.map((role) => (
            <Card key={role.id}>
              <CardContent className="py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{role.nome}</p>
                    <p className="text-xs text-mm-muted">{role.descricao}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost" onClick={() => handleToggleRoleEdit(role)}>
                      {editandoRole === role.id ? <X className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                {editandoRole === role.id && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    <p className="text-sm font-medium">Permissões do papel:</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {permissions?.map((p) => (
                        <label
                          key={p.id}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded border text-xs cursor-pointer",
                            rolePermsSelecionadas.includes(p.id)
                              ? "border-mm-accent bg-mm-accent/10"
                              : "border-border"
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={rolePermsSelecionadas.includes(p.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setRolePermsSelecionadas((prev) => [...prev, p.id]);
                              } else {
                                setRolePermsSelecionadas((prev) => prev.filter((id) => id !== p.id));
                              }
                            }}
                            className="accent-mm-accent"
                          />
                          <div>
                            <p className="font-medium">{p.nome}</p>
                            <p className="text-[10px] text-mm-muted">{p.scope}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleSalvarRole(role.id)}
                      disabled={syncRole.isPending}
                      className="bg-mm-accent text-white"
                    >
                      <Check className="h-4 w-4 mr-1" /> Salvar Permissões
                    </Button>
                  </div>
                )}

                {editandoRole !== role.id && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {role.permissions?.map((p: Permission) => (
                      <Badge key={p.id} variant="outline" className="text-xs">
                        {p.nome}
                      </Badge>
                    )) ?? <span className="text-xs text-mm-muted">Nenhuma permissão</span>}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ====================================================================== */
/* BADGE DE SCOPES (carrega do endpoint)                                  */
/* ====================================================================== */

function UserScopesBadge({ userId }: { userId: number }) {
  const { data } = useUserPermissions(userId);
  if (!data) return null;
  return (
    <div className="flex flex-wrap gap-1 max-w-[300px] justify-end">
      {data.scopes.slice(0, 4).map((s: string) => (
        <Badge key={s} variant="secondary" className="text-[10px]">
          {s}
        </Badge>
      ))}
      {data.scopes.length > 4 && (
        <Badge variant="secondary" className="text-[10px]">
          +{data.scopes.length - 4}
        </Badge>
      )}
    </div>
  );
}

/* ====================================================================== */
/* EDITOR DE PERMISSÕES POR USUÁRIO                                       */
/* ====================================================================== */

function UserPermissionsEditor({
  userId,
  permissions,
  roles,
  addPerm,
  removePerm,
  addRole,
  removeRole,
}: {
  userId: number;
  permissions: import("@/routes/core/types").Permission[];
  roles: import("@/routes/core/types").Role[];
  addPerm: ReturnType<typeof useAddUserPermission>;
  removePerm: ReturnType<typeof useRemoveUserPermission>;
  addRole: ReturnType<typeof useAddUserRole>;
  removeRole: ReturnType<typeof useRemoveUserRole>;
}) {
  const { data: up } = useUserPermissions(userId);
  const [aba, setAba] = useState<"roles" | "perms">("roles");

  const userRoleIds = new Set(up?.roles.map((r: Role) => r.id) ?? []);
  const userPermIds = new Set(up?.permissions.map((p: Permission) => p.id) ?? []);

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button
          onClick={() => setAba("roles")}
          className={cn(
            "px-3 py-1 text-xs font-medium rounded-full",
            aba === "roles" ? "bg-mm-accent text-white" : "bg-muted text-mm-muted"
          )}
        >
          Papéis
        </button>
        <button
          onClick={() => setAba("perms")}
          className={cn(
            "px-3 py-1 text-xs font-medium rounded-full",
            aba === "perms" ? "bg-mm-accent text-white" : "bg-muted text-mm-muted"
          )}
        >
          Permissões Individuais
        </button>
      </div>

      {/* Papéis */}
      {aba === "roles" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
          {roles.map((r: Role) => {
            const ativo = userRoleIds.has(r.id);
            return (
              <div
                key={r.id}
                className={cn(
                  "flex items-center justify-between p-3 rounded border text-sm",
                  ativo ? "border-mm-accent bg-mm-accent/5" : "border-border"
                )}
              >
                <div>
                  <p className="font-medium">{r.nome}</p>
                  <p className="text-xs text-mm-muted">{r.descricao}</p>
                </div>
                <Button
                  size="sm"
                  variant={ativo ? "destructive" : "default"}
                  className={cn("h-7 text-xs", !ativo && "bg-mm-accent text-white")}
                  onClick={async () => {
                    try {
                      if (ativo) {
                        await removeRole.mutateAsync({ userId, roleId: r.id });
                        toast.success("Papel removido");
                      } else {
                        await addRole.mutateAsync({ userId, roleId: r.id });
                        toast.success("Papel adicionado");
                      }
                    } catch (err: any) {
                      toast.error(err?.response?.data?.detail || "Erro");
                    }
                  }}
                  disabled={addRole.isPending || removeRole.isPending}
                >
                  {ativo ? <Trash2 className="h-3 w-3" /> : <Plus className="h-3 w-3" />}
                </Button>
              </div>
            );
          })}
        </div>
      )}

      {/* Permissões Individuais */}
      {aba === "perms" && (
        <div className="space-y-3">
          {[...new Set(permissions.map((p) => p.categoria))].map((cat) => (
            <div key={cat}>
              <p className="text-xs font-semibold uppercase text-mm-muted mb-1">{cat}</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {permissions
                  .filter((p) => p.categoria === cat)
                  .map((p) => {
                    const ativo = userPermIds.has(p.id);
                    return (
                      <label
                        key={p.id}
                        className={cn(
                          "flex items-center gap-2 p-2 rounded border text-xs cursor-pointer",
                          ativo ? "border-mm-accent bg-mm-accent/10" : "border-border"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={ativo}
                          onChange={async (e) => {
                            try {
                              if (e.target.checked) {
                                await addPerm.mutateAsync({ userId, permissionId: p.id });
                                toast.success("Permissão adicionada");
                              } else {
                                await removePerm.mutateAsync({ userId, permissionId: p.id });
                                toast.success("Permissão removida");
                              }
                            } catch (err: any) {
                              toast.error(err?.response?.data?.detail || "Erro");
                            }
                          }}
                          disabled={addPerm.isPending || removePerm.isPending}
                          className="accent-mm-accent"
                        />
                        <div>
                          <p className="font-medium">{p.nome}</p>
                          <p className="text-[10px] text-mm-muted">{p.scope}</p>
                        </div>
                      </label>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
