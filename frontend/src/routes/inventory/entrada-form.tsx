import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Save } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useProdutos } from "@/routes/inventory/hooks";

const schema = z.object({
  produto_id: z.coerce.number().int().positive("Selecione um produto"),
  data: z.string().min(1, "Data obrigatória"),
  quantidade: z.string().min(1, "Qtd obrigatória"),
  custo_unitario: z.string().default("0"),
  documento: z.string().default(""),
  observacao: z.string().default(""),
});

type FormValues = z.input<typeof schema>;

export function EntradaFormPage() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const { data: produtos } = useProdutos({ ativo: true });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      data: new Date().toISOString().slice(0, 10),
      custo_unitario: "0",
      documento: "",
      observacao: "",
    },
  });

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = {
      ...values,
      quantidade: Number(values.quantidade),
      custo_unitario: Number(values.custo_unitario),
    };
    try {
      await api.post("/inventory/entradas", payload);
      toast.success("Entrada registrada - estoque atualizado (média ponderada)");
      navigate("/inventory/produtos");
    } catch (err) {
      toast.error("Falha ao registrar entrada");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/inventory/produtos")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">Registrar entrada de estoque</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            A entrada recalcula o custo médio ponderado automaticamente.
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="produto_id">Produto</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("produto_id")}
                >
                  <option value="">Selecione...</option>
                  {produtos?.items.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.sku} - {p.nome} (atual: {p.estoque_atual} {p.unidade})
                    </option>
                  ))}
                </select>
                {form.formState.errors.produto_id && (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.produto_id.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="data">Data</Label>
                <Input id="data" type="date" {...form.register("data")} />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="quantidade">Quantidade</Label>
                <Input id="quantidade" type="number" step="0.01" {...form.register("quantidade")} />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="custo_unitario">Custo unitário (R$)</Label>
                <Input
                  id="custo_unitario"
                  type="number"
                  step="0.01"
                  {...form.register("custo_unitario")}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="documento">Documento (NF)</Label>
                <Input id="documento" {...form.register("documento")} />
              </div>

              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="observacao">Observação</Label>
                <Input id="observacao" {...form.register("observacao")} />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" type="button" onClick={() => navigate("/inventory/produtos")}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="mr-2" size={16} /> {saving ? "Salvando..." : "Registrar entrada"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}