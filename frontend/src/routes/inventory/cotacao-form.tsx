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
import { useFornecedores } from "@/routes/inventory/hooks";
import type { Cotacao } from "@/routes/inventory/types";

const precoSchema = z.object({
  fornecedor_id: z.coerce.number().int().positive(),
  valor_unitario: z.string().default("0"),
});

const itemSchema = z.object({
  produto_id: z.coerce.number().int().positive("Selecione"),
  quantidade: z.string().min(1, "Qtd"),
  precos: z.array(precoSchema),
});

const schema = z.object({
  observacao: z.string().default(""),
  itens: z.array(itemSchema).min(1, "Pelo menos 1 item"),
});

type FormValues = z.input<typeof schema>;

export function CotacaoFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const { data: produtos } = useProdutos({ ativo: true });
  const { data: fornecedores } = useFornecedores(true);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      observacao: "",
      itens: [
        {
          produto_id: 0 as unknown as number,
          quantidade: "1",
          precos: [],
        },
      ],
    },
  });
  const fields = useFieldArray({ control: form.control, name: "itens" });

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Cotacao>(`/inventory/cotacoes/${id}`)
      .then((res) => {
        const c = res.data;
        if (c.status !== "ABERTA") {
          toast.error("Cotação não está ABERTA - não pode editar");
          navigate("/inventory/cotacoes");
          return;
        }
        form.reset({
          observacao: c.observacao,
          itens: c.itens.map((it) => ({
            produto_id: String(it.produto_id) as unknown as number,
            quantidade: String(it.quantidade),
            precos: it.precos.map((p) => ({
              fornecedor_id: String(p.fornecedor_id) as unknown as number,
              valor_unitario: String(p.valor_unitario),
            })),
          })),
        });
      })
      .catch(() => toast.error("Cotação não encontrada"));
  }, [id, isEdit, form, navigate]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = {
      ...values,
      itens: values.itens.map((i) => ({
        produto_id: Number(i.produto_id),
        quantidade: Number(i.quantidade),
        precos: i.precos.map((p) => ({
          fornecedor_id: Number(p.fornecedor_id),
          valor_unitario: Number(p.valor_unitario),
        })),
      })),
    };
    try {
      if (isEdit) {
        await api.patch(`/inventory/cotacoes/${id}`, payload);
        toast.success("Cotação atualizada");
      } else {
        await api.post(`/inventory/cotacoes`, payload);
        toast.success("Cotação criada");
      }
      navigate("/inventory/cotacoes");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/inventory/cotacoes")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar cotação" : "Nova cotação"}
        </h1>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Observação</CardTitle></CardHeader>
        <CardContent>
          <Input {...form.register("observacao")} placeholder="notas internas" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row justify-between">
          <CardTitle className="text-base">Itens + grade de preços por fornecedor</CardTitle>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() =>
              fields.append({
                produto_id: 0 as unknown as number,
                quantidade: "1",
                precos: [],
              })
            }
          >
            <Plus className="mr-1" size={14} /> Item
          </Button>
        </CardHeader>
        <CardContent>
          {form.formState.errors.itens?.message && (
            <p className="text-xs text-destructive mb-2">{form.formState.errors.itens.message}</p>
          )}
          <div className="space-y-4">
            {fields.fields.map((f, idx) => (
              <div key={f.id} className="border border-border rounded-md p-4 space-y-3">
                <div className="grid grid-cols-[1fr_120px_40px] gap-2 items-end">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Produto</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...form.register(`itens.${idx}.produto_id`)}
                    >
                      <option value="0">Selecione...</option>
                      {produtos?.items.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.sku} - {p.nome}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Qtd</Label>
                    <Input type="number" step="0.01" {...form.register(`itens.${idx}.quantidade`)} />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => fields.remove(idx)}
                  >
                    <Trash2 size={16} className="text-destructive" />
                  </Button>
                </div>

                <PrecoPorItem
                  fornecedores={fornecedores ?? []}
                  selectedIndex={idx}
                  control={form.control}
                />
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-6">
            <Button variant="outline" type="button" onClick={() => navigate("/inventory/cotacoes")}>
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

function PrecoPorItem({
  fornecedores,
  selectedIndex,
  control,
}: {
  fornecedores: { id: number; nome: string }[];
  selectedIndex: number;
  control: ReturnType<typeof useForm<FormValues>>["control"];
}) {
  // sub-field-array para preços
  const preçosFields = useFieldArray({
    control,
    name: `itens.${selectedIndex}.precos` as const,
  });

  return (
    <div className="ml-2 border-l-2 border-mm-accent/30 pl-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-mm-muted">Preços por fornecedor</span>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={() =>
            preçosFields.append({
              fornecedor_id: 0 as unknown as number,
              valor_unitario: "0",
            })
          }
        >
          <Plus size={14} /> Adicionar
        </Button>
      </div>
      {preçosFields.fields.map((pf, pIdx) => (
        <div key={pf.id} className="grid grid-cols-[1fr_120px_32px] gap-2 items-end">
          <div>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...control.register(`itens.${selectedIndex}.precos.${pIdx}.fornecedor_id` as const)}
            >
              <option value="0">Selecione...</option>
              {fornecedores
                .filter(
                  (f) =>
                    !preçosFields
                      .fields
                      .some((p, ix) => ix !== pIdx && String((p as any).fornecedor_id) === String(f.id))
                )
                .map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.nome}
                  </option>
                ))}
            </select>
          </div>
          <Input
            type="number"
            step="0.01"
            placeholder="R$ unit"
            {...control.register(`itens.${selectedIndex}.precos.${pIdx}.valor_unitario` as const)}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => preçosFields.remove(pIdx)}
          >
            <Trash2 size={14} className="text-destructive" />
          </Button>
        </div>
      ))}
      {preçosFields.fields.length === 0 && (
        <p className="text-xs text-mm-muted">Nenhum preço cadastrado.</p>
      )}
    </div>
  );
}