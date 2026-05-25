'use client'
// app/b/page.tsx
// Discovery público — busca barbearias

import { useEffect, useState } from 'react'
import { Search, MapPin, Star, Scissors, Clock, ChevronRight, X } from 'lucide-react'
import { publicApi } from '@/lib/api'
import { useRouter } from 'next/navigation'

function Skeleton({ className = '' }: { className?: string }) { return <div className={`bg-white/[0.05] rounded-xl animate-pulse ${className}`} /> }

function BarbershopCard({ shop, onClick }: { shop: any; onClick: () => void }) {
  return (
    <button onClick={onClick} className="w-full flex items-start gap-4 p-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10 active:scale-[0.98] transition-all text-left">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
        <Scissors size={22} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-white font-bold text-base truncate">{shop.name}</div>
        {shop.city && <div className="flex items-center gap-1 mt-0.5"><MapPin size={11} className="text-white/30" /><span className="text-white/40 text-xs">{shop.city}</span></div>}
        <div className="flex items-center gap-3 mt-2">
          {shop.type && <span className="text-xs bg-white/[0.06] text-white/40 px-2.5 py-1 rounded-full capitalize">{shop.type === 'barbershop' ? 'Barbearia' : shop.type === 'salon' ? 'Salão' : 'Studio'}</span>}
          <span className="flex items-center gap-1 text-xs text-white/30"><Clock size={11} /> Agenda online</span>
        </div>
      </div>
      <ChevronRight size={16} className="text-white/20 flex-shrink-0 mt-1" />
    </button>
  )
}

export default function DiscoveryPage() {
  const router  = useRouter()
  const [shops,   setShops]   = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')

  useEffect(() => {
    const t = setTimeout(async () => {
      setLoading(true)
      try {
        const { data } = await publicApi.home({ q: search })
        setShops(data.barbershops || data.results || data || [])
      } catch { setShops([]) }
      finally { setLoading(false) }
    }, search ? 400 : 0)
    return () => clearTimeout(t)
  }, [search])

  return (
    <div className="min-h-screen bg-[#0A0A0F]" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
      {/* Header */}
      <div className="bg-gradient-to-b from-[#0D0D14] to-[#0A0A0F] px-4 pt-8 pb-6">
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
            <Scissors size={15} className="text-white" />
          </div>
          <span className="text-white font-bold text-lg">Beauti</span>
        </div>
        <h1 className="text-white font-black text-3xl mb-1">Agende agora</h1>
        <p className="text-white/40 text-sm">Barbearias, salões e studios perto de você</p>
        <div className="relative mt-5">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar barbearia, cidade..."
            className="w-full h-12 pl-11 pr-10 rounded-2xl bg-white/[0.07] border border-white/[0.10] text-white placeholder-white/30 focus:outline-none focus:border-[#6366f1]/50 transition-colors"
            style={{ fontSize: '16px' }}
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white">
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Lista */}
      <div className="px-4 pb-12">
        {loading ? (
          <div className="space-y-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-24" />)}</div>
        ) : shops.length === 0 ? (
          <div className="text-center py-16">
            <Scissors size={40} className="text-white/10 mx-auto mb-3" />
            <p className="text-white/30 text-sm">{search ? `Nenhum resultado para "${search}"` : 'Nenhum estabelecimento cadastrado'}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {shops.map((shop: any) => (
              <BarbershopCard key={shop.id || shop.slug} shop={shop} onClick={() => router.push(`/b/${shop.slug}`)} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="text-center pb-8 text-white/20 text-xs" style={{ paddingBottom: 'calc(32px + env(safe-area-inset-bottom))' }}>
        Beauti · Gestão de barbearias
      </div>
    </div>
  )
}


// ════════════════════════════════════════════════════════════════
// SALVAR COMO: app/b/[slug]/page.tsx
// ════════════════════════════════════════════════════════════════