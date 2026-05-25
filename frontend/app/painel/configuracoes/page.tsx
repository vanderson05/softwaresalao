'use client'
// app/painel/configuracoes/page.tsx

import { useEffect, useState } from 'react'
import {
  Building2, Users, Scissors, Bot, CreditCard,
  X, Plus, ChevronRight, Check, Save, Trash2,
  Clock, Settings
} from 'lucide-react'
import { setupApi, professionalsApi, servicesApi, agentApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }
const inputClass = "w-full h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

const WEEKDAYS = [
  { id: 0, label: 'Segunda' }, { id: 1, label: 'Terça' }, { id: 2, label: 'Quarta' },
  { id: 3, label: 'Quinta' }, { id: 4, label: 'Sexta' }, { id: 5, label: 'Sábado' }, { id: 6, label: 'Domingo' },
]

const PLAN_INFO: Record<string, { label: string; color: string; description: string }> = {
  trial:      { label: 'Trial',      color: 'text-amber-400',  description: '14 dias de acesso completo'          },
  starter:    { label: 'Starter',    color: 'text-slate-400',  description: '1 profissional · R$99,90/mês'        },
  pro:        { label: 'Pro',        color: 'text-indigo-400', description: 'Até 5 profissionais · R$149,90/mês'  },
  advanced:   { label: 'Advanced',   color: 'text-purple-400', description: 'Até 15 profissionais · R$199,90/mês' },
  enterprise: { label: 'Enterprise', color: 'text-emerald-400',description: 'Ilimitado · R$279,90/mês'            },
}

type Tab = 'estabelecimento' | 'profissionais' | 'servicos' | 'agente' | 'plano'

