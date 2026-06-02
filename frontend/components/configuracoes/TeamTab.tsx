'use client'
// Aba "Equipe" para app/painel/configuracoes/page.tsx
// Adicionar como nova aba nas configurações

import { useEffect, useState } from 'react'
import {
  Plus, X, Eye, EyeOff, Shield, ShieldCheck,
  ShieldOff, Settings, Trash2, Users, Link,
  ChevronDown, ChevronUp
} from 'lucide-react'
import { toast } from 'sonner'
import { professionalsApi } from '@/lib/api'

const inputClass = "w-full h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

const ROLE_CONFIG = {
  owner: {
    label: 'Dono',
    color: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    description: 'Acesso total ao sistema',
    permissions: ['Agenda completa', 'Financeiro', 'CRM', 'Configurações', 'Equipe'],
  },
  manager: {
    label: 'Administrativo',
    color: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
    description: 'Acesso administrativo sem configurações',
    permissions: ['Agenda completa', 'Financeiro', 'CRM', 'Relatórios', 'Produtos'],
  },
  receptionist: {
    label: 'Agenda completa',
    color: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
    description: 'Gerencia agenda de todos sem acesso financeiro',
    permissions: ['Agenda completa', 'CRM básico'],
  },
  professional: {
    label: 'Profissional',
    color: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
    description: 'Acessa apenas a própria agenda',
    permissions: ['Própria agenda', 'Comanda própria'],
  },
}

