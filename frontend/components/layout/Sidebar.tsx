'use client'
// components/layout/Sidebar.tsx

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard, Calendar, Users, TrendingUp,
  Package, Bot, BarChart3, Settings, LogOut,
  Lock, Scissors, ChevronRight
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { clearAuth } from '@/lib/api'

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard',  path: '/painel',           icon: LayoutDashboard, locked: false },
  { key: 'agenda',    label: 'Agenda',     path: '/painel/agenda',    icon: Calendar,        locked: false },
  { key: 'crm',       label: 'Clientes',   path: '/painel/clientes',  icon: Users,           locked: false },
  { key: 'financial', label: 'Financeiro', path: '/painel/financeiro',icon: TrendingUp,      locked: false },
  { key: 'products',  label: 'Produtos',   path: '/painel/produtos',  icon: Package,         locked: false },
  { key: 'agent',     label: 'Agente IA',  path: '/painel/agente',    icon: Bot,             locked: false },
  { key: 'reports',   label: 'Relatórios', path: '/painel/relatorios',icon: BarChart3,       locked: false },
]

const PLAN_LABELS: Record<string, string> = {
  trial:      'Trial',
  starter:    'Starter',
  pro:        'Pro',
  advanced:   'Advanced',
  enterprise: 'Enterprise',
}

const PLAN_COLORS: Record<string, string> = {
  trial:      'bg-amber-500/20 text-amber-400',
  starter:    'bg-slate-500/20 text-slate-400',
  pro:        'bg-indigo-500/20 text-indigo-400',
  advanced:   'bg-purple-500/20 text-purple-400',
  enterprise: 'bg-emerald-500/20 text-emerald-400',
}

const MODULE_PLAN: Record<string, string> = {
  crm:       'Pro',
  financial: 'Pro',
  products:  'Pro',
  reports:   'Pro',
  agent:     'Starter',
}

export default function Sidebar() {
  const pathname = usePathname()
  const router   = useRouter()
  const { tenant, clearAuth: clearStore } = useAuthStore()
  const { hasModule, plan, isTrial } = usePermissions()

  function handleLogout() {
    clearAuth()
    clearStore()
    router.replace('/login')
  }

  return (
    <aside className="hidden md:flex flex-col w-60 min-h-screen bg-[#0D0D14] border-r border-white/[0.06] fixed left-0 top-0 bottom-0 z-30">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/[0.06]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] flex items-center justify-center flex-shrink-0">
          <Scissors size={15} className="text-white" />
        </div>
        <div className="min-w-0">
          <div className="text-white font-bold text-sm truncate">{tenant?.name || 'Beauti'}</div>
          <div className={`text-xs px-1.5 py-0.5 rounded-md font-medium inline-block mt-0.5 ${PLAN_COLORS[plan] || PLAN_COLORS.starter}`}>
            {PLAN_LABELS[plan] || plan}
            {isTrial && ' · 14 dias'}
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ key, label, path, icon: Icon }) => {
          const locked   = key !== 'dashboard' && !hasModule(key)
          const active   = key === 'dashboard' ? pathname === '/painel' : pathname.startsWith(path)
          const reqPlan  = MODULE_PLAN[key]

          return (
            <div key={key}>
              {locked ? (
                <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/25 cursor-default group relative">
                  <Icon size={18} />
                  <span className="text-sm font-medium flex-1">{label}</span>
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] text-white/20">{reqPlan}</span>
                    <Lock size={12} className="text-white/20" />
                  </div>
                  {/* Tooltip upgrade */}
                  <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-[#1a1a2e] border border-white/10 rounded-lg px-3 py-2 text-xs text-white/70 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                    🔒 Disponível no plano <strong className="text-white">{reqPlan}</strong>
                    <br />
                    <span className="text-white/40">Faça upgrade para desbloquear</span>
                  </div>
                </div>
              ) : (
                <Link
                  href={path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 ${
                    active
                      ? 'bg-[#6366f1]/15 text-white'
                      : 'text-white/50 hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  <Icon size={18} className={active ? 'text-[#6366f1]' : ''} />
                  <span className="text-sm font-medium flex-1">{label}</span>
                  {active && <ChevronRight size={14} className="text-[#6366f1]" />}
                </Link>
              )}
            </div>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-3 border-t border-white/[0.06] space-y-0.5">
        {/* Trial banner */}
        {isTrial && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2.5 mb-3">
            <div className="text-amber-400 text-xs font-semibold">Trial — {tenant?.trial_days_remaining || 0} dias restantes</div>
            <div className="text-amber-400/60 text-xs mt-0.5">Assine para não perder o acesso</div>
            <button className="mt-2 w-full bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold py-1.5 rounded-lg transition-colors">
              Ver planos
            </button>
          </div>
        )}

        <Link
          href="/painel/configuracoes"
          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
            pathname.startsWith('/painel/configuracoes')
              ? 'bg-[#6366f1]/15 text-white'
              : 'text-white/50 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Settings size={18} />
          <span className="text-sm font-medium">Configurações</span>
        </Link>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/30 hover:text-red-400 hover:bg-red-500/[0.06] transition-all"
        >
          <LogOut size={18} />
          <span className="text-sm font-medium">Sair</span>
        </button>
      </div>
    </aside>
  )
}