'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { setupApi, professionalsApi, servicesApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { toast } from 'sonner'
import { Check, Building2, Users, Scissors, Clock } from 'lucide-react'

const STEPS = [
  { id: 1, title: 'Estabelecimento', icon: Building2 },
  { id: 2, title: 'Profissionais',   icon: Users },
  { id: 3, title: 'Serviços',        icon: Scissors },
  { id: 4, title: 'Horários',        icon: Clock },
]

const WEEKDAYS = [
  { id: 0, label: 'Seg' },
  { id: 1, label: 'Ter' },
  { id: 2, label: 'Qua' },
  { id: 3, label: 'Qui' },
  { id: 4, label: 'Sex' },
  { id: 5, label: 'Sáb' },
  { id: 6, label: 'Dom' },
]

export default function SetupPage() {
  const router  = useRouter()
  const { tenant, setTenant } = useAuthStore()
  const [step,    setStep]    = useState(1)
  const [loading, setLoading] = useState(false)

  // Passo 1
  const [address, setAddress] = useState('')
  const [city,    setCity]    = useState('')
  const [hours,   setHours]   = useState(
    WEEKDAYS.map((d) => ({ weekday: d.id, open_time: '09:00', close_time: '18:00', is_closed: d.id === 6 }))
  )

  // Passo 2
  const [profName,       setProfName]       = useState('')
  const [profCommission, setProfCommission] = useState('40')
  const [professionals,  setProfessionals]  = useState<any[]>([])

  // Passo 3
  const [svcName,     setSvcName]     = useState('')
  const [svcDuration, setSvcDuration] = useState('30')
  const [svcPrice,    setSvcPrice]    = useState('')
  const [services,    setServices]    = useState<any[]>([])

  // Passo 4
  const [schedules, setSchedules] = useState<any[]>([])

    useEffect(() => {
    const token = localStorage.getItem('beauti_token')
    if (!token) {
        router.replace('/login')
        return
    }
    if (tenant?.setup_completed) {
        router.replace('/painel')
    }
    }, [tenant, router])

  function updateHour(weekday: number, field: string, value: string | boolean) {
    setHours((prev) => prev.map((h) => h.weekday === weekday ? { ...h, [field]: value } : h))
  }

  async function handleStep1() {
    if (!address || !city) { toast.error('Informe o endereço e a cidade.'); return }
    setLoading(true)
    try {
      await setupApi.updateEstablishment({
        address, city,
        business_hours: hours,
      })
      toast.success('Estabelecimento configurado!')
      setStep(2)
    } catch { toast.error('Erro ao salvar.') }
    finally { setLoading(false) }
  }

  async function handleAddProfessional() {
    if (!profName) { toast.error('Informe o nome.'); return }
    setLoading(true)
    try {
      const { data } = await professionalsApi.create({ name: profName, commission_pct: Number(profCommission), slot_interval: 30 })
      setProfessionals((prev) => [...prev, data])
      setProfName(''); setProfCommission('40')
      toast.success(`${data.name} adicionado!`)
    } catch { toast.error('Erro ao adicionar.') }
    finally { setLoading(false) }
  }

  async function handleAddService() {
    if (!svcName || !svcPrice) { toast.error('Preencha todos os campos.'); return }
    setLoading(true)
    try {
      const { data } = await servicesApi.create({ name: svcName, duration_min: Number(svcDuration), price: Number(svcPrice) })
      setServices((prev) => [...prev, data])
      setSvcName(''); setSvcPrice(''); setSvcDuration('30')
      toast.success(`${data.name} adicionado!`)
    } catch { toast.error('Erro ao adicionar.') }
    finally { setLoading(false) }
  }

  async function handleStep4() {
    if (professionals.length === 0) { toast.error('Adicione pelo menos 1 profissional.'); return }
    setLoading(true)
    try {
      for (const prof of professionals) {
        const profSchedules = schedules.filter((s) => s.professional_id === prof.id)
        if (profSchedules.length === 0) {
          // Usa horários padrão do estabelecimento
          const defaultSchedules = hours
            .filter((h) => !h.is_closed)
            .map((h) => ({ weekday: h.weekday, start_time: h.open_time, end_time: h.close_time }))
          await professionalsApi.scheduleBulk({ professional_id: prof.id, schedules: defaultSchedules })
        }
      }
      const { data } = await setupApi.complete()
      setTenant({ ...tenant!, setup_completed: true })
      toast.success('Tudo pronto! Bem-vindo ao Beauti 🎉')
      router.replace('/painel')
    } catch (err: any) {
      const errors = err.response?.data?.errors
      toast.error(errors?.[0] || 'Erro ao concluir setup.')
    }
    finally { setLoading(false) }
  }

  const inputClass = "w-full h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"
  const btnClass   = "w-full h-11 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl text-sm transition-colors disabled:opacity-50"

  return (
    <div className="min-h-screen bg-[#0A0A0F] flex flex-col items-center justify-center p-4">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] mb-3">
          <span className="text-white text-xl font-bold">B</span>
        </div>
        <h1 className="text-white font-bold text-xl">Configurar minha barbearia</h1>
        <p className="text-white/40 text-sm mt-1">Leva menos de 5 minutos</p>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center gap-2 mb-8">
        {STEPS.map((s, i) => (
          <div key={s.id} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
              step > s.id  ? 'bg-[#10B981] text-white' :
              step === s.id ? 'bg-[#6366f1] text-white' :
              'bg-white/10 text-white/30'
            }`}>
              {step > s.id ? <Check size={14} /> : s.id}
            </div>
            <span className={`text-xs hidden sm:block ${step === s.id ? 'text-white' : 'text-white/30'}`}>
              {s.title}
            </span>
            {i < STEPS.length - 1 && <div className={`w-6 h-px ${step > s.id ? 'bg-[#10B981]' : 'bg-white/10'}`} />}
          </div>
        ))}
      </div>

      {/* Card */}
      <div className="w-full max-w-md bg-white/[0.04] border border-white/10 rounded-2xl p-6">

        {/* Passo 1 */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-white font-semibold text-lg">Dados do estabelecimento</h2>
            <div>
              <label className="text-white/60 text-sm block mb-1.5">Endereço</label>
              <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Av. Paulista, 1234" className={inputClass} />
            </div>
            <div>
              <label className="text-white/60 text-sm block mb-1.5">Cidade</label>
              <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="São Paulo" className={inputClass} />
            </div>
            <div>
              <label className="text-white/60 text-sm block mb-3">Horários de funcionamento</label>
              <div className="space-y-2">
                {WEEKDAYS.map((d) => {
                  const h = hours.find((x) => x.weekday === d.id)!
                  return (
                    <div key={d.id} className="flex items-center gap-3">
                      <span className="text-white/40 text-xs w-8">{d.label}</span>
                      <input type="checkbox" checked={!h.is_closed} onChange={(e) => updateHour(d.id, 'is_closed', !e.target.checked)}
                        className="accent-[#6366f1]" />
                      {!h.is_closed ? (
                        <div className="flex items-center gap-2 flex-1">
                          <input type="time" value={h.open_time}  onChange={(e) => updateHour(d.id, 'open_time',  e.target.value)}
                            className="flex-1 h-8 px-2 rounded-lg bg-white/[0.06] border border-white/10 text-white text-xs focus:outline-none" />
                          <span className="text-white/30 text-xs">às</span>
                          <input type="time" value={h.close_time} onChange={(e) => updateHour(d.id, 'close_time', e.target.value)}
                            className="flex-1 h-8 px-2 rounded-lg bg-white/[0.06] border border-white/10 text-white text-xs focus:outline-none" />
                        </div>
                      ) : (
                        <span className="text-white/20 text-xs">Fechado</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
            <button onClick={handleStep1} disabled={loading} className={btnClass}>
              {loading ? 'Salvando...' : 'Continuar →'}
            </button>
          </div>
        )}

        {/* Passo 2 */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-white font-semibold text-lg">Profissionais</h2>
            {professionals.length > 0 && (
              <div className="space-y-2">
                {professionals.map((p) => (
                  <div key={p.id} className="flex items-center gap-2 bg-white/[0.04] rounded-xl px-3 py-2.5">
                    <Check size={14} className="text-[#10B981]" />
                    <span className="text-white text-sm">{p.name}</span>
                    <span className="text-white/30 text-xs ml-auto">{p.commission_pct}% comissão</span>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input value={profName} onChange={(e) => setProfName(e.target.value)} placeholder="Nome do profissional"
                className="flex-1 h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors" />
              <input value={profCommission} onChange={(e) => setProfCommission(e.target.value)} placeholder="%" type="number"
                className="w-16 h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors" />
            </div>
            <button onClick={handleAddProfessional} disabled={loading}
              className="w-full h-10 border border-[#6366f1]/40 text-[#6366f1] hover:bg-[#6366f1]/10 font-medium rounded-xl text-sm transition-colors disabled:opacity-50">
              + Adicionar profissional
            </button>
            {professionals.length > 0 && (
              <button onClick={() => setStep(3)} className={btnClass}>Continuar →</button>
            )}
          </div>
        )}

        {/* Passo 3 */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-white font-semibold text-lg">Serviços</h2>
            {services.length > 0 && (
              <div className="space-y-2">
                {services.map((s) => (
                  <div key={s.id} className="flex items-center gap-2 bg-white/[0.04] rounded-xl px-3 py-2.5">
                    <Check size={14} className="text-[#10B981]" />
                    <span className="text-white text-sm">{s.name}</span>
                    <span className="text-white/30 text-xs ml-auto">R${s.price} · {s.duration_min}min</span>
                  </div>
                ))}
              </div>
            )}
            <input value={svcName} onChange={(e) => setSvcName(e.target.value)} placeholder="Nome do serviço" className={inputClass} />
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="text-white/40 text-xs block mb-1">Duração (min)</label>
                <input value={svcDuration} onChange={(e) => setSvcDuration(e.target.value)} type="number" placeholder="30" className={inputClass} />
              </div>
              <div className="flex-1">
                <label className="text-white/40 text-xs block mb-1">Preço (R$)</label>
                <input value={svcPrice} onChange={(e) => setSvcPrice(e.target.value)} type="number" placeholder="35" className={inputClass} />
              </div>
            </div>
            <button onClick={handleAddService} disabled={loading}
              className="w-full h-10 border border-[#6366f1]/40 text-[#6366f1] hover:bg-[#6366f1]/10 font-medium rounded-xl text-sm transition-colors disabled:opacity-50">
              + Adicionar serviço
            </button>
            {services.length > 0 && (
              <button onClick={() => setStep(4)} className={btnClass}>Continuar →</button>
            )}
          </div>
        )}

        {/* Passo 4 */}
        {step === 4 && (
          <div className="space-y-4">
            <h2 className="text-white font-semibold text-lg">Horários dos profissionais</h2>
            <p className="text-white/40 text-sm">
              Os horários do estabelecimento serão aplicados automaticamente a todos os profissionais. Você pode ajustar individualmente depois.
            </p>
            <div className="bg-white/[0.04] rounded-xl p-4 space-y-2">
              {hours.filter((h) => !h.is_closed).map((h) => (
                <div key={h.weekday} className="flex justify-between text-sm">
                  <span className="text-white/50">{WEEKDAYS.find((d) => d.id === h.weekday)?.label}</span>
                  <span className="text-white/70">{h.open_time} – {h.close_time}</span>
                </div>
              ))}
            </div>
            <button onClick={handleStep4} disabled={loading} className={btnClass}>
              {loading ? 'Finalizando...' : '🎉 Concluir configuração'}
            </button>
          </div>
        )}
      </div>

      <p className="text-white/20 text-xs mt-6">
        Passo {step} de 4 · Você pode editar tudo depois nas configurações
      </p>
    </div>
  )
}