'use client'
// components/agenda/NewAppointmentSheet.tsx
// Sheet de novo agendamento — 3 etapas simples

import { useState, useEffect } from 'react'
import { X, ChevronLeft, ChevronRight, Check, User, Scissors, Clock } from 'lucide-react'
import { professionalsApi, servicesApi, slotsApi, appointmentsApi } from '@/lib/api'
import { toast } from 'sonner'

function toISO(d: Date) {
  return d.toISOString().split('T')[0]
}

function addDays(d: Date, n: number) {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

function formatDateShort(iso: string) {
  return new Date(iso + 'T00:00').toLocaleDateString('pt-BR', {
    weekday: 'short', day: 'numeric', month: 'short'
  }).replace('.', '')
}

function isToday(iso: string) {
  return iso === toISO(new Date())
}

export default function NewAppointmentSheet({
  professionals: initialProfessionals,
  initialDate,
  onClose,
  onCreated,
}: {
  professionals: any[]
  initialDate: string
  onClose: () => void
  onCreated: () => void
}) {
  const [step,     setStep]     = useState(1)
  const [loading,  setLoading]  = useState(false)

  // Etapa 1
  const [professionals, setProfessionals] = useState<any[]>(initialProfessionals)
  const [services,      setServices]      = useState<any[]>([])
  const [selectedProf,  setSelectedProf]  = useState<any>(null)
  const [selectedSvc,   setSelectedSvc]   = useState<any>(null)

  // Etapa 2
  const [selectedDate,  setSelectedDate]  = useState(initialDate)
  const [slots,         setSlots]         = useState<any[]>([])
  const [selectedSlot,  setSelectedSlot]  = useState<any>(null)
  const [loadingSlots,  setLoadingSlots]  = useState(false)

  // Etapa 3
  const [clientName,    setClientName]    = useState('')
  const [clientPhone,   setClientPhone]   = useState('')
  const [source,        setSource]        = useState<'panel'|'link'|'whatsapp'>('panel')

  // Carrega serviços
  useEffect(() => {
    if (professionals.length === 0) {
      professionalsApi.list().then(({ data }) => setProfessionals(data)).catch(() => {})
    }
    servicesApi.list().then(({ data }) => setServices(data)).catch(() => {})
  }, [])

  // Carrega slots ao mudar profissional, serviço ou data
  useEffect(() => {
    if (!selectedProf || !selectedSvc || !selectedDate) return
    setLoadingSlots(true)
    setSelectedSlot(null)
    slotsApi.get({
      service_id:      selectedSvc.id,
      date:            selectedDate,
      professional_id: selectedProf.id,
    }).then(({ data }) => {
      setSlots(data.slots || [])
    }).catch(() => setSlots([]))
    .finally(() => setLoadingSlots(false))
  }, [selectedProf, selectedSvc, selectedDate])

  async function handleCreate() {
    if (!clientName.trim()) { toast.error('Informe o nome do cliente.'); return }
    setLoading(true)
    try {
      await appointmentsApi.create({
        professional_id: selectedProf.id,
        service_id:      selectedSvc.id,
        starts_at:       selectedSlot.datetime,
        client_name:     clientName.trim(),
        client_phone:    clientPhone.trim(),
        source,
      })
      toast.success('Agendamento criado! ✅')
      onCreated()
    } catch (err: any) {
      const msg = err.response?.data?.non_field_errors?.[0]
        || err.response?.data?.error
        || 'Erro ao criar agendamento.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  // Dias para seleção (hoje + 14 dias)
  const dateOptions = Array.from({ length: 15 }, (_, i) => {
    const d = addDays(new Date(), i)
    return toISO(d)
  })

  const inputClass = "w-full h-12 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />

      {/* Sheet */}
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)', maxHeight: '90vh', overflowY: 'auto' }}
      >
        {/* Handle mobile */}
        <div className="md:hidden flex justify-center pt-3 pb-1 sticky top-0">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center gap-3 px-5 pt-4 pb-3 border-b border-white/[0.06] sticky top-0 bg-[#0D0D14] z-10">
          {step > 1 && (
            <button onClick={() => setStep(s => s - 1)} className="w-8 h-8 flex items-center justify-center text-white/40 hover:text-white rounded-lg hover:bg-white/[0.06] transition-all">
              <ChevronLeft size={18} />
            </button>
          )}
          <div className="flex-1">
            <h3 className="text-white font-bold text-base">
              {step === 1 && 'Profissional e serviço'}
              {step === 2 && 'Data e horário'}
              {step === 3 && 'Dados do cliente'}
            </h3>
            <div className="flex gap-1.5 mt-1.5">
              {[1,2,3].map(s => (
                <div key={s} className={`h-1 rounded-full transition-all ${s <= step ? 'bg-[#6366f1]' : 'bg-white/10'} ${s === step ? 'w-6' : 'w-3'}`} />
              ))}
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center text-white/30 hover:text-white rounded-lg hover:bg-white/[0.06] transition-all">
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4">

          {/* Etapa 1 — Profissional + Serviço */}
          {step === 1 && (
            <div className="space-y-5">
              <div>
                <label className="text-white/40 text-xs font-medium uppercase tracking-wide block mb-3">
                  Profissional
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {professionals.map(prof => (
                    <button
                      key={prof.id}
                      onClick={() => setSelectedProf(prof)}
                      className={`flex items-center gap-2.5 p-3.5 rounded-xl border transition-all active:scale-[0.98] ${
                        selectedProf?.id === prof.id
                          ? 'bg-[#6366f1]/15 border-[#6366f1]/50 text-white'
                          : 'bg-white/[0.04] border-white/[0.08] text-white/50 hover:border-white/20'
                      }`}
                    >
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs font-bold">{prof.name[0]}</span>
                      </div>
                      <span className="text-sm font-medium truncate">{prof.name.split(' ')[0]}</span>
                      {selectedProf?.id === prof.id && <Check size={14} className="ml-auto text-[#6366f1] flex-shrink-0" />}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-white/40 text-xs font-medium uppercase tracking-wide block mb-3">
                  Serviço
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {services.map(svc => (
                    <button
                      key={svc.id}
                      onClick={() => setSelectedSvc(svc)}
                      className={`w-full flex items-center justify-between px-4 py-3.5 rounded-xl border transition-all active:scale-[0.98] ${
                        selectedSvc?.id === svc.id
                          ? 'bg-[#6366f1]/15 border-[#6366f1]/50'
                          : 'bg-white/[0.04] border-white/[0.08] hover:border-white/20'
                      }`}
                    >
                      <div className="text-left">
                        <div className={`text-sm font-medium ${selectedSvc?.id === svc.id ? 'text-white' : 'text-white/70'}`}>
                          {svc.name}
                        </div>
                        <div className="text-white/30 text-xs mt-0.5">{svc.duration_min}min</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-semibold ${selectedSvc?.id === svc.id ? 'text-[#6366f1]' : 'text-white/40'}`}>
                          R${Number(svc.price).toFixed(0)}
                        </span>
                        {selectedSvc?.id === svc.id && <Check size={14} className="text-[#6366f1]" />}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setStep(2)}
                disabled={!selectedProf || !selectedSvc}
                className="w-full flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold py-3.5 rounded-xl transition-all active:scale-[0.98] disabled:opacity-30"
              >
                Continuar
                <ChevronRight size={18} />
              </button>
            </div>
          )}

          {/* Etapa 2 — Data + Slots */}
          {step === 2 && (
            <div className="space-y-4">
              {/* Seleção de data */}
              <div>
                <label className="text-white/40 text-xs font-medium uppercase tracking-wide block mb-3">Data</label>
                <div className="flex gap-2 overflow-x-auto pb-1" style={{ WebkitOverflowScrolling: 'touch' as any }}>
                  {dateOptions.map(iso => {
                    const today = isToday(iso)
                    const selected = iso === selectedDate
                    return (
                      <button
                        key={iso}
                        onClick={() => setSelectedDate(iso)}
                        className={`flex flex-col items-center px-3 py-2.5 rounded-xl border min-w-[56px] transition-all active:scale-95 flex-shrink-0 ${
                          selected
                            ? 'bg-[#6366f1] border-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.4)]'
                            : 'bg-white/[0.04] border-white/[0.08] text-white/50 hover:border-white/20'
                        }`}
                      >
                        <span className="text-[10px] font-medium capitalize">
                          {today ? 'hoje' : formatDateShort(iso).split(' ')[0]}
                        </span>
                        <span className="text-lg font-black leading-tight">{iso.split('-')[2]}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Slots */}
              <div>
                <label className="text-white/40 text-xs font-medium uppercase tracking-wide block mb-3">
                  Horário disponível
                </label>
                {loadingSlots ? (
                  <div className="grid grid-cols-4 gap-2">
                    {[1,2,3,4,5,6,7,8].map(i => <div key={i} className="h-10 bg-white/[0.06] rounded-xl animate-pulse" />)}
                  </div>
                ) : slots.length === 0 ? (
                  <div className="text-center py-6 text-white/30 text-sm">
                    Nenhum horário disponível nesta data
                  </div>
                ) : (
                  <div className="grid grid-cols-4 gap-2">
                    {slots.map(slot => (
                      <button
                        key={slot.time}
                        onClick={() => setSelectedSlot(slot)}
                        className={`py-2.5 rounded-xl text-sm font-medium transition-all active:scale-95 ${
                          selectedSlot?.time === slot.time
                            ? 'bg-[#6366f1] text-white shadow-[0_0_12px_rgba(99,102,241,0.4)]'
                            : 'bg-white/[0.06] text-white/60 border border-white/[0.08] hover:bg-white/10'
                        }`}
                      >
                        {slot.time}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => setStep(3)}
                disabled={!selectedSlot}
                className="w-full flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold py-3.5 rounded-xl transition-all active:scale-[0.98] disabled:opacity-30"
              >
                Continuar
                <ChevronRight size={18} />
              </button>
            </div>
          )}

          {/* Etapa 3 — Cliente */}
          {step === 3 && (
            <div className="space-y-4">
              {/* Resumo */}
              <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-white/40">Profissional</span>
                  <span className="text-white font-medium">{selectedProf?.name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/40">Serviço</span>
                  <span className="text-white font-medium">{selectedSvc?.name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/40">Horário</span>
                  <span className="text-[#6366f1] font-bold">{selectedSlot?.time} · {formatDateShort(selectedDate)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/40">Valor</span>
                  <span className="text-white font-medium">R${Number(selectedSvc?.price || 0).toFixed(2)}</span>
                </div>
              </div>

              <div>
                <label className="text-white/50 text-sm block mb-1.5">Nome do cliente *</label>
                <input
                  value={clientName}
                  onChange={e => setClientName(e.target.value)}
                  placeholder="João Silva"
                  className={inputClass}
                  style={{ fontSize: '16px' }} // Evita zoom no iOS
                />
              </div>

              <div>
                <label className="text-white/50 text-sm block mb-1.5">Telefone (opcional)</label>
                <input
                  value={clientPhone}
                  onChange={e => setClientPhone(e.target.value)}
                  placeholder="19999999999"
                  type="tel"
                  className={inputClass}
                  style={{ fontSize: '16px' }}
                />
              </div>

              <div>
                <label className="text-white/50 text-sm block mb-2">Canal</label>
                <div className="flex gap-2">
                  {[
                    { value: 'panel',    label: 'Painel'    },
                    { value: 'link',     label: 'Link'      },
                    { value: 'whatsapp', label: 'WhatsApp'  },
                  ].map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => setSource(value as any)}
                      className={`flex-1 py-2.5 rounded-xl text-xs font-medium transition-all active:scale-95 ${
                        source === value
                          ? 'bg-[#6366f1] text-white'
                          : 'bg-white/[0.06] text-white/40 border border-white/[0.08]'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleCreate}
                disabled={loading || !clientName.trim()}
                className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-40 text-base"
              >
                {loading ? 'Criando...' : '✅ Confirmar agendamento'}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}