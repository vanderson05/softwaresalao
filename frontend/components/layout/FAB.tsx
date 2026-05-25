'use client'
import { Plus } from 'lucide-react'
import { useRouter } from 'next/navigation'
 
export default function FAB() {
  const router = useRouter()
 
  return (
    <button
      onClick={() => router.push('/painel/agenda/novo')}
      className="md:hidden fixed right-4 z-30 w-14 h-14 bg-[#6366f1] hover:bg-[#4f46e5] active:bg-[#4338ca] text-white rounded-full shadow-[0_4px_24px_rgba(99,102,241,0.5)] flex items-center justify-center active:scale-95 transition-all"
      style={{ bottom: `calc(72px + env(safe-area-inset-bottom))` }}
      aria-label="Novo agendamento"
    >
      <Plus size={26} strokeWidth={2.5} />
    </button>
  )
}