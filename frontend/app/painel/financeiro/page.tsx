'use client'
// app/painel/financeiro/page.tsx
// Módulo financeiro completo

import { useEffect, useState, useCallback } from 'react'
import {
  ChevronLeft, ChevronRight, DollarSign, TrendingUp,
  TrendingDown, BarChart3, Calendar, Award, Package,
  Plus, Trash2, Check, X, AlertTriangle, Clock,
  CreditCard, Wallet
} from 'lucide-react'
import { financialApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { ComissoesTab } from '@/components/financeiro/ComissoesTab'
import { toast } from 'sonner'


// ── Helpers ───────────────────────────────────────────────────
function formatCurrency(v: number) { return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }
function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }
const MONTHS = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const MONTHS_FULL = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

const inputClass = "w-full h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

const EXPENSE_CATEGORIES = [
  { value: 'rent',        label: 'Aluguel',           emoji: '🏠' },
  { value: 'energy',      label: 'Energia elétrica',  emoji: '⚡' },
  { value: 'water',       label: 'Água',              emoji: '💧' },
  { value: 'internet',    label: 'Internet',          emoji: '📶' },
  { value: 'product',     label: 'Compra produto',    emoji: '📦' },
  { value: 'salary',      label: 'Salário fixo',      emoji: '👤' },
  { value: 'commission',  label: 'Comissão',          emoji: '💰' },
  { value: 'maintenance', label: 'Manutenção',        emoji: '🔧' },
  { value: 'marketing',   label: 'Marketing',         emoji: '📣' },
  { value: 'other',       label: 'Outros',            emoji: '📋' },
]

// ── Month nav ─────────────────────────────────────────────────
function useMonthNav(initialYear: number, initialMonth: number) {
  const [year,  setYear]  = useState(initialYear)
  const [month, setMonth] = useState(initialMonth)
  function addMonth(n: number) {
    let m = month + n, y = year
    if (m > 12) { m = 1; y++ }
    if (m < 1)  { m = 12; y-- }
    setMonth(m); setYear(y)
  }
  return { year, month, addMonth }
}