// ── Professional Sheet ────────────────────────────────────────
function ProfessionalSheet({ prof, onClose, onSaved }: { prof?: any; onClose: () => void; onSaved: () => void }) {
  const isEdit = !!prof
  const [form, setForm] = useState({
    name:            prof?.name            || '',
    commission_pct:  prof?.commission_pct  || '40',
    slot_interval:   prof?.slot_interval   || '30',
    employment_type: prof?.employment_type || 'commissioned',
  })
  const [loading, setLoading] = useState(false)

  async function handleSave() {
    if (!form.name) { toast.error('Informe o nome.'); return }
    setLoading(true)
    try {
      if (isEdit) {
        await professionalsApi.update(prof.id, { ...form, commission_pct: Number(form.commission_pct), slot_interval: Number(form.slot_interval) })
      } else {
        await professionalsApi.create({ ...form, commission_pct: Number(form.commission_pct), slot_interval: Number(form.slot_interval) })
      }
      toast.success(isEdit ? 'Profissional atualizado!' : 'Profissional criado!')
      onSaved()
    } catch { toast.error('Erro ao salvar.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">{isEdit ? 'Editar profissional' : 'Novo profissional'}</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div><label className="text-white/50 text-sm block mb-1.5">Nome *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Carlos Silva" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-white/50 text-sm block mb-1.5">Comissão (%)</label><input type="number" value={form.commission_pct} onChange={e => setForm(f => ({ ...f, commission_pct: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div>
              <label className="text-white/50 text-sm block mb-1.5">Intervalo de slot</label>
              <select value={form.slot_interval} onChange={e => setForm(f => ({ ...f, slot_interval: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }}>
                {[15,20,30,45,60].map(v => <option key={v} value={v}>{v} min</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-white/50 text-sm block mb-2">Tipo de vínculo</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { v: 'commissioned', l: 'Comissionado', d: 'Pode cancelar próprios' },
                { v: 'employed',     l: 'Contratado',   d: 'Não cancela sozinho'    },
              ].map(({ v, l, d }) => (
                <button key={v} onClick={() => setForm(f => ({ ...f, employment_type: v }))} className={`p-3 rounded-xl border text-left transition-all active:scale-[0.98] ${form.employment_type === v ? 'bg-[#6366f1]/15 border-[#6366f1]/40' : 'bg-white/[0.04] border-white/[0.08]'}`}>
                  <div className={`text-sm font-medium ${form.employment_type === v ? 'text-white' : 'text-white/50'}`}>{l}</div>
                  <div className="text-white/30 text-xs mt-0.5">{d}</div>
                </button>
              ))}
            </div>
          </div>
          <button onClick={handleSave} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Salvando...' : isEdit ? 'Salvar alterações' : 'Criar profissional'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Service Sheet ─────────────────────────────────────────────
function ServiceSheet({ service, onClose, onSaved }: { service?: any; onClose: () => void; onSaved: () => void }) {
  const isEdit = !!service
  const [form, setForm] = useState({ name: service?.name || '', duration_min: service?.duration_min || '30', price: service?.price || '' })
  const [loading, setLoading] = useState(false)

  async function handleSave() {
    if (!form.name || !form.price) { toast.error('Preencha todos os campos.'); return }
    setLoading(true)
    try {
      if (isEdit) {
        await servicesApi.update(service.id, { ...form, duration_min: Number(form.duration_min), price: Number(form.price) })
      } else {
        await servicesApi.create({ ...form, duration_min: Number(form.duration_min), price: Number(form.price) })
      }
      toast.success(isEdit ? 'Serviço atualizado!' : 'Serviço criado!')
      onSaved()
    } catch { toast.error('Erro ao salvar.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-96 z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">{isEdit ? 'Editar serviço' : 'Novo serviço'}</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div><label className="text-white/50 text-sm block mb-1.5">Nome *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Corte masculino" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-white/50 text-sm block mb-1.5">Duração</label>
              <select value={form.duration_min} onChange={e => setForm(f => ({ ...f, duration_min: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }}>
                {[15,20,30,45,60,90,120].map(v => <option key={v} value={v}>{v} min</option>)}
              </select>
            </div>
            <div><label className="text-white/50 text-sm block mb-1.5">Preço (R$) *</label><input type="number" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} placeholder="35" className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <button onClick={handleSave} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Salvando...' : isEdit ? 'Salvar' : 'Criar serviço'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function ConfiguracoesPage() {
  const { tenant, setTenant } = useAuthStore()
  const { plan, isTrial } = usePermissions()
  const [tab, setTab] = useState<Tab>('estabelecimento')
  const [loading, setLoading] = useState(false)

  // Estabelecimento
  const [estab, setEstab] = useState<any>(null)
  const [hours, setHours] = useState<any[]>([])

  // Profissionais
  const [professionals, setProfessionals] = useState<any[]>([])
  const [editProf, setEditProf] = useState<any>(null)
  const [showNewProf, setShowNewProf] = useState(false)

  // Serviços
  const [services, setServices] = useState<any[]>([])
  const [editSvc, setEditSvc] = useState<any>(null)
  const [showNewSvc, setShowNewSvc] = useState(false)

  // Agente
  const [agentConfig, setAgentConfig] = useState<any>(null)

  useEffect(() => {
    if (tab === 'estabelecimento') {
      setupApi.establishment().then(({ data }) => {
        setEstab(data)
        setHours(data.business_hours?.length ? data.business_hours : WEEKDAYS.map(d => ({ weekday: d.id, open_time: '09:00', close_time: '18:00', is_closed: d.id === 6 })))
      }).catch(() => {})
    }
    if (tab === 'profissionais') {
      professionalsApi.list().then(({ data }) => setProfessionals(data)).catch(() => {})
    }
    if (tab === 'servicos') {
      servicesApi.list().then(({ data }) => setServices(data)).catch(() => {})
    }
    if (tab === 'agente') {
      agentApi.config().then(({ data }) => setAgentConfig(data)).catch(() => {})
    }
  }, [tab])

  function updateHour(weekday: number, field: string, value: any) {
    setHours(prev => prev.map(h => h.weekday === weekday ? { ...h, [field]: value } : h))
  }

  async function saveEstab() {
    if (!estab?.address || !estab?.city) { toast.error('Endereço e cidade são obrigatórios.'); return }
    setLoading(true)
    try {
      await setupApi.updateEstablishment({ address: estab.address, city: estab.city, phone: estab.phone, business_hours: hours })
      toast.success('Estabelecimento atualizado!')
    } catch { toast.error('Erro ao salvar.') }
    finally { setLoading(false) }
  }

  async function saveAgent() {
    setLoading(true)
    try {
      await agentApi.updateConfig(agentConfig)
      toast.success('Agente atualizado!')
    } catch { toast.error('Erro ao salvar.') }
    finally { setLoading(false) }
  }

  async function deleteProf(id: string) {
    if (!confirm('Remover profissional?')) return
    try {
      await professionalsApi.delete(id)
      setProfessionals(prev => prev.filter(p => p.id !== id))
      toast.success('Profissional removido.')
    } catch { toast.error('Erro ao remover.') }
  }

  async function deleteSvc(id: string) {
    if (!confirm('Remover serviço?')) return
    try {
      await servicesApi.delete(id)
      setServices(prev => prev.filter(s => s.id !== id))
      toast.success('Serviço removido.')
    } catch { toast.error('Erro ao remover.') }
  }

  const planInfo = PLAN_INFO[plan] || PLAN_INFO.trial

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-2xl">
      <div className="mb-5">
        <h1 className="text-white font-bold text-xl">Configurações</h1>
        <p className="text-white/30 text-sm mt-0.5">Gerencie sua barbearia</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-6" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        {[
          { key: 'estabelecimento', label: '🏪 Estabelecimento', icon: Building2 },
          { key: 'profissionais',   label: '👤 Profissionais',   icon: Users     },
          { key: 'servicos',        label: '✂️ Serviços',        icon: Scissors  },
          { key: 'agente',          label: '🤖 Agente IA',       icon: Bot       },
          { key: 'plano',           label: '💎 Plano',           icon: CreditCard},
        ].map(({ key, label }) => (
          <button key={key} onClick={() => setTab(key as Tab)} className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${tab === key ? 'bg-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>{label}</button>
        ))}
      </div>

      {/* ── Estabelecimento ── */}
      {tab === 'estabelecimento' && (
        <div className="space-y-4 pb-24 md:pb-6">
          {!estab ? <Skeleton className="h-48" /> : (
            <>
              <div><label className="text-white/50 text-sm block mb-1.5">Nome da barbearia</label><input value={estab.name || ''} disabled className={`${inputClass} opacity-50 cursor-not-allowed`} /></div>
              <div><label className="text-white/50 text-sm block mb-1.5">Endereço</label><input value={estab.address || ''} onChange={e => setEstab((s: any) => ({ ...s, address: e.target.value }))} placeholder="Rua das Flores, 123" className={inputClass} style={{ fontSize: '16px' }} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-white/50 text-sm block mb-1.5">Cidade</label><input value={estab.city || ''} onChange={e => setEstab((s: any) => ({ ...s, city: e.target.value }))} placeholder="São Paulo" className={inputClass} style={{ fontSize: '16px' }} /></div>
                <div><label className="text-white/50 text-sm block mb-1.5">Telefone</label><input value={estab.phone || ''} onChange={e => setEstab((s: any) => ({ ...s, phone: e.target.value }))} placeholder="19999999999" type="tel" className={inputClass} style={{ fontSize: '16px' }} /></div>
              </div>
              <div>
                <label className="text-white/50 text-sm block mb-3">Horários de funcionamento</label>
                <div className="space-y-2">
                  {WEEKDAYS.map(d => {
                    const h = hours.find(x => x.weekday === d.id) || { weekday: d.id, open_time: '09:00', close_time: '18:00', is_closed: false }
                    return (
                      <div key={d.id} className="flex items-center gap-3 bg-white/[0.03] border border-white/[0.05] rounded-xl px-3 py-2.5">
                        <span className="text-white/40 text-xs w-16 flex-shrink-0">{d.label}</span>
                        <input type="checkbox" checked={!h.is_closed} onChange={e => updateHour(d.id, 'is_closed', !e.target.checked)} className="accent-[#6366f1] w-4 h-4 flex-shrink-0" />
                        {!h.is_closed ? (
                          <div className="flex items-center gap-2 flex-1">
                            <input type="time" value={h.open_time} onChange={e => updateHour(d.id, 'open_time', e.target.value)} className="flex-1 h-9 px-2 rounded-lg bg-white/[0.06] border border-white/10 text-white text-xs focus:outline-none" />
                            <span className="text-white/20 text-xs">–</span>
                            <input type="time" value={h.close_time} onChange={e => updateHour(d.id, 'close_time', e.target.value)} className="flex-1 h-9 px-2 rounded-lg bg-white/[0.06] border border-white/10 text-white text-xs focus:outline-none" />
                          </div>
                        ) : <span className="text-white/20 text-xs flex-1">Fechado</span>}
                      </div>
                    )
                  })}
                </div>
              </div>
              <button onClick={saveEstab} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2">
                <Save size={16} /> {loading ? 'Salvando...' : 'Salvar alterações'}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Profissionais ── */}
      {tab === 'profissionais' && (
        <div className="space-y-3 pb-24 md:pb-6">
          <button onClick={() => setShowNewProf(true)} className="w-full flex items-center gap-3 p-4 rounded-2xl border border-dashed border-white/20 text-white/40 hover:text-white hover:border-white/30 transition-all active:scale-[0.98]">
            <Plus size={18} /><span className="text-sm font-medium">Adicionar profissional</span>
          </button>
          {professionals.map(p => (
            <div key={p.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm">{p.name[0]}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white font-medium text-sm truncate">{p.name}</div>
                <div className="text-white/30 text-xs">{p.commission_pct}% comissão · slot {p.slot_interval}min · {p.employment_type === 'commissioned' ? 'comissionado' : 'contratado'}</div>
              </div>
              <div className="flex gap-1.5 flex-shrink-0">
                <button onClick={() => setEditProf(p)} className="w-9 h-9 flex items-center justify-center bg-white/[0.06] hover:bg-white/10 border border-white/[0.08] rounded-xl text-white/40 hover:text-white transition-all active:scale-95">
                  <Settings size={15} />
                </button>
                <button onClick={() => deleteProf(p.id)} className="w-9 h-9 flex items-center justify-center bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl text-red-400 transition-all active:scale-95">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Serviços ── */}
      {tab === 'servicos' && (
        <div className="space-y-3 pb-24 md:pb-6">
          <button onClick={() => setShowNewSvc(true)} className="w-full flex items-center gap-3 p-4 rounded-2xl border border-dashed border-white/20 text-white/40 hover:text-white hover:border-white/30 transition-all active:scale-[0.98]">
            <Plus size={18} /><span className="text-sm font-medium">Adicionar serviço</span>
          </button>
          {services.map(s => (
            <div key={s.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#6366f1]/10 border border-[#6366f1]/20 flex items-center justify-center flex-shrink-0">
                <Scissors size={16} className="text-[#6366f1]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white font-medium text-sm truncate">{s.name}</div>
                <div className="text-white/30 text-xs">{s.duration_min}min · R${Number(s.price).toFixed(2)}</div>
              </div>
              <div className="flex gap-1.5 flex-shrink-0">
                <button onClick={() => setEditSvc(s)} className="w-9 h-9 flex items-center justify-center bg-white/[0.06] hover:bg-white/10 border border-white/[0.08] rounded-xl text-white/40 hover:text-white transition-all active:scale-95">
                  <Settings size={15} />
                </button>
                <button onClick={() => deleteSvc(s.id)} className="w-9 h-9 flex items-center justify-center bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl text-red-400 transition-all active:scale-95">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Agente IA ── */}
      {tab === 'agente' && (
        <div className="space-y-4 pb-24 md:pb-6">
          {!agentConfig ? <Skeleton className="h-48" /> : (
            <>
              <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 mb-2">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${agentConfig.wa_token ? 'bg-emerald-400' : 'bg-red-400'}`} />
                  <span className="text-white/50 text-sm">{agentConfig.wa_token ? 'WhatsApp conectado' : 'WhatsApp não configurado'}</span>
                </div>
                <div className="text-white/30 text-xs">Configure o token Meta para ativar o agente</div>
              </div>
              {[
                { field: 'agent_name',    label: 'Nome do agente',   placeholder: 'Beauti Assistente'    },
                { field: 'wa_phone_number_id', label: 'Phone Number ID (Meta)', placeholder: '1234567890' },
                { field: 'wa_token',      label: 'Token de acesso (Meta)', placeholder: 'EAABxxxxxx'    },
                { field: 'wa_verify_token', label: 'Verify Token (webhook)', placeholder: 'beauti_2026' },
              ].map(({ field, label, placeholder }) => (
                <div key={field}>
                  <label className="text-white/50 text-sm block mb-1.5">{label}</label>
                  <input value={agentConfig[field] || ''} onChange={e => setAgentConfig((c: any) => ({ ...c, [field]: e.target.value }))} placeholder={placeholder} className={inputClass} style={{ fontSize: '16px' }} />
                </div>
              ))}
              <div>
                <label className="text-white/50 text-sm block mb-1.5">Tom do agente</label>
                <div className="grid grid-cols-3 gap-2">
                  {[{ v: 'formal', l: 'Formal' }, { v: 'friendly', l: 'Amigável' }, { v: 'casual', l: 'Casual' }].map(({ v, l }) => (
                    <button key={v} onClick={() => setAgentConfig((c: any) => ({ ...c, tone: v }))} className={`py-2.5 rounded-xl text-sm font-medium transition-all active:scale-95 ${agentConfig.tone === v ? 'bg-[#6366f1] text-white' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>{l}</button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-white/50 text-sm block mb-1.5">Prompt personalizado</label>
                <textarea value={agentConfig.custom_prompt || ''} onChange={e => setAgentConfig((c: any) => ({ ...c, custom_prompt: e.target.value }))} placeholder="Ex: Sempre mencionar promoções de segunda-feira..." rows={3} className="w-full px-4 py-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 resize-none" style={{ fontSize: '16px' }} />
              </div>
              <button onClick={saveAgent} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2">
                <Save size={16} /> {loading ? 'Salvando...' : 'Salvar configurações'}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Plano ── */}
      {tab === 'plano' && (
        <div className="space-y-4 pb-24 md:pb-6">
          <div className="bg-gradient-to-br from-[#6366f1]/20 to-[#8B5CF6]/10 border border-[#6366f1]/30 rounded-2xl p-6 text-center">
            <div className={`text-3xl font-black mb-1 ${planInfo.color}`}>{planInfo.label}</div>
            <div className="text-white/50 text-sm">{planInfo.description}</div>
            {isTrial && tenant?.trial_days_remaining !== undefined && (
              <div className="mt-3 bg-amber-500/20 border border-amber-500/30 rounded-xl px-4 py-2.5 inline-block">
                <span className="text-amber-300 text-sm font-semibold">{tenant.trial_days_remaining} dias restantes no trial</span>
              </div>
            )}
          </div>

          <div className="space-y-2">
            {[
              { plan: 'starter',    name: 'Starter',    price: 'R$99,90',  profs: '1',    features: ['Agenda', 'Agente WhatsApp IA', 'Link público']              },
              { plan: 'pro',        name: 'Pro',        price: 'R$149,90', profs: 'até 5', features: ['+ CRM', 'Financeiro', 'Comissões', 'Pacotes', 'Relatórios'] },
              { plan: 'advanced',   name: 'Advanced',   price: 'R$199,90', profs: 'até 15',features: ['+ Insights IA', 'Domínio customizado', 'Blast promoções']   },
              { plan: 'enterprise', name: 'Enterprise', price: 'R$279,90', profs: 'ilimitado', features: ['+ Suporte dedicado', 'SLA', 'Onboarding assistido']     },
            ].map(p => (
              <div key={p.plan} className={`bg-white/[0.03] border rounded-2xl p-5 transition-all ${plan === p.plan ? 'border-[#6366f1]/40 bg-[#6366f1]/5' : 'border-white/[0.06]'}`}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-bold">{p.name}</span>
                      {plan === p.plan && <span className="text-xs bg-[#6366f1] text-white px-2 py-0.5 rounded-full">Atual</span>}
                    </div>
                    <div className="text-white/30 text-xs mt-0.5">{p.profs} profissional{p.profs !== '1' ? 'is' : ''}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">{p.price}</div>
                    <div className="text-white/30 text-xs">/mês</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {p.features.map(f => <span key={f} className="text-xs bg-white/[0.06] text-white/40 px-2.5 py-1 rounded-full">{f}</span>)}
                </div>
                {plan !== p.plan && (
                  <button className="mt-3 w-full py-2.5 rounded-xl border border-[#6366f1]/30 text-[#6366f1] text-sm font-medium hover:bg-[#6366f1]/10 transition-all active:scale-[0.98]">
                    Fazer upgrade
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sheets */}
      {showNewProf && <ProfessionalSheet onClose={() => setShowNewProf(false)} onSaved={() => { setShowNewProf(false); professionalsApi.list().then(({ data }) => setProfessionals(data)) }} />}
      {editProf && <ProfessionalSheet prof={editProf} onClose={() => setEditProf(null)} onSaved={() => { setEditProf(null); professionalsApi.list().then(({ data }) => setProfessionals(data)) }} />}
      {showNewSvc && <ServiceSheet onClose={() => setShowNewSvc(false)} onSaved={() => { setShowNewSvc(false); servicesApi.list().then(({ data }) => setServices(data)) }} />}
      {editSvc && <ServiceSheet service={editSvc} onClose={() => setEditSvc(null)} onSaved={() => { setEditSvc(null); servicesApi.list().then(({ data }) => setServices(data)) }} />}
    </div>
  )
}