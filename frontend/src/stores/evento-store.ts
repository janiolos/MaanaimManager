import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Evento {
  id: number;
  nome: string;
  data_inicio: string;
  data_fim: string;
  status: string;
  ativo: boolean;
}

interface EventoState {
  eventoId: number | null;
  evento: Evento | null;
  setEvento: (evento: Evento) => void;
  clearEvento: () => void;
}

export const useEventoStore = create<EventoState>()(
  persist(
    (set) => ({
      eventoId: null,
      evento: null,
      setEvento: (evento) => set({ evento, eventoId: evento.id }),
      clearEvento: () => set({ evento: null, eventoId: null }),
    }),
    { name: "maanaim-evento" },
  ),
);