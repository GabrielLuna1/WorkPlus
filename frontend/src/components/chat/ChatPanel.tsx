"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import {
  MessageCircle,
  X,
  Send,
  Trash2,
  Plus,
  ChevronDown,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { useChat } from "@/lib/chat-context";
import {
  criarSessaoChat,
  listarSessoesChat,
  deletarSessaoChat,
  listarMensagensChat,
  enviarMensagemChat,
  type ChatSession,
  type ChatMessage as ChatMessageType,
} from "@/lib/api";

export function ChatPanel() {
  const pathname = usePathname();
  const chatCtx = useChat();
  const { open, setOpen, vagaContext, clearVagaContext } = chatCtx;
  const [sessoes, setSessoes] = useState<ChatSession[]>([]);
  const [sessaoAtiva, setSessaoAtiva] = useState<ChatSession | null>(null);
  const [mensagens, setMensagens] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamBuffer, setStreamBuffer] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSessoes, setShowSessoes] = useState(false);
  const [toolRunning, setToolRunning] = useState(false);
  const [toolName, setToolName] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef("");

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (open) {
      loadSessoes();
    } else {
      clearVagaContext();
    }
  }, [open]);

  const autoSentRef = useRef(false);

  useEffect(() => {
    if (open && vagaContext && sessoes.length === 0) {
      handleNovaSessao();
    }
  }, [open, vagaContext, sessoes.length]);

  useEffect(() => {
    if (open && vagaContext && sessaoAtiva && mensagens.length === 0 && !autoSentRef.current) {
      autoSentRef.current = true;
      const timer = setTimeout(() => {
        setInput("");
        streamRef.current = "";
        setStreamBuffer("");

        const userMsg: ChatMessageType = {
          id: "auto-" + Date.now(),
          sessao_id: sessaoAtiva.id,
          papel: "user",
          conteudo: `Analise esta vaga em detalhes: ${vagaContext.titulo} na ${vagaContext.empresa}`,
          metadata: { vaga_id: vagaContext.vagaId },
          created_at: new Date().toISOString(),
        };
        setMensagens((prev) => [...prev, userMsg]);

        setStreaming(true);
        enviarMensagemChat(
          sessaoAtiva.id,
          `Analise esta vaga em detalhes: ${vagaContext.titulo} na ${vagaContext.empresa}`,
          (token) => {
            streamRef.current += token;
            setStreamBuffer(streamRef.current);
          },
          () => {
            setStreaming(false);
            setToolRunning(false);
            const finalContent = streamRef.current;
            streamRef.current = "";
            setStreamBuffer("");
            if (finalContent) {
              setMensagens((prev) => [...prev, {
                id: "assistant-" + Date.now(),
                sessao_id: sessaoAtiva.id,
                papel: "assistant",
                conteudo: finalContent,
                metadata: null,
                created_at: new Date().toISOString(),
              }]);
            }
            listarSessoesChat().then(setSessoes).catch(() => {});
          },
          (error) => {
            setStreaming(false);
            setToolRunning(false);
            setMensagens((prev) => [...prev, {
              id: "error-" + Date.now(),
              sessao_id: sessaoAtiva.id,
              papel: "assistant",
              conteudo: `Erro: ${error}`,
              metadata: null,
              created_at: new Date().toISOString(),
            }]);
          },
          (tool, params) => { setToolRunning(true); setToolName(tool); },
          (result) => {
            setToolRunning(false);
            if (result.success && result.result) {
              setMensagens((prev) => [...prev, {
                id: "tool-" + Date.now(),
                sessao_id: sessaoAtiva.id,
                papel: "assistant",
                conteudo: typeof result.result === "string" ? result.result : JSON.stringify(result.result),
                metadata: { tool_result: toolName },
                created_at: new Date().toISOString(),
              }]);
            }
            listarSessoesChat().then(setSessoes).catch(() => {});
          },
          vagaContext.vagaId,
        );
      }, 600);
      return () => clearTimeout(timer);
    }
    if (!open) {
      autoSentRef.current = false;
    }
  }, [open, vagaContext, sessaoAtiva, mensagens.length]);

  useEffect(() => {
    scrollToBottom();
  }, [mensagens, streamBuffer, scrollToBottom]);

  async function loadSessoes() {
    try {
      const data = await listarSessoesChat();
      setSessoes(data);
      if (data.length > 0 && !sessaoAtiva) {
        selecionarSessao(data[0]);
      }
    } catch {
      // silently fail
    }
  }

  async function selecionarSessao(sessao: ChatSession) {
    setSessaoAtiva(sessao);
    setShowSessoes(false);
    setMensagens([]);
    setStreamBuffer("");
    try {
      const msgs = await listarMensagensChat(sessao.id);
      setMensagens(msgs);
    } catch {
      // silently fail
    }
  }

  async function handleNovaSessao() {
    setLoading(true);
    try {
      const sessao = await criarSessaoChat();
      setSessoes((prev) => [sessao, ...prev]);
      await selecionarSessao(sessao);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }

  async function handleDeletarSessao(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    try {
      await deletarSessaoChat(id);
      setSessoes((prev) => prev.filter((s) => s.id !== id));
      if (sessaoAtiva?.id === id) {
        setSessaoAtiva(null);
        setMensagens([]);
      }
    } catch {
      // silently fail
    }
  }

  async function handleSend() {
    const msg = input.trim();
    if (!msg || !sessaoAtiva || streaming) return;

    setInput("");
    setStreamBuffer("");
    streamRef.current = "";

    const userMsg: ChatMessageType = {
      id: "temp-" + Date.now(),
      sessao_id: sessaoAtiva.id,
      papel: "user",
      conteudo: msg,
      metadata: null,
      created_at: new Date().toISOString(),
    };
    setMensagens((prev) => [...prev, userMsg]);

    setStreaming(true);
    setToolRunning(false);
    setToolName("");

    try {
      const vagaId = vagaContext?.vagaId;
      await enviarMensagemChat(
        sessaoAtiva.id,
        msg,
        (token) => {
          streamRef.current += token;
          setStreamBuffer(streamRef.current);
        },
        () => {
          setStreaming(false);
          setToolRunning(false);
          const finalContent = streamRef.current;
          streamRef.current = "";
          setStreamBuffer("");

          if (finalContent) {
            const assistantMsg: ChatMessageType = {
              id: "assistant-" + Date.now(),
              sessao_id: sessaoAtiva.id,
              papel: "assistant",
              conteudo: finalContent,
              metadata: null,
              created_at: new Date().toISOString(),
            };
            setMensagens((prev) => [...prev, assistantMsg]);
          }

          listarSessoesChat().then(setSessoes).catch(() => {});
        },
        (error) => {
          setStreaming(false);
          setToolRunning(false);
          const errorMsg: ChatMessageType = {
            id: "error-" + Date.now(),
            sessao_id: sessaoAtiva.id,
            papel: "assistant",
            conteudo: `Erro: ${error}`,
            metadata: null,
            created_at: new Date().toISOString(),
          };
          setMensagens((prev) => [...prev, errorMsg]);
        },
        (tool, params) => {
          setToolRunning(true);
          setToolName(tool);
        },
        (result) => {
          setToolRunning(false);
          if (result.success && result.result) {
            const toolMsg: ChatMessageType = {
              id: "tool-" + Date.now(),
              sessao_id: sessaoAtiva.id,
              papel: "assistant",
              conteudo: typeof result.result === 'string'
                ? result.result
                : JSON.stringify(result.result),
              metadata: { tool_result: toolName },
              created_at: new Date().toISOString(),
            };
            setMensagens((prev) => [...prev, toolMsg]);
          } else if (!result.success && result.error) {
            const errMsg: ChatMessageType = {
              id: "toolerr-" + Date.now(),
              sessao_id: sessaoAtiva.id,
              papel: "assistant",
              conteudo: `❌ ${result.error}`,
              metadata: null,
              created_at: new Date().toISOString(),
            };
            setMensagens((prev) => [...prev, errMsg]);
          }
          listarSessoesChat().then(setSessoes).catch(() => {});
        },
        vagaId,
      );
    } catch (err) {
      setStreaming(false);
      setToolRunning(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-accent hover:bg-accent-hover shadow-lg shadow-accent/20 flex items-center justify-center transition-all hover:scale-105 active:scale-95"
        title="Abrir chat"
      >
        <MessageCircle className="w-6 h-6 text-black" />
      </button>
    );
  }

  if (pathname === "/hub") return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[400px] h-[580px] flex flex-col rounded-2xl border border-hairline bg-surface shadow-2xl shadow-black/50 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-hairline">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="w-8 h-8 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
            <MessageCircle className="w-4 h-4 text-accent" />
          </div>
          <div className="flex-1 min-w-0">
            <button
              onClick={() => setShowSessoes((v) => !v)}
              className="flex items-center gap-1 hover:text-accent transition-colors"
            >
              <span className="text-sm font-medium text-ink truncate">
                {sessaoAtiva?.titulo || "WorkHunter Copilot"}
              </span>
              <ChevronDown
                className={`w-3.5 h-3.5 text-ink-subtle transition-transform ${showSessoes ? "rotate-180" : ""}`}
              />
            </button>
            {streaming && !toolRunning && (
              <span className="text-xs text-accent flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-dot" />
                Escrevendo...
              </span>
            )}
            {toolRunning && (
              <span className="text-xs text-accent flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                {toolName === "analyze_vaga" && "Analisando vaga..."}
                {toolName === "calcular_match" && "Calculando match..."}
                {toolName === "pipeline_status" && "Consultando pipeline..."}
                {toolName === "analisar_match" && "Analisando match..."}
                {toolName === "gerar_cover_letter" && "Gerando cover letter..."}
                {![ "analyze_vaga", "calcular_match", "pipeline_status", "analisar_match", "gerar_cover_letter" ].includes(toolName) && "Executando..."}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="p-1.5 rounded-lg hover:bg-surface-3 text-ink-subtle hover:text-ink transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Session switcher */}
      {showSessoes && (
        <div className="absolute top-[60px] left-0 right-0 z-10 bg-surface border border-hairline rounded-xl mx-2 shadow-xl max-h-[200px] overflow-y-auto">
          <button
            onClick={handleNovaSessao}
            disabled={loading}
            className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-accent hover:bg-accent/10 transition-colors border-b border-hairline"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Nova conversa
          </button>
          {sessoes.map((s) => (
            <div
              key={s.id}
              className={`flex items-center gap-2 px-3 py-2.5 text-sm cursor-pointer transition-colors group ${
                sessaoAtiva?.id === s.id
                  ? "bg-accent/10 text-accent"
                  : "text-ink-subtle hover:bg-surface-3 hover:text-ink"
              }`}
              onClick={() => selecionarSessao(s)}
            >
              <span className="flex-1 truncate">{s.titulo}</span>
              <button
                onClick={(e) => handleDeletarSessao(e, s.id)}
                className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-danger/20 hover:text-danger transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-2">
        {mensagens.length === 0 && !streamBuffer && (
          <div className="flex flex-col items-center justify-center h-full px-8 text-center">
            <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mb-3">
              <MessageCircle className="w-6 h-6 text-accent" />
            </div>
            <p className="text-sm font-medium text-ink mb-1">
              Job Hunter Copilot
            </p>
            <p className="text-xs text-ink-subtle leading-relaxed">
              Pergunte sobre vagas, peça análise de compatibilidade, otimize
              seu currículo ou gerencie candidaturas.
            </p>
          </div>
        )}

        {mensagens.map((msg) => (
          <ChatMessage
            key={msg.id}
            papel={msg.papel}
            conteudo={msg.conteudo}
            metadata={msg.metadata}
          />
        ))}

        {streamBuffer && (
          <ChatMessage
            papel="assistant"
            conteudo={streamBuffer}
            isStreaming
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Vaga context badge */}
      {vagaContext && (
        <div className="px-3 pt-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent/10 border border-accent/20 text-xs text-accent">
            <ExternalLink className="w-3 h-3 shrink-0" />
            <span className="flex-1 truncate font-medium">
              {vagaContext.titulo} @ {vagaContext.empresa}
            </span>
            <button
              onClick={() => clearVagaContext()}
              className="p-0.5 rounded hover:bg-accent/20 transition-colors"
              title="Remover contexto da vaga"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t border-hairline">
        <div className="flex items-center gap-2 bg-surface-2 rounded-xl border border-hairline px-3 py-2 focus-within:border-accent/50 transition-colors">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              sessaoAtiva
                ? "Digite sua mensagem..."
                : "Crie uma conversa primeiro..."
            }
            disabled={!sessaoAtiva || streaming}
            className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-tertiary outline-none disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !sessaoAtiva || streaming}
            className="p-1.5 rounded-lg bg-accent/20 text-accent hover:bg-accent/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            {streaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-[10px] text-ink-tertiary text-center mt-1.5">
          As respostas são geradas por IA. Verifique informações importantes.
        </p>
      </div>
    </div>
  );
}
