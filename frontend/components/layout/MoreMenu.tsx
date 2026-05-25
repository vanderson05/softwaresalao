'use client'
// components/layout/MoreMenu.tsx
// Drawer "Mais" do bottom nav mobile
 
import { useRouter, usePathname } from 'next/navigation'
import { Package, Bot, BarChart3, Settings, LogOut, X, Lock } from 'lucide-react'
import { useAuthStore } from '@/lib/store'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { clearAuth } from '@/lib/api'
import { useEffect } from 'react'
 
const MORE_ITEMS = [
  { key: 'products', label: 'Produtos',   path: '/painel/produtos',   icon: Package,  reqPlan: 'Pro'  },
  { key: 'agent',    label: 'Agente IA',  path: '/painel/agente',     icon: Bot,      reqPlan: null   },
  { key: 'reports',  label: 'Relatórios', path: '/painel/relatorios', icon: BarChart3,reqPlan: 'Pro'  },
  { key: 'configuracoes', label: 'Configurações', path: '/painel/configuracoes', icon: Settings, reqPlan: null },
]
 
export default function MoreMenu({ onClose }: { onClose: () => void }) {
  const router   = useRouter()
  const pathname = usePathname()
  const { clearAuth: clearStore, tenant } = useAuthStore()
  const { hasModule } = usePermissions()
 
  // Fecha ao navegar
  useEffect(() => { onClose() }, [pathname])
 
  // Fecha ao clicar fora
  function handleLogout() {
    clearAuth()
    clearStore()
    router.replace('/login')
  }
 
  return (
    <>
      {/* Overlay */}
      <div
        className="md:hidden fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
        onClick={onClose}
      />
 
      {/* Drawer */}
      <div
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#0D0D14] rounded-t-2xl border-t border-white/10 animate-slide-in-bottom"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>
 
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06]">
          <div>
            <div className="text-white font-semibold text-sm">{tenant?.name}</div>
            <div className="text-white/30 text-xs">Mais opções</div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center text-white/40">
            <X size={18} />
          </button>
        </div>
 
        <nav className="px-3 py-3 space-y-0.5">
          {MORE_ITEMS.map(({ key, label, path, icon: Icon, reqPlan }) => {
            const locked = !hasModule(key)
            return (
              <div key={key}>
                {locked ? (
                  <div className="flex items-center gap-4 px-4 py-3.5 rounded-xl text-white/25">
                    <Icon size={20} />
                    <span className="text-sm font-medium flex-1">{label}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full text-white/30">
                        {reqPlan}
                      </span>
                      <Lock size={14} />
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => router.push(path)}
                    className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-white/60 hover:text-white hover:bg-white/[0.04] active:bg-white/[0.08] transition-all active:scale-[0.98]"
                  >
                    <Icon size={20} />
                    <span className="text-sm font-medium">{label}</span>
                  </button>
                )}
              </div>
            )
          })}
        </nav>
 
        <div className="px-3 pb-3 pt-1 border-t border-white/[0.06]">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-red-400/70 hover:text-red-400 hover:bg-red-500/[0.06] active:scale-[0.98] transition-all"
          >
            <LogOut size={20} />
            <span className="text-sm font-medium">Sair da conta</span>
          </button>
        </div>
      </div>
    </>
  )
}