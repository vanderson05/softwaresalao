'use client'
// app/painel/layout.tsx
// Layout do painel — sidebar desktop + bottom nav mobile

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { appointmentsApi } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import BottomNav from '@/components/layout/BottomNav'

export default function PainelLayout({ children }: { children: React.ReactNode }) {
  const router   = useRouter()
  const { tenant, role } = useAuthStore()
  const [pendingCount, setPendingCount] = useState(0)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('beauti_token')
    if (!token) {
      router.replace('/login')
      return
    }
    // Profissional vai para tela própria
    if (role === 'professional') {
      router.replace('/profissional')
      return
    }
    setReady(true)
  }, [role, router])

  // Busca agendamentos pendentes para badge
  useEffect(() => {
    if (!ready) return
    appointmentsApi.list({ status: 'pending' })
      .then(({ data }) => setPendingCount(data.length))
      .catch(() => {})

    // Atualiza a cada 60 segundos
    const interval = setInterval(() => {
      appointmentsApi.list({ status: 'pending' })
        .then(({ data }) => setPendingCount(data.length))
        .catch(() => {})
    }, 60000)

    return () => clearInterval(interval)
  }, [ready])

  if (!ready) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#6366f1] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0A0F]">
      {/* Sidebar — desktop */}
      <Sidebar />

      {/* Conteúdo principal */}
      <main
        className="md:ml-60 min-h-screen"
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        {/* Header mobile */}
        <MobileHeader pendingCount={pendingCount} />

        {/* Conteúdo */}
        <div
          className="pb-24 md:pb-8"
          style={{ paddingBottom: `calc(96px + env(safe-area-inset-bottom))` }}
        >
          {children}
        </div>
      </main>

      {/* Bottom nav — mobile */}
      <BottomNav pendingCount={pendingCount} />

      {/* FAB — mobile */}
      <FABButton />
    </div>
  )
}

// ── Header mobile ──────────────────────────────────────────────
function MobileHeader({ pendingCount }: { pendingCount: number }) {
  const { tenant } = useAuthStore()

  return (
    <header
      className="md:hidden flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-[#0D0D14]/80 backdrop-blur-md sticky top-0 z-20"
    >
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center">
          <span className="text-white text-xs font-bold">B</span>
        </div>
        <span className="text-white font-semibold text-sm truncate max-w-[140px]">
          {tenant?.name || 'Beauti'}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {pendingCount > 0 && (
          <div className="flex items-center gap-1.5 bg-amber-500/15 border border-amber-500/25 rounded-full px-2.5 py-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span className="text-amber-400 text-xs font-semibold">{pendingCount} pendente{pendingCount > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </header>
  )
}

// ── FAB ────────────────────────────────────────────────────────
function FABButton() {
  const router = useRouter()
  const { usePathname } = require('next/navigation')
  const pathname = usePathname()

  // FAB só aparece na agenda e dashboard
  const showFAB = pathname === '/painel' || pathname === '/painel/agenda'

  if (!showFAB) return null

  return (
    <button
      onClick={() => router.push('/painel/agenda/novo')}
      className="md:hidden fixed right-4 z-30 w-14 h-14 bg-[#6366f1] hover:bg-[#4f46e5] active:bg-[#4338ca] text-white rounded-full shadow-[0_4px_24px_rgba(99,102,241,0.5)] flex items-center justify-center active:scale-95 transition-all"
      style={{ bottom: `calc(80px + env(safe-area-inset-bottom))` }}
      aria-label="Novo agendamento"
    >
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    </button>
  )
}