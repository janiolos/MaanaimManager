import { useState } from "react";
import { X, Search, HelpCircle, BookOpen } from "lucide-react";
import { Button } from "./ui/button";

interface HelpSection {
  id: string;
  title: string;
  emoji: string;
  description: string;
  topics: {
    question: string;
    answer: string;
  }[];
}

const HELP_DATA: HelpSection[] = [
  {
    id: "overview",
    title: "Visão Geral",
    emoji: "🚀",
    description: "Bem-vindo ao Maanaim Manager! Este sistema foi feito para gerenciar retiros espirituais, o estoque da fazenda, alojamentos e vendas nos pontos de venda (cantinas, livrarias, etc.) de forma simples e integrada.",
    topics: [
      {
        question: "Como começar a usar o sistema?",
        answer: "No topo da tela, você verá qual evento (retiro) está ativo no momento. Se não houver evento ativo, escolha um na tela inicial para liberar os outros menus. A maioria das funções do sistema muda dependendo de qual retiro está selecionado.",
      },
      {
        question: "O que é o fuso horário e a data?",
        answer: "Todo o sistema opera no fuso horário de Brasília (America/São_Paulo). As datas de entrada, saída e lançamentos financeiros seguem essa regra para garantir que não haja erros de contabilidade ou reservas.",
      },
    ],
  },
  {
    id: "eventos",
    title: "Eventos (Retiros)",
    emoji: "📅",
    description: "Aqui você gerencia o ciclo de vida dos retiros na fazenda. Um evento passa por PLANEJADO, EM_ANDAMENTO e, finalmente, ENCERRADO.",
    topics: [
      {
        question: "Como encerrar um evento?",
        answer: "Quando o retiro termina, o administrador clica em 'Encerrar Evento'. Isso altera o status do evento para fechado. Atenção: isso bloqueia automaticamente qualquer nova venda no PDV, novos lançamentos no financeiro e novas reservas de chalés para evitar erros e fraudes.",
      },
      {
        question: "O que acontece com os estoques ao encerrar?",
        answer: "Ao encerrar o evento, o estoque de produtos perecíveis (como salgados, refrigerantes) nos pontos de venda locais é zerado automaticamente, pois esses itens não podem ser acumulados para o próximo retiro. Os itens marcados como 'Perenes' (livros, camisetas) continuam intactos no estoque.",
      },
    ],
  },
  {
    id: "financeiro",
    title: "Financeiro",
    emoji: "💰",
    description: "O financeiro controla todo o dinheiro que entra (receitas) e sai (despesas) relacionado ao retiro selecionado.",
    topics: [
      {
        question: "Como lançar uma entrada ou saída manual?",
        answer: "Acesse o menu Financeiro -> Lançamentos e clique em 'Novo Lançamento'. Informe se é uma Receita (entrada) ou Despesa (saída), a categoria (ex: alimentação, transporte), o valor e a forma de pagamento (Dinheiro, PIX, Cartão).",
      },
      {
        question: "O que é DRE e Fluxo de Caixa?",
        answer: "O DRE resume o lucro ou prejuízo do retiro agrupado por categorias. O Fluxo de Caixa mostra as entradas e saídas dia a dia com o saldo acumulado. Ambos podem ser exportados em PDF (para impressão) ou planilha (Excel/CSV).",
      },
      {
        question: "Posso alterar lançamentos de um evento fechado?",
        answer: "Não. Para garantir a segurança dos relatórios contábeis, o sistema impede qualquer alteração, exclusão ou inserção de lançamentos em retiros que já foram encerrados.",
      },
    ],
  },
  {
    id: "estoque",
    title: "Estoque Central",
    emoji: "📦",
    description: "Gerencia a entrada de mercadorias compradas de fornecedores e a saída para consumo interno ou transferência para os pontos de venda locais.",
    topics: [
      {
        question: "Qual a diferença entre itens Perecíveis e Perenes?",
        answer: "Itens Perenes (como camisetas, Bíblias) duram por tempo indeterminado e seus estoques não são zerados no fechamento dos retiros. Itens Perecíveis (como pão, leite, refrigerante) têm seu estoque zerado nos PDVs locais quando o evento atual é encerrado.",
      },
      {
        question: "Como transferir produtos do estoque central para uma cantina?",
        answer: "No menu de Estoque, você pode gerar uma Transferência. Isso retira a quantidade selecionada do estoque central da fazenda e envia para o subestoque do ponto de venda (PDV) escolhido.",
      },
      {
        question: "O estoque central é bloqueado quando um evento fecha?",
        answer: "Não. O estoque central é contínuo e funciona de forma perene, permitindo compras, cotações e inventários a qualquer momento, independente se um retiro específico foi encerrado.",
      },
    ],
  },
  {
    id: "hospedagem",
    title: "Hospedagem (Chalés)",
    emoji: "🏨",
    description: "Controla a alocação de participantes e trabalhadores nos chalés da fazenda durante o retiro.",
    topics: [
      {
        question: "Como fazer uma reserva de chalé?",
        answer: "No mapa de chalés, selecione um chalé ativo, informe o nome do responsável, a quantidade de pessoas e as datas de entrada e saída. O sistema avisa se a capacidade do chalé for excedida.",
      },
      {
        question: "O que é o bloqueio/manutenção de chalé?",
        answer: "Se um chalé estiver com goteira, lâmpada queimada ou indisponível, você cria uma 'Ação de Chalé' do tipo MANUTENÇÃO ou BLOQUEIO para o período. O sistema impedirá novas reservas nesse chalé enquanto ele estiver bloqueado.",
      },
      {
        question: "Como a reserva gera financeiro?",
        answer: "Ao marcar uma reserva como 'Paga' e definir a forma de pagamento, o sistema gera automaticamente uma receita na categoria 'Hospedagem' no módulo Financeiro, unificando os dados.",
      },
    ],
  },
  {
    id: "pos",
    title: "PDV (Pontos de Venda)",
    emoji: "🛒",
    description: "É a tela de caixa usada na cantina, secretaria, livraria ou fazendinha para registrar vendas rápidas para os retirantes.",
    topics: [
      {
        question: "Como abrir e fechar o caixa?",
        answer: "Antes de começar a vender, o operador do caixa clica em 'Abrir Caixa'. No fim do dia ou turno, ele clica em 'Fechar Caixa', inserindo os valores contados na gaveta para conciliação.",
      },
      {
        question: "O PDV funciona sem internet?",
        answer: "Sim! Se a internet da fazenda oscilar ou cair, você pode continuar registrando as vendas normalmente no celular ou computador. As vendas são salvas na memória do navegador e serão transmitidas ao servidor central automaticamente assim que a conexão voltar. Não há risco de duplicar vendas ou baixar estoque duplicado.",
      },
    ],
  },
];

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function HelpModal({ isOpen, onClose }: HelpModalProps) {
  const [activeTab, setActiveTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");

  if (!isOpen) return null;

  // Filtra os tópicos baseado na busca
  const filteredData = HELP_DATA.map((section) => {
    const matchedTopics = section.topics.filter(
      (topic) =>
        topic.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        topic.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
        section.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
    return { ...section, matchedTopics };
  }).filter((section) => section.matchedTopics.length > 0 || searchQuery === "");

  const activeSection = filteredData.find((s) => s.id === activeTab) || filteredData[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative flex flex-col w-full max-w-4xl h-[80vh] bg-white rounded-lg shadow-mm-lg overflow-hidden border border-mm-borderc">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-mm-primary text-white border-b border-mm-primary-dark">
          <div className="flex items-center gap-2">
            <BookOpen className="text-mm-accent h-5 w-5" />
            <h2 className="text-lg font-semibold font-display">Manual de Ajuda ao Usuário</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-white/80 hover:text-white rounded hover:bg-white/10 transition-colors"
            aria-label="Fechar ajuda"
          >
            <X size={20} />
          </button>
        </div>

        {/* Search bar */}
        <div className="flex items-center gap-2 px-6 py-3 bg-mm-bg border-b border-mm-borderc">
          <Search size={18} className="text-mm-muted" />
          <input
            type="text"
            placeholder="Digite sua dúvida aqui... (Ex: 'como fechar caixa', 'hospedagem')"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-transparent border-0 outline-none text-sm text-mm-ink placeholder:text-mm-muted"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="text-xs text-mm-muted hover:text-mm-ink underline"
            >
              Limpar busca
            </button>
          )}
        </div>

        {/* Content layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-1/3 border-r border-mm-borderc bg-mm-bg/50 overflow-y-auto">
            <nav className="p-2 space-y-1">
              {filteredData.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveTab(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm font-medium rounded transition-colors ${
                    activeSection?.id === section.id
                      ? "bg-mm-primary text-white"
                      : "text-mm-ink hover:bg-mm-borderc/40"
                  }`}
                >
                  <span className="text-base" aria-hidden>
                    {section.emoji}
                  </span>
                  <span>{section.title}</span>
                </button>
              ))}
              {filteredData.length === 0 && (
                <p className="text-xs text-mm-muted p-4 text-center">Nenhum resultado encontrado.</p>
              )}
            </nav>
          </div>

          {/* Details Pane */}
          <div className="w-2/3 p-6 overflow-y-auto bg-white flex flex-col justify-between">
            {activeSection ? (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-bold font-display text-mm-primary flex items-center gap-2">
                    <span aria-hidden>{activeSection.emoji}</span>
                    {activeSection.title}
                  </h3>
                  <p className="mt-2 text-sm text-mm-muted leading-relaxed">
                    {activeSection.description}
                  </p>
                </div>

                <div className="border-t border-mm-borderc pt-4 space-y-4">
                  <h4 className="text-sm font-semibold text-mm-primary uppercase tracking-wider">
                    Dúvidas Frequentes:
                  </h4>
                  <div className="space-y-4">
                    {(searchQuery ? activeSection.matchedTopics : activeSection.topics).map(
                      (topic, i) => (
                        <div key={i} className="p-3.5 bg-mm-bg/40 rounded-md border border-mm-borderc/40">
                          <h5 className="font-semibold text-sm text-mm-primary flex items-start gap-1.5">
                            <span className="text-mm-accent font-bold">Q.</span>
                            {topic.question}
                          </h5>
                          <p className="mt-1.5 text-xs text-mm-ink/90 leading-relaxed pl-4 border-l border-mm-accent/30">
                            {topic.answer}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center p-6">
                <HelpCircle size={48} className="text-mm-muted/60 mb-2" />
                <p className="text-sm text-mm-muted">Selecione um tópico na barra lateral.</p>
              </div>
            )}

            <div className="mt-6 pt-4 border-t border-mm-borderc text-right">
              <Button onClick={onClose} variant="secondary" size="sm">
                Entendi, fechar ajuda
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
