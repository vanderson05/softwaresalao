'use client'
// components/agenda/AppointmentSheet.tsx

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  X, Check, XCircle, Clock, Phone, Scissors,
  User, AlertTriangle, ChevronRight, DollarSign,
  Plus, Trash2, Package, Search
} from 'lucide-react'
import { appointmentsApi, financialApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
}
function formatCurrency(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending:    { label: 'Aguardando confirmação', color: 'text-amber-400'  },
  confirmed:  { label: 'Confirmado',             color: 'text-indigo-400' },
  in_comanda: { label: 'Em atendimento',          color: 'text-purple-400' },
  completed:  { label: 'Realizado',              color: 'text-emerald-400'},
  cancelled:  { label: 'Cancelado',              color: 'text-red-400'    },
  no_show:    { label: 'Não compareceu',          color: 'text-slate-400'  },
}

const inputClass = "w-full h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors"

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} />
}

function InfoRow({ icon: Icon, label, value, sub, action }: {
  icon: any; label: string; value: string; sub?: string
  action?: { label: string; href: string }
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon size={15} className="text-white/40" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-white/30 text-xs">{label}</div>
        <div className="text-white text-sm font-medium truncate">{value}</div>
        {sub && <div className="text-white/30 text-xs capitalize">{sub}</div>}
      </div>
      {action && (
        <a href={action.href} className="text-[#6366f1] text-xs font-medium border border-[#6366f1]/30 px-2.5 py-1.5 rounded-lg hover:bg-[#6366f1]/10 transition-all flex-shrink-0">
          {action.label}
        </a>
      )}
    </div>
  )
}