// ── Stat Card ─────────────────────────────────────────────────
function StatCard({ label, value, sub, icon: Icon, color, loading, variant = 'default' }: any) {
  if (loading) return <Skeleton className="h-24" />
  const bgColor = variant === 'profit' ? 'bg-emerald-500/10 border-emerald-500/20'
                : variant === 'loss'   ? 'bg-red-500/10 border-red-500/20'
                : 'bg-white/[0.03] border-white/[0.06]'
  return (
    <div className={`border rounded-2xl p-4 flex items-start gap-3 ${bgColor}`}>
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div className="min-w-0">
        <div className="text-white/40 text-xs">{label}</div>
        <div className={`font-bold text-lg leading-tight ${variant === 'profit' ? 'text-emerald-300' : variant === 'loss' ? 'text-red-300' : 'text-white'}`}>{value}</div>
        {sub && <div className="text-white/30 text-xs mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

// ── Expense Sheet ─────────────────────────────────────────────
function ExpenseSheet({ onClose, onSaved, defaultDate }: { onClose: () => void; onSaved: () => void; defaultDate: string }) {
  const [form, setForm] = useState({ description: '', amount: '', category: 'other', date: defaultDate, notes: '' })
  const [loading, setLoading] = useState(false)

  async function handleSave() {
    if (!form.description || !form.amount) { toast.error('Descrição e valor são obrigatórios.'); return }
    setLoading(true)
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.post('/financial/expenses/', { ...form, amount: Number(form.amount) })
      )
      toast.success('Despesa lançada!')
      onSaved()
    } catch { toast.error('Erro ao lançar despesa.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto" style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">Lançar despesa</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="text-white/50 text-sm block mb-2">Categoria</label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {EXPENSE_CATEGORIES.map(cat => (
                <button key={cat.value} onClick={() => setForm(f => ({ ...f, category: cat.value }))}
                  className={`flex items-center gap-2 p-3 rounded-xl border text-left transition-all active:scale-[0.98] text-sm ${form.category === cat.value ? 'bg-[#6366f1]/15 border-[#6366f1]/40 text-white' : 'bg-white/[0.03] border-white/[0.07] text-white/50'}`}>
                  <span>{cat.emoji}</span> {cat.label}
                </button>
              ))}
            </div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Descrição *</label><input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Ex: Conta de energia maio" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-white/50 text-sm block mb-1.5">Valor *</label><input type="number" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="R$" className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div><label className="text-white/50 text-sm block mb-1.5">Data</label><input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Observações</label><input value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Opcional" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <button onClick={handleSave} disabled={loading} className="w-full h-12 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Lançando...' : 'Lançar despesa'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Payable Sheet ─────────────────────────────────────────────
function PayableSheet({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ description: '', amount: '', category: 'other', due_date: '', recurrence: 'once', notes: '' })
  const [loading, setLoading] = useState(false)

  async function handleSave() {
    if (!form.description || !form.amount || !form.due_date) { toast.error('Preencha todos os campos obrigatórios.'); return }
    setLoading(true)
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.post('/financial/payables/', { ...form, amount: Number(form.amount) })
      )
      toast.success(form.recurrence === 'monthly' ? 'Conta criada (12 meses)!' : 'Conta a pagar criada!')
      onSaved()
    } catch { toast.error('Erro ao criar.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto" style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">Nova conta a pagar</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="text-white/50 text-sm block mb-2">Categoria</label>
            <div className="grid grid-cols-2 gap-2">
              {EXPENSE_CATEGORIES.slice(0, 6).map(cat => (
                <button key={cat.value} onClick={() => setForm(f => ({ ...f, category: cat.value }))}
                  className={`flex items-center gap-2 p-2.5 rounded-xl border text-left text-xs transition-all ${form.category === cat.value ? 'bg-[#6366f1]/15 border-[#6366f1]/40 text-white' : 'bg-white/[0.03] border-white/[0.07] text-white/50'}`}>
                  <span>{cat.emoji}</span> {cat.label}
                </button>
              ))}
            </div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Descrição *</label><input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Ex: Aluguel da barbearia" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-white/50 text-sm block mb-1.5">Valor *</label><input type="number" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="R$" className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div><label className="text-white/50 text-sm block mb-1.5">Vencimento *</label><input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <div>
            <label className="text-white/50 text-sm block mb-2">Recorrência</label>
            <div className="grid grid-cols-3 gap-2">
              {[{ v: 'once', l: 'Única' }, { v: 'monthly', l: 'Mensal' }, { v: 'weekly', l: 'Semanal' }].map(({ v, l }) => (
                <button key={v} onClick={() => setForm(f => ({ ...f, recurrence: v }))}
                  className={`py-2.5 rounded-xl text-sm font-medium border transition-all ${form.recurrence === v ? 'bg-[#6366f1] text-white border-[#6366f1]' : 'bg-white/[0.04] text-white/40 border-white/[0.06]'}`}>{l}</button>
              ))}
            </div>
            {form.recurrence === 'monthly' && <p className="text-white/30 text-xs mt-1.5">Serão criadas 12 parcelas automaticamente</p>}
          </div>
          <button onClick={handleSave} disabled={loading} className="w-full h-12 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Criando...' : 'Criar conta a pagar'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────
type Tab = 'caixa' | 'overview' | 'comissoes' | 'despesas' | 'apagar'

export default function FinanceiroPage() {
  const { hasModule } = usePermissions()
  const [tab, setTab] = useState<Tab>('caixa')

  // Datas
  const today = new Date()
  const [cashboxDate, setCashboxDate] = useState(today.toISOString().split('T')[0])
  const { year, month, addMonth }     = useMonthNav(today.getFullYear(), today.getMonth() + 1)

  // Dados
  const [loading,   setLoading]   = useState(true)
  const [cashbox,   setCashbox]   = useState<any>(null)
  const [overview,  setOverview]  = useState<any>(null)
  const [commissions, setCommissions] = useState<any>(null)
  const [expenses,  setExpenses]  = useState<any>(null)
  const [payables,  setPayables]  = useState<any>(null)

  // Sheets
  const [showExpense,  setShowExpense]  = useState(false)
  const [showPayable,  setShowPayable]  = useState(false)
  const [payingId,     setPayingId]     = useState<string | null>(null)

  function addDate(n: number) {
    const d = new Date(cashboxDate + 'T00:00'); d.setDate(d.getDate() + n)
    setCashboxDate(d.toISOString().split('T')[0])
  }

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      if (tab === 'caixa') {
        const { data } = await financialApi.cashbox({ date: cashboxDate })
        setCashbox(data)
      } else if (tab === 'overview') {
        const { data } = await import('@/lib/api').then(({ default: api }) =>
          api.get('/financial/overview/', { params: { year, month } })
        )
        setOverview(data)
      } else if (tab === 'comissoes') {
        const { data } = await financialApi.commissions({ year, month })
        setCommissions(data)
      } else if (tab === 'despesas') {
        const { data } = await import('@/lib/api').then(({ default: api }) =>
          api.get('/financial/expenses/', { params: { year, month } })
        )
        setExpenses(data)
      } else if (tab === 'apagar') {
        const { data } = await import('@/lib/api').then(({ default: api }) =>
          api.get('/financial/payables/')
        )
        setPayables(data)
      }
    } catch { toast.error('Erro ao carregar.') }
    finally { setLoading(false) }
  }, [tab, cashboxDate, year, month])

  useEffect(() => { loadData() }, [loadData])

  async function handleDeleteExpense(id: string) {
    if (!confirm('Remover despesa?')) return
    try {
      await import('@/lib/api').then(({ default: api }) => api.delete(`/financial/expenses/${id}/`))
      toast.success('Despesa removida.')
      loadData()
    } catch { toast.error('Erro ao remover.') }
  }

  async function handlePayPayable(id: string) {
    try {
      await import('@/lib/api').then(({ default: api }) =>
        api.patch(`/financial/payables/${id}/`, { action: 'pay' })
      )
      toast.success('Marcado como pago! Lançado nas despesas.')
      setPayingId(null)
      loadData()
    } catch { toast.error('Erro.') }
  }

  async function handleDeletePayable(id: string) {
    if (!confirm('Remover conta?')) return
    try {
      await import('@/lib/api').then(({ default: api }) => api.delete(`/financial/payables/${id}/`))
      toast.success('Conta removida.')
      loadData()
    } catch { toast.error('Erro ao remover.') }
  }

  if (!hasModule('financial')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-4"><span className="text-3xl">🔒</span></div>
        <h2 className="text-white font-bold text-xl mb-2">Financeiro</h2>
        <p className="text-white/40 text-sm mb-6 max-w-xs">Disponível a partir do plano <strong className="text-white">Pro</strong>.</p>
        <button className="bg-[#6366f1] text-white font-semibold px-6 py-3 rounded-xl">Ver planos</button>
      </div>
    )
  }

  const isToday = cashboxDate === today.toISOString().split('T')[0]

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-3xl">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-white font-bold text-xl">Financeiro</h1>
          <p className="text-white/30 text-sm mt-0.5">Gestão completa do estabelecimento</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowExpense(true)} className="flex items-center gap-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-600/30 text-red-300 text-xs font-semibold px-3 py-2 rounded-xl transition-all active:scale-95">
            <TrendingDown size={14} /> Despesa
          </button>
          <button onClick={() => setShowPayable(true)} className="flex items-center gap-1.5 bg-amber-600/20 hover:bg-amber-600/30 border border-amber-600/30 text-amber-300 text-xs font-semibold px-3 py-2 rounded-xl transition-all active:scale-95">
            <Clock size={14} /> A pagar
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-5" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        {[
          { key: 'caixa',    label: '💰 Caixa do dia'      },
          { key: 'overview', label: '📊 Visão geral'       },
          { key: 'comissoes',label: '👤 Comissões'         },
          { key: 'despesas', label: '📉 Despesas'          },
          { key: 'apagar',   label: '⏰ A pagar'           },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => setTab(key as Tab)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${tab === key ? 'bg-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Caixa do Dia ── */}
      {tab === 'caixa' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button onClick={() => addDate(-1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronLeft size={18} /></button>
            <div className="flex-1 text-center">
              <div className={`font-bold ${isToday ? 'text-[#6366f1]' : 'text-white'}`}>{isToday ? 'Hoje' : new Date(cashboxDate + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' })}</div>
              <div className="text-white/30 text-xs capitalize">{new Date(cashboxDate + 'T00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}</div>
            </div>
            <button onClick={() => addDate(1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronRight size={18} /></button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Receita total" value={loading ? '—' : formatCurrency(cashbox?.total_revenue || 0)} icon={DollarSign} color="bg-emerald-600" loading={loading} />
            <StatCard label="Ticket médio" value={loading ? '—' : formatCurrency(cashbox?.avg_ticket || 0)} icon={TrendingUp} color="bg-[#6366f1]" loading={loading} />
            <StatCard label="Atendimentos" value={loading ? '—' : String(cashbox?.appointments?.completed || 0)} sub={`de ${cashbox?.appointments?.total || 0} previstos`} icon={Calendar} color="bg-purple-600" loading={loading} />
            <StatCard label="Comissões" value={loading ? '—' : formatCurrency(cashbox?.total_commission || 0)} icon={Award} color="bg-amber-600" loading={loading} />
          </div>

          {!loading && cashbox && Object.keys(cashbox.by_payment || {}).length > 0 && (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.06]"><h3 className="text-white font-semibold text-sm">Por pagamento</h3></div>
              <div className="px-5 py-4 space-y-3">
                {Object.entries(cashbox.by_payment).map(([method, value]) => {
                  const labels: Record<string, string> = { pix: '💸 Pix', cash: '💵 Dinheiro', credit: '💳 Crédito', debit: '💳 Débito', other: '🔄 Outro' }
                  const pct = cashbox.total_revenue > 0 ? Math.round((value as number) / cashbox.total_revenue * 100) : 0
                  return (
                    <div key={method} className="flex items-center gap-3">
                      <span className="text-white/50 text-sm flex-1">{labels[method] || method}</span>
                      <div className="w-20 h-1.5 bg-white/[0.06] rounded-full overflow-hidden"><div className="h-full bg-emerald-500 rounded-full" style={{ width: `${pct}%` }} /></div>
                      <span className="text-white/30 text-xs w-8 text-right">{pct}%</span>
                      <span className="text-white font-medium text-sm w-20 text-right">{formatCurrency(value as number)}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {!loading && cashbox?.by_professional?.length > 0 && (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.06]"><h3 className="text-white font-semibold text-sm">Por profissional</h3></div>
              <div className="px-5 py-4 space-y-3">
                {cashbox.by_professional.map((p: any) => (
                  <div key={p.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center"><span className="text-white text-xs font-bold">{p.name[0]}</span></div>
                      <div><div className="text-white/70 text-sm">{p.name}</div><div className="text-white/30 text-xs">{p.appointments} atend.</div></div>
                    </div>
                    <div className="text-right"><div className="text-white font-semibold text-sm">{formatCurrency(p.revenue)}</div><div className="text-amber-400/70 text-xs">comissão: {formatCurrency(p.commission)}</div></div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Visão Geral ── */}
      {tab === 'overview' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button onClick={() => addMonth(-1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronLeft size={18} /></button>
            <div className="flex-1 text-center"><div className="text-white font-bold">{MONTHS_FULL[month - 1]} {year}</div></div>
            <button onClick={() => addMonth(1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronRight size={18} /></button>
          </div>

          {loading ? <div className="space-y-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-24" />)}</div> : overview && (
            <>
              {/* Resumo financeiro */}
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Receita" value={formatCurrency(overview.summary.revenue)} icon={TrendingUp} color="bg-emerald-600" loading={false} />
                <StatCard label="Despesas" value={formatCurrency(overview.summary.expenses)} icon={TrendingDown} color="bg-red-600" loading={false} />
                <StatCard label="Lucro bruto" value={formatCurrency(overview.summary.gross_profit)} sub="receita - comissões" icon={DollarSign} color="bg-[#6366f1]" loading={false} variant={overview.summary.gross_profit >= 0 ? 'profit' : 'loss'} />
                <StatCard label="Lucro líquido" value={formatCurrency(overview.summary.net_profit)} sub={`margem ${overview.summary.margin_pct}%`} icon={Wallet} color="bg-purple-600" loading={false} variant={overview.summary.net_profit >= 0 ? 'profit' : 'loss'} />
              </div>

              {/* Produtos vendidos */}
              {overview.products_sold?.length > 0 && (
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between">
                    <h3 className="text-white font-semibold text-sm">Produtos vendidos</h3>
                    <div className="text-white/30 text-xs">Receita: {formatCurrency(overview.summary.products_revenue)} · Lucro: {formatCurrency(overview.summary.products_profit)}</div>
                  </div>
                  <div className="px-5 py-3 space-y-2">
                    {overview.products_sold.map((p: any) => (
                      <div key={p.name} className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
                        <div><div className="text-white/70 text-sm">{p.name}</div><div className="text-white/30 text-xs">{p.quantity}x · custo: {formatCurrency(p.cost)}</div></div>
                        <div className="text-right"><div className="text-white text-sm font-semibold">{formatCurrency(p.revenue)}</div><div className="text-emerald-400/70 text-xs">lucro: {formatCurrency(p.profit)}</div></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Despesas por categoria */}
              {overview.expenses_by_category?.length > 0 && (
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-white/[0.06]"><h3 className="text-white font-semibold text-sm">Despesas por categoria</h3></div>
                  <div className="px-5 py-3 space-y-2">
                    {overview.expenses_by_category.map((c: any) => {
                      const maxVal = overview.expenses_by_category[0].amount
                      const pct = (c.amount / maxVal) * 100
                      return (
                        <div key={c.category} className="flex items-center gap-3">
                          <span className="text-white/40 text-xs w-28 flex-shrink-0 truncate">{c.category}</span>
                          <div className="flex-1 h-2 bg-white/[0.06] rounded-full overflow-hidden"><div className="h-full bg-red-500 rounded-full transition-all" style={{ width: `${pct}%` }} /></div>
                          <span className="text-white/50 text-sm w-20 text-right flex-shrink-0">{formatCurrency(c.amount)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── Comissões ── */}
      {tab === 'comissoes' && (
        <ComissoesTab year={year} month={month} addMonth={addMonth} />
      )}
      {/* ── Despesas ── */}
      {tab === 'despesas' && (
        <div className="space-y-4 pb-24 md:pb-6">
          <div className="flex items-center gap-3">
            <button onClick={() => addMonth(-1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronLeft size={18} /></button>
            <div className="flex-1 text-center"><div className="text-white font-bold">{MONTHS_FULL[month - 1]} {year}</div></div>
            <button onClick={() => addMonth(1)} className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center text-white/50 hover:text-white active:scale-95 transition-all"><ChevronRight size={18} /></button>
          </div>

          {!loading && expenses && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl px-5 py-4 flex items-center justify-between">
              <div><div className="text-red-300 font-bold text-lg">{formatCurrency(expenses.total)}</div><div className="text-red-400/60 text-xs mt-0.5">Total de despesas no período</div></div>
              <TrendingDown size={28} className="text-red-400/40" />
            </div>
          )}

          <button onClick={() => setShowExpense(true)} className="w-full flex items-center gap-3 p-4 rounded-2xl border border-dashed border-red-500/20 text-red-400/60 hover:text-red-300 hover:border-red-500/40 transition-all active:scale-[0.98]">
            <Plus size={18} /><span className="text-sm font-medium">Lançar nova despesa</span>
          </button>

          {loading ? <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-14" />)}</div>
            : expenses?.expenses?.length === 0 ? (
              <div className="text-center py-10 text-white/30 text-sm">Nenhuma despesa neste período</div>
            ) : (
              <div className="space-y-2">
                {expenses?.expenses?.map((e: any) => {
                  const cat = EXPENSE_CATEGORIES.find(c => c.label === e.category) || EXPENSE_CATEGORIES[EXPENSE_CATEGORIES.length - 1]
                  return (
                    <div key={e.id} className="flex items-center gap-3 bg-white/[0.03] border border-white/[0.06] rounded-xl px-4 py-3">
                      <span className="text-xl flex-shrink-0">{cat.emoji}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-white/70 text-sm font-medium truncate">{e.description}</div>
                        <div className="text-white/30 text-xs">{e.category} · {new Date(e.date + 'T00:00').toLocaleDateString('pt-BR')}</div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-red-300 font-semibold text-sm">{formatCurrency(e.amount)}</span>
                        <button onClick={() => handleDeleteExpense(e.id)} className="w-7 h-7 flex items-center justify-center text-white/20 hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10"><Trash2 size={14} /></button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          }
        </div>
      )}

      {/* ── A Pagar ── */}
      {tab === 'apagar' && (
        <div className="space-y-4 pb-24 md:pb-6">
          {!loading && payables?.summary && (
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4">
                <div className="text-amber-400/60 text-xs">Pendente</div>
                <div className="text-amber-300 font-bold text-xl">{formatCurrency(payables.summary.total_pending)}</div>
                <div className="text-amber-400/40 text-xs mt-0.5">{payables.summary.count_pending} conta(s)</div>
              </div>
              <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4">
                <div className="text-red-400/60 text-xs">Em atraso</div>
                <div className="text-red-300 font-bold text-xl">{formatCurrency(payables.summary.total_overdue)}</div>
                <div className="text-red-400/40 text-xs mt-0.5">{payables.summary.count_overdue} conta(s)</div>
              </div>
            </div>
          )}

          <button onClick={() => setShowPayable(true)} className="w-full flex items-center gap-3 p-4 rounded-2xl border border-dashed border-amber-500/20 text-amber-400/60 hover:text-amber-300 hover:border-amber-500/40 transition-all active:scale-[0.98]">
            <Plus size={18} /><span className="text-sm font-medium">Adicionar conta a pagar</span>
          </button>

          {loading ? <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-20" />)}</div>
            : payables?.payables?.length === 0 ? (
              <div className="text-center py-10 text-white/30 text-sm">Nenhuma conta cadastrada</div>
            ) : (
              <div className="space-y-2">
                {payables?.payables?.map((p: any) => {
                  const isOverdue = p.status === 'overdue'
                  const isPaid    = p.status === 'paid'
                  const daysText  = p.days_until < 0 ? `${Math.abs(p.days_until)}d em atraso`
                                  : p.days_until === 0 ? 'Vence hoje'
                                  : `Vence em ${p.days_until}d`
                  const cat = EXPENSE_CATEGORIES.find(c => c.value === p.category) || EXPENSE_CATEGORIES[EXPENSE_CATEGORIES.length - 1]
                  return (
                    <div key={p.id} className={`bg-white/[0.03] border rounded-2xl p-4 transition-all ${isOverdue ? 'border-red-500/30 bg-red-500/5' : isPaid ? 'border-emerald-500/20 opacity-60' : 'border-white/[0.06]'}`}>
                      <div className="flex items-start gap-3">
                        <span className="text-xl flex-shrink-0 mt-0.5">{cat.emoji}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-white/80 font-medium text-sm truncate">{p.description}</div>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={`text-xs ${isOverdue ? 'text-red-400' : isPaid ? 'text-emerald-400' : 'text-white/30'}`}>{isPaid ? '✅ Pago' : daysText}</span>
                            {p.recurrence === 'monthly' && <span className="text-white/20 text-xs">· mensal</span>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className={`font-bold text-sm ${isOverdue ? 'text-red-300' : isPaid ? 'text-white/30 line-through' : 'text-white'}`}>{formatCurrency(p.amount)}</span>
                          {!isPaid && (
                            <button onClick={() => handlePayPayable(p.id)} className="w-8 h-8 flex items-center justify-center bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-lg text-emerald-400 transition-all active:scale-95">
                              <Check size={14} />
                            </button>
                          )}
                          <button onClick={() => handleDeletePayable(p.id)} className="w-8 h-8 flex items-center justify-center text-white/20 hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10"><Trash2 size={14} /></button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          }
        </div>
      )}

      {showExpense && <ExpenseSheet defaultDate={cashboxDate} onClose={() => setShowExpense(false)} onSaved={() => { setShowExpense(false); loadData() }} />}
      {showPayable && <PayableSheet onClose={() => setShowPayable(false)} onSaved={() => { setShowPayable(false); loadData() }} />}
    </div>
  )
}