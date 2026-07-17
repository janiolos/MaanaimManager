import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Save, Paperclip, Trash2, Eye, FileText, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useCategorias, useContas } from "@/routes/finance/hooks";
import type { Lancamento, AnexoLancamento } from "@/routes/finance/types";

const schema = z.object({
  tipo: z.enum(["RECEITA", "DESPESA"]),
  categoria_id: z.coerce.number().int().positive("Selecione categoria"),
  conta_id: z.coerce.number().int().positive("Selecione conta"),
  data: z.string().min(1, "Informe a data"),
  descricao: z.string().min(1, "Informe descrição"),
  valor: z.string().min(1, "Informe valor"),
  forma_pagamento: z.enum(["DINHEIRO", "PIX", "CARTAO", "OUTRO"]),
});

type FormValues = z.input<typeof schema>;

export function FinanceFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [anexos, setAnexos] = useState<AnexoLancamento[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      tipo: "RECEITA",
      forma_pagamento: "DINHEIRO",
    },
  });

  const tipoWatch = form.watch("tipo");
  const { data: categorias } = useCategorias(tipoWatch);
  const { data: contas } = useContas();

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Lancamento>(`/finance/lancamentos/${id}`)
      .then((res) => {
        const l = res.data;
        form.reset({
          tipo: l.tipo,
          categoria_id: String(l.categoria_id) as unknown as number,
          conta_id: String(l.conta_id) as unknown as number,
          data: l.data,
          descricao: l.descricao,
          valor: l.valor,
          forma_pagamento: l.forma_pagamento,
        });
        setAnexos(l.anexos || []);
      })
      .catch(() => toast.error("Lançamento não encontrado"));
  }, [id, isEdit, form]);

  async function uploadFileForLancamento(lancamentoId: number, fileToUpload: File) {
    const formData = new FormData();
    formData.append("file", fileToUpload);
    formData.append("descricao", fileToUpload.name);

    const res = await api.post<{ id: number; arquivo: string; descricao: string }>(
      `/finance/lancamentos/${lancamentoId}/anexos`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return res.data;
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];

    if (isEdit && id) {
      setUploading(true);
      try {
        const newAnexo = await uploadFileForLancamento(Number(id), file);
        setAnexos((prev) => [...prev, newAnexo as unknown as AnexoLancamento]);
        toast.success("Comprovante enviado com sucesso");
      } catch (err) {
        toast.error("Falha ao enviar comprovante");
      } finally {
        setUploading(false);
      }
    } else {
      setSelectedFile(file);
    }
  }

  async function handleDeleteAnexo(anexoId: number) {
    if (!window.confirm("Deseja realmente remover este anexo?")) return;
    try {
      await api.delete(`/finance/lancamentos/${id}/anexos/${anexoId}`);
      setAnexos((prev) => prev.filter((a) => a.id !== anexoId));
      toast.success("Anexo removido");
    } catch {
      toast.error("Falha ao remover anexo");
    }
  }

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = { ...values, valor: Number(values.valor) };
    try {
      let targetId = id;
      if (isEdit) {
        await api.patch(`/finance/lancamentos/${id}`, payload);
        toast.success("Lançamento atualizado");
      } else {
        const res = await api.post<Lancamento>(`/finance/lancamentos`, payload);
        targetId = String(res.data.id);
        toast.success("Lançamento criado");
      }

      if (selectedFile && targetId) {
        try {
          await uploadFileForLancamento(Number(targetId), selectedFile);
          toast.success("Comprovante enviado com sucesso");
        } catch {
          toast.error("Lançamento criado, mas falha ao subir comprovante");
        }
      }

      navigate("/finance");
    } catch (err) {
      toast.error("Falha ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/finance")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar lançamento" : "Novo lançamento"}
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Dados do lançamento</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Tipo</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("tipo")}
                >
                  <option value="RECEITA">Receita</option>
                  <option value="DESPESA">Despesa</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="data">Data</Label>
                <Input id="data" type="date" {...form.register("data")} />
                {form.formState.errors.data && (
                  <p className="text-xs text-destructive">{form.formState.errors.data.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>Categoria</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("categoria_id")}
                >
                  <option value="">Selecione...</option>
                  {categorias?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
                {form.formState.errors.categoria_id && (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.categoria_id.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>Conta de caixa</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("conta_id")}
                >
                  <option value="">Selecione...</option>
                  {contas?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
                {form.formState.errors.conta_id && (
                  <p className="text-xs text-destructive">{form.formState.errors.conta_id.message}</p>
                )}
              </div>

              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="descricao">Descrição</Label>
                <Input id="descricao" {...form.register("descricao")} />
                {form.formState.errors.descricao && (
                  <p className="text-xs text-destructive">{form.formState.errors.descricao.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="valor">Valor (R$)</Label>
                <Input
                  id="valor"
                  type="number"
                  step="0.01"
                  placeholder="0,00"
                  {...form.register("valor")}
                />
                {form.formState.errors.valor && (
                  <p className="text-xs text-destructive">{form.formState.errors.valor.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>Forma de pagamento</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("forma_pagamento")}
                >
                  <option value="DINHEIRO">Dinheiro</option>
                  <option value="PIX">PIX</option>
                  <option value="CARTAO">Cartão</option>
                  <option value="OUTRO">Outro</option>
                </select>
              </div>
            </div>

            {/* Seção de Anexos */}
            <div className="border-t pt-4 space-y-3">
              <Label className="text-sm font-semibold flex items-center gap-1.5 text-mm-primary">
                <Paperclip size={16} /> Comprovante / Nota Fiscal
              </Label>
              <p className="text-xs text-mm-muted">
                Envie a foto ou arquivo PDF referente a esta entrada/saída financeira para registro.
              </p>

              {/* Arquivos já existentes */}
              {isEdit && anexos.length > 0 && (
                <div className="space-y-2">
                  {anexos.map((a) => (
                    <div
                      key={a.id}
                      className="flex items-center justify-between p-2.5 bg-mm-bg rounded border text-sm"
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        <FileText size={16} className="text-mm-muted flex-shrink-0" />
                        <span className="truncate font-medium">{a.descricao}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <a
                          href={`/media/${a.arquivo}`}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1 hover:bg-mm-borderc rounded text-mm-blue"
                          title="Visualizar anexo"
                        >
                          <Eye size={16} />
                        </a>
                        <button
                          type="button"
                          onClick={() => handleDeleteAnexo(a.id)}
                          className="p-1 hover:bg-mm-borderc rounded text-mm-danger"
                          title="Remover anexo"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Seleção de arquivo */}
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 px-3 py-2 bg-mm-bg hover:bg-mm-borderc/40 border rounded cursor-pointer text-sm font-medium transition-colors">
                  <Upload size={16} className="text-mm-muted" />
                  <span>{selectedFile ? selectedFile.name : "Escolher arquivo..."}</span>
                  <input
                    type="file"
                    accept="image/*,application/pdf"
                    onChange={handleFileChange}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
                {uploading && <span className="text-xs text-mm-muted">Subindo arquivo...</span>}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button variant="outline" type="button" onClick={() => navigate("/finance")}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saving || uploading}>
                <Save className="mr-2" size={16} /> {saving ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}