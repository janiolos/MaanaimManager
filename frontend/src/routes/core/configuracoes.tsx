import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

interface ConfigSistema {
  id: number;
  nome_sistema: string;
  rotulo_evento_singular: string;
  rotulo_evento_plural: string;
  modulo_financeiro_ativo: boolean;
  modulo_estoque_ativo: boolean;
  modulo_hospedagem_ativo: boolean;
  modulo_notificacoes_ativo: boolean;
  modulo_pos_ativo: boolean;
}

export function ConfiguracoesPage() {
  const [config, setConfig] = useState<ConfigSistema | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/core/configuracao")
      .then((res) => setConfig(res.data))
      .catch(() => toast.error("Erro ao carregar configurações"))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      await api.patch("/core/configuracao", config);
      toast.success("Configurações salvas");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-sm text-mm-muted">Carregando...</p>;
  if (!config) return <p className="text-sm text-mm-muted">Nenhuma configuração encontrada.</p>;

  return (
    <div className="space-y-4 max-w-2xl">
      <h1 className="text-2xl font-bold tracking-tight">Configurações do Sistema</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Geral</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Nome do Sistema</Label>
            <Input
              value={config.nome_sistema}
              onChange={(e) => setConfig({ ...config, nome_sistema: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Rótulo Evento (singular)</Label>
              <Input
                value={config.rotulo_evento_singular}
                onChange={(e) => setConfig({ ...config, rotulo_evento_singular: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Rótulo Evento (plural)</Label>
              <Input
                value={config.rotulo_evento_plural}
                onChange={(e) => setConfig({ ...config, rotulo_evento_plural: e.target.value })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Módulos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <ToggleRow
            label="Financeiro"
            value={config.modulo_financeiro_ativo}
            onChange={(v) => setConfig({ ...config, modulo_financeiro_ativo: v })}
          />
          <ToggleRow
            label="Estoque"
            value={config.modulo_estoque_ativo}
            onChange={(v) => setConfig({ ...config, modulo_estoque_ativo: v })}
          />
          <ToggleRow
            label="Hospedagem"
            value={config.modulo_hospedagem_ativo}
            onChange={(v) => setConfig({ ...config, modulo_hospedagem_ativo: v })}
          />
          <ToggleRow
            label="Notificações"
            value={config.modulo_notificacoes_ativo}
            onChange={(v) => setConfig({ ...config, modulo_notificacoes_ativo: v })}
          />
          <ToggleRow
            label="PDV (Ponto de Venda)"
            value={config.modulo_pos_ativo}
            onChange={(v) => setConfig({ ...config, modulo_pos_ativo: v })}
          />
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={saving} className="w-full">
        <Save className="h-4 w-4 mr-1" />
        {saving ? "Salvando..." : "Salvar Configurações"}
      </Button>
    </div>
  );
}

function ToggleRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between p-3 rounded border border-border cursor-pointer hover:bg-muted/50">
      <span className="text-sm font-medium">{label}</span>
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        className="h-5 w-5 accent-mm-accent"
      />
    </label>
  );
}
