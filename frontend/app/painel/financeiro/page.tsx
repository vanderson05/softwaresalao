'use client'
// app/painel/financeiro/page.tsx

import { useEffect, useState } from 'react'
import {
  TrendingUp, DollarSign, BarChart3, Users,
  ChevronLeft, ChevronRight, Calendar, Award
} from 'lucide-react'
import { financialApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

// ── Helpers ───────────────────────────────────────────────────

function formatCurrency(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} />
}

const PAYMENT_LABELS: Record<string, { label: string; emoji: string; color: string }> = {
  pix:    { label: 'Pix',     emoji: '💸', color: 'bg-emerald-500' },
  cash:   { label: 'Dinheiro',emoji: '💵', color: 'bg-amber-500'   },
  credit: { label: 'Crédito', emoji: '💳', color: 'bg-indigo-500'  },
  debit:  { label: 'Débito',  emoji: '💳', color: 'bg-purple-500'  },
  other:  { label: 'Outro',   emoji: '🔄', color: 'bg-slate-500'   },
}

const MONTHS = [
  'Janeiro','Fevereiro','Março','Abril','Maio','Junho',
  'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'
]

// ── Stat Card ─────────────────────────────────────────────────

function StatCard({ label, value, sub, icon: Icon, color, loading }: {
  label: string; value: string; sub?: string; icon: any; color: string; loading: boolean
}) {
  if (loading) return <Skeleton className="h-24" />
  return (
    <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-start gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div>
        <div className="text-white/40 text-xs">{label}</div>
        <div className="text-white font-bold text-xl leading-tight">{value}</div>
        {sub && <div className="text-white/30 text-xs mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

// ── Bar Chart simples ─────────────────────────────────────────

function SimpleBar({ label, value, max, color = 'bg-[#6366f1]' }: {
  label: string; value: number; max: number; color?: string
}) {
  const pct = max > 0 ? Math.max(4, (value / max) * 100) : 4
  return (
    <div className="flex items-center gap-3">
      <span className="text-white/40 text-xs w-8 flex-shrink-0">{label}</span>
      <div className="flex-1 h-5 bg-white/[0.04] rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-white/50 text-xs w-20 text-right flex-shrink-0">
        {formatCurrency(value)}
      </span>
    </div>
  )
}

// ── Abas ──────────────────────────────────────────────────────

type Tab = 'caixa' | 'mensal' | 'comissoes'

// ── Main Page ─────────────────────────────────────────────────

export default function FinanceiroPage() {
  const { hasModule } = usePermissions()

  const [tab,       setTab]       = useState<Tab>('caixa')
  const [loading,   setLoading]   = useState(true)

  // Caixa do dia
  const [cashboxDate, setCashboxDate] = useState(new Date().toISOString().split('T')[0])
  const [cashbox,     setCashbox]     = useState<any>(null)

  // Mensal
  const today = new Date()
  const [year,    setYear]    = useState(today.getFullYear())
  const [month,   setMonth]   = useState(today.getMonth() + 1)
  const [report,  setReport]  = useState<any>(null)

  // Comissões
  const [commYear,  setCommYear]  = useState(today.getFullYear())
  const [commMonth, setCommMonth] = useState(today.getMonth() + 1)
  const [commData,  setCommData]  = useState<any>(null)

  useEffect(() => {
    setLoading(true)
    if (tab === 'caixa') {
      financialApi.cashbox({ date: cashboxDate })
        .then(({ data }) => setCashbox(data))
        .catch(() => toast.error('Erro ao carregar caixa.'))
        .finally(() => setLoading(false))
    } else if (tab === 'mensal') {
      financialApi.reportMonthly({ year, month })
        .then(({ data }) => setReport(data))
        .catch(() => toast.error('Erro ao carregar relatório.'))
        .finally(() => setLoading(false))
    } else if (tab === 'comissoes') {
      financialApi.commissions({ year: commYear, month: commMonth })
        .then(({ data }) => setCommData(data))
        .catch(() => toast.error('Erro ao carregar comissões.'))
        .finally(() => setLoading(false))
    }
  }, [tab, cashboxDate, year, month, commYear, commMonth])

  function addDate(n: number) {
    const d = new Date(cashboxDate + 'T00:00')
    d.setDate(d.getDate() + n)
    setCashboxDate(d.toISOString().split('T')[0])
  }

  function addMonth(n: number) {
    let m = month + n
    let y = year
    if (m > 12) { m = 1;  y++ }
    if (m < 1)  { m = 12; y-- }
    setMonth(m); setYear(y)
  }

  function addCommMonth(n: number) {
    let m = commMonth + n
    let y = commYear
    if (m > 12) { m = 1;  y++ }
    if (m < 1)  { m = 12; y-- }
    setCommMonth(m); setCommYear(y)
  }

  const isToday = cashboxDate === new Date().toISOString().split('T')[0]

  if (!hasModule('financial')) {
    return <LockedModule module="Financeiro" plan="Pro" />
  }

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-3xl">
      {/* Header */}
      <div className="mb-5">
        <h1 className="text-white font-bold text-xl">Financeiro</h1>
        <p className="text-white/30 text-sm mt-0.5">Caixa, relatórios e comissões</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-5" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        {[
          { key: 'caixa',    label: '💰 Caixa do dia' },
          { key: 'mensal',   label: '📊 Relatório mensal' },
          { key: 'comissoes',label: '👤 Comissões' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key as Tab)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${
              tab === key
                ? 'bg-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]'
                : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Caixa do dia ── */}
      {tab === 'caixa' && (
        <div className="space-y-4">
          {/* Navegação de data */}
          <div className="flex items-center gap-3">
            <button onClick={() => addDate(-1)} className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10 active:scale-95 transition-all">
              <ChevronLeft size={18} />
            </button>
            <div className="flex-1 text-center">
              <div className={`font-bold ${isToday ? 'text-[#6366f1]' : 'text-white'}`}>
                {isToday ? 'Hoje' : new Date(cashboxDate + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' })}
              </div>
              <div className="text-white/30 text-xs capitalize">
                {new Date(cashboxDate + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
              </div>
            </div>
            <button onClick={() => addDate(1)} className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10 active:scale-95 transition-all">
              <ChevronRight size={18} />
            </button>
            {!isToday && (
              <button onClick={() => setCashboxDate(new Date().toISOString().split('T')[0])} className="text-[#6366f1] text-xs border border-[#6366f1]/30 px-3 py-1.5 rounded-lg">
                Hoje
              </button>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Receita total"    value={loading ? '—' : formatCurrency(cashbox?.total_revenue || 0)}   icon={DollarSign} color="bg-emerald-600" loading={loading} />
            <StatCard label="Ticket médio"     value={loading ? '—' : formatCurrency(cashbox?.avg_ticket || 0)}      icon={TrendingUp} color="bg-[#6366f1]"   loading={loading} />
            <StatCard label="Atendimentos"     value={loading ? '—' : String(cashbox?.appointments?.completed || 0)} sub={`de ${cashbox?.appointments?.total || 0} previstos`} icon={Calendar} color="bg-purple-600" loading={loading} />
            <StatCard label="Comissões"        value={loading ? '—' : formatCurrency(cashbox?.total_commission || 0)} icon={Award}     color="bg-amber-600"   loading={loading} />
          </div>

          {/* Por pagamento */}
          {!loading && cashbox && Object.keys(cashbox.by_payment || {}).length > 0 && (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.06]">
                <h3 className="text-white font-semibold text-sm">Por forma de pagamento</h3>
              </div>
              <div className="px-5 py-4 space-y-3">
                {Object.entries(cashbox.by_payment).map(([method, value]) => {
                  const cfg = PAYMENT_LABELS[method] || { label: method, emoji: '💰', color: 'bg-slate-500' }
                  const pct = cashbox.total_revenue > 0 ? Math.round((value as number) / cashbox.total_revenue * 100) : 0
                  return (
                    <div key={method} className="flex items-center gap-3">
                      <span className="text-base w-6">{cfg.emoji}</span>
                      <span className="text-white/50 text-sm flex-1">{cfg.label}</span>
                      <div className="w-20 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                        <div className={`h-full ${cfg.color} rounded-full`} style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-white/30 text-xs w-8 text-right">{pct}%</span>
                      <span className="text-white text-sm font-medium w-20 text-right">{formatCurrency(value as number)}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Por profissional */}
          {!loading && cashbox?.by_professional?.length > 0 && (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.06]">
                <h3 className="text-white font-semibold text-sm">Por profissional</h3>
              </div>
              <div className="px-5 py-4 space-y-3">
                {cashbox.by_professional.map((p: any) => (
                  <div key={p.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                        <span className="text-white text-xs font-bold">{p.name[0]}</span>
                      </div>
                      <div>
                        <div className="text-white/70 text-sm">{p.name}</div>
                        <div className="text-white/30 text-xs">{p.appointments} atend.</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-semibold text-sm">{formatCurrency(p.revenue)}</div>
                      <div className="text-amber-400/70 text-xs">comissão: {formatCurrency(p.commission)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && (!cashbox || cashbox.total_revenue === 0) && (
            <div className="text-center py-10">
              <DollarSign size={36} className="text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm">Nenhum lançamento neste dia</p>
            </div>
          )}
        </div>
      )}

      {/* ── Relatório Mensal ── */}
      {tab === 'mensal' && (
        <div className="space-y-4">
          {/* Navegação de mês */}
          <div className="flex items-center gap-3">
            <button onClick={() => addMonth(-1)} className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all">
              <ChevronLeft size={18} />
            </button>
            <div className="flex-1 text-center">
              <div className="text-white font-bold">{MONTHS[month - 1]} {year}</div>
            </div>
            <button onClick={() => addMonth(1)} className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all">
              <ChevronRight size={18} />
            </button>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <Skeleton key={i} className="h-24" />)}
            </div>
          ) : report ? (
            <>
              {/* Resumo */}
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Receita total"  value={formatCurrency(report.summary.total_revenue)}      icon={DollarSign} color="bg-emerald-600" loading={false} />
                <StatCard label="Atendimentos"   value={String(report.summary.total_appointments)}         icon={Calendar}   color="bg-[#6366f1]"  loading={false} />
                <StatCard label="Ticket médio"   value={formatCurrency(report.summary.avg_ticket)}         icon={TrendingUp} color="bg-purple-600" loading={false} />
                <StatCard label="Comissões"      value={formatCurrency(report.summary.total_commission)}   icon={Award}      color="bg-amber-600"  loading={false} />
              </div>

              {/* Melhor dia */}
              {report.summary.best_day && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl px-5 py-4 flex items-center gap-3">
                  <span className="text-2xl">🏆</span>
                  <div>
                    <div className="text-emerald-300 font-semibold text-sm">Melhor dia do mês</div>
                    <div className="text-white/50 text-xs">
                      {new Date(report.summary.best_day.date + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
                      {' — '}{formatCurrency(report.summary.best_day.revenue)}
                    </div>
                  </div>
                </div>
              )}

              {/* Por serviço */}
              {report.by_service?.length > 0 && (
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-white/[0.06]">
                    <h3 className="text-white font-semibold text-sm">Por serviço</h3>
                  </div>
                  <div className="px-5 py-4 space-y-3">
                    {report.by_service.slice(0, 5).map((s: any) => (
                      <SimpleBar
                        key={s.name}
                        label={s.name.split(' ')[0]}
                        value={s.revenue}
                        max={report.by_service[0].revenue}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Por profissional */}
              {report.by_professional?.length > 0 && (
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-white/[0.06]">
                    <h3 className="text-white font-semibold text-sm">Por profissional</h3>
                  </div>
                  <div className="px-5 py-4 space-y-3">
                    {report.by_professional.map((p: any, i: number) => (
                      <div key={p.name} className="flex items-center gap-3">
                        <span className="text-white/20 text-xs w-4">{i + 1}°</span>
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                          <span className="text-white text-xs font-bold">{p.name[0]}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-white/70 text-sm truncate">{p.name}</div>
                          <div className="text-white/30 text-xs">{p.appointments} atend.</div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-semibold text-sm">{formatCurrency(p.revenue)}</div>
                          <div className="text-amber-400/60 text-xs">{formatCurrency(p.commission)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-10">
              <BarChart3 size={36} className="text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm">Sem dados neste período</p>
            </div>
          )}
        </div>
      )}

      {/* ── Comissões ── */}
      {tab === 'comissoes' && (
        <div className="space-y-4 pb-24 md:pb-6">
          {/* Navegação de mês */}
          <div className="flex items-center gap-3">
            <button onClick={() => addCommMonth(-1)} className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all">
              <ChevronLeft size={18} />
            </button>
            <div className="flex-1 text-center">
              <div className="text-white font-bold">{MONTHS[commMonth - 1]} {commYear}</div>
            </div>
            <button onClick={() => addCommMonth(1)} className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all">
              <ChevronRight size={18} />
            </button>
          </div>

          {loading ? (
            <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-24" />)}</div>
          ) : commData ? (
            <>
              {/* Total a pagar */}
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl px-5 py-4 flex items-center justify-between">
                <div>
                  <div className="text-amber-300 font-bold text-lg">{formatCurrency(commData.total_to_pay)}</div>
                  <div className="text-amber-400/60 text-xs mt-0.5">Total a pagar em comissões</div>
                </div>
                <Award size={28} className="text-amber-400/40" />
              </div>

              {/* Por profissional */}
              <div className="space-y-3">
                {commData.professionals?.length === 0 ? (
                  <div className="text-center py-8 text-white/30 text-sm">Nenhuma comissão neste período</div>
                ) : (
                  commData.professionals?.map((p: any) => (
                    <div key={p.professional_id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                          <span className="text-white font-bold">{p.name[0]}</span>
                        </div>
                        <div>
                          <div className="text-white font-semibold">{p.name}</div>
                          <div className="text-white/30 text-xs">{p.commission_pct}% de comissão · {p.appointments} atend.</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white/[0.04] rounded-xl p-3">
                          <div className="text-white/30 text-xs">Receita gerada</div>
                          <div className="text-white font-bold mt-0.5">{formatCurrency(p.revenue_generated)}</div>
                        </div>
                        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3">
                          <div className="text-amber-400/60 text-xs">Comissão a pagar</div>
                          <div className="text-amber-300 font-bold mt-0.5">{formatCurrency(p.commission_total)}</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-10">
              <Users size={36} className="text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm">Sem dados neste período</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Módulo bloqueado ──────────────────────────────────────────

function LockedModule({ module, plan }: { module: string; plan: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-4">
        <span className="text-3xl">🔒</span>
      </div>
      <h2 className="text-white font-bold text-xl mb-2">{module}</h2>
      <p className="text-white/40 text-sm mb-6 max-w-xs">
        Disponível a partir do plano <strong className="text-white">{plan}</strong>.
      </p>
      <button className="bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold px-6 py-3 rounded-xl transition-all active:scale-95">
        Ver planos
      </button>
    </div>
  )
}