'use client'
// app/b/[slug]/page.tsx
// Perfil público da barbearia + agendamento pelo link

import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  Scissors, MapPin, Clock, Phone, Star, ChevronLeft,
  ChevronRight, Check, X, User, Calendar, Package,
  LogOut, ArrowLeft
} from 'lucide-react'
import { publicApi, setClientToken } from '@/lib/api'
import { toast } from 'sonner'

// ── Helpers ───────────────────────────────────────────────────
function formatTime(iso: string) { return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) }
function addDays(d: Date, n: number) { const r = new Date(d); r.setDate(r.getDate() + n); return r }
function toISO(d: Date) { return d.toISOString().split('T')[0] }
function isToday(iso: string) { return iso === toISO(new Date()) }
function formatDateShort(iso: string) {
  return new Date(iso + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' }).replace('.', '')
}
function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.06] rounded-xl animate-pulse ${className}`} /> }
const inputClass = "w-full h-12 px-4 rounded-xl bg-white/[0.08] border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

// ── OTP Auth Sheet ────────────────────────────────────────────
function AuthSheet({ slug, onAuth, onClose }: { slug: string; onAuth: (token: string, client: any, isNew: boolean) => void; onClose: () => void }) {
  const [step,    setStep]    = useState<'phone' | 'code'>('phone')
  const [phone,   setPhone]   = useState('')
  const [code,    setCode]    = useState('')
  const [loading, setLoading] = useState(false)

  async function handleRequestCode() {
    const clean = phone.replace(/\D/g, '')
    if (clean.length < 10) { toast.error('Informe um telefone válido.'); return }
    setLoading(true)
    try {
      await publicApi.requestCode(slug, clean)
      setStep('code')
      toast.success('Código enviado via WhatsApp!')
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Erro ao enviar código.')
    } finally { setLoading(false) }
  }

  async function handleVerify() {
    if (code.length !== 6) { toast.error('Código deve ter 6 dígitos.'); return }
    setLoading(true)
    try {
      const { data } = await publicApi.verifyCode(slug, { phone: phone.replace(/\D/g, ''), code })
      setClientToken(data.token)
      onAuth(data.token, data.client, data.is_new_client)
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Código incorreto.')
    } finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#0D0D14] border-t border-white/10 rounded-t-3xl shadow-2xl" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="px-5 pt-4 pb-6">
          <div className="text-center mb-6">
            <div className="w-12 h-12 rounded-2xl bg-[#25D366]/15 border border-[#25D366]/30 flex items-center justify-center mx-auto mb-3">
              <Phone size={22} className="text-[#25D366]" />
            </div>
            <h3 className="text-white font-bold text-xl">
              {step === 'phone' ? 'Entrar com WhatsApp' : 'Digite o código'}
            </h3>
            <p className="text-white/40 text-sm mt-1">
              {step === 'phone' ? 'Enviaremos um código de verificação' : `Código enviado para ${phone}`}
            </p>
          </div>

          {step === 'phone' ? (
            <div className="space-y-4">
              <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="(19) 99999-9999" type="tel" className={inputClass} style={{ fontSize: '16px' }} />
              <button onClick={handleRequestCode} disabled={loading} className="w-full h-13 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-bold py-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 text-base">
                {loading ? 'Enviando...' : 'Enviar código →'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input value={code} onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="000000" type="tel" maxLength={6} className={`${inputClass} text-center text-2xl font-bold tracking-[0.5em]`} style={{ fontSize: '24px' }} />
              <button onClick={handleVerify} disabled={loading || code.length !== 6} className="w-full h-13 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-bold py-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 text-base">
                {loading ? 'Verificando...' : 'Confirmar →'}
              </button>
              <button onClick={() => setStep('phone')} className="w-full text-white/30 text-sm py-2 hover:text-white/60 transition-colors">
                ← Usar outro número
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

// ── Booking Flow ──────────────────────────────────────────────
function BookingSheet({ slug, professionals, services, onClose, onBooked }: any) {
  const [step,         setStep]         = useState(1)
  const [selectedProf, setSelectedProf] = useState<any>(null)
  const [selectedSvc,  setSelectedSvc]  = useState<any>(null)
  const [selectedDate, setSelectedDate] = useState(toISO(new Date()))
  const [slots,        setSlots]        = useState<any[]>([])
  const [selectedSlot, setSelectedSlot] = useState<any>(null)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [loading,      setLoading]      = useState(false)

  const dateOptions = Array.from({ length: 14 }, (_, i) => toISO(addDays(new Date(), i)))

  useEffect(() => {
    if (!selectedProf || !selectedSvc || !selectedDate) return
    setLoadingSlots(true); setSelectedSlot(null)
    publicApi.slots(slug, { service_id: selectedSvc.id, date: selectedDate, professional_id: selectedProf.id })
      .then(({ data }) => setSlots(data.slots || []))
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false))
  }, [selectedProf, selectedSvc, selectedDate])

  async function handleBook() {
    setLoading(true)
    try {
      await publicApi.book(slug, {
        service_id:      selectedSvc.id,
        professional_id: selectedProf.id,
        starts_at:       selectedSlot.datetime,
      })
      toast.success('Agendamento confirmado! ✅')
      onBooked()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Erro ao agendar.')
    } finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#0D0D14] border-t border-white/10 rounded-t-3xl shadow-2xl overflow-y-auto" style={{ maxHeight: '88vh', paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="flex justify-center pt-3 pb-1 sticky top-0 bg-[#0D0D14]"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>

        {/* Header */}
        <div className="flex items-center gap-3 px-5 pt-3 pb-4 border-b border-white/[0.06] sticky top-4 bg-[#0D0D14] z-10">
          {step > 1 && <button onClick={() => setStep(s => s - 1)} className="w-8 h-8 flex items-center justify-center text-white/40 hover:text-white"><ChevronLeft size={18} /></button>}
          <div className="flex-1">
            <h3 className="text-white font-bold text-base">
              {step === 1 && 'Escolha o serviço'}{step === 2 && 'Escolha a data e hora'}{step === 3 && 'Confirmar agendamento'}
            </h3>
            <div className="flex gap-1.5 mt-1.5">
              {[1,2,3].map(s => <div key={s} className={`h-1 rounded-full transition-all ${s <= step ? 'bg-[#6366f1]' : 'bg-white/10'} ${s === step ? 'w-6' : 'w-3'}`} />)}
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>

        <div className="px-5 py-4">
          {/* Passo 1 — Profissional + Serviço */}
          {step === 1 && (
            <div className="space-y-5">
              <div>
                <label className="text-white/40 text-xs uppercase tracking-wide block mb-3">Profissional</label>
                <div className="grid grid-cols-2 gap-2">
                  {professionals.map((p: any) => (
                    <button key={p.id} onClick={() => setSelectedProf(p)} className={`flex items-center gap-2.5 p-3.5 rounded-xl border transition-all active:scale-[0.98] ${selectedProf?.id === p.id ? 'bg-[#6366f1]/15 border-[#6366f1]/50 text-white' : 'bg-white/[0.04] border-white/[0.08] text-white/50'}`}>
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs font-bold">{p.name[0]}</span>
                      </div>
                      <span className="text-sm font-medium truncate">{p.name.split(' ')[0]}</span>
                      {selectedProf?.id === p.id && <Check size={14} className="ml-auto text-[#6366f1] flex-shrink-0" />}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-white/40 text-xs uppercase tracking-wide block mb-3">Serviço</label>
                <div className="space-y-2 max-h-52 overflow-y-auto">
                  {services.map((s: any) => (
                    <button key={s.id} onClick={() => setSelectedSvc(s)} className={`w-full flex items-center justify-between px-4 py-3.5 rounded-xl border transition-all active:scale-[0.98] ${selectedSvc?.id === s.id ? 'bg-[#6366f1]/15 border-[#6366f1]/50' : 'bg-white/[0.04] border-white/[0.08]'}`}>
                      <div className="text-left">
                        <div className={`text-sm font-medium ${selectedSvc?.id === s.id ? 'text-white' : 'text-white/70'}`}>{s.name}</div>
                        <div className="text-white/30 text-xs">{s.duration_min}min</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold ${selectedSvc?.id === s.id ? 'text-[#6366f1]' : 'text-white/40'}`}>R${Number(s.price).toFixed(0)}</span>
                        {selectedSvc?.id === s.id && <Check size={14} className="text-[#6366f1]" />}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              <button onClick={() => setStep(2)} disabled={!selectedProf || !selectedSvc} className="w-full flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold py-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-30">
                Continuar <ChevronRight size={18} />
              </button>
            </div>
          )}

          {/* Passo 2 — Data + Slots */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="text-white/40 text-xs uppercase tracking-wide block mb-3">Data</label>
                <div className="flex gap-2 overflow-x-auto pb-1" style={{ WebkitOverflowScrolling: 'touch' as any }}>
                  {dateOptions.map(iso => (
                    <button key={iso} onClick={() => setSelectedDate(iso)} className={`flex flex-col items-center px-3 py-2.5 rounded-xl border min-w-[54px] transition-all active:scale-95 flex-shrink-0 ${iso === selectedDate ? 'bg-[#6366f1] border-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.4)]' : 'bg-white/[0.05] border-white/[0.08] text-white/50'}`}>
                      <span className="text-[10px] font-medium capitalize">{isToday(iso) ? 'hoje' : formatDateShort(iso).split(' ')[0]}</span>
                      <span className="text-lg font-black leading-tight">{iso.split('-')[2]}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-white/40 text-xs uppercase tracking-wide block mb-3">Horário disponível</label>
                {loadingSlots ? (
                  <div className="grid grid-cols-4 gap-2">{[1,2,3,4,5,6,7,8].map(i => <div key={i} className="h-10 bg-white/[0.06] rounded-xl animate-pulse" />)}</div>
                ) : slots.length === 0 ? (
                  <div className="text-center py-6 text-white/30 text-sm">Nenhum horário disponível</div>
                ) : (
                  <div className="grid grid-cols-4 gap-2">
                    {slots.map(slot => (
                      <button key={slot.time} onClick={() => setSelectedSlot(slot)} className={`py-2.5 rounded-xl text-sm font-medium transition-all active:scale-95 ${selectedSlot?.time === slot.time ? 'bg-[#6366f1] text-white shadow-[0_0_12px_rgba(99,102,241,0.4)]' : 'bg-white/[0.06] text-white/60 border border-white/[0.08]'}`}>
                        {slot.time}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button onClick={() => setStep(3)} disabled={!selectedSlot} className="w-full flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold py-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-30">
                Continuar <ChevronRight size={18} />
              </button>
            </div>
          )}

          {/* Passo 3 — Confirmar */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-4 space-y-3">
                {[
                  { label: 'Profissional', value: selectedProf?.name },
                  { label: 'Serviço',      value: `${selectedSvc?.name} · ${selectedSvc?.duration_min}min` },
                  { label: 'Horário',      value: `${selectedSlot?.time} · ${formatDateShort(selectedDate)}` },
                  { label: 'Valor',        value: `R${Number(selectedSvc?.price).toFixed(2)}` },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-white/40">{label}</span>
                    <span className={`font-medium ${label === 'Horário' ? 'text-[#6366f1]' : 'text-white'}`}>{value}</span>
                  </div>
                ))}
              </div>
              <button onClick={handleBook} disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 text-base">
                {loading ? 'Agendando...' : '✅ Confirmar agendamento'}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function PublicProfilePage() {
  const { slug }  = useParams<{ slug: string }>()
  const router    = useRouter()
  const [profile,       setProfile]       = useState<any>(null)
  const [services,      setServices]      = useState<any[]>([])
  const [professionals, setProfessionals] = useState<any[]>([])
  const [packages,      setPackages]      = useState<any[]>([])
  const [loading,       setLoading]       = useState(true)
  const [tab,           setTab]           = useState<'agendar' | 'pacotes'>('agendar')
  const [clientToken,   setClientTokenState] = useState<string | null>(null)
  const [clientData,    setClientData]    = useState<any>(null)
  const [myAppointments, setMyAppts]      = useState<any[]>([])
  const [showAuth,      setShowAuth]      = useState(false)
  const [showBooking,   setShowBooking]   = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('beauti_client_token')
    if (token) { setClientTokenState(token) }

    Promise.all([
      publicApi.profile(slug),
      publicApi.services(slug),
      publicApi.professionals(slug),
      publicApi.packages?.(slug).catch(() => ({ data: [] })),
    ]).then(([profRes, svcRes, prosRes, pkgRes]) => {
      setProfile(profRes.data)
      setServices(svcRes.data || [])
      setProfessionals(prosRes.data || [])
      setPackages(pkgRes?.data || [])
    }).catch(() => toast.error('Erro ao carregar.'))
    .finally(() => setLoading(false))
  }, [slug])

  useEffect(() => {
    if (!clientToken) return
    publicApi.myAppointments(slug)
      .then(({ data }) => setMyAppts(data.appointments || data || []))
      .catch(() => {})
  }, [clientToken, slug])

  function handleAuth(token: string, client: any, isNew: boolean) {
    setClientTokenState(token)
    setClientData(client)
    setShowAuth(false)
    toast.success(isNew ? `Bem-vindo, ${client.name || ''}!` : `Bem-vindo de volta!`)
  }

  function handleLogout() {
    localStorage.removeItem('beauti_client_token')
    setClientTokenState(null)
    setClientData(null)
    setMyAppts([])
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] px-4 py-8">
        <Skeleton className="h-40 mb-4" />
        <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-16" />)}</div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
        <div className="text-center">
          <Scissors size={40} className="text-white/10 mx-auto mb-3" />
          <p className="text-white/30">Barbearia não encontrada</p>
          <button onClick={() => router.push('/b')} className="mt-4 text-[#6366f1] text-sm">← Ver todas</button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0A0F]" style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}>
      {/* Header */}
      <div className="bg-gradient-to-b from-[#0D0D14] to-[#0A0A0F] px-4 pt-4 pb-0">
        <div className="flex items-center justify-between mb-5">
          <button onClick={() => router.push('/b')} className="w-9 h-9 flex items-center justify-center text-white/40 hover:text-white rounded-xl hover:bg-white/[0.06] transition-all">
            <ArrowLeft size={18} />
          </button>
          {clientToken ? (
            <button onClick={handleLogout} className="flex items-center gap-1.5 text-white/30 hover:text-white text-xs transition-colors">
              <LogOut size={14} /> Sair
            </button>
          ) : (
            <button onClick={() => setShowAuth(true)} className="flex items-center gap-1.5 text-[#6366f1] text-sm font-medium border border-[#6366f1]/30 px-3 py-1.5 rounded-lg hover:bg-[#6366f1]/10 transition-all">
              <User size={14} /> Entrar
            </button>
          )}
        </div>

        {/* Profile card */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
            <Scissors size={26} className="text-white" />
          </div>
          <div>
            <h1 className="text-white font-black text-2xl leading-tight">{profile.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              {profile.city && <div className="flex items-center gap-1"><MapPin size={11} className="text-white/30" /><span className="text-white/40 text-xs">{profile.city}</span></div>}
              <span className="text-white/20 text-xs capitalize">{profile.type === 'barbershop' ? 'Barbearia' : profile.type === 'salon' ? 'Salão' : 'Studio'}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 pb-4" style={{ WebkitOverflowScrolling: 'touch' as any }}>
          {[
            { key: 'agendar',   label: '✂️ Agendar'   },
            { key: 'pacotes',   label: '📦 Pacotes'   },
            ...(clientToken ? [{ key: 'minha-conta', label: '👤 Minha conta' }] : []),
          ].map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key as any)} className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${tab === key ? 'bg-[#6366f1] text-white' : 'bg-white/[0.07] text-white/50 border border-white/[0.08]'}`}>{label}</button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-8">

        {/* ── Agendar ── */}
        {tab === 'agendar' && (
          <div className="space-y-4">
            {/* Profissionais */}
            {professionals.length > 0 && (
              <div>
                <h3 className="text-white/40 text-xs uppercase tracking-wide mb-3">Profissionais</h3>
                <div className="flex gap-2 overflow-x-auto pb-1" style={{ WebkitOverflowScrolling: 'touch' as any }}>
                  {professionals.map((p: any) => (
                    <div key={p.id} className="flex-shrink-0 flex flex-col items-center gap-1.5 px-4 py-3 bg-white/[0.04] border border-white/[0.06] rounded-2xl">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                        <span className="text-white font-bold">{p.name[0]}</span>
                      </div>
                      <span className="text-white/60 text-xs">{p.name.split(' ')[0]}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Serviços */}
            {services.length > 0 && (
              <div>
                <h3 className="text-white/40 text-xs uppercase tracking-wide mb-3">Serviços</h3>
                <div className="space-y-2">
                  {services.map((s: any) => (
                    <div key={s.id} className="flex items-center justify-between p-4 bg-white/[0.03] border border-white/[0.06] rounded-2xl">
                      <div>
                        <div className="text-white font-medium text-sm">{s.name}</div>
                        <div className="text-white/30 text-xs mt-0.5">{s.duration_min} minutos</div>
                      </div>
                      <div className="text-[#6366f1] font-bold">R${Number(s.price).toFixed(0)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CTA Agendar */}
            <button
              onClick={() => clientToken ? setShowBooking(true) : setShowAuth(true)}
              className="w-full bg-[#6366f1] hover:bg-[#4f46e5] text-white font-bold py-4 rounded-2xl transition-all active:scale-[0.98] text-base shadow-[0_4px_20px_rgba(99,102,241,0.4)]"
            >
              {clientToken ? 'Agendar agora ✂️' : 'Entrar para agendar →'}
            </button>
          </div>
        )}

        {/* ── Pacotes ── */}
        {tab === 'pacotes' && (
          <div className="space-y-3">
            {packages.length === 0 ? (
              <div className="text-center py-12 text-white/30 text-sm">Nenhum pacote disponível</div>
            ) : packages.map((p: any) => (
              <div key={p.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="text-white font-bold">{p.name}</div>
                    <div className="text-white/40 text-sm">{p.service?.name || p.service_name}</div>
                  </div>
                  <div className="text-[#6366f1] font-bold text-lg">R${Number(p.price).toFixed(0)}</div>
                </div>
                <div className="text-white/30 text-xs">{p.sessions} sessões · economia de R${((p.original_price || 0) - p.price).toFixed(0)}</div>
                {p.description && <p className="text-white/30 text-xs mt-2">{p.description}</p>}
              </div>
            ))}
          </div>
        )}

        {/* ── Minha conta ── */}
        {(tab as string) === 'minha-conta' && clientToken && (
          <div className="space-y-3">
            {clientData && (
              <div className="bg-white/[0.04] border border-white/[0.06] rounded-2xl p-4 flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                  <span className="text-white font-bold">{(clientData.name || '?')[0]}</span>
                </div>
                <div>
                  <div className="text-white font-semibold">{clientData.name || 'Cliente'}</div>
                  <div className="text-white/40 text-sm">{clientData.phone}</div>
                </div>
              </div>
            )}
            <h3 className="text-white/40 text-xs uppercase tracking-wide">Meus agendamentos</h3>
            {myAppointments.length === 0 ? (
              <div className="text-center py-8 text-white/30 text-sm">Nenhum agendamento</div>
            ) : myAppointments.map((a: any) => (
              <div key={a.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-white font-medium text-sm">{a.service_name || a.service}</div>
                    <div className="text-white/40 text-xs mt-0.5">
                      {a.professional_name || a.professional} · {new Date(a.starts_at).toLocaleDateString('pt-BR')} {formatTime(a.starts_at)}
                    </div>
                  </div>
                  <div className={`text-xs px-2.5 py-1 rounded-full ${
                    a.status === 'confirmed' ? 'bg-indigo-500/10 text-indigo-400' :
                    a.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                    a.status === 'cancelled' ? 'bg-red-500/10 text-red-400' :
                    'bg-amber-500/10 text-amber-400'
                  }`}>
                    {a.status === 'confirmed' ? 'Confirmado' : a.status === 'completed' ? 'Realizado' : a.status === 'cancelled' ? 'Cancelado' : 'Pendente'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showAuth    && <AuthSheet slug={slug} onAuth={handleAuth} onClose={() => setShowAuth(false)} />}
      {showBooking && (
        <BookingSheet
          slug={slug}
          professionals={professionals}
          services={services}
          onClose={() => setShowBooking(false)}
          onBooked={() => { setShowBooking(false); publicApi.myAppointments(slug).then(({ data }) => setMyAppts(data.appointments || data || [])) }}
        />
      )}
    </div>
  )
}