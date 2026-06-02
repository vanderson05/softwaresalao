'use client'
// Aba Comissões atualizada — substitui o bloco {tab === 'comissoes'} em
// app/painel/financeiro/page.tsx
//
// INSTRUÇÕES:
// 1. Adicionar import no topo da página:
//    import { ComissoesTab } from '@/components/financeiro/ComissoesTab'
//
// 2. Substituir o bloco {tab === 'comissoes' && (...)} por:
//    {tab === 'comissoes' && <ComissoesTab year={year} month={month} addMonth={addMonth} />}

import { useEffect, useState, useCallback } from 'react'
import {
  ChevronLeft, ChevronRight, Award, Check,
  Trash2, RefreshCw, Plus, AlertTriangle, Clock
} from 'lucide-react'
import { toast } from 'sonner'

function formatCurrency(v: number) { return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }
function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }

const MONTHS_FULL = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

// ── Generate Sheet ────────────────────────────────────────────
function GenerateSheet({
  professionals, refDate, onClose, onGenerated
}: {
  professionals: any[]; refDate: string
  onClose: () => void; onGenerated: () => void
}) {
  const [selected, setSelected] = useState<string[]>(professionals.map(p => p.id))
  const [force,    setForce]    = useState(false)
  const [loading,  setLoading]  = useState(false)

  function toggleAll() {
    setSelected(s => s.length === professionals.length ? [] : professionals.map(p => p.id))
  }
  function toggle(id: string) {
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  }

  async function handleGenerate() {
    if (selected.length === 0) { toast.error('Selecione ao menos um profissional.'); return }
    setLoading(true)
    try {
      const { data } = await import('@/lib/api').then(({ default: api }) =>
        api.post('/financial/commission-payables/generate/', {
          ref_date:         refDate,
          professional_ids: selected,
          force,
        })
      )
      const msg = data.generated?.length > 0
        ? `${data.generated.length} pagamento(s) gerado(s)!`
        : 'Nenhum pagamento gerado — verifique se há atendimentos no período.'
      toast.success(msg)
      if (data.skipped?.length > 0) {
        data.skipped.forEach((s: any) => toast.info(`${s.professional}: ${s.reason}`))
      }
      onGenerated()
    } catch { toast.error('Erro ao gerar pagamentos.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[440px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto"
        style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>

        <div className="px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">Gerar pagamentos de comissão</h3>
          <p className="text-white/40 text-xs mt-1">
            Será calculado o período de acordo com a frequência de cada profissional.
          </p>
        </div>

        <div className="px-5 py-4 space-y-4">
          {/* Selecionar profissionais */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-white/50 text-sm">Profissionais</label>
              <button onClick={toggleAll} className="text-[#6366f1] text-xs hover:text-[#818cf8] transition-colors">
                {selected.length === professionals.length ? 'Desmarcar todos' : 'Selecionar todos'}
              </button>
            </div>
            <div className="space-y-2">
              {professionals.map(p => (
                <button
                  key={p.id}
                  onClick={() => toggle(p.id)}
                  className={`w-full flex items-center gap-3 p-3.5 rounded-xl border text-left transition-all active:scale-[0.98] ${
                    selected.includes(p.id)
                      ? 'bg-amber-500/10 border-amber-500/30'
                      : 'bg-white/[0.03] border-white/[0.07]'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                    selected.includes(p.id) ? 'bg-amber-500 border-amber-500' : 'border-white/20'
                  }`}>
                    {selected.includes(p.id) && <Check size={12} className="text-white" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium ${selected.includes(p.id) ? 'text-white' : 'text-white/50'}`}>
                      {p.name}
                    </div>
                    <div className="text-white/30 text-xs">
                      {p.commission_pct}% · {p.frequency_label}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Forçar regerar */}
          <div className="flex items-center justify-between bg-white/[0.03] border border-white/[0.06] rounded-xl px-4 py-3">
            <div>
              <div className="text-white/70 text-sm">Forçar regerar</div>
              <div className="text-white/30 text-xs mt-0.5">Recria mesmo se já existe para o período</div>
            </div>
            <button
              onClick={() => setForce(f => !f)}
              className={`w-12 h-6 rounded-full transition-all ${force ? 'bg-amber-500' : 'bg-white/20'}`}
            >
              <div className={`w-5 h-5 rounded-full bg-white shadow mx-0.5 transition-all ${force ? 'translate-x-6' : 'translate-x-0'}`} />
            </button>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || selected.length === 0}
            className="w-full h-12 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Gerando...' : `Gerar para ${selected.length} profissional(is)`}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Comissoes Tab ─────────────────────────────────────────────
export function ComissoesTab({ year, month, addMonth }: {
  year: number; month: number; addMonth: (n: number) => void
}) {
  const [data,         setData]         = useState<any>(null)
  const [loading,      setLoading]      = useState(true)
  const [showGenerate, setShowGenerate] = useState(false)
  const [filter,       setFilter]       = useState<'all' | 'pending' | 'paid' | 'overdue'>('all')

  const refDate = `${year}-${String(month).padStart(2, '0')}-01`

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const { data: d } = await import('@/lib/api').then(({ default: api }) =>
        api.get('/financial/commission-payables/')
      )
      setData(d)
    } catch { toast.error('Erro ao carregar comissões.') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  async function handlePay(id: string) {
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.patch(`/financial/payables/${id}/`, { action: 'pay' })
      )
      toast.success('Comissão paga! Lançada nas despesas automaticamente.')
      loadData()
    } catch { toast.error('Erro ao marcar como pago.') }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remover este pagamento?')) return
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.delete(`/financial/payables/${id}/`)
      )
      toast.success('Removido.')
      loadData()
    } catch { toast.error('Erro ao remover.') }
  }

  const payables = (data?.payables || []).filter((p: any) => {
    if (filter === 'all')     return true
    if (filter === 'overdue') return p.status === 'overdue'
    return p.status === filter
  })

  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="space-y-4 pb-24 md:pb-6">
      {/* Navegação de mês */}
      <div className="flex items-center gap-3">
        <button onClick={() => addMonth(-1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronLeft size={18} /></button>
        <div className="flex-1 text-center"><div className="text-white font-bold">{MONTHS_FULL[month - 1]} {year}</div></div>
        <button onClick={() => addMonth(1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronRight size={18} /></button>
      </div>

      {/* Summary */}
      {!loading && data?.summary && (
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4">
            <div className="text-amber-400/60 text-xs">Pendente</div>
            <div className="text-amber-300 font-bold text-xl">{formatCurrency(data.summary.total_pending)}</div>
          </div>
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-4">
            <div className="text-emerald-400/60 text-xs">Pago no total</div>
            <div className="text-emerald-300 font-bold text-xl">{formatCurrency(data.summary.total_paid)}</div>
          </div>
        </div>
      )}

      {/* Ações */}
      <div className="flex gap-2">
        <button
          onClick={() => setShowGenerate(true)}
          className="flex items-center gap-2 bg-amber-600/20 hover:bg-amber-600/30 border border-amber-600/30 text-amber-300 text-sm font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95"
        >
          <RefreshCw size={15} /> Gerar pagamentos
        </button>
        <button onClick={loadData} className="w-10 h-10 flex items-center justify-center bg-white/[0.06] border border-white/[0.08] rounded-xl text-white/40 hover:text-white active:scale-95 transition-all">
          <RefreshCw size={15} />
        </button>
      </div>

      {/* Configuração de frequência */}
      {!loading && data?.professionals?.length > 0 && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/[0.06]">
            <h3 className="text-white/50 text-xs font-medium uppercase tracking-wide">Frequência configurada</h3>
          </div>
          <div className="px-5 py-3 space-y-2">
            {data.professionals.map((p: any) => (
              <div key={p.id} className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                    <span className="text-white text-xs font-bold">{p.name[0]}</span>
                  </div>
                  <span className="text-white/60 text-sm">{p.name}</span>
                </div>
                <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-1 rounded-full">
                  {p.frequency_label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filtro de status */}
      <div className="flex gap-2 overflow-x-auto pb-1" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        {[
          { key: 'all',     label: 'Todos'     },
          { key: 'pending', label: '⏰ Pendente' },
          { key: 'overdue', label: '🔴 Em atraso'},
          { key: 'paid',    label: '✅ Pago'    },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => setFilter(key as any)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all flex-shrink-0 active:scale-95 ${filter === key ? 'bg-[#6366f1] text-white' : 'bg-white/[0.06] text-white/40 border border-white/[0.06]'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* Lista de pagamentos */}
      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-20" />)}</div>
      ) : payables.length === 0 ? (
        <div className="text-center py-10">
          <Award size={36} className="text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm">
            {filter === 'all'
              ? 'Nenhum pagamento gerado ainda'
              : `Nenhum pagamento com status "${filter}"`
            }
          </p>
          {filter === 'all' && (
            <button
              onClick={() => setShowGenerate(true)}
              className="mt-3 flex items-center gap-2 bg-amber-600/20 border border-amber-600/30 text-amber-300 text-sm font-medium px-4 py-2 rounded-xl mx-auto active:scale-95 transition-all"
            >
              <Plus size={14} /> Gerar primeiro pagamento
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {payables.map((p: any) => {
            const isOverdue = p.status === 'overdue'
            const isPaid    = p.status === 'paid'
            const daysText  = p.days_until < 0 ? `${Math.abs(p.days_until)}d em atraso`
                            : p.days_until === 0 ? 'Vence hoje!'
                            : `Vence em ${p.days_until}d`
            return (
              <div key={p.id} className={`bg-white/[0.03] border rounded-2xl p-4 transition-all ${
                isOverdue ? 'border-red-500/30 bg-red-500/5'
                : isPaid  ? 'border-emerald-500/20 opacity-60'
                : 'border-white/[0.06]'
              }`}>
                <div className="flex items-start gap-3">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    isPaid ? 'bg-emerald-500/15' : isOverdue ? 'bg-red-500/15' : 'bg-amber-500/15'
                  }`}>
                    {isPaid
                      ? <Check size={16} className="text-emerald-400" />
                      : isOverdue
                      ? <AlertTriangle size={16} className="text-red-400" />
                      : <Clock size={16} className="text-amber-400" />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white/80 font-medium text-sm truncate">{p.description}</div>
                    <div className={`text-xs mt-0.5 ${isOverdue ? 'text-red-400' : isPaid ? 'text-emerald-400' : 'text-white/30'}`}>
                      {isPaid ? `Pago em ${new Date(p.paid_at).toLocaleDateString('pt-BR')}` : daysText}
                      {' · '}{new Date(p.due_date + 'T00:00').toLocaleDateString('pt-BR')}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`font-bold text-sm ${isPaid ? 'text-white/40 line-through' : 'text-white'}`}>
                      {formatCurrency(p.amount)}
                    </span>
                    {!isPaid && (
                      <button
                        onClick={() => handlePay(p.id)}
                        className="w-8 h-8 flex items-center justify-center bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-lg text-emerald-400 transition-all active:scale-95"
                        title="Marcar como pago"
                      >
                        <Check size={14} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(p.id)}
                      className="w-8 h-8 flex items-center justify-center text-white/20 hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showGenerate && data?.professionals && (
        <GenerateSheet
          professionals={data.professionals}
          refDate={refDate}
          onClose={() => setShowGenerate(false)}
          onGenerated={() => { setShowGenerate(false); loadData() }}
        />
      )}
    </div>
  )
}