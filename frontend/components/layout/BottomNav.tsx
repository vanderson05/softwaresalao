'use client'
// components/layout/BottomNav.tsx
// Navegação mobile — bottom tab bar com safe area PWA

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard, Calendar, Users,
  TrendingUp, MoreHorizontal
} from 'lucide-react'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { useState } from 'react'
import MoreMenu from './MoreMenu'

const BOTTOM_TABS = [
  { key: 'dashboard', label: 'Início',      path: '/painel',           icon: LayoutDashboard },
  { key: 'agenda',    label: 'Agenda',      path: '/painel/agenda',    icon: Calendar        },
  { key: 'crm',       label: 'Clientes',    path: '/painel/clientes',  icon: Users           },
  { key: 'financial', label: 'Financeiro',  path: '/painel/financeiro',icon: TrendingUp      },
]

export default function BottomNav({ pendingCount = 0 }: { pendingCount?: number }) {
  const pathname = usePathname()
  const { hasModule } = usePermissions()
  const [moreOpen, setMoreOpen] = useState(false)

  return (
    <>
      {/* Bottom nav */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#0D0D14]/95 backdrop-blur-md border-t border-white/[0.06]"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="flex items-center justify-around px-2 pt-2 pb-1">
          {BOTTOM_TABS.map(({ key, label, path, icon: Icon }) => {
            const locked = key !== 'dashboard' && !hasModule(key)
            const active = key === 'dashboard'
              ? pathname === '/painel'
              : pathname.startsWith(path)

            if (locked) {
              return (
                <button
                  key={key}
                  onClick={() => {/* show upgrade modal */}}
                  className="flex flex-col items-center gap-1 px-3 py-1 min-w-[44px] min-h-[44px] justify-center opacity-30"
                >
                  <Icon size={22} className="text-white/30" />
                  <span className="text-[10px] text-white/30">{label}</span>
                </button>
              )
            }

            return (
              <Link
                key={key}
                href={path}
                className={`flex flex-col items-center gap-1 px-3 py-1 min-w-[44px] min-h-[44px] justify-center relative transition-all active:scale-95 ${
                  active ? 'text-[#6366f1]' : 'text-white/40'
                }`}
              >
                <div className="relative">
                  <Icon size={22} />
                  {/* Badge pendentes na agenda */}
                  {key === 'agenda' && pendingCount > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                      {pendingCount > 9 ? '9+' : pendingCount}
                    </span>
                  )}
                </div>
                <span className="text-[10px] font-medium">{label}</span>
                {active && (
                  <span className="absolute top-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-[#6366f1] rounded-full" />
                )}
              </Link>
            )
          })}

          {/* Mais */}
          <button
            onClick={() => setMoreOpen(true)}
            className="flex flex-col items-center gap-1 px-3 py-1 min-w-[44px] min-h-[44px] justify-center text-white/40 active:scale-95 transition-all"
          >
            <MoreHorizontal size={22} />
            <span className="text-[10px] font-medium">Mais</span>
          </button>
        </div>
      </nav>

      {/* More menu drawer */}
      {moreOpen && <MoreMenu onClose={() => setMoreOpen(false)} />}
    </>
  )
}