// ── New Member Sheet ──────────────────────────────────────────
function NewMemberSheet({
  onClose, onCreated, professionals
}: {
  onClose: () => void; onCreated: () => void; professionals: any[]
}) {
  const [form, setForm] = useState({
    name:            '',
    email:           '',
    password:        '',
    role:            'professional',
    title:           '',
    professional_id: '',
  })
  const [showPass,  setShowPass]  = useState(false)
  const [showPerms, setShowPerms] = useState(false)
  const [loading,   setLoading]   = useState(false)

  const roleInfo = ROLE_CONFIG[form.role as keyof typeof ROLE_CONFIG]
  const availableProfs = professionals.filter(p => !p.user)

  async function handleCreate() {
    if (!form.name || !form.email || !form.password) {
      toast.error('Nome, e-mail e senha são obrigatórios.'); return
    }
    setLoading(true)
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.post('/team/', {
          name:            form.name,
          email:           form.email,
          password:        form.password,
          role:            form.role,
          title:           form.title,
          professional_id: form.professional_id || undefined,
        })
      )
      toast.success(`Acesso criado para ${form.name}!`)
      onCreated()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Erro ao criar acesso.')
    } finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[440px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto"
        style={{ maxHeight: '88vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="md:hidden flex justify-center pt-3 pb-1 sticky top-0 bg-[#0D0D14]">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>

        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06] sticky top-4 bg-[#0D0D14] z-10">
          <h3 className="text-white font-bold text-base">Adicionar membro</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {/* Dados pessoais */}
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-white/50 text-sm block mb-1.5">Nome completo *</label>
              <input
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Carlos Silva"
                className={inputClass}
                style={{ fontSize: '16px' }}
              />
            </div>
            <div className="col-span-2">
              <label className="text-white/50 text-sm block mb-1.5">E-mail *</label>
              <input
                type="email"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                placeholder="carlos@barbearia.com"
                className={inputClass}
                style={{ fontSize: '16px' }}
              />
            </div>
          </div>

          {/* Cargo e permissão */}
          <div>
            <label className="text-white/50 text-sm block mb-1.5">
              Cargo <span className="text-white/20">(livre — ex: Recepcionista, Gerente)</span>
            </label>
            <input
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Ex: Recepcionista, Barbeiro, Gerente..."
              className={inputClass}
              style={{ fontSize: '16px' }}
            />
          </div>

          {/* Permissões */}
          <div>
            <label className="text-white/50 text-sm block mb-2">Nível de acesso *</label>
            <div className="space-y-2">
              {Object.entries(ROLE_CONFIG).filter(([k]) => k !== 'owner').map(([key, cfg]) => (
                <button
                  key={key}
                  onClick={() => setForm(f => ({ ...f, role: key, professional_id: key !== 'professional' ? '' : f.professional_id }))}
                  className={`w-full p-4 rounded-xl border text-left transition-all active:scale-[0.98] ${
                    form.role === key
                      ? 'bg-[#6366f1]/15 border-[#6366f1]/40'
                      : 'bg-white/[0.03] border-white/[0.07] hover:border-white/15'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${cfg.color}`}>
                        {cfg.label}
                      </span>
                      {form.role === key && (
                        <ShieldCheck size={14} className="text-[#6366f1]" />
                      )}
                    </div>
                  </div>
                  <p className="text-white/40 text-xs">{cfg.description}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {cfg.permissions.map(p => (
                      <span key={p} className="text-xs bg-white/[0.06] text-white/30 px-2 py-0.5 rounded-full">{p}</span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Vincular profissional — só se role = professional */}
          {form.role === 'professional' && availableProfs.length > 0 && (
            <div>
              <label className="text-white/50 text-sm block mb-1.5">
                Vincular à agenda <span className="text-white/20">(opcional)</span>
              </label>
              <select
                value={form.professional_id}
                onChange={e => setForm(f => ({ ...f, professional_id: e.target.value }))}
                className={inputClass}
                style={{ fontSize: '16px' }}
              >
                <option value="">Não vincular agora</option>
                {availableProfs.map((p: any) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <p className="text-white/20 text-xs mt-1.5">
                Vinculando, este usuário verá os agendamentos de {availableProfs.find(p => p.id === form.professional_id)?.name || 'esse profissional'} na tela do profissional
              </p>
            </div>
          )}

          {/* Senha */}
          <div>
            <label className="text-white/50 text-sm block mb-1.5">Senha temporária *</label>
            <div className="relative">
              <input
                type={showPass ? 'text' : 'password'}
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                placeholder="Mínimo 6 caracteres"
                className={`${inputClass} pr-11`}
                style={{ fontSize: '16px' }}
              />
              <button
                onClick={() => setShowPass(s => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white transition-colors"
              >
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <p className="text-white/20 text-xs mt-1.5">
              Compartilhe com {form.name || 'o membro'} — ele pode trocar depois
            </p>
          </div>

          <button
            onClick={handleCreate}
            disabled={loading}
            className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {loading ? 'Criando acesso...' : 'Criar acesso'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Edit Member Sheet ─────────────────────────────────────────
function EditMemberSheet({
  member, onClose, onSaved, professionals
}: {
  member: any; onClose: () => void; onSaved: () => void; professionals: any[]
}) {
  const [form, setForm] = useState({
    title:        member.title || '',
    role:         member.role  || 'professional',
    new_password: '',
    is_active:    member.is_active,
  })
  const [showPass, setShowPass] = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [linkProf, setLinkProf] = useState('')

  const roleInfo     = ROLE_CONFIG[member.role as keyof typeof ROLE_CONFIG]
  const availProfs   = professionals.filter(p => !p.user || p.user?.id === member.user_id)

  async function handleSave() {
    setLoading(true)
    try {
      const payload: any = { title: form.title, role: form.role, is_active: form.is_active }
      if (form.new_password) payload.new_password = form.new_password
      await import('@/lib/api').then(({ default: api }) =>
        api.patch(`/team/${member.id}/`, payload)
      )
      toast.success('Membro atualizado!')
      onSaved()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Erro ao atualizar.')
    } finally { setLoading(false) }
  }

  async function handleLink() {
    if (!linkProf) return
    setLoading(true)
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.post(`/team/${member.id}/link-professional/`, { professional_id: linkProf })
      )
      toast.success('Vinculado com sucesso!')
      onSaved()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Erro ao vincular.')
    } finally { setLoading(false) }
  }

  async function handleRemove() {
    if (!confirm(`Remover acesso de ${member.name}?`)) return
    setLoading(true)
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.delete(`/team/${member.id}/`)
      )
      toast.success('Acesso removido.')
      onSaved()
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'Erro ao remover.')
    } finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto"
        style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>

        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
              <span className="text-white font-bold">{member.name[0]}</span>
            </div>
            <div>
              <div className="text-white font-bold">{member.name}</div>
              <div className="text-white/40 text-xs">{member.email}</div>
            </div>
          </div>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="text-white/50 text-sm block mb-1.5">Cargo (livre)</label>
            <input
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Ex: Recepcionista, Gerente Sênior..."
              className={inputClass}
              style={{ fontSize: '16px' }}
            />
          </div>

          {member.role !== 'owner' && (
            <div>
              <label className="text-white/50 text-sm block mb-2">Nível de acesso</label>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(ROLE_CONFIG).filter(([k]) => k !== 'owner').map(([key, cfg]) => (
                  <button
                    key={key}
                    onClick={() => setForm(f => ({ ...f, role: key }))}
                    className={`py-2.5 px-2 rounded-xl border text-center transition-all active:scale-95 ${
                      form.role === key ? 'bg-[#6366f1]/15 border-[#6366f1]/40' : 'bg-white/[0.04] border-white/[0.07]'
                    }`}
                  >
                    <div className="text-white text-xs font-medium">{cfg.label}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Vincular profissional */}
          {form.role === 'professional' && !member.professional && availProfs.length > 0 && (
            <div>
              <label className="text-white/50 text-sm block mb-1.5">Vincular à agenda</label>
              <div className="flex gap-2">
                <select
                  value={linkProf}
                  onChange={e => setLinkProf(e.target.value)}
                  className={`flex-1 ${inputClass}`}
                  style={{ fontSize: '16px' }}
                >
                  <option value="">Selecionar profissional</option>
                  {availProfs.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
                <button
                  onClick={handleLink}
                  disabled={!linkProf || loading}
                  className="w-11 h-11 flex items-center justify-center bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-xl transition-all active:scale-95 disabled:opacity-50"
                >
                  <Link size={16} />
                </button>
              </div>
            </div>
          )}

          {member.professional && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 flex items-center gap-2">
              <Link size={14} className="text-emerald-400 flex-shrink-0" />
              <span className="text-emerald-300 text-sm">Vinculado: <strong>{member.professional.name}</strong></span>
            </div>
          )}

          {/* Senha */}
          <div>
            <label className="text-white/50 text-sm block mb-1.5">Nova senha <span className="text-white/20">(deixe em branco para manter)</span></label>
            <div className="relative">
              <input
                type={showPass ? 'text' : 'password'}
                value={form.new_password}
                onChange={e => setForm(f => ({ ...f, new_password: e.target.value }))}
                placeholder="Nova senha..."
                className={`${inputClass} pr-11`}
                style={{ fontSize: '16px' }}
              />
              <button onClick={() => setShowPass(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white transition-colors">
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center justify-between bg-white/[0.03] border border-white/[0.06] rounded-xl px-4 py-3">
            <div>
              <div className="text-white text-sm font-medium">Acesso ativo</div>
              <div className="text-white/30 text-xs mt-0.5">{form.is_active ? 'Pode fazer login' : 'Bloqueado'}</div>
            </div>
            <button
              onClick={() => setForm(f => ({ ...f, is_active: !f.is_active }))}
              className={`w-12 h-6 rounded-full transition-all ${form.is_active ? 'bg-[#6366f1]' : 'bg-white/20'}`}
            >
              <div className={`w-5 h-5 rounded-full bg-white shadow mx-0.5 transition-all ${form.is_active ? 'translate-x-6' : 'translate-x-0'}`} />
            </button>
          </div>

          <button
            onClick={handleSave}
            disabled={loading}
            className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {loading ? 'Salvando...' : 'Salvar alterações'}
          </button>

          {member.role !== 'owner' && (
            <button
              onClick={handleRemove}
              disabled={loading}
              className="w-full h-12 bg-red-500/10 hover:bg-red-500/15 border border-red-500/20 text-red-400 font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <ShieldOff size={18} /> Remover acesso
            </button>
          )}
        </div>
      </div>
    </>
  )
}

// ── Team Tab ──────────────────────────────────────────────────
export function TeamTab() {
  const [members,       setMembers]       = useState<any[]>([])
  const [professionals, setProfessionals] = useState<any[]>([])
  const [loading,       setLoading]       = useState(true)
  const [showNew,       setShowNew]       = useState(false)
  const [editMember,    setEditMember]    = useState<any>(null)

  async function loadData() {
    setLoading(true)
    try {
      const [membersRes, profsRes] = await Promise.all([
        import('@/lib/api').then(({ default: api }) => api.get('/team/')),
        professionalsApi.list(),
      ])
      setMembers(membersRes.data || [])
      setProfessionals(profsRes.data || [])
    } catch { toast.error('Erro ao carregar equipe.') }
    finally { setLoading(false) }
  }

  useEffect(() => { loadData() }, [])

  return (
    <div className="space-y-3 pb-24 md:pb-6">
      {/* Adicionar */}
      <button
        onClick={() => setShowNew(true)}
        className="w-full flex items-center gap-3 p-4 rounded-2xl border border-dashed border-white/20 text-white/40 hover:text-white hover:border-white/30 transition-all active:scale-[0.98] min-h-[60px]"
      >
        <Plus size={18} />
        <span className="text-sm font-medium">Adicionar membro da equipe</span>
      </button>

      {/* Lista */}
      {loading ? (
        <div className="space-y-2">
          {[1,2,3].map(i => <div key={i} className="h-20 bg-white/[0.04] rounded-2xl animate-pulse" />)}
        </div>
      ) : members.length === 0 ? (
        <div className="text-center py-8">
          <Users size={32} className="text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm">Nenhum membro além de você</p>
        </div>
      ) : (
        members.map(member => {
          const roleInfo = ROLE_CONFIG[member.role as keyof typeof ROLE_CONFIG] || ROLE_CONFIG.professional
          return (
            <div key={member.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm">{member.name[0]}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium text-sm truncate">{member.name}</span>
                  {!member.is_active && (
                    <span className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full flex-shrink-0">Bloqueado</span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  {member.title && (
                    <span className="text-white/40 text-xs">{member.title}</span>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${roleInfo.color}`}>
                    {roleInfo.label}
                  </span>
                  {member.professional && (
                    <span className="text-white/20 text-xs flex items-center gap-1">
                      <Link size={10} /> {member.professional.name}
                    </span>
                  )}
                </div>
              </div>
              {member.role !== 'owner' && (
                <button
                  onClick={() => setEditMember(member)}
                  className="w-9 h-9 flex items-center justify-center bg-white/[0.06] hover:bg-white/10 border border-white/[0.08] rounded-xl text-white/40 hover:text-white transition-all active:scale-95 flex-shrink-0"
                >
                  <Settings size={15} />
                </button>
              )}
            </div>
          )
        })
      )}

      {showNew && (
        <NewMemberSheet
          onClose={() => setShowNew(false)}
          onCreated={() => { setShowNew(false); loadData() }}
          professionals={professionals}
        />
      )}
      {editMember && (
        <EditMemberSheet
          member={editMember}
          onClose={() => setEditMember(null)}
          onSaved={() => { setEditMember(null); loadData() }}
          professionals={professionals}
        />
      )}
    </div>
  )
}