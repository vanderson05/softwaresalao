'use client'
// app/b/page.tsx
// Discovery público — versão com alto impacto visual

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, MapPin, Scissors, Clock, Star, X, ChevronRight, Sparkles } from 'lucide-react'
import { publicApi } from '@/lib/api'

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/[0.06] rounded-2xl animate-pulse ${className}`} />
}

const TYPE_LABELS: Record<string, { label: string; emoji: string; color: string }> = {
  barbershop: { label: 'Barbearia', emoji: '✂️', color: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/20' },
  salon:      { label: 'Salão',     emoji: '💇', color: 'bg-pink-500/15 text-pink-300 border-pink-500/20'      },
  studio:     { label: 'Studio',    emoji: '💈', color: 'bg-purple-500/15 text-purple-300 border-purple-500/20' },
}

// Gradientes por índice para dar variedade visual nos cards
const CARD_GRADIENTS = [
  'from-[#6366f1] to-[#8B5CF6]',
  'from-[#8B5CF6] to-[#EC4899]',
  'from-[#06b6d4] to-[#6366f1]',
  'from-[#10b981] to-[#06b6d4]',
  'from-[#f59e0b] to-[#ef4444]',
  'from-[#EC4899] to-[#f59e0b]',
]

function BarbershopCard({ shop, index, onClick }: { shop: any; index: number; onClick: () => void }) {
  const gradient = CARD_GRADIENTS[index % CARD_GRADIENTS.length]
  const typeInfo = TYPE_LABELS[shop.type] || TYPE_LABELS.barbershop
  const initials = shop.name.split(' ').map((w: string) => w[0]).slice(0, 2).join('').toUpperCase()

  return (
    <button
      onClick={onClick}
      className="w-full group text-left bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.07] hover:border-white/15 rounded-2xl overflow-hidden transition-all duration-200 active:scale-[0.98]"
    >
      {/* Faixa colorida no topo */}
      <div className={`h-1.5 w-full bg-gradient-to-r ${gradient}`} />

      <div className="flex items-center gap-4 p-4">
        {/* Avatar */}
        <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center flex-shrink-0 shadow-lg`}>
          <span className="text-white font-black text-xl">{initials}</span>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-white font-bold text-base leading-tight truncate group-hover:text-white/90 transition-colors">
              {shop.name}
            </h3>
            <ChevronRight size={16} className="text-white/20 group-hover:text-white/50 transition-colors flex-shrink-0 mt-0.5" />
          </div>

          <div className="flex items-center gap-1.5 mt-1">
            {shop.city && (
              <div className="flex items-center gap-1">
                <MapPin size={11} className="text-white/30 flex-shrink-0" />
                <span className="text-white/40 text-xs truncate">{shop.city}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 mt-2.5">
            <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${typeInfo.color}`}>
              {typeInfo.emoji} {typeInfo.label}
            </span>
            <span className="flex items-center gap-1 text-xs text-white/25 bg-white/[0.05] px-2.5 py-1 rounded-full border border-white/[0.06]">
              <Clock size={10} /> Agenda online
            </span>
          </div>
        </div>
      </div>
    </button>
  )
}

export default function DiscoveryPage() {
  const router  = useRouter()
  const [shops,   setShops]   = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')
  const [focused, setFocused] = useState(false)

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
    <div
      className="min-h-screen bg-[#0A0A0F]"
      style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      {/* Hero header */}
      <div className="relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff04_1px,transparent_1px),linear-gradient(to_bottom,#ffffff04_1px,transparent_1px)] bg-[size:48px_48px]" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-80 h-40 bg-[#6366f1]/20 rounded-full blur-[60px] pointer-events-none" />

        <div className="relative px-4 pt-8 pb-6">
          {/* Logo */}
          <div className="flex items-center gap-2.5 mb-8">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)]">
              <Scissors size={16} className="text-white" />
            </div>
            <span className="text-white font-black text-xl tracking-tight">Beauti</span>
          </div>

          {/* Headline */}
          <div className="mb-6">
            <div className="inline-flex items-center gap-2 bg-white/[0.06] border border-white/10 rounded-full px-3 py-1.5 mb-4">
              <Sparkles size={12} className="text-[#6366f1]" />
              <span className="text-white/50 text-xs font-medium">Agenda online · Sem app</span>
            </div>
            <h1 className="text-white font-black text-3xl leading-tight">
              Agende seu<br />
              <span className="bg-gradient-to-r from-[#6366f1] via-[#8B5CF6] to-[#EC4899] bg-clip-text text-transparent">
                próximo corte
              </span>
            </h1>
            <p className="text-white/40 text-sm mt-2">
              Barbearias, salões e studios perto de você
            </p>
          </div>

          {/* Search bar */}
          <div className={`relative transition-all duration-200 ${focused ? 'scale-[1.02]' : ''}`}>
            <Search size={17} className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${focused ? 'text-[#6366f1]' : 'text-white/25'}`} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Buscar barbearia ou cidade..."
              className={`w-full h-14 pl-12 pr-12 rounded-2xl text-sm text-white placeholder-white/30 transition-all focus:outline-none ${
                focused
                  ? 'bg-white/[0.09] border-2 border-[#6366f1]/60 shadow-[0_0_24px_rgba(99,102,241,0.2)]'
                  : 'bg-white/[0.06] border border-white/[0.10]'
              }`}
              style={{ fontSize: '16px' }}
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center text-white/30 hover:text-white bg-white/[0.08] rounded-full transition-all"
              >
                <X size={13} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Resultados */}
      <div className="px-4 pb-12">
        {/* Contador */}
        {!loading && shops.length > 0 && (
          <div className="flex items-center justify-between mb-4">
            <span className="text-white/30 text-sm">
              {search ? `${shops.length} resultado${shops.length !== 1 ? 's' : ''} para "${search}"` : `${shops.length} estabelecimento${shops.length !== 1 ? 's' : ''}`}
            </span>
          </div>
        )}

        {loading ? (
          <div className="space-y-3">
            {[1,2,3,4].map(i => (
              <div key={i} className="bg-white/[0.03] border border-white/[0.07] rounded-2xl overflow-hidden">
                <div className="h-1.5 bg-white/[0.08] animate-pulse" />
                <div className="flex gap-4 p-4">
                  <Skeleton className="w-14 h-14 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-3 w-1/3" />
                    <Skeleton className="h-6 w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : shops.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mx-auto mb-4">
              <Scissors size={28} className="text-white/20" />
            </div>
            <p className="text-white/40 font-medium">
              {search ? `Nenhum resultado para "${search}"` : 'Nenhum estabelecimento ainda'}
            </p>
            <p className="text-white/20 text-sm mt-1">
              {search ? 'Tente outro nome ou cidade' : 'Em breve mais barbearias aqui'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {shops.map((shop: any, i: number) => (
              <BarbershopCard
                key={shop.id || shop.slug}
                shop={shop}
                index={i}
                onClick={() => router.push(`/b/${shop.slug}`)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div
        className="text-center text-white/15 text-xs pb-6"
        style={{ paddingBottom: 'calc(24px + env(safe-area-inset-bottom))' }}
      >
        Beauti · Gestão para barbearias e salões
      </div>
    </div>
  )
}