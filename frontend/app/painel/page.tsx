'use client'
// app/painel/page.tsx — Dashboard do barbeiro

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  TrendingUp, Calendar, Clock, Users,
  ChevronRight, AlertTriangle, Cake, Package,
  CheckCircle2, Circle, XCircle
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'
import { appointmentsApi, financialApi, crmApi } from '@/lib/api'

// ── Helpers ───────────────────────────────────────────────────

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Bom dia'
  if (h < 18) return 'Boa tarde'
  return 'Boa noite'
}

function formatDate() {
  return new Date().toLocaleDateString('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
}

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const STATUS_STYLES: Record<string, { bg: string; text: string; icon: any; label: string }> = {
  pending:    { bg: 'bg-amber-500/10',  text: 'text-amber-400',  icon: Circle,       label: 'Pendente'   },
  confirmed:  { bg: 'bg-indigo-500/10', text: 'text-indigo-400', icon: Clock,        label: 'Confirmado' },
  completed:  { bg: 'bg-emerald-500/10',text: 'text-emerald-400',icon: CheckCircle2, label: 'Realizado'  },
  cancelled:  { bg: 'bg-red-500/10',    text: 'text-red-400',    icon: XCircle,      label: 'Cancelado'  },
  in_comanda: { bg: 'bg-purple-500/10', text: 'text-purple-400', icon: Clock,        label: 'Em atend.'  },
}

// ── Skeleton ──────────────────────────────────────────────────
function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/[0.06] rounded-xl animate-pulse ${className}`} />
}

// ── Stat Card ─────────────────────────────────────────────────
function StatCard({
  label, value, sub, icon: Icon, color, loading
}: {
  label: string; value: string; sub?: string
  icon: any; color: string; loading: boolean
}) {
  if (loading) return <Skeleton className="h-24" />

  return (
    <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-start gap-3 hover:border-white/10 transition-colors">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div className="min-w-0">
        <div className="text-white/40 text-xs font-medium truncate">{label}</div>
        <div className="text-white font-bold text-xl leading-tight mt-0.5">{value}</div>
        {sub && <div className="text-white/30 text-xs mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

// ── Appointment Row ───────────────────────────────────────────
function AppointmentRow({ appt, onConfirm }: { appt: any; onConfirm?: (id: string) => void }) {
  const status = STATUS_STYLES[appt.status] || STATUS_STYLES.pending
  const Icon   = status.icon
  const time   = new Date(appt.starts_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="flex items-center gap-3 py-3 border-b border-white/[0.04] last:border-0 group">
      {/* Hora */}
      <div className="text-white/50 text-sm font-mono w-12 flex-shrink-0">{time}</div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="text-white text-sm font-medium truncate">{appt.client_name}</div>
        <div className="text-white/30 text-xs truncate">{appt.service_name} · {appt.professional_name}</div>
      </div>

      {/* Status */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0 ${status.bg} ${status.text}`}>
        <Icon size={11} />
        <span className="hidden sm:inline">{status.label}</span>
      </div>

      {/* Confirmar pendente */}
      {appt.status === 'pending' && onConfirm && (
        <button
          onClick={() => onConfirm(appt.id)}
          className="hidden group-hover:flex items-center gap-1 text-xs text-[#6366f1] border border-[#6366f1]/30 px-2.5 py-1 rounded-lg hover:bg-[#6366f1]/10 transition-all flex-shrink-0"
        >
          Confirmar
        </button>
      )}
    </div>
  )
}

