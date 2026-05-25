'use client'
// app/painel/agenda/page.tsx

import { useEffect, useRef, useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ChevronLeft, ChevronRight, Plus, Calendar } from 'lucide-react'
import { appointmentsApi, professionalsApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import AppointmentSheet from '@/components/agenda/AppointmentSheet'
import NewAppointmentSheet from '@/components/agenda/NewAppointmentSheet'

// ── Helpers ───────────────────────────────────────────────────

function toISO(d: Date) {
  return d.toISOString().split('T')[0]
}

function addDays(d: Date, n: number) {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

function formatHeader(d: Date) {
  return d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' })
    .replace('.', '').replace(/^\w/, c => c.toUpperCase())
}

function formatFull(d: Date) {
  return d.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
}

function isToday(d: Date) {
  return toISO(d) === toISO(new Date())
}

const STATUS_CONFIG: Record<string, { bg: string; border: string; dot: string; label: string }> = {
  pending:    { bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   dot: 'bg-amber-400',   label: 'Pendente'   },
  confirmed:  { bg: 'bg-indigo-500/10',  border: 'border-indigo-500/30',  dot: 'bg-indigo-400',  label: 'Confirmado' },
  in_comanda: { bg: 'bg-purple-500/10',  border: 'border-purple-500/30',  dot: 'bg-purple-400',  label: 'Em atend.'  },
  completed:  { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', dot: 'bg-emerald-400', label: 'Realizado'  },
  cancelled:  { bg: 'bg-red-500/5',      border: 'border-red-500/20',     dot: 'bg-red-400',     label: 'Cancelado'  },
  no_show:    { bg: 'bg-slate-500/5',    border: 'border-slate-500/20',   dot: 'bg-slate-500',   label: 'Faltou'     },
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

// ── Appointment Card ──────────────────────────────────────────

function AppointmentCard({ appt, onClick }: { appt: any; onClick: () => void }) {
  const cfg = STATUS_CONFIG[appt.status] || STATUS_CONFIG.confirmed
  const isDone = ['completed', 'cancelled', 'no_show'].includes(appt.status)

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-2xl border p-3.5 transition-all active:scale-[0.98] hover:border-white/20 ${cfg.bg} ${cfg.border} ${isDone ? 'opacity-50' : ''}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className="text-white font-semibold text-sm leading-tight truncate">{appt.client_name}</span>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
          <span className="text-white/40 text-xs">{cfg.label}</span>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-white/40 text-xs truncate">{appt.service_name}</span>
        <span className="text-white/30 text-xs font-mono ml-2 flex-shrink-0">
          {formatTime(appt.starts_at)} – {formatTime(appt.ends_at)}
        </span>
      </div>
      {appt.price_snapshot > 0 && (
        <div className="text-white/30 text-xs mt-1">
          R$ {Number(appt.price_snapshot).toFixed(2)}
        </div>
      )}
    </button>
  )
}

// ── Professional Column (desktop) ─────────────────────────────

function ProfColumn({
  professional, appointments, onSelect
}: {
  professional: any
  appointments: any[]
  onSelect: (appt: any) => void
}) {
  const sorted = [...appointments].sort(
    (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
  )

  return (
    <div className="flex-1 min-w-[200px]">
      {/* Header do profissional */}
      <div className="sticky top-0 z-10 bg-[#0A0A0F] pb-3">
        <div className="flex items-center gap-2 px-1">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">{professional.name[0]}</span>
          </div>
          <span className="text-white font-medium text-sm truncate">{professional.name}</span>
          {appointments.length > 0 && (
            <span className="ml-auto bg-white/10 text-white/40 text-xs px-2 py-0.5 rounded-full flex-shrink-0">
              {appointments.filter(a => !['cancelled','no_show'].includes(a.status)).length}
            </span>
          )}
        </div>
      </div>

      {/* Agendamentos */}
      <div className="space-y-2 px-1">
        {sorted.length === 0 ? (
          <div className="text-center py-8 text-white/20 text-xs">Sem agendamentos</div>
        ) : (
          sorted.map(appt => (
            <AppointmentCard key={appt.id} appt={appt} onClick={() => onSelect(appt)} />
          ))
        )}
      </div>
    </div>
  )
}

// ── Mobile Professional Tabs ──────────────────────────────────

function ProfTabs({
  professionals, selected, onChange, counts
}: {
  professionals: any[]
  selected: string
  onChange: (id: string) => void
  counts: Record<string, number>
}) {
  const scrollRef = useRef<HTMLDivElement>(null)

  return (
    <div
      ref={scrollRef}
      className="flex gap-2 overflow-x-auto scrollbar-hide px-4 py-3"
      style={{ WebkitOverflowScrolling: 'touch' }}
    >
      {professionals.map(prof => {
        const active = prof.id === selected
        const count  = counts[prof.id] || 0
        return (
          <button
            key={prof.id}
            onClick={() => onChange(prof.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${
              active
                ? 'bg-[#6366f1] text-white shadow-[0_0_20px_rgba(99,102,241,0.4)]'
                : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'
            }`}
          >
            {prof.name.split(' ')[0]}
            {count > 0 && (
              <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                active ? 'bg-white/20 text-white' : 'bg-white/10 text-white/40'
              }`}>
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

// ── Date Navigator ────────────────────────────────────────────

function DateNav({ date, onChange }: { date: Date; onChange: (d: Date) => void }) {
  const today = isToday(date)

  return (
    <div className="flex items-center gap-3 px-4 md:px-6 py-4">
      <button
        onClick={() => onChange(addDays(date, -1))}
        className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 active:scale-95 transition-all"
      >
        <ChevronLeft size={18} />
      </button>

      <div className="flex-1 text-center">
        <div className={`font-bold text-base ${today ? 'text-[#6366f1]' : 'text-white'}`}>
          {today ? 'Hoje' : formatHeader(date)}
        </div>
        <div className="text-white/30 text-xs capitalize">{formatFull(date)}</div>
      </div>

      <button
        onClick={() => onChange(addDays(date, 1))}
        className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 active:scale-95 transition-all"
      >
        <ChevronRight size={18} />
      </button>

      {!today && (
        <button
          onClick={() => onChange(new Date())}
          className="text-[#6366f1] text-xs font-medium border border-[#6366f1]/30 px-3 py-1.5 rounded-lg hover:bg-[#6366f1]/10 active:scale-95 transition-all"
        >
          Hoje
        </button>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────

export default function AgendaPage() {
  const { isStaff } = usePermissions()
  const [date,          setDate]          = useState(new Date())
  const [professionals, setProfessionals] = useState<any[]>([])
  const [agendaData,    setAgendaData]    = useState<Record<string, any[]>>({})
  const [loading,       setLoading]       = useState(true)
  const [selectedProf,  setSelectedProf]  = useState<string>('')
  const [selectedAppt,  setSelectedAppt]  = useState<any>(null)
  const [showNewSheet,  setShowNewSheet]  = useState(false)

  // Carrega profissionais uma vez
  useEffect(() => {
    professionalsApi.list().then(({ data }) => {
      setProfessionals(data)
      if (data.length > 0) setSelectedProf(data[0].id)
    }).catch(() => {})
  }, [])

  // Carrega agenda ao mudar data
  const loadAgenda = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await appointmentsApi.agendaDay({ date: toISO(date) })
      const map: Record<string, any[]> = {}
      ;(data.professionals || []).forEach((p: any) => {
        map[p.professional.id] = p.appointments.map((a: any) => ({
          ...a,
          professional_name: p.professional.name,
          professional_id:   p.professional.id,
        }))
      })
      setAgendaData(map)
    } catch {}
    finally { setLoading(false) }
  }, [date])

  useEffect(() => { loadAgenda() }, [loadAgenda])

  // Contagem por profissional para as pills
  const counts: Record<string, number> = {}
  professionals.forEach(p => {
    counts[p.id] = (agendaData[p.id] || [])
      .filter(a => !['cancelled','no_show'].includes(a.status)).length
  })

  const totalToday = Object.values(counts).reduce((a, b) => a + b, 0)

  return (
    <div className="h-full flex flex-col">
      {/* Date Navigator */}
      <DateNav date={date} onChange={setDate} />

      {/* Contador */}
      {!loading && totalToday > 0 && (
        <div className="px-4 md:px-6 mb-2">
          <span className="text-white/30 text-xs">
            {totalToday} agendamento{totalToday !== 1 ? 's' : ''} hoje
          </span>
        </div>
      )}

      {/* Desktop — colunas */}
      <div className="hidden md:flex flex-1 gap-4 px-6 pb-6 overflow-x-auto">
        {loading ? (
          <div className="flex gap-4 w-full">
            {[1,2].map(i => (
              <div key={i} className="flex-1 space-y-3">
                <div className="h-8 bg-white/[0.06] rounded-xl animate-pulse" />
                {[1,2,3].map(j => <div key={j} className="h-20 bg-white/[0.04] rounded-2xl animate-pulse" />)}
              </div>
            ))}
          </div>
        ) : professionals.length === 0 ? (
          <EmptyState onNew={() => setShowNewSheet(true)} />
        ) : (
          professionals.map(prof => (
            <ProfColumn
              key={prof.id}
              professional={prof}
              appointments={agendaData[prof.id] || []}
              onSelect={setSelectedAppt}
            />
          ))
        )}
      </div>

      {/* Mobile — pills + lista */}
      <div className="md:hidden flex flex-col flex-1 overflow-hidden">
        {professionals.length > 1 && (
          <ProfTabs
            professionals={professionals}
            selected={selectedProf}
            onChange={setSelectedProf}
            counts={counts}
          />
        )}

        <div className="flex-1 overflow-y-auto px-4 pb-32" style={{ WebkitOverflowScrolling: 'touch' as any }}>
          {loading ? (
            <div className="space-y-3 pt-2">
              {[1,2,3].map(i => <div key={i} className="h-20 bg-white/[0.04] rounded-2xl animate-pulse" />)}
            </div>
          ) : !selectedProf || (agendaData[selectedProf] || []).length === 0 ? (
            <EmptyState onNew={() => setShowNewSheet(true)} />
          ) : (
            <div className="space-y-2 pt-2">
              {[...(agendaData[selectedProf] || [])]
                .sort((a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime())
                .map(appt => (
                  <AppointmentCard key={appt.id} appt={appt} onClick={() => setSelectedAppt(appt)} />
                ))
              }
            </div>
          )}
        </div>
      </div>

      {/* FAB novo agendamento */}
      {isStaff && (
        <button
          onClick={() => setShowNewSheet(true)}
          className="md:hidden fixed right-4 z-30 w-14 h-14 bg-[#6366f1] hover:bg-[#4f46e5] active:bg-[#4338ca] text-white rounded-full shadow-[0_4px_24px_rgba(99,102,241,0.5)] flex items-center justify-center active:scale-95 transition-all"
          style={{ bottom: `calc(80px + env(safe-area-inset-bottom))` }}
        >
          <Plus size={26} strokeWidth={2.5} />
        </button>
      )}

      {/* Desktop — botão novo agendamento */}
      {isStaff && (
        <button
          onClick={() => setShowNewSheet(true)}
          className="hidden md:flex fixed right-6 bottom-6 items-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold px-5 py-3 rounded-xl shadow-[0_4px_24px_rgba(99,102,241,0.4)] transition-all hover:scale-[1.02] z-30"
        >
          <Plus size={18} />
          Novo agendamento
        </button>
      )}

      {/* Bottom sheet — detalhe do agendamento */}
      {selectedAppt && (
        <AppointmentSheet
          appointment={selectedAppt}
          onClose={() => setSelectedAppt(null)}
          onUpdated={() => { setSelectedAppt(null); loadAgenda() }}
        />
      )}

      {/* Bottom sheet — novo agendamento */}
      {showNewSheet && (
        <NewAppointmentSheet
          professionals={professionals}
          initialDate={toISO(date)}
          onClose={() => setShowNewSheet(false)}
          onCreated={() => { setShowNewSheet(false); loadAgenda() }}
        />
      )}
    </div>
  )
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Calendar size={40} className="text-white/10 mb-3" />
      <p className="text-white/30 text-sm mb-4">Nenhum agendamento neste dia</p>
      <button
        onClick={onNew}
        className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all active:scale-95"
      >
        <Plus size={16} />
        Criar agendamento
      </button>
    </div>
  )
}