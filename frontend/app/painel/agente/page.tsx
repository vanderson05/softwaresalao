'use client'
// app/painel/agente/page.tsx
// Painel do agente WhatsApp com IA

import { useEffect, useState } from 'react'
import { Bot, MessageCircle, Send, RefreshCw, Clock, User, X, Check, AlertCircle } from 'lucide-react'
import { agentApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

// ── Test Chat ─────────────────────────────────────────────────
function TestChat({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: 'Olá! Sou o agente de teste. Como posso ajudar?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSend() {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)
    try {
      const { data } = await agentApi.test(userMsg)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response || data.reply || 'Sem resposta.' }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Erro ao conectar com o agente. Verifique o token da OpenAI.' }])
    } finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl flex flex-col"
        style={{ height: '70vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        {/* Handle */}
        <div className="md:hidden flex justify-center pt-3 pb-1 flex-shrink-0">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06] flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#25D366]/15 border border-[#25D366]/30 flex items-center justify-center">
              <Bot size={18} className="text-[#25D366]" />
            </div>
            <div>
              <div className="text-white font-semibold text-sm">Testar agente</div>
              <div className="text-white/30 text-xs">Simula uma conversa WhatsApp</div>
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ WebkitOverflowScrolling: 'touch' as any }}>
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#6366f1] text-white rounded-br-sm'
                  : 'bg-white/[0.07] border border-white/[0.08] text-white/80 rounded-bl-sm'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white/[0.07] border border-white/[0.08] px-4 py-3 rounded-2xl rounded-bl-sm">
                <div className="flex gap-1">
                  {[0,1,2].map(i => <div key={i} className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />)}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-white/[0.06] flex-shrink-0">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Digite uma mensagem..."
              className="flex-1 h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors"
              style={{ fontSize: '16px' }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="w-11 h-11 flex items-center justify-center bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-xl transition-all active:scale-95 disabled:opacity-40 flex-shrink-0"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

// ── Conversation Card ─────────────────────────────────────────
function ConversationCard({ conv, onClick }: { conv: any; onClick: () => void }) {
  const lastMsg = conv.history?.[conv.history.length - 1]
  return (
    <button onClick={onClick} className="w-full flex items-center gap-3 p-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10 active:scale-[0.98] transition-all text-left min-h-[72px]">
      <div className="w-10 h-10 rounded-full bg-[#25D366]/15 border border-[#25D366]/20 flex items-center justify-center flex-shrink-0">
        <MessageCircle size={18} className="text-[#25D366]" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-white font-semibold text-sm truncate">{conv.phone || 'Desconhecido'}</div>
        {lastMsg && (
          <div className="text-white/30 text-xs truncate mt-0.5">
            {lastMsg.role === 'user' ? '👤 ' : '🤖 '}{lastMsg.content?.substring(0, 60)}...
          </div>
        )}
      </div>
      <div className="text-right flex-shrink-0">
        <div className="text-white/20 text-xs">{conv.updated_at ? formatTime(conv.updated_at) : '—'}</div>
        <div className="text-white/20 text-xs mt-0.5">{conv.history?.length || 0} msgs</div>
      </div>
    </button>
  )
}

// ── Conversation Detail ───────────────────────────────────────
function ConversationDetail({ conv, onClose }: { conv: any; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl flex flex-col"
        style={{ height: '75vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="md:hidden flex justify-center pt-3 pb-1 flex-shrink-0"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06] flex-shrink-0">
          <div>
            <div className="text-white font-bold">{conv.phone}</div>
            <div className="text-white/30 text-xs">{conv.history?.length || 0} mensagens</div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ WebkitOverflowScrolling: 'touch' as any }}>
          {(conv.history || []).map((msg: any, i: number) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#25D366]/20 text-white rounded-br-sm'
                  : 'bg-white/[0.07] border border-white/[0.08] text-white/80 rounded-bl-sm'
              }`}>
                <div className="text-[10px] text-white/30 mb-1">{msg.role === 'user' ? '👤 Cliente' : '🤖 Agente'}</div>
                {msg.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function AgentePage() {
  const { hasModule } = usePermissions()
  const [config,        setConfig]        = useState<any>(null)
  const [conversations, setConversations] = useState<any[]>([])
  const [loading,       setLoading]       = useState(true)
  const [showTest,      setShowTest]      = useState(false)
  const [selectedConv,  setSelectedConv]  = useState<any>(null)
  const [refreshing,    setRefreshing]    = useState(false)

  async function loadData() {
    try {
      const [configRes, convsRes] = await Promise.all([
        agentApi.config(),
        agentApi.conversations({ limit: 20 }),
      ])
      setConfig(configRes.data)
      setConversations(Array.isArray(convsRes.data) ? convsRes.data : convsRes.data?.results || [])
    } catch { toast.error('Erro ao carregar dados do agente.') }
    finally { setLoading(false); setRefreshing(false) }
  }

  useEffect(() => { loadData() }, [])

  function handleRefresh() {
    setRefreshing(true); loadData()
  }

  const isConnected = config?.wa_token && config?.wa_phone_number_id
  const webhookUrl  = typeof window !== 'undefined'
    ? `${process.env.NEXT_PUBLIC_API_URL}/api/webhook/`
    : ''

  if (!hasModule('agent')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-4"><span className="text-3xl">🔒</span></div>
        <h2 className="text-white font-bold text-xl mb-2">Agente WhatsApp IA</h2>
        <p className="text-white/40 text-sm mb-6 max-w-xs">Disponível a partir do plano <strong className="text-white">Starter</strong>.</p>
        <button className="bg-[#6366f1] text-white font-semibold px-6 py-3 rounded-xl">Ver planos</button>
      </div>
    )
  }

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-3xl">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-white font-bold text-xl">Agente WhatsApp IA</h1>
          <p className="text-white/30 text-sm mt-0.5">GPT-4 respondendo seus clientes 24h</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleRefresh} disabled={refreshing} className="w-10 h-10 flex items-center justify-center bg-white/[0.06] border border-white/[0.08] rounded-xl text-white/40 hover:text-white active:scale-95 transition-all disabled:opacity-50">
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          </button>
          <button onClick={() => setShowTest(true)} className="flex items-center gap-2 bg-[#25D366]/20 hover:bg-[#25D366]/30 border border-[#25D366]/30 text-[#25D366] text-sm font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95">
            <Bot size={16} /> Testar agente
          </button>
        </div>
      </div>

      {/* Status */}
      {loading ? <Skeleton className="h-20 mb-4" /> : (
        <div className={`flex items-start gap-4 rounded-2xl p-4 border mb-5 ${isConnected ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${isConnected ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
            {isConnected ? <Check size={18} className="text-emerald-400" /> : <AlertCircle size={18} className="text-red-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className={`font-semibold text-sm ${isConnected ? 'text-emerald-300' : 'text-red-300'}`}>
              {isConnected ? 'WhatsApp conectado' : 'WhatsApp não configurado'}
            </div>
            <div className={`text-xs mt-0.5 ${isConnected ? 'text-emerald-400/60' : 'text-red-400/60'}`}>
              {isConnected
                ? `Agente "${config?.agent_name || 'Beauti'}" ativo · ${conversations.length} conversas`
                : 'Configure o token Meta em Configurações → Agente IA'
              }
            </div>
          </div>
        </div>
      )}

      {/* Webhook info */}
      {isConnected && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 mb-5">
          <div className="text-white/40 text-xs font-medium mb-2 uppercase tracking-wide">URL do Webhook (Meta)</div>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-white/60 text-xs bg-white/[0.04] px-3 py-2 rounded-lg truncate">{webhookUrl}</code>
            <button
              onClick={() => { navigator.clipboard.writeText(webhookUrl); toast.success('Copiado!') }}
              className="text-[#6366f1] text-xs border border-[#6366f1]/30 px-3 py-2 rounded-lg hover:bg-[#6366f1]/10 flex-shrink-0 transition-all"
            >
              Copiar
            </button>
          </div>
        </div>
      )}

      {/* Stats rápidos */}
      {!loading && config && (
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-3 text-center">
            <div className="text-white font-bold text-xl">{conversations.length}</div>
            <div className="text-white/30 text-xs mt-0.5">Conversas ativas</div>
          </div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-3 text-center">
            <div className={`font-bold text-xl ${config.agent_name ? 'text-white' : 'text-white/30'}`}>
              {config.agent_name || '—'}
            </div>
            <div className="text-white/30 text-xs mt-0.5">Nome do agente</div>
          </div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-3 text-center">
            <div className="text-white font-bold text-sm capitalize">{config.tone || 'friendly'}</div>
            <div className="text-white/30 text-xs mt-0.5">Tom</div>
          </div>
        </div>
      )}

      {/* Conversas recentes */}
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-white/40 text-xs font-medium uppercase tracking-wide">Conversas recentes</h2>
        <span className="text-white/20 text-xs">TTL: 24h</span>
      </div>

      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-16" />)}</div>
      ) : conversations.length === 0 ? (
        <div className="text-center py-12">
          <MessageCircle size={36} className="text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm">Nenhuma conversa ainda</p>
          <p className="text-white/20 text-xs mt-1">
            {isConnected ? 'Aguardando mensagens no WhatsApp' : 'Configure o WhatsApp para começar'}
          </p>
        </div>
      ) : (
        <div className="space-y-2 pb-24 md:pb-6">
          {conversations.map((conv: any) => (
            <ConversationCard key={conv.id} conv={conv} onClick={() => setSelectedConv(conv)} />
          ))}
        </div>
      )}

      {showTest      && <TestChat onClose={() => setShowTest(false)} />}
      {selectedConv  && <ConversationDetail conv={selectedConv} onClose={() => setSelectedConv(null)} />}
    </div>
  )
}