function ActionBtn({ label, icon: Icon, color, onClick, loading }: {
  label: string; icon: any; color: string; onClick: () => void; loading: boolean
}) {
  return (
    <button onClick={onClick} disabled={loading}
      className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl font-semibold text-sm transition-all active:scale-[0.98] disabled:opacity-50 ${color}`}>
      <Icon size={18} />
      <span className="flex-1 text-left">{label}</span>
      {!loading && <ChevronRight size={16} className="opacity-50" />}
    </button>
  )
}

// ── Product Autocomplete ──────────────────────────────────────
function ProductSearch({
  products, onSelect
}: {
  products: any[]
  onSelect: (product: any) => void
}) {
  const [query,   setQuery]   = useState('')
  const [open,    setOpen]    = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 6)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
        <input
          value={query}
          onChange={e => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          placeholder="Buscar produto do estoque..."
          className={`${inputClass} pl-9`}
          style={{ fontSize: '16px' }}
        />
      </div>
      {open && query.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1a2e] border border-white/10 rounded-xl shadow-xl z-20 overflow-hidden">
          {filtered.length === 0 ? (
            <div className="px-4 py-3 text-white/30 text-sm">Nenhum produto encontrado</div>
          ) : (
            filtered.map(p => (
              <button
                key={p.id}
                onClick={() => { onSelect(p); setQuery(''); setOpen(false) }}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.06] transition-colors text-left border-b border-white/[0.04] last:border-0"
              >
                <div>
                  <div className="text-white text-sm">{p.name}</div>
                  {p.track_stock && (
                    <div className={`text-xs mt-0.5 ${p.stock_qty <= p.stock_alert ? 'text-amber-400' : 'text-white/30'}`}>
                      {p.stock_qty} em estoque
                    </div>
                  )}
                </div>
                <span className="text-[#6366f1] font-semibold text-sm">{formatCurrency(p.price)}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Sheet ────────────────────────────────────────────────
export default function AppointmentSheet({
  appointment, onClose, onUpdated
}: {
  appointment: any; onClose: () => void; onUpdated: () => void
}) {
  const { isStaff } = usePermissions()

  type Step = 'detail' | 'comanda' | 'checkout' | 'cancel'
  const [step,            setStep]           = useState<Step>('detail')
  const [loading,         setLoading]        = useState(false)
  const [paymentMethod,   setPaymentMethod]  = useState('pix')

  // Comanda
  const [comanda,         setComanda]        = useState<any>(null)
  const [loadingComanda,  setLoadingComanda] = useState(false)
  const [products,        setProducts]       = useState<any[]>([])

  // Novo item — modo: 'idle' | 'stock' | 'manual'
  const [addMode,   setAddMode]   = useState<'idle' | 'stock' | 'manual'>('idle')
  const [itemDesc,  setItemDesc]  = useState('')
  const [itemPrice, setItemPrice] = useState('')
  const [savingItem,setSavingItem]= useState(false)

  const status      = STATUS_LABELS[appointment.status] || { label: appointment.status, color: 'text-white/50' }
  const canConfirm  = isStaff && appointment.status === 'pending'
  const canComplete = isStaff && ['confirmed', 'in_comanda'].includes(appointment.status)
  const canCancel   = isStaff && !['completed','cancelled','no_show'].includes(appointment.status)
  const canNoShow   = isStaff && appointment.status === 'confirmed'
  const isDone      = ['completed','cancelled','no_show'].includes(appointment.status)

  const loadComanda = useCallback(async () => {
    setLoadingComanda(true)
    try {
      const { data } = await financialApi.comanda(appointment.id)
      setComanda(data)
    } catch { toast.error('Erro ao carregar comanda.') }
    finally { setLoadingComanda(false) }
  }, [appointment.id])

  useEffect(() => {
    if (step === 'comanda') {
      loadComanda()
      // Carrega produtos do estoque
      financialApi.products().then(({ data }) => setProducts(data || [])).catch(() => {})
    }
  }, [step, loadComanda])

  // ── Ações ─────────────────────────────────────────────────

  async function handleConfirm() {
    setLoading(true)
    try {
      await appointmentsApi.confirm(appointment.id)
      toast.success('Agendamento confirmado!')
      onUpdated()
    } catch { toast.error('Erro ao confirmar.') }
    finally { setLoading(false) }
  }

  async function handleNoShow() {
    setLoading(true)
    try {
      await appointmentsApi.noShow(appointment.id)
      toast.success('Marcado como não compareceu.')
      onUpdated()
    } catch { toast.error('Erro.') }
    finally { setLoading(false) }
  }

  async function handleCancel() {
    setLoading(true)
    try {
      await appointmentsApi.cancel(appointment.id, { reason: 'Cancelado pelo barbeiro' })
      toast.success('Agendamento cancelado.')
      onUpdated()
    } catch { toast.error('Erro ao cancelar.') }
    finally { setLoading(false) }
  }

  // Adiciona produto do estoque
  async function handleAddFromStock(product: any) {
    setSavingItem(true)
    try {
      await financialApi.addItem(appointment.id, {
        product_id:  product.id,
        description: product.name,
        unit_price:  product.price,
        quantity:    1,
      })
      setAddMode('idle')
      await loadComanda()
      toast.success(`${product.name} adicionado!`)
    } catch { toast.error('Erro ao adicionar produto.') }
    finally { setSavingItem(false) }
  }

  // Adiciona item manual
  async function handleAddManual() {
    if (!itemDesc.trim() || !itemPrice) { toast.error('Preencha descrição e valor.'); return }
    setSavingItem(true)
    try {
      await financialApi.addItem(appointment.id, {
        description: itemDesc.trim(),
        unit_price:  Number(itemPrice),
        quantity:    1,
      })
      setItemDesc(''); setItemPrice(''); setAddMode('idle')
      await loadComanda()
      toast.success('Item adicionado!')
    } catch { toast.error('Erro ao adicionar item.') }
    finally { setSavingItem(false) }
  }

  async function handleRemoveItem(itemId: string) {
    try {
      await financialApi.removeItem(itemId)
      await loadComanda()
    } catch { toast.error('Erro ao remover.') }
  }

  function goToCheckout() {
    // Avisa se tem item preenchido mas não salvo
    if (addMode !== 'idle' && (itemDesc || itemPrice)) {
      toast.warning('Você tem um item não salvo. Confirme ou descarte antes de continuar.')
      return
    }
    if (!comanda || comanda.items?.length === 0) {
      toast.warning('Adicione ao menos um item na comanda.')
      return
    }
    setStep('checkout')
  }

  async function handleCheckout() {
    setLoading(true)
    try {
      await financialApi.checkout(appointment.id, { payment_method: paymentMethod })
      toast.success('Atendimento concluído! 🎉')
      onUpdated()
    } catch { toast.error('Erro ao finalizar.') }
    finally { setLoading(false) }
  }

  const serviceDuration = appointment.service_duration ? `${appointment.service_duration}min` : ''
  const serviceLabel    = serviceDuration ? `${appointment.service_name} · ${serviceDuration}` : appointment.service_name
  const comandaTotal    = comanda?.total ?? Number(appointment.price_snapshot || 0)

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />

      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[440px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto"
        style={{ maxHeight: '90vh', paddingBottom: 'env(safe-area-inset-bottom)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="md:hidden flex justify-center pt-3 pb-1 sticky top-0 bg-[#0D0D14]">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-start justify-between px-5 pt-4 pb-3 border-b border-white/[0.06] sticky top-4 bg-[#0D0D14] z-10">
          <div>
            <h3 className="text-white font-bold text-lg leading-tight">{appointment.client_name}</h3>
            <span className={`text-sm font-medium ${status.color}`}>{status.label}</span>
          </div>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white rounded-xl hover:bg-white/[0.06] transition-all ml-2 flex-shrink-0">
            <X size={18} />
          </button>
        </div>

        {/* ── Detalhe ── */}
        {step === 'detail' && (
          <div className="px-5 py-4">
            <div className="space-y-3 mb-5">
              <InfoRow icon={Scissors}   label="Serviço"      value={serviceLabel} />
              <InfoRow icon={User}       label="Profissional" value={appointment.professional_name} />
              <InfoRow icon={Clock}      label="Horário"
                value={`${formatTime(appointment.starts_at)} – ${formatTime(appointment.ends_at)}`}
                sub={formatDate(appointment.starts_at)}
              />
              {appointment.client_phone && (
                <InfoRow icon={Phone} label="Telefone" value={appointment.client_phone}
                  action={{ label: 'Ligar', href: `tel:${appointment.client_phone}` }}
                />
              )}
              <InfoRow icon={DollarSign} label="Valor" value={formatCurrency(Number(appointment.price_snapshot || 0))} />
            </div>
            {!isDone && (
              <div className="space-y-2.5">
                {canConfirm && (
                  <ActionBtn label="Confirmar agendamento" icon={Check}
                    color="bg-[#6366f1] hover:bg-[#4f46e5] text-white"
                    onClick={handleConfirm} loading={loading}
                  />
                )}
                {canComplete && (
                  <ActionBtn label="Abrir comanda" icon={Package}
                    color="bg-emerald-600 hover:bg-emerald-500 text-white"
                    onClick={() => setStep('comanda')} loading={false}
                  />
                )}
                {canNoShow && (
                  <ActionBtn label="Não compareceu" icon={AlertTriangle}
                    color="bg-white/[0.06] hover:bg-white/10 text-white/60 border border-white/[0.08]"
                    onClick={handleNoShow} loading={loading}
                  />
                )}
                {canCancel && (
                  <ActionBtn label="Cancelar agendamento" icon={XCircle}
                    color="bg-red-500/10 hover:bg-red-500/15 text-red-400 border border-red-500/20"
                    onClick={() => setStep('cancel')} loading={false}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Comanda ── */}
        {step === 'comanda' && (
          <div className="px-5 py-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-white font-bold text-base">Comanda</h4>
              <span className="text-white/30 text-xs">{appointment.client_name}</span>
            </div>

            {loadingComanda ? (
              <div className="space-y-2 mb-4"><Skeleton className="h-14" /><Skeleton className="h-14" /></div>
            ) : (
              <>
                {/* Lista de itens */}
                <div className="space-y-2 mb-4">
                  {comanda?.items?.length === 0 ? (
                    <div className="text-center py-4 text-white/20 text-sm">Nenhum item na comanda</div>
                  ) : comanda?.items?.map((item: any) => (
                    <div key={item.id} className="flex items-center gap-3 bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-white text-sm font-medium truncate">{item.description}</div>
                        <div className="text-white/30 text-xs">x{item.quantity} · {formatCurrency(item.unit_price)}</div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-white font-semibold text-sm">{formatCurrency(item.total)}</span>
                        <button onClick={() => handleRemoveItem(item.id)}
                          className="w-7 h-7 flex items-center justify-center text-white/20 hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Adicionar item */}
                {addMode === 'idle' && (
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    <button onClick={() => setAddMode('stock')}
                      className="flex items-center justify-center gap-2 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] hover:bg-white/10 text-white/50 hover:text-white transition-all text-sm">
                      <Package size={15} /> Produto estoque
                    </button>
                    <button onClick={() => setAddMode('manual')}
                      className="flex items-center justify-center gap-2 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] hover:bg-white/10 text-white/50 hover:text-white transition-all text-sm">
                      <Plus size={15} /> Item manual
                    </button>
                  </div>
                )}

                {/* Busca de produto no estoque */}
                {addMode === 'stock' && (
                  <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-4 mb-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-white/50 text-xs font-medium uppercase tracking-wide">Produto do estoque</p>
                      <button onClick={() => setAddMode('idle')} className="text-white/30 hover:text-white"><X size={16} /></button>
                    </div>
                    <ProductSearch
                      products={products}
                      onSelect={handleAddFromStock}
                    />
                    {savingItem && (
                      <div className="text-center text-white/40 text-xs py-2">Adicionando...</div>
                    )}
                    <p className="text-white/20 text-xs">
                      Produto não está no estoque?{' '}
                      <button onClick={() => setAddMode('manual')} className="text-[#6366f1] underline">
                        Adicionar manualmente
                      </button>
                    </p>
                  </div>
                )}

                {/* Item manual */}
                {addMode === 'manual' && (
                  <div className="bg-white/[0.04] border border-white/[0.08] rounded-2xl p-4 mb-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-white/50 text-xs font-medium uppercase tracking-wide">Item manual</p>
                      <button onClick={() => { setAddMode('idle'); setItemDesc(''); setItemPrice('') }}
                        className="text-white/30 hover:text-white"><X size={16} /></button>
                    </div>
                    <input
                      value={itemDesc}
                      onChange={e => setItemDesc(e.target.value)}
                      placeholder="Descrição (ex: Pomada Capilar)"
                      className={inputClass}
                      style={{ fontSize: '16px' }}
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={itemPrice}
                        onChange={e => setItemPrice(e.target.value)}
                        placeholder="Valor R$"
                        className={`${inputClass} flex-1`}
                        style={{ fontSize: '16px' }}
                      />
                      <button
                        onClick={handleAddManual}
                        disabled={savingItem || !itemDesc || !itemPrice}
                        className="w-11 h-11 flex items-center justify-center bg-[#6366f1] hover:bg-[#4f46e5] rounded-xl text-white disabled:opacity-40 transition-all active:scale-95"
                      >
                        {savingItem ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Check size={18} />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Total */}
                <div className="flex items-center justify-between bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-3.5 mb-4">
                  <span className="text-white/50 font-medium">Total</span>
                  <span className="text-white font-black text-xl">{formatCurrency(comanda?.total || 0)}</span>
                </div>

                {/* Ações */}
                <div className="flex gap-2">
                  <button onClick={() => setStep('detail')}
                    className="flex-1 py-3 rounded-xl bg-white/[0.06] text-white/50 text-sm font-medium border border-white/[0.08] hover:bg-white/10 transition-all">
                    Voltar
                  </button>
                  <button onClick={goToCheckout}
                    className="flex-[2] py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold transition-all active:scale-[0.98]">
                    Ir para pagamento →
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Checkout ── */}
        {step === 'checkout' && (
          <div className="px-5 py-4">
            <h4 className="text-white font-bold text-base mb-1">Forma de pagamento</h4>
            <p className="text-white/40 text-sm mb-5">{appointment.client_name} · {appointment.service_name}</p>

            <div className="grid grid-cols-2 gap-2 mb-5">
              {[
                { value: 'pix',    label: '💸 Pix'      },
                { value: 'cash',   label: '💵 Dinheiro' },
                { value: 'credit', label: '💳 Crédito'  },
                { value: 'debit',  label: '💳 Débito'   },
              ].map(({ value, label }) => (
                <button key={value} onClick={() => setPaymentMethod(value)}
                  className={`py-4 rounded-xl text-sm font-medium transition-all active:scale-95 ${
                    paymentMethod === value
                      ? 'bg-[#6366f1] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)]'
                      : 'bg-white/[0.06] text-white/50 border border-white/[0.08] hover:bg-white/10'
                  }`}>
                  {label}
                </button>
              ))}
            </div>

            {/* Resumo dos itens */}
            {comanda?.items?.length > 0 && (
              <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl px-4 py-3 mb-4 space-y-1.5">
                {comanda.items.map((item: any) => (
                  <div key={item.id} className="flex items-center justify-between text-sm">
                    <span className="text-white/50 truncate flex-1 mr-3">{item.description}</span>
                    <span className="text-white/70 flex-shrink-0">{formatCurrency(item.total)}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center justify-between bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-4 mb-5">
              <span className="text-white/50 text-sm">Total a cobrar</span>
              <span className="text-white font-black text-2xl">{formatCurrency(comandaTotal)}</span>
            </div>

            <div className="flex gap-2">
              <button onClick={() => setStep('comanda')}
                className="flex-1 py-3 rounded-xl bg-white/[0.06] text-white/50 text-sm font-medium border border-white/[0.08] hover:bg-white/10 transition-all">
                Voltar
              </button>
              <button onClick={handleCheckout} disabled={loading}
                className="flex-[2] py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold transition-all disabled:opacity-50 active:scale-[0.98]">
                {loading ? 'Finalizando...' : '✅ Confirmar pagamento'}
              </button>
            </div>
          </div>
        )}

        {/* ── Cancelar ── */}
        {step === 'cancel' && (
          <div className="px-5 py-4">
            <div className="text-center mb-5">
              <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-3">
                <XCircle size={22} className="text-red-400" />
              </div>
              <h4 className="text-white font-semibold text-lg">Cancelar agendamento?</h4>
              <p className="text-white/40 text-sm mt-1">{appointment.client_name} — {formatTime(appointment.starts_at)}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setStep('detail')}
                className="flex-1 py-3 rounded-xl bg-white/[0.06] text-white/50 text-sm font-medium border border-white/[0.08]">
                Voltar
              </button>
              <button onClick={handleCancel} disabled={loading}
                className="flex-[2] py-3 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-bold transition-all disabled:opacity-50">
                {loading ? 'Cancelando...' : 'Sim, cancelar'}
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}