import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useProdutos } from "@/routes/inventory/hooks";
import type { Requisicao } from "@/routes/inventory/types";
import { REQUISICAO_AREA_LABELS } from "@/routes/inventory/types";

const itemSchema = z.object({
  produto_id: z.coerce.number().int().positive("Selecione"),
  quantidade: z.string().min(1, "Qtd"),
});

const schema = z.object({
  area: z.enum(["COZINHA", "COPA", "CANTINA", "COPA_PASTORES", "SECRETARIA"]),
  observacao: z.string().default(""),
  itens: z.array(itemSchema).min(1, "Pelo menos 1 item"),
});

type FormValues = z.input<typeof schema>;

export function RequisicaoFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const { data: produtos } = useProdutos({ ativo: true });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      area: "COZINHA",
      observacao: "",
      itens: [{ produto_id: 0 as unknown as number, quantidade: "1" }],
    },
  });
  const fields = useFieldArray({ control: form.control, name: "itens" });

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Requisicao>(`/inventory/requisicoes/${id}`)
      .then((res) => {
        const r = res.data;
        if (r.status !== "ABERTA") {
          toast.error("Requisição não está ABERTA - não pode editar");
          navigate("/inventory/requisicoes");
          return;
        }
        form.reset({
          area: r.area as FormValues["area"],
          observacao: r.observacao,
          itens: r.itens.map((i) => ({
            produto_id: String(i.produto_id) as unknown as number,
            quantidade: String(i.quantidade),
          })),
        });
      })
      .catch(() => toast.error("Requisição não encontrada"));
  }, [id, isEdit, form, navigate]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = {
      ...values,
      itens: values.itens.map((i) => ({
        produto_id: Number(i.produto_id),
        quantidade: Number(i.quantidade),
      })),
    };
    try {
      if (isEdit) {
        await api.patch(`/inventory/requisicoes/${id}`, payload);
        toast.success("Requisição atualizada");
      } else {
        await api.post(`/inventory/requisicoes`, payload);
        toast.success("Requisição criada");
      }
      navigate("/inventory/requisicoes");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/inventory/requisicoes")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar requisição" : "Nova requisição"}
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cabeçalho</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Área</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                {...form.register("area")}
              >
                {Object.entries(REQUISICAO_AREA_LABELS).map(([v, label]) => (
                  <option key={v} value={v}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="observacao">Observação</Label>
              <Input id="observacao" {...form.register("observacao")} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row justify-between">
          <CardTitle className="text-base">Itens</CardTitle>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => fields.append({ produto_id: 0 as unknown as number, quantidade: "1" })}
          >
            <Plus className="mr-1" size={14} /> Item
          </Button>
        </CardHeader>
        <CardContent>
          {form.formState.errors.itens?.message && (
            <p className="text-xs text-destructive mb-2">{form.formState.errors.itens.message}</p>
          )}
          <div className="space-y-2">
            {fields.fields.map((f, idx) => (
              <div key={f.id} className="grid grid-cols-[1fr_100px_40px] gap-2 items-end">
                <div className="space-y-1.5">
                  <Label className="text-xs">Produto</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    {...form.register(`itens.${idx}.produto_id`)}
                  >
                    <option value="0">Selecione...</option>
                    {produtos?.items
                      .filter(
                        (p) =>
                          // esconde produto já selecionado em outro item
                          !form
                            .getValues("itens")
                            .some((i, ix) => ix !== idx && String(i.produto_id) === String(p.id))
                      )
                      .map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.sku} - {p.nome} (disp: {p.estoque_atual} {p.unidade})
                        </option>
                      ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Qtd</Label>
                  <Input
                    type="number"
                    step="0.01"
                    {...form.register(`itens.${idx}.quantidade` as const)}
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => fields.remove(idx)}
                  disabled={fields.fields.length <= 1}
                >
                  <Trash2 size={16} className="text-destructive" />
                </Button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-6">
            <Button variant="outline" type="button" onClick={() => navigate("/inventory/requisicoes")}>
              Cancelar
            </Button>
            <Button type="submit" onClick={form.handleSubmit(onSubmit)} disabled={saving}>
              <Save className="mr-2" size={16} /> {saving ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}