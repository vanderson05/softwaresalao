'use client'
// app/painel/relatorios/page.tsx
// Relatórios avançados — visão consolidada do negócio

import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, TrendingUp, Users, DollarSign, Award, BarChart3, Calendar } from 'lucide-react'
import { financialApi, crmApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

function formatCurrency(v: number) { return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }
function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }

const MONTHS = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const MONTHS_FULL = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

function StatCard({ label, value, sub, icon: Icon, color, loading }: any) {
  if (loading) return <Skeleton className="h-24" />
  return (
    <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-start gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div className="min-w-0">
        <div className="text-white/40 text-xs truncate">{label}</div>
        <div className="text-white font-bold text-lg leading-tight">{value}</div>
        {sub && <div className="text-white/30 text-xs mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

function SimpleBar({ label, value, max, color = 'bg-[#6366f1]', extra }: any) {
  const pct = max > 0 ? Math.max(4, (value / max) * 100) : 4
  return (
    <div className="flex items-center gap-3">
      <span className="text-white/40 text-xs w-16 flex-shrink-0 truncate">{label}</span>
      <div className="flex-1 h-5 bg-white/[0.04] rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-white/50 text-xs w-20 text-right flex-shrink-0">{extra || formatCurrency(value)}</span>
    </div>
  )
}

export default function RelatoriosPage() {
  const { hasModule } = usePermissions()
  const today = new Date()
  const [year,    setYear]    = useState(today.getFullYear())
  const [month,   setMonth]   = useState(today.getMonth() + 1)
  const [loading, setLoading] = useState(true)
  const [report,  setReport]  = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const [commissions, setCommissions] = useState<any>(null)

  function addMonth(n: number) {
    let m = month + n, y = year
    if (m > 12) { m = 1;  y++ }
    if (m < 1)  { m = 12; y-- }
    setMonth(m); setYear(y)
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([
      financialApi.reportMonthly({ year, month }),
      crmApi.summary(),
      financialApi.commissions({ year, month }),
    ]).then(([repRes, sumRes, commRes]) => {
      setReport(repRes.data)
      setSummary(sumRes.data)
      setCommissions(commRes.data)
    }).catch(() => toast.error('Erro ao carregar relatórios.'))
    .finally(() => setLoading(false))
  }, [year, month])

  if (!hasModule('reports')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-4"><span className="text-3xl">🔒</span></div>
        <h2 className="text-white font-bold text-xl mb-2">Relatórios</h2>
        <p className="text-white/40 text-sm mb-6 max-w-xs">Disponível a partir do plano <strong className="text-white">Pro</strong>.</p>
        <button className="bg-[#6366f1] text-white font-semibold px-6 py-3 rounded-xl">Ver planos</button>
      </div>
    )
  }

  const maxRevenue = report?.by_professional?.[0]?.revenue || 1
  const maxService = report?.by_service?.[0]?.revenue || 1

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-3xl">
      <div className="mb-5">
        <h1 className="text-white font-bold text-xl">Relatórios</h1>
        <p className="text-white/30 text-sm mt-0.5">Visão consolidada do negócio</p>
      </div>

      {/* Navegação de mês */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => addMonth(-1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all">
          <ChevronLeft size={18} />
        </button>
        <div className="flex-1 text-center">
          <div className="text-white font-bold text-lg">{MONTHS_FULL[month - 1]} {year}</div>
        </div>
        <button onClick={() => addMonth(1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all">
          <ChevronRight size={18} />
        </button>
      </div>

      {/* Stats principais */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <StatCard label="Receita total"   value={loading ? '—' : formatCurrency(report?.summary?.total_revenue || 0)}      icon={DollarSign} color="bg-emerald-600" loading={loading} />
        <StatCard label="Atendimentos"    value={loading ? '—' : String(report?.summary?.total_appointments || 0)}          icon={Calendar}   color="bg-[#6366f1]"  loading={loading} />
        <StatCard label="Ticket médio"    value={loading ? '—' : formatCurrency(report?.summary?.avg_ticket || 0)}          icon={TrendingUp} color="bg-purple-600" loading={loading} />
        <StatCard label="Total clientes"  value={loading ? '—' : String(summary?.total_clients || 0)}                       icon={Users}      color="bg-amber-600"  loading={loading} sub={`${summary?.new_this_month || 0} novos`} />
      </div>

      {/* Melhor dia */}
      {!loading && report?.summary?.best_day && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl px-5 py-4 flex items-center gap-3 mb-6">
          <span className="text-2xl">🏆</span>
          <div>
            <div className="text-emerald-300 font-semibold text-sm">Melhor dia do mês</div>
            <div className="text-white/50 text-xs capitalize">
              {new Date(report.summary.best_day.date + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
              {' — '}{formatCurrency(report.summary.best_day.revenue)}
            </div>
          </div>
        </div>
      )}

      {/* Receita semanal */}
      {!loading && report?.by_week?.length > 0 && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden mb-4">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h3 className="text-white font-semibold text-sm">Receita por semana</h3>
          </div>
          <div className="px-5 py-4 space-y-3">
            {report.by_week.map((w: any, i: number) => (
              <SimpleBar key={w.week} label={`Sem. ${i + 1}`} value={w.revenue} max={Math.max(...report.by_week.map((x: any) => x.revenue))} />
            ))}
          </div>
        </div>
      )}

      {/* Por profissional */}
      {!loading && report?.by_professional?.length > 0 && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden mb-4">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h3 className="text-white font-semibold text-sm">Por profissional</h3>
          </div>
          <div className="px-5 py-4 space-y-4">
            {report.by_professional.map((p: any, i: number) => (
              <div key={p.name}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-white/20 text-xs w-4">{i+1}°</span>
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                      <span className="text-white text-[10px] font-bold">{p.name[0]}</span>
                    </div>
                    <span className="text-white/70 text-sm">{p.name}</span>
                    <span className="text-white/20 text-xs">{p.appointments} atend.</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white text-sm font-semibold">{formatCurrency(p.revenue)}</div>
                    <div className="text-amber-400/60 text-xs">{formatCurrency(p.commission)}</div>
                  </div>
                </div>
                <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className="h-full bg-[#6366f1] rounded-full" style={{ width: `${(p.revenue / maxRevenue) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Por serviço */}
      {!loading && report?.by_service?.length > 0 && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden mb-4">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h3 className="text-white font-semibold text-sm">Por serviço</h3>
          </div>
          <div className="px-5 py-4 space-y-3">
            {report.by_service.slice(0, 6).map((s: any) => (
              <div key={s.name} className="flex items-center gap-3">
                <span className="text-white/40 text-xs flex-1 truncate">{s.name}</span>
                <span className="text-white/30 text-xs w-12 text-right">{s.count}x</span>
                <div className="w-20 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: `${(s.revenue / maxService) * 100}%` }} />
                </div>
                <span className="text-white/50 text-xs w-20 text-right">{formatCurrency(s.revenue)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Por pagamento */}
      {!loading && report?.by_payment && Object.keys(report.by_payment).length > 0 && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden mb-4">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h3 className="text-white font-semibold text-sm">Por forma de pagamento</h3>
          </div>
          <div className="px-5 py-4 space-y-3">
            {Object.entries(report.by_payment).map(([method, value]) => {
              const labels: Record<string, string> = { pix: '💸 Pix', cash: '💵 Dinheiro', credit: '💳 Crédito', debit: '💳 Débito', other: '🔄 Outro' }
              const pct = report.summary.total_revenue > 0 ? Math.round((value as number) / report.summary.total_revenue * 100) : 0
              return (
                <div key={method} className="flex items-center gap-3">
                  <span className="text-white/50 text-sm flex-1">{labels[method] || method}</span>
                  <div className="w-24 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-white/30 text-xs w-8 text-right">{pct}%</span>
                  <span className="text-white text-sm font-medium w-20 text-right">{formatCurrency(value as number)}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Comissões resumo */}
      {!loading && commissions?.professionals?.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl overflow-hidden mb-6">
          <div className="px-5 py-4 border-b border-amber-500/20 flex items-center justify-between">
            <h3 className="text-amber-300 font-semibold text-sm">Comissões a pagar</h3>
            <span className="text-amber-300 font-bold">{formatCurrency(commissions.total_to_pay)}</span>
          </div>
          <div className="px-5 py-3 space-y-2">
            {commissions.professionals.map((p: any) => (
              <div key={p.professional_id} className="flex items-center justify-between">
                <span className="text-white/50 text-sm">{p.name} <span className="text-white/20">({p.commission_pct}%)</span></span>
                <span className="text-amber-300 font-semibold text-sm">{formatCurrency(p.commission_total)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CRM insights */}
      {!loading && summary && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden pb-24 md:pb-6">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h3 className="text-white font-semibold text-sm">Clientes</h3>
          </div>
          <div className="divide-y divide-white/[0.04]">
            {[
              { label: 'Total de clientes',     value: summary.total_clients     },
              { label: 'Ativos (últimos 30d)',  value: summary.active_last_30d   },
              { label: 'Inativos (+30d)',        value: summary.inactive_over_30d },
              { label: 'Novos este mês',        value: summary.new_this_month    },
              { label: 'Aniversários esta semana', value: summary.birthdays_this_week },
              { label: 'Assinaturas ativas',    value: summary.active_subscriptions },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between px-5 py-3">
                <span className="text-white/40 text-sm">{label}</span>
                <span className="text-white font-semibold text-sm">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}