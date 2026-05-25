'use client'
// app/painel/clientes/page.tsx
// CRM completo — Clientes, Insights, Pacotes e Assinaturas

import { useEffect, useState, useCallback } from 'react'
import {
  Search, Users, TrendingUp, UserPlus, Clock,
  ChevronRight, X, Calendar, Star, CreditCard,
  FileText, Plus, Package, RefreshCw, Check,
  Cake, MoreVertical
} from 'lucide-react'
import { crmApi, agentApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

// ── Helpers ───────────────────────────────────────────────────

function formatCurrency(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}
function daysAgo(iso: string | null) {
  if (!iso) return null
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (days === 0) return 'hoje'
  if (days === 1) return 'ontem'
  return `há ${days} dias`
}
function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} />
}

const inputClass = "w-full h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

// ── Insight Card ──────────────────────────────────────────────
function InsightCard({ label, value, sub, icon: Icon, color }: any) {
  return (
    <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-start gap-3">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={16} className="text-white" />
      </div>
      <div>
        <div className="text-white/40 text-xs">{label}</div>
        <div className="text-white font-bold text-lg leading-tight">{value}</div>
        {sub && <div className="text-white/30 text-xs mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

// ── Client Card ───────────────────────────────────────────────
function ClientCard({ client, onClick }: { client: any; onClick: () => void }) {
  const initials = client.name?.split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase() || '?'
  const ago = daysAgo(client.last_visit_at)
  const isInactive = client.last_visit_at && (Date.now() - new Date(client.last_visit_at).getTime()) > 30 * 86400000
  return (
    <button onClick={onClick} className="w-full flex items-center gap-3 p-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10 active:scale-[0.98] transition-all text-left min-h-[64px]">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
        <span className="text-white text-sm font-bold">{initials}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-white font-semibold text-sm truncate">{client.name}</div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-white/30 text-xs">{client.phone}</span>
          {ago && <span className={`text-xs ${isInactive ? 'text-amber-400/70' : 'text-white/20'}`}>· {ago}</span>}
        </div>
      </div>
      <div className="text-right flex-shrink-0">
        <div className="text-white/50 text-xs font-medium">{client.total_visits} visitas</div>
        <div className="text-white/30 text-xs">{formatCurrency(client.total_spent || 0)}</div>
      </div>
      <ChevronRight size={14} className="text-white/20 flex-shrink-0" />
    </button>
  )
}

// ── Client Detail Sheet ───────────────────────────────────────
function ClientSheet({ clientId, onClose }: { clientId: string; onClose: () => void }) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'overview' | 'history' | 'packages'>('overview')

  useEffect(() => {
    crmApi.client(clientId).then(({ data }) => setData(data)).catch(() => toast.error('Erro ao carregar.')).finally(() => setLoading(false))
  }, [clientId])

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto" style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1 sticky top-0 bg-[#0D0D14]"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        {loading ? (
          <div className="p-5 space-y-3"><Skeleton className="h-16" /><Skeleton className="h-24" /><Skeleton className="h-32" /></div>
        ) : data && (
          <>
            <div className="flex items-start justify-between px-5 pt-4 pb-4 border-b border-white/[0.06] sticky top-5 bg-[#0D0D14] z-10">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
                  <span className="text-white font-bold text-base">{data.client.name?.split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase()}</span>
                </div>
                <div>
                  <div className="text-white font-bold text-base">{data.client.name}</div>
                  <div className="text-white/40 text-sm">{data.client.phone}</div>
                </div>
              </div>
              <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
            </div>
            <div className="flex border-b border-white/[0.06] px-5">
              {[{ key: 'overview', label: 'Geral' }, { key: 'history', label: 'Histórico' }, { key: 'packages', label: 'Pacotes' }].map(({ key, label }) => (
                <button key={key} onClick={() => setTab(key as any)} className={`py-3 px-1 mr-5 text-sm font-medium border-b-2 transition-all ${tab === key ? 'border-[#6366f1] text-white' : 'border-transparent text-white/30'}`}>{label}</button>
              ))}
            </div>
            <div className="px-5 py-4">
              {tab === 'overview' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    {[{ label: 'Visitas', value: data.profile.total_visits, icon: Calendar }, { label: 'Gasto', value: formatCurrency(data.profile.total_spent), icon: TrendingUp }, { label: 'Pontos', value: data.profile.loyalty_points, icon: Star }].map(({ label, value, icon: Icon }) => (
                      <div key={label} className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-3 text-center">
                        <Icon size={14} className="text-white/30 mx-auto mb-1" />
                        <div className="text-white font-bold text-sm leading-tight">{value}</div>
                        <div className="text-white/30 text-xs mt-0.5">{label}</div>
                      </div>
                    ))}
                  </div>
                  <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl divide-y divide-white/[0.04]">
                    <div className="flex justify-between px-4 py-3"><span className="text-white/30 text-sm">Última visita</span><span className="text-white/70 text-sm">{formatDate(data.profile.last_visit_at)}</span></div>
                    <div className="flex justify-between px-4 py-3"><span className="text-white/30 text-sm">Cliente desde</span><span className="text-white/70 text-sm">{formatDate(data.profile.since)}</span></div>
                    {data.profile.birthdate && <div className="flex justify-between px-4 py-3"><span className="text-white/30 text-sm">Aniversário</span><span className="text-white/70 text-sm">{new Date(data.profile.birthdate + 'T00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: 'long' })}</span></div>}
                  </div>
                  {data.subscription && (
                    <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-1"><CreditCard size={14} className="text-indigo-400" /><span className="text-indigo-300 text-sm font-semibold">{data.subscription.name}</span></div>
                      <div className="text-white/40 text-xs">{data.subscription.type === 'unlimited' ? 'Visitas ilimitadas' : `${data.subscription.visits_remaining ?? '—'} visitas restantes`} · R${Number(data.subscription.price).toFixed(2)}/mês</div>
                    </div>
                  )}
                  {data.profile.notes && (
                    <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3">
                      <div className="text-white/30 text-xs mb-1 flex items-center gap-1"><FileText size={12} /> Observações</div>
                      <p className="text-white/60 text-sm">{data.profile.notes}</p>
                    </div>
                  )}
                </div>
              )}
              {tab === 'history' && (
                <div className="space-y-1">
                  {!data.appointments?.length ? <div className="text-center py-8 text-white/30 text-sm">Sem histórico</div> : data.appointments.map((a: any) => (
                    <div key={a.id} className="flex items-center gap-3 py-3 border-b border-white/[0.04] last:border-0">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${a.status === 'completed' ? 'bg-emerald-400' : a.status === 'cancelled' ? 'bg-red-400' : 'bg-white/20'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-white/70 text-sm truncate">{a.service}</div>
                        <div className="text-white/30 text-xs">{formatDate(a.starts_at)} · {a.professional}</div>
                      </div>
                      <div className="text-white/40 text-sm flex-shrink-0">{formatCurrency(a.price)}</div>
                    </div>
                  ))}
                </div>
              )}
              {tab === 'packages' && (
                <div className="space-y-3">
                  {!data.packages?.length ? <div className="text-center py-8 text-white/30 text-sm">Sem pacotes ativos</div> : data.packages.map((p: any) => (
                    <div key={p.id} className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-4">
                      <div className="flex justify-between mb-2"><span className="text-white font-medium text-sm">{p.package_name}</span><span className="text-white/40 text-xs">{p.service}</span></div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-white/[0.06] rounded-full overflow-hidden"><div className="h-full bg-[#6366f1] rounded-full" style={{ width: `${(p.sessions_remaining / p.sessions_total) * 100}%` }} /></div>
                        <span className="text-white/50 text-xs">{p.sessions_remaining}/{p.sessions_total}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}

// ── Pacotes Sheet ─────────────────────────────────────────────
function PackageSheet({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ name: '', service_id: '', sessions: '4', price: '', description: '' })
  const [services, setServices] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    import('@/lib/api').then(({ servicesApi }) => servicesApi.list().then(({ data }) => setServices(data)).catch(() => {}))
  }, [])

  async function handleCreate() {
    if (!form.name || !form.service_id || !form.price) { toast.error('Preencha todos os campos obrigatórios.'); return }
    setLoading(true)
    try {
      await import('@/lib/api').then(({ default: api }) => api.post('/packages/', {
        name: form.name,
        service_id: form.service_id,
        sessions: Number(form.sessions),        // ← correto
        price: Number(form.price),
        description: form.description,
      }))
      toast.success('Pacote criado!')
      onCreated()
    } catch { toast.error('Erro ao criar pacote.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">Novo pacote</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div><label className="text-white/50 text-sm block mb-1.5">Nome do pacote *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Ex: Pacote 4 Cortes" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div>
            <label className="text-white/50 text-sm block mb-1.5">Serviço *</label>
            <select value={form.service_id} onChange={e => setForm(f => ({ ...f, service_id: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }}>
              <option value="">Selecionar serviço</option>
              {services.map((s: any) => <option key={s.id} value={s.id}>{s.name} — R${s.price}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-white/50 text-sm block mb-1.5">Sessões</label><input type="number" value={form.sessions} onChange={e => setForm(f => ({ ...f, sessions: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div><label className="text-white/50 text-sm block mb-1.5">Preço total *</label><input type="number" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} placeholder="R$" className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Descrição</label><input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Opcional" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <button onClick={handleCreate} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Criando...' : 'Criar pacote'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Assinatura Sheet ──────────────────────────────────────────
function SubscriptionSheet({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ client_phone: '', client_name: '', name: '', type: 'limited', visits_per_month: '4', price: '', active_from: new Date().toISOString().split('T')[0], active_until: '', notes: '' })
  const [loading, setLoading] = useState(false)

  async function handleCreate() {
    if (!form.client_phone || !form.name || !form.price) { toast.error('Preencha os campos obrigatórios.'); return }
    setLoading(true)
    try {
      await crmApi.createSubscription({ ...form, visits_per_month: form.type === 'limited' ? Number(form.visits_per_month) : null, price: Number(form.price), active_until: form.active_until || null })
      toast.success('Assinatura criada!')
      onCreated()
    } catch (err: any) { toast.error(err.response?.data?.error || 'Erro ao criar.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto" style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">Nova assinatura</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2"><label className="text-white/50 text-sm block mb-1.5">Telefone do cliente *</label><input value={form.client_phone} onChange={e => setForm(f => ({ ...f, client_phone: e.target.value }))} placeholder="19999999999" type="tel" className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div className="col-span-2"><label className="text-white/50 text-sm block mb-1.5">Nome do cliente</label><input value={form.client_name} onChange={e => setForm(f => ({ ...f, client_name: e.target.value }))} placeholder="João Silva" className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Nome da assinatura *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Ex: Plano Mensal 4x" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div>
            <label className="text-white/50 text-sm block mb-2">Tipo</label>
            <div className="grid grid-cols-2 gap-2">
              {[{ v: 'limited', l: 'Limitado (N/mês)' }, { v: 'unlimited', l: 'Ilimitado' }].map(({ v, l }) => (
                <button key={v} onClick={() => setForm(f => ({ ...f, type: v }))} className={`py-3 rounded-xl text-sm font-medium transition-all active:scale-95 ${form.type === v ? 'bg-[#6366f1] text-white' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>{l}</button>
              ))}
            </div>
          </div>
          {form.type === 'limited' && (
            <div><label className="text-white/50 text-sm block mb-1.5">Visitas por mês</label><input type="number" value={form.visits_per_month} onChange={e => setForm(f => ({ ...f, visits_per_month: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-white/50 text-sm block mb-1.5">Valor/mês *</label><input type="number" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} placeholder="R$" className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div><label className="text-white/50 text-sm block mb-1.5">Início</label><input type="date" value={form.active_from} onChange={e => setForm(f => ({ ...f, active_from: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Válido até (opcional)</label><input type="date" value={form.active_until} onChange={e => setForm(f => ({ ...f, active_until: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
          <button onClick={handleCreate} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Criando...' : 'Criar assinatura'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Locked Module ─────────────────────────────────────────────
function LockedModule({ module, plan }: { module: string; plan: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-4"><span className="text-3xl">🔒</span></div>
      <h2 className="text-white font-bold text-xl mb-2">{module}</h2>
      <p className="text-white/40 text-sm mb-6 max-w-xs">Disponível a partir do plano <strong className="text-white">{plan}</strong>.</p>
      <button className="bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold px-6 py-3 rounded-xl transition-all active:scale-95">Ver planos</button>
    </div>
  )
}

// ── Main Tabs ─────────────────────────────────────────────────
type MainTab = 'clientes' | 'pacotes' | 'assinaturas'
type ClientTab = 'all' | 'inactive' | 'birthdays' | 'top'

export default function ClientesPage() {
  const { hasModule } = usePermissions()
  const [mainTab, setMainTab] = useState<MainTab>('clientes')

  // Clientes
  const [clientTab, setClientTab] = useState<ClientTab>('all')
  const [clients, setClients] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [inactiveDays, setInactiveDays] = useState(30)

  // Pacotes
  const [packages, setPackages] = useState<any[]>([])
  const [showPackageSheet, setShowPackageSheet] = useState(false)

  // Assinaturas
  const [subscriptions, setSubscriptions] = useState<any[]>([])
  const [showSubSheet, setShowSubSheet] = useState(false)

  const loadClients = useCallback(async () => {
    setLoading(true)
    try {
      if (clientTab === 'all') {
        const { data } = await crmApi.clients({ q: search })
        setClients(data.clients || [])
      } else if (clientTab === 'inactive') {
        const { data } = await crmApi.inactive({ days: inactiveDays })
        setClients(data.clients || [])
      } else if (clientTab === 'birthdays') {
        const { data } = await crmApi.birthdays()
        setClients(data.clients || [])
      } else if (clientTab === 'top') {
        const { data } = await crmApi.top({ order: 'spent', limit: 20 })
        setClients(data.clients || [])
      }
    } catch { toast.error('Erro ao carregar.') }
    finally { setLoading(false) }
  }, [clientTab, search, inactiveDays])

  async function loadPackages() {
    try {
      const { data } = await import('@/lib/api').then(({ default: api }) => api.get('/packages/'))
      setPackages(data || [])
    } catch {}
  }

  async function loadSubscriptions() {
    try {
      const { data } = await crmApi.subscriptions({ status: 'all' })
      setSubscriptions(Array.isArray(data) ? data : [])
    } catch {}
  }

  useEffect(() => { crmApi.summary().then(({ data }) => setSummary(data)).catch(() => {}) }, [])
  useEffect(() => { const t = setTimeout(loadClients, search ? 400 : 0); return () => clearTimeout(t) }, [loadClients, search])
  useEffect(() => { if (mainTab === 'pacotes') loadPackages() }, [mainTab])
  useEffect(() => { if (mainTab === 'assinaturas') loadSubscriptions() }, [mainTab])

  if (!hasModule('crm')) return <LockedModule module="CRM de Clientes" plan="Pro" />

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-3xl">
      {/* Header com tab principal */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-white font-bold text-xl">Clientes</h1>
          <p className="text-white/30 text-sm mt-0.5">{summary ? `${summary.total_clients} cadastrados` : '—'}</p>
        </div>
        {mainTab === 'pacotes' && (
          <button onClick={() => setShowPackageSheet(true)} className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95">
            <Plus size={16} /> Novo pacote
          </button>
        )}
        {mainTab === 'assinaturas' && (
          <button onClick={() => setShowSubSheet(true)} className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95">
            <Plus size={16} /> Nova assinatura
          </button>
        )}
      </div>

      {/* Main tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-5" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        {[
          { key: 'clientes',     label: '👥 Clientes'     },
          { key: 'pacotes',      label: '📦 Pacotes'      },
          { key: 'assinaturas',  label: '🔄 Assinaturas'  },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => setMainTab(key as MainTab)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${mainTab === key ? 'bg-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Aba Clientes ── */}
      {mainTab === 'clientes' && (
        <>
          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              <InsightCard label="Total"           value={summary.total_clients}     icon={Users}     color="bg-[#6366f1]"    />
              <InsightCard label="Ativos (30d)"    value={summary.active_last_30d}   icon={TrendingUp} color="bg-emerald-600" />
              <InsightCard label="Inativos (+30d)" value={summary.inactive_over_30d} icon={Clock}      color="bg-amber-600" sub="sem visita" />
              <InsightCard label="Novos este mês"  value={summary.new_this_month}    icon={UserPlus}   color="bg-purple-600"  />
            </div>
          )}
          <div className="flex gap-2 overflow-x-auto pb-1 mb-4" style={{ WebkitOverflowScrolling: 'touch' as any }}>
            {[{ key: 'all', label: 'Todos' }, { key: 'inactive', label: `Inativos +${inactiveDays}d` }, { key: 'birthdays', label: '🎂 Aniversários' }, { key: 'top', label: '⭐ Top' }].map(({ key, label }) => (
              <button key={key} onClick={() => setClientTab(key as ClientTab)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${clientTab === key ? 'bg-white/15 text-white border border-white/20' : 'bg-white/[0.04] text-white/40 border border-white/[0.06]'}`}>
                {label}
              </button>
            ))}
          </div>
          {clientTab === 'inactive' && (
            <div className="flex gap-2 mb-4">
              {[15, 30, 60, 90].map(d => (
                <button key={d} onClick={() => setInactiveDays(d)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all min-h-[36px] ${inactiveDays === d ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-white/[0.04] text-white/30 border border-white/[0.06]'}`}>{d}d</button>
              ))}
            </div>
          )}
          {clientTab === 'all' && (
            <div className="relative mb-4">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nome ou telefone..." className="w-full h-11 pl-10 pr-4 rounded-xl bg-white/[0.05] border border-white/[0.08] text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/40 transition-colors" style={{ fontSize: '16px' }} />
              {search && <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white"><X size={14} /></button>}
            </div>
          )}
          {loading ? (
            <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-16" />)}</div>
          ) : clients.length === 0 ? (
            <div className="text-center py-12"><Users size={36} className="text-white/10 mx-auto mb-3" /><p className="text-white/30 text-sm">Nenhum cliente encontrado</p></div>
          ) : (
            <div className="space-y-2 pb-24 md:pb-6">
              {clients.map(c => <ClientCard key={c.client_id} client={c} onClick={() => setSelectedId(c.client_id)} />)}
            </div>
          )}
        </>
      )}

      {/* ── Aba Pacotes ── */}
      {mainTab === 'pacotes' && (
        <div className="space-y-3 pb-24 md:pb-6">
          {packages.length === 0 ? (
            <div className="text-center py-12">
              <Package size={36} className="text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm mb-4">Nenhum pacote criado ainda</p>
              <button onClick={() => setShowPackageSheet(true)} className="flex items-center gap-2 bg-[#6366f1] text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all active:scale-95 mx-auto">
                <Plus size={16} /> Criar primeiro pacote
              </button>
            </div>
          ) : packages.map((p: any) => (
            <div key={p.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-white font-semibold">{p.name}</div>
                  <div className="text-white/40 text-sm mt-0.5">{p.service_name || p.service?.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-[#6366f1] font-bold">{p.price ? formatCurrency(Number(p.price)) : '—'}</div>
                  <div className="text-white/30 text-xs">{p.sessions} sessões</div>
                </div>
              </div>
              {p.description && <p className="text-white/30 text-xs">{p.description}</p>}
            </div>
          ))}
        </div>
      )}

      {/* ── Aba Assinaturas ── */}
      {mainTab === 'assinaturas' && (
        <div className="space-y-3 pb-24 md:pb-6">
          {subscriptions.length === 0 ? (
            <div className="text-center py-12">
              <RefreshCw size={36} className="text-white/10 mx-auto mb-3" />
              <p className="text-white/30 text-sm mb-4">Nenhuma assinatura ativa</p>
              <button onClick={() => setShowSubSheet(true)} className="flex items-center gap-2 bg-[#6366f1] text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all active:scale-95 mx-auto">
                <Plus size={16} /> Criar primeira assinatura
              </button>
            </div>
          ) : subscriptions.map((s: any) => (
            <div key={s.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-white font-semibold">{s.name}</div>
                  <div className="text-white/40 text-sm mt-0.5">{s.client?.name} · {s.client?.phone}</div>
                </div>
                <div className="text-right">
                  <div className="text-[#6366f1] font-bold">{formatCurrency(Number(s.price))}<span className="text-white/30 text-xs font-normal">/mês</span></div>
                  <div className={`text-xs mt-0.5 px-2 py-0.5 rounded-full inline-block ${s.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{s.status === 'active' ? 'Ativa' : s.status}</div>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-white/30">
                <span>{s.type === 'unlimited' ? 'Ilimitado' : `${s.visits_used || 0}/${s.visits_per_month} visitas usadas`}</span>
                {s.active_until && <span>até {formatDate(s.active_until)}</span>}
              </div>
              {s.type === 'limited' && s.visits_per_month && (
                <div className="mt-2 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className="h-full bg-[#6366f1] rounded-full transition-all" style={{ width: `${Math.min(100, ((s.visits_used || 0) / s.visits_per_month) * 100)}%` }} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedId && <ClientSheet clientId={selectedId} onClose={() => setSelectedId(null)} />}
      {showPackageSheet && <PackageSheet onClose={() => setShowPackageSheet(false)} onCreated={() => { setShowPackageSheet(false); loadPackages() }} />}
      {showSubSheet && <SubscriptionSheet onClose={() => setShowSubSheet(false)} onCreated={() => { setShowSubSheet(false); loadSubscriptions() }} />}
    </div>
  )
}