'use client'
// app/painel/produtos/page.tsx

import { useEffect, useState, useCallback } from 'react'
import { Package, Plus, X, AlertTriangle, ChevronRight, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'
import { financialApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

function formatCurrency(v: number) { return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }
function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }
const inputClass = "w-full h-11 px-4 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  product: { label: 'Produto',       color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  extra:   { label: 'Serviço extra', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  other:   { label: 'Outro',         color: 'bg-slate-500/10 text-slate-400 border-slate-500/20'   },
}

// ── Product Sheet ─────────────────────────────────────────────
function ProductSheet({ product, onClose, onSaved }: { product?: any; onClose: () => void; onSaved: () => void }) {
  const isEdit = !!product
  const [form, setForm] = useState({
    name:        product?.name        || '',
    category:    product?.category    || 'product',
    price:       product?.price       || '',
    cost_price:  product?.cost_price  || '',
    stock_qty:   product?.stock_qty   || '0',
    stock_alert: product?.stock_alert || '5',
    track_stock: product?.track_stock ?? true,
  })
  const [loading, setLoading] = useState(false)

  async function handleSave() {
    if (!form.name || !form.price) { toast.error('Nome e preço são obrigatórios.'); return }
    setLoading(true)
    try {
      if (isEdit) {
        await financialApi.createProduct // PATCH — usando endpoint de update
        await import('@/lib/api').then(({ default: api }) => api.patch(`/financial/products/${product.id}/`, form))
      } else {
        await financialApi.createProduct({ ...form, price: Number(form.price), cost_price: Number(form.cost_price || 0), stock_qty: Number(form.stock_qty), stock_alert: Number(form.stock_alert) })
      }
      toast.success(isEdit ? 'Produto atualizado!' : 'Produto criado!')
      onSaved()
    } catch { toast.error('Erro ao salvar.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-[420px] z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl overflow-y-auto" style={{ maxHeight: '85vh', paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <h3 className="text-white font-bold text-base">{isEdit ? 'Editar produto' : 'Novo produto'}</h3>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div><label className="text-white/50 text-sm block mb-1.5">Nome *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Pomada Capilar" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div>
            <label className="text-white/50 text-sm block mb-2">Categoria</label>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
                <button key={k} onClick={() => setForm(f => ({ ...f, category: k }))} className={`py-2.5 rounded-xl text-xs font-medium transition-all active:scale-95 border ${form.category === k ? 'bg-[#6366f1] text-white border-[#6366f1]' : 'bg-white/[0.04] text-white/40 border-white/[0.06]'}`}>{v.label}</button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-white/50 text-sm block mb-1.5">Preço venda *</label><input type="number" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} placeholder="R$" className={inputClass} style={{ fontSize: '16px' }} /></div>
            <div><label className="text-white/50 text-sm block mb-1.5">Preço custo</label><input type="number" value={form.cost_price} onChange={e => setForm(f => ({ ...f, cost_price: e.target.value }))} placeholder="R$" className={inputClass} style={{ fontSize: '16px' }} /></div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-white/50 text-sm">Controlar estoque</label>
              <button onClick={() => setForm(f => ({ ...f, track_stock: !f.track_stock }))} className={`w-12 h-6 rounded-full transition-all ${form.track_stock ? 'bg-[#6366f1]' : 'bg-white/20'}`}>
                <div className={`w-5 h-5 rounded-full bg-white shadow transition-all mx-0.5 ${form.track_stock ? 'translate-x-6' : 'translate-x-0'}`} />
              </button>
            </div>
            {form.track_stock && (
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-white/50 text-sm block mb-1.5">Qtd. inicial</label><input type="number" value={form.stock_qty} onChange={e => setForm(f => ({ ...f, stock_qty: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
                <div><label className="text-white/50 text-sm block mb-1.5">Alerta em</label><input type="number" value={form.stock_alert} onChange={e => setForm(f => ({ ...f, stock_alert: e.target.value }))} className={inputClass} style={{ fontSize: '16px' }} /></div>
              </div>
            )}
          </div>
          <button onClick={handleSave} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Salvando...' : isEdit ? 'Salvar alterações' : 'Criar produto'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Stock Sheet ───────────────────────────────────────────────
function StockSheet({ product, onClose, onSaved }: { product: any; onClose: () => void; onSaved: () => void }) {
  const [type, setType] = useState<'in' | 'out' | 'adjust'>('in')
  const [quantity, setQuantity] = useState('')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSave() {
    if (!quantity || Number(quantity) <= 0) { toast.error('Informe a quantidade.'); return }
    setLoading(true)
    try {
      await financialApi.addStock(product.id, { type, quantity: Number(quantity), reason })
      toast.success('Estoque atualizado!')
      onSaved()
    } catch { toast.error('Erro ao atualizar estoque.') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-96 z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl shadow-2xl" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
        <div className="md:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 bg-white/20 rounded-full" /></div>
        <div className="flex items-center justify-between px-5 pt-4 pb-4 border-b border-white/[0.06]">
          <div><h3 className="text-white font-bold text-base">Movimentar estoque</h3><p className="text-white/40 text-xs mt-0.5">{product.name} · atual: {product.stock_qty}</p></div>
          <button onClick={onClose} className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="text-white/50 text-sm block mb-2">Tipo de movimentação</label>
            <div className="grid grid-cols-3 gap-2">
              {[{ v: 'in', l: '📦 Entrada', c: 'bg-emerald-500' }, { v: 'out', l: '📤 Saída', c: 'bg-red-500' }, { v: 'adjust', l: '🔄 Ajuste', c: 'bg-amber-500' }].map(({ v, l, c }) => (
                <button key={v} onClick={() => setType(v as any)} className={`py-3 rounded-xl text-xs font-medium transition-all active:scale-95 ${type === v ? `${c} text-white` : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>{l}</button>
              ))}
            </div>
          </div>
          <div><label className="text-white/50 text-sm block mb-1.5">Quantidade</label><input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} placeholder="0" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <div><label className="text-white/50 text-sm block mb-1.5">Motivo (opcional)</label><input value={reason} onChange={e => setReason(e.target.value)} placeholder="Ex: Compra fornecedor" className={inputClass} style={{ fontSize: '16px' }} /></div>
          <button onClick={handleSave} disabled={loading} className="w-full h-12 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? 'Salvando...' : 'Confirmar movimentação'}
          </button>
        </div>
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function ProdutosPage() {
  const { hasModule } = usePermissions()
  const [products, setProducts] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [editProduct, setEditProduct] = useState<any>(null)
  const [stockProduct, setStockProduct] = useState<any>(null)
  const [filterCategory, setFilterCategory] = useState<string>('all')

  const loadProducts = useCallback(async () => {
    setLoading(true)
    try {
      const [prodRes, alertRes] = await Promise.all([financialApi.products(), financialApi.stockAlerts()])
      setProducts(prodRes.data || [])
      setAlerts(alertRes.data.alerts || [])
    } catch { toast.error('Erro ao carregar produtos.') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadProducts() }, [loadProducts])

  if (!hasModule('products')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-4"><span className="text-3xl">🔒</span></div>
        <h2 className="text-white font-bold text-xl mb-2">Produtos e Estoque</h2>
        <p className="text-white/40 text-sm mb-6 max-w-xs">Disponível a partir do plano <strong className="text-white">Pro</strong>.</p>
        <button className="bg-[#6366f1] text-white font-semibold px-6 py-3 rounded-xl">Ver planos</button>
      </div>
    )
  }

  const filtered = filterCategory === 'all' ? products : products.filter(p => p.category === filterCategory)
  const totalValue = products.reduce((acc, p) => acc + (p.track_stock ? Number(p.price) * p.stock_qty : 0), 0)

  return (
    <div className="px-4 py-5 md:px-6 md:py-6 max-w-3xl">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-white font-bold text-xl">Produtos</h1>
          <p className="text-white/30 text-sm mt-0.5">{products.length} produto{products.length !== 1 ? 's' : ''} · estoque: {formatCurrency(totalValue)}</p>
        </div>
        <button onClick={() => setShowNew(true)} className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-all active:scale-95">
          <Plus size={16} /> Novo
        </button>
      </div>

      {/* Alertas de estoque */}
      {alerts.length > 0 && (
        <div className="mb-5 space-y-2">
          {alerts.map(a => (
            <div key={a.id} className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
              <AlertTriangle size={16} className="text-amber-400 flex-shrink-0" />
              <span className="text-amber-300 text-sm flex-1"><strong>{a.name}</strong> — estoque baixo ({a.stock_qty} un.)</span>
              <button onClick={() => setStockProduct(products.find(p => p.id === a.id))} className="text-amber-400 text-xs border border-amber-400/30 px-2.5 py-1 rounded-lg hover:bg-amber-400/10 flex-shrink-0">Repor</button>
            </div>
          ))}
        </div>
      )}

      {/* Filtro por categoria */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-4" style={{ WebkitOverflowScrolling: 'touch' as any }}>
        {[{ k: 'all', l: 'Todos' }, { k: 'product', l: 'Produtos' }, { k: 'extra', l: 'Extras' }, { k: 'other', l: 'Outros' }].map(({ k, l }) => (
          <button key={k} onClick={() => setFilterCategory(k)} className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex-shrink-0 active:scale-95 ${filterCategory === k ? 'bg-[#6366f1] text-white' : 'bg-white/[0.06] text-white/50 border border-white/[0.08]'}`}>{l}</button>
        ))}
      </div>

      {/* Lista */}
      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-20" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <Package size={36} className="text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm mb-4">Nenhum produto cadastrado</p>
          <button onClick={() => setShowNew(true)} className="flex items-center gap-2 bg-[#6366f1] text-white text-sm font-semibold px-5 py-2.5 rounded-xl active:scale-95 mx-auto"><Plus size={16} /> Criar produto</button>
        </div>
      ) : (
        <div className="space-y-2 pb-24 md:pb-6">
          {filtered.map(p => {
            const catCfg = CATEGORY_LABELS[p.category] || CATEGORY_LABELS.other
            const margin = p.margin_pct || 0
            return (
              <div key={p.id} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4 hover:border-white/10 transition-all">
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white font-semibold text-sm truncate">{p.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${catCfg.color}`}>{catCfg.label}</span>
                      {p.stock_low && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex-shrink-0">⚠️ Baixo</span>}
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-[#6366f1] font-bold text-sm">{formatCurrency(Number(p.price))}</span>
                      {p.cost_price > 0 && <span className="text-white/30">custo: {formatCurrency(Number(p.cost_price))}</span>}
                      {margin > 0 && <span className="text-emerald-400/70">margem: {margin}%</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {p.track_stock && (
                      <button onClick={() => setStockProduct(p)} className="flex items-center gap-1.5 bg-white/[0.06] hover:bg-white/10 border border-white/[0.08] px-3 py-2 rounded-xl text-white/50 hover:text-white text-xs font-medium transition-all active:scale-95 min-h-[36px]">
                        <Package size={13} /> {p.stock_qty}
                      </button>
                    )}
                    <button onClick={() => setEditProduct(p)} className="w-9 h-9 flex items-center justify-center bg-white/[0.06] hover:bg-white/10 border border-white/[0.08] rounded-xl text-white/40 hover:text-white transition-all active:scale-95">
                      <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showNew && <ProductSheet onClose={() => setShowNew(false)} onSaved={() => { setShowNew(false); loadProducts() }} />}
      {editProduct && <ProductSheet product={editProduct} onClose={() => setEditProduct(null)} onSaved={() => { setEditProduct(null); loadProducts() }} />}
      {stockProduct && <StockSheet product={stockProduct} onClose={() => setStockProduct(null)} onSaved={() => { setStockProduct(null); loadProducts() }} />}
    </div>
  )
}