// ── Dashboard Page ────────────────────────────────────────────
export default function DashboardPage() {
  const router   = useRouter()
  const { tenant } = useAuthStore()

  const [loading,      setLoading]      = useState(true)
  const [cashbox,      setCashbox]      = useState<any>(null)
  const [appointments, setAppointments] = useState<any[]>([])
  const [birthdays,    setBirthdays]    = useState<any[]>([])
  const [stockAlerts,  setStockAlerts]  = useState<any[]>([])

  const today = new Date().toISOString().split('T')[0]

  useEffect(() => {
    async function loadData() {
      try {
        const [cashRes, agendaRes] = await Promise.all([
          financialApi.cashbox({ date: today }),
          appointmentsApi.agendaDay({ date: today }),
        ])
        setCashbox(cashRes.data)

        // Aplana agendamentos de todos os profissionais
        const allAppts = (agendaRes.data.professionals || [])
          .flatMap((p: any) => p.appointments.map((a: any) => ({
            ...a,
            professional_name: p.professional.name,
          })))
          .sort((a: any, b: any) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime())

        setAppointments(allAppts)

        // Carrega aniversários e alertas em background
        crmApi.birthdays()
          .then(({ data }) => setBirthdays(data.clients || []))
          .catch(() => {})

        financialApi.stockAlerts()
          .then(({ data }) => setStockAlerts(data.alerts || []))
          .catch(() => {})

      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [today])

  async function handleConfirm(id: string) {
    try {
      await appointmentsApi.confirm(id)
      setAppointments((prev) =>
        prev.map((a) => a.id === id ? { ...a, status: 'confirmed' } : a)
      )
    } catch {}
  }

  const completed = appointments.filter((a) => a.status === 'completed').length
  const total     = appointments.filter((a) => a.status !== 'cancelled').length
  const pending   = appointments.filter((a) => a.status === 'pending').length
  const upcoming  = appointments
    .filter((a) => ['pending', 'confirmed'].includes(a.status))
    .slice(0, 5)

  const hasAlerts = birthdays.length > 0 || stockAlerts.length > 0

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-2xl mx-auto md:max-w-none">
      {/* Saudação */}
      <div className="mb-6">
        <h1 className="text-white font-bold text-xl md:text-2xl">
          {greeting()}{tenant?.name ? `, ${tenant.name.split(' ')[0]}` : ''}! 👋
        </h1>
        <p className="text-white/30 text-sm mt-0.5 capitalize">{formatDate()}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="Receita hoje"
          value={loading ? '—' : formatCurrency(cashbox?.total_revenue || 0)}
          sub={loading ? '' : `${completed} atendimento${completed !== 1 ? 's' : ''}`}
          icon={TrendingUp}
          color="bg-emerald-500"
          loading={loading}
        />
        <StatCard
          label="Agenda hoje"
          value={loading ? '—' : `${completed}/${total}`}
          sub={loading ? '' : `${total - completed} restante${total - completed !== 1 ? 's' : ''}`}
          icon={Calendar}
          color="bg-[#6366f1]"
          loading={loading}
        />
        <StatCard
          label="Ticket médio"
          value={loading ? '—' : formatCurrency(cashbox?.avg_ticket || 0)}
          icon={TrendingUp}
          color="bg-purple-500"
          loading={loading}
        />
        <StatCard
          label="Pendentes"
          value={loading ? '—' : String(pending)}
          sub={pending > 0 ? 'aguardando confirmação' : 'tudo confirmado ✓'}
          icon={Clock}
          color={pending > 0 ? 'bg-amber-500' : 'bg-slate-600'}
          loading={loading}
        />
      </div>

      {/* Alertas */}
      {hasAlerts && !loading && (
        <div className="mb-6 space-y-2">
          {birthdays.map((b) => (
            <div key={b.client_id} className="flex items-center gap-3 bg-pink-500/10 border border-pink-500/20 rounded-xl px-4 py-3">
              <Cake size={16} className="text-pink-400 flex-shrink-0" />
              <span className="text-pink-300 text-sm flex-1">
                {b.is_today ? '🎂 Hoje é aniversário de' : '🎉 Aniversário em breve:'}{' '}
                <strong>{b.name}</strong>
                {!b.is_today && ` — em ${b.days_until} dia${b.days_until !== 1 ? 's' : ''}`}
              </span>
            </div>
          ))}
          {stockAlerts.map((s) => (
            <div key={s.id} className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
              <Package size={16} className="text-amber-400 flex-shrink-0" />
              <span className="text-amber-300 text-sm flex-1">
                <strong>{s.name}</strong> — estoque baixo ({s.stock_qty} restante{s.stock_qty !== 1 ? 's' : ''})
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Próximos agendamentos */}
      <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden mb-6">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
          <h2 className="text-white font-semibold text-sm">Próximos hoje</h2>
          <button
            onClick={() => router.push('/painel/agenda')}
            className="flex items-center gap-1 text-[#6366f1] text-xs font-medium hover:text-[#818cf8] transition-colors"
          >
            Ver agenda
            <ChevronRight size={14} />
          </button>
        </div>

        <div className="px-5">
          {loading ? (
            <div className="space-y-4 py-4">
              {[1,2,3].map((i) => <Skeleton key={i} className="h-12" />)}
            </div>
          ) : upcoming.length === 0 ? (
            <div className="py-8 text-center">
              <Calendar size={32} className="text-white/10 mx-auto mb-2" />
              <p className="text-white/30 text-sm">Nenhum agendamento pendente</p>
              <button
                onClick={() => router.push('/painel/agenda/novo')}
                className="mt-3 text-[#6366f1] text-sm font-medium hover:text-[#818cf8] transition-colors"
              >
                + Criar agendamento
              </button>
            </div>
          ) : (
            upcoming.map((appt) => (
              <AppointmentRow key={appt.id} appt={appt} onConfirm={handleConfirm} />
            ))
          )}
        </div>
      </div>

      {/* Caixa por forma de pagamento */}
      {!loading && cashbox && Object.keys(cashbox.by_payment || {}).length > 0 && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h2 className="text-white font-semibold text-sm">Caixa de hoje por pagamento</h2>
          </div>
          <div className="px-5 py-3">
            {Object.entries(cashbox.by_payment).map(([method, value]) => {
              const labels: Record<string, string> = {
                pix: 'Pix', cash: 'Dinheiro', credit: 'Crédito', debit: 'Débito', other: 'Outro'
              }
              const pct = cashbox.total_revenue > 0
                ? Math.round((value as number) / cashbox.total_revenue * 100)
                : 0
              return (
                <div key={method} className="flex items-center gap-3 py-2.5 border-b border-white/[0.04] last:border-0">
                  <span className="text-white/50 text-sm flex-1">{labels[method] || method}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-24 h-1.5 bg-white/[0.06] rounded-full overflow-hidden hidden sm:block">
                      <div className="h-full bg-[#6366f1] rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-white/30 text-xs w-8 text-right">{pct}%</span>
                    <span className="text-white text-sm font-medium w-20 text-right">
                      {formatCurrency(value as number)}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}