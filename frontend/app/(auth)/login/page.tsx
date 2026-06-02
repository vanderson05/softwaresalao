'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi, setAuthTokens } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { toast } from 'sonner'

export default function LoginPage() {
  const router  = useRouter()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [loading,  setLoading]  = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await authApi.login({ email, password })
      setAuthTokens(data.tokens.access, data.tokens.refresh)
      setAuth(data.user, data.tenant, data.role, data.professional_id)
      toast.success('Bem-vindo de volta!')
      router.replace(data.tenant.setup_completed ? '/painel' : '/setup')
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'E-mail ou senha incorretos.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0A0A0F] p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-[#6366f1] to-[#8B5CF6] mb-4">
            <span className="text-white text-2xl font-bold">B</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Beauti</h1>
          <p className="text-white/40 text-sm mt-1">Gestão de barbearias</p>
        </div>

        <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-5">Entrar na sua conta</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-white/60 block mb-1.5">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                className="w-full h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-white/60 block mb-1.5">Senha</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl text-sm transition-colors disabled:opacity-50 mt-2"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-white/30 mt-4">
          Não tem conta?{' '}
          <a href="/cadastro" className="text-[#6366f1] font-medium hover:text-[#818cf8] transition-colors">
            Criar agora — 14 dias grátis
          </a>
        </p>
        <p className="text-center mt-2">
          <a href="/" className="text-white/20 text-xs hover:text-white/40 transition-colors">
            ← Voltar ao início
          </a>
        </p>
      </div>
    </div>
  )
}