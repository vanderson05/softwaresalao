'use client'
// app/profissional/page.tsx
// Tela do profissional — mobile-first, agenda própria + comanda

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { appointmentsApi, financialApi } from '@/lib/api'
import { clearAuth } from '@/lib/api'
import { toast } from 'sonner'
import {
  Scissors, LogOut, Check, Clock, X,
  ChevronRight, DollarSign, Plus, Trash2
} from 'lucide-react'

// ── Helpers ───────────────────────────────────────────────────
function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
function formatDate() {
  return new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
}
function formatCurrency(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const STATUS_CONFIG: Record<string, { bg: string; border: string; dot: string; label: string; icon: any }> = {
  pending:    { bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   dot: 'bg-amber-400',   label: 'Pendente',   icon: Clock        },
  confirmed:  { bg: 'bg-indigo-500/10',  border: 'border-indigo-500/30',  dot: 'bg-indigo-400',  label: 'Confirmado', icon: Clock        },
  in_comanda: { bg: 'bg-purple-500/10',  border: 'border-purple-500/30',  dot: 'bg-purple-400',  label: 'Em atend.',  icon: Scissors     },
  completed:  { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', dot: 'bg-emerald-400', label: 'Realizado',  icon: Check        },
  cancelled:  { bg: 'bg-red-500/5',      border: 'border-red-500/20',     dot: 'bg-red-400',     label: 'Cancelado',  icon: X            },
  no_show:    { bg: 'bg-slate-500/5',    border: 'border-slate-500/20',   dot: 'bg-slate-500',   label: 'Faltou',     icon: X            },
}

// ── Comanda Sheet ─────────────────────────────────────────────
function CommandaSheet({
  appointmentId, clientName, serviceName, onClose, onCompleted
}: {
  appointmentId: string; clientName: string; serviceName: string
  onClose: () => void; onCompleted: () => void
}) {
  const [comanda,     setComanda]     = useState<any>(null)
  const [loading,     setLoading]     = useState(true)
  const [step,        setStep]        = useState<'items' | 'checkout'>('items')
  const [payMethod,   setPayMethod]   = useState('pix')
  const [addingItem,  setAddingItem]  = useState(false)
  const [products,    setProducts]    = useState<any[]>([])
  const [description, setDescription] = useState('')
  const [unitPrice,   setUnitPrice]   = useState('')
  const [submitting,  setSubmitting]  = useState(false)

  const loadComanda = useCallback(async () => {
    try {
      const { data } = await financialApi.comanda(appointmentId)
      setComanda(data)
    } catch { toast.error('Erro ao abrir comanda.') }
    finally { setLoading(false) }
  }, [appointmentId])

  useEffect(() => {
    loadComanda()
    import('@/lib/api').then(({ financialApi: fa }) =>
      fa.products().then(({ data }) => setProducts(data)).catch(() => {})
    )
  }, [loadComanda])

  async function handleAddItem() {
    if (!description || !unitPrice) { toast.error('Preencha todos os campos.'); return }
    setSubmitting(true)
    try {
      await financialApi.addItem(appointmentId, { description, unit_price: Number(unitPrice), quantity: 1 })
      setDescription(''); setUnitPrice(''); setAddingItem(false)
      await loadComanda()
      toast.success('Item adicionado!')
    } catch { toast.error('Erro ao adicionar item.') }
    finally { setSubmitting(false) }
  }

  async function handleRemoveItem(itemId: string) {
    try {
      await financialApi.removeItem(itemId)
      await loadComanda()
    } catch { toast.error('Erro ao remover.') }
  }

  async function handleCheckout() {
    setSubmitting(true)
    try {
      await financialApi.checkout(appointmentId, { payment_method: payMethod })
      toast.success('Atendimento finalizado! 🎉')
      onCompleted()
    } catch { toast.error('Erro ao finalizar.') }
    finally { setSubmitting(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50" onClick={onClose} />
      <div
        className="fixed bottom-0 left-0 right-0 z-50 bg-[#0D0D14] border-t border-white/10 rounded-t-3xl shadow-2xl overflow-y-auto"
        style={{ maxHeight: '90vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="flex justify-center pt-3 pb-1 sticky top-0 bg-[#0D0D14]">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-start justify-between px-5 pt-3 pb-4 border-b border-white/[0.06]">
          <div>
            <h3 className="text-white font-bold text-lg">{clientName}</h3>
            <p className="text-white/40 text-sm">{serviceName}</p>
          </div>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-[#6366f1] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="px-5 py-4">
            {step === 'items' && (
              <>
                {/* Itens */}
                <div className="space-y-2 mb-4">
                  {comanda?.items?.map((item: any) => (
                    <div key={item.id} className="flex items-center gap-3 bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-white text-sm font-medium truncate">{item.description}</div>
                        <div className="text-white/30 text-xs">x{item.quantity} · {formatCurrency(item.unit_price)}</div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-white font-semibold text-sm">{formatCurrency(item.total)}</span>
                        <button onClick={() => handleRemoveItem(item.id)} className="w-7 h-7 flex items-center justify-center text-white/20 hover:text-red-400 transition-colors">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Adicionar item */}
                {addingItem ? (
                  <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-4 mb-4 space-y-3">
                    <h4 className="text-white/60 text-sm font-medium">Adicionar item</h4>
                    <input
                      value={description}
                      onChange={e => setDescription(e.target.value)}
                      placeholder="Descrição (ex: Pomada Capilar)"
                      className="w-full h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors"
                      style={{ fontSize: '16px' }}
                    />
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={unitPrice}
                        onChange={e => setUnitPrice(e.target.value)}
                        placeholder="Valor (R$)"
                        className="flex-1 h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors"
                        style={{ fontSize: '16px' }}
                      />
                      <button onClick={() => setAddingItem(false)} className="w-11 h-11 flex items-center justify-center bg-white/[0.06] border border-white/[0.08] rounded-xl text-white/40">
                        <X size={18} />
                      </button>
                      <button onClick={handleAddItem} disabled={submitting} className="w-11 h-11 flex items-center justify-center bg-[#6366f1] rounded-xl text-white disabled:opacity-50">
                        <Check size={18} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <button onClick={() => setAddingItem(true)} className="w-full flex items-center gap-2 justify-center py-3 rounded-xl border border-dashed border-white/20 text-white/40 hover:text-white hover:border-white/30 transition-all mb-4">
                    <Plus size={16} /> Adicionar item
                  </button>
                )}

                {/* Total */}
                <div className="flex items-center justify-between bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-3 mb-5">
                  <span className="text-white/50 font-medium">Total</span>
                  <span className="text-white font-black text-xl">{formatCurrency(comanda?.total || 0)}</span>
                </div>

                <button
                  onClick={() => setStep('checkout')}
                  className="w-full h-13 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-xl transition-all active:scale-[0.98] text-base"
                >
                  Finalizar atendimento →
                </button>
              </>
            )}

            {step === 'checkout' && (
              <>
                <h4 className="text-white font-semibold mb-4">Forma de pagamento</h4>
                <div className="grid grid-cols-2 gap-2 mb-5">
                  {[
                    { v: 'pix',    l: '💸 Pix'      },
                    { v: 'cash',   l: '💵 Dinheiro'  },
                    { v: 'credit', l: '💳 Crédito'   },
                    { v: 'debit',  l: '💳 Débito'    },
                  ].map(({ v, l }) => (
                    <button
                      key={v}
                      onClick={() => setPayMethod(v)}
                      className={`py-4 rounded-xl text-sm font-medium transition-all active:scale-95 ${payMethod === v ? 'bg-[#6366f1] text-white' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}
                    >
                      {l}
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-between bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-4 mb-5">
                  <span className="text-white/50">Total a cobrar</span>
                  <span className="text-white font-black text-2xl">{formatCurrency(comanda?.total || 0)}</span>
                </div>

                <div className="flex gap-3">
                  <button onClick={() => setStep('items')} className="flex-1 py-3.5 rounded-xl bg-white/[0.06] text-white/50 text-sm font-medium border border-white/[0.08]">
                    Voltar
                  </button>
                  <button
                    onClick={handleCheckout}
                    disabled={submitting}
                    className="flex-[2] py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm transition-all active:scale-[0.98] disabled:opacity-50"
                  >
                    {submitting ? 'Finalizando...' : '✅ Confirmar pagamento'}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function ProfissionalPage() {
  const router = useRouter()
  const { user, tenant, role, clearAuth: clearStore } = useAuthStore()
  const [appointments, setAppointments] = useState<any[]>([])
  const [loading,      setLoading]      = useState(true)
  const [activeAppt,   setActiveAppt]   = useState<any>(null)
  const today = new Date().toISOString().split('T')[0]

  useEffect(() => {
    const token = localStorage.getItem('beauti_token')
    if (!token) { router.replace('/login'); return }
    if (role === 'owner' || role === 'manager') { router.replace('/painel'); return }
    loadAgenda()
  }, [role, router])

  async function loadAgenda() {
    setLoading(true)
    try {
      const { data } = await appointmentsApi.agendaDay({ date: today })
      const all = (data.professionals || [])
        .flatMap((p: any) => p.appointments.map((a: any) => ({ ...a, professional_name: p.professional.name })))
        .sort((a: any, b: any) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime())
      setAppointments(all)
    } catch { toast.error('Erro ao carregar agenda.') }
    finally { setLoading(false) }
  }

  function handleLogout() {
    clearAuth(); clearStore(); router.replace('/login')
  }

  const upcoming  = appointments.filter(a => ['pending', 'confirmed'].includes(a.status))
  const done      = appointments.filter(a => a.status === 'completed')
  const total     = appointments.filter(a => a.status !== 'cancelled').length
  const nextAppt  = upcoming[0]

  return (
    <div
      className="min-h-screen bg-[#0A0A0F] flex flex-col"
      style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-4 bg-[#0D0D14] border-b border-white/[0.06] sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
            <Scissors size={18} className="text-white" />
          </div>
          <div>
            <div className="text-white font-semibold text-sm">{user?.name || 'Profissional'}</div>
            <div className="text-white/30 text-xs capitalize">{formatDate()}</div>
          </div>
        </div>
        <button onClick={handleLogout} className="w-10 h-10 flex items-center justify-center text-white/30 hover:text-white transition-colors rounded-xl hover:bg-white/[0.06]">
          <LogOut size={18} />
        </button>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 px-4 py-4">
        {[
          { label: 'Hoje',     value: total,          color: 'text-white'         },
          { label: 'Feitos',   value: done.length,    color: 'text-emerald-400'   },
          { label: 'Faltam',   value: upcoming.length,color: 'text-[#6366f1]'    },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white/[0.04] border border-white/[0.06] rounded-2xl p-3 text-center">
            <div className={`text-2xl font-black ${color}`}>{value}</div>
            <div className="text-white/30 text-xs mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Próximo destaque */}
      {nextAppt && (
        <div className="mx-4 mb-4">
          <div className="bg-gradient-to-r from-[#6366f1]/20 to-[#8B5CF6]/10 border border-[#6366f1]/30 rounded-2xl p-5">
            <div className="text-white/50 text-xs font-medium uppercase tracking-wide mb-2">Próximo atendimento</div>
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="text-white font-bold text-xl leading-tight truncate">{nextAppt.client_name}</div>
                <div className="text-white/50 text-sm mt-0.5">{nextAppt.service_name}</div>
                <div className="flex items-center gap-2 mt-3">
                  <Clock size={14} className="text-[#6366f1]" />
                  <span className="text-[#6366f1] font-bold text-lg">{formatTime(nextAppt.starts_at)}</span>
                  <span className="text-white/30 text-sm">– {formatTime(nextAppt.ends_at)}</span>
                </div>
              </div>
              <button
                onClick={() => setActiveAppt(nextAppt)}
                className="bg-[#6366f1] hover:bg-[#4f46e5] active:bg-[#4338ca] text-white font-semibold text-sm px-5 py-3 rounded-xl transition-all active:scale-95 flex-shrink-0 min-h-[44px]"
              >
                Atender
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lista completa */}
      <div className="flex-1 overflow-y-auto px-4" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        <h2 className="text-white/30 text-xs font-medium uppercase tracking-wide mb-3">
          Todos os agendamentos
        </h2>

        {loading ? (
          <div className="space-y-3">
            {[1,2,3].map(i => <div key={i} className="h-20 bg-white/[0.04] rounded-2xl animate-pulse" />)}
          </div>
        ) : appointments.length === 0 ? (
          <div className="text-center py-16">
            <Check size={40} className="text-white/10 mx-auto mb-3" />
            <p className="text-white/30">Nenhum agendamento hoje</p>
          </div>
        ) : (
          <div className="space-y-2 pb-8">
            {appointments.map(appt => {
              const cfg  = STATUS_CONFIG[appt.status] || STATUS_CONFIG.confirmed
              const Icon = cfg.icon
              const isDone = ['completed', 'cancelled', 'no_show'].includes(appt.status)
              const canOpen = ['confirmed', 'pending', 'in_comanda'].includes(appt.status)

              return (
                <button
                  key={appt.id}
                  onClick={() => canOpen && setActiveAppt(appt)}
                  disabled={!canOpen}
                  className={`w-full flex items-center gap-4 p-4 rounded-2xl border transition-all text-left ${cfg.bg} ${cfg.border} ${isDone ? 'opacity-50' : 'active:scale-[0.98]'}`}
                >
                  <div className="text-white/40 text-sm font-mono w-12 flex-shrink-0">
                    {formatTime(appt.starts_at)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`font-semibold text-sm truncate ${isDone ? 'text-white/40' : 'text-white'}`}>
                      {appt.client_name}
                    </div>
                    <div className="text-white/30 text-xs truncate mt-0.5">{appt.service_name}</div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                    <span className="text-white/30 text-xs">{cfg.label}</span>
                  </div>
                  {canOpen && <ChevronRight size={14} className="text-white/20 flex-shrink-0" />}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Comanda Sheet */}
      {activeAppt && (
        <CommandaSheet
          appointmentId={activeAppt.id}
          clientName={activeAppt.client_name}
          serviceName={activeAppt.service_name}
          onClose={() => setActiveAppt(null)}
          onCompleted={() => { setActiveAppt(null); loadAgenda() }}
        />
      )}
    </div>
  )
}