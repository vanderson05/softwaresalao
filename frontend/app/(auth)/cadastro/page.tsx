'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi, setAuthTokens } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { toast } from 'sonner'

export default function CadastroPage() {
  const router  = useRouter()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    business_name: '', phone: '', email: '', password: '', type: 'barbershop',
  })

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.register(form)
      const { data } = await authApi.login({ email: form.email, password: form.password })
      setAuthTokens(data.tokens.access, data.tokens.refresh)
      setAuth(data.user, data.tenant, data.role)
      toast.success('Conta criada! Vamos configurar sua barbearia.')
      router.replace('/setup')
    } catch (err: any) {
      const errors = err.response?.data
      toast.error(errors?.email?.[0] || errors?.error || 'Erro ao criar conta.')
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
          <h1 className="text-2xl font-bold text-white">Criar conta grátis</h1>
          <p className="text-white/40 text-sm mt-1">14 dias grátis · Sem cartão de crédito</p>
        </div>

        <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { field: 'business_name', label: 'Nome da barbearia', placeholder: 'Barbearia do Carlão', type: 'text' },
              { field: 'phone', label: 'Telefone (WhatsApp)', placeholder: '19999999999', type: 'text' },
              { field: 'email', label: 'E-mail', placeholder: 'seu@email.com', type: 'email' },
              { field: 'password', label: 'Senha', placeholder: 'Mínimo 8 caracteres', type: 'password' },
            ].map(({ field, label, placeholder, type }) => (
              <div key={field}>
                <label className="text-sm font-medium text-white/60 block mb-1.5">{label}</label>
                <input
                  type={type}
                  value={form[field as keyof typeof form]}
                  onChange={(e) => update(field, e.target.value)}
                  placeholder={placeholder}
                  required
                  className="w-full h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder-white/20 text-sm focus:outline-none focus:border-[#6366f1]/60 focus:ring-1 focus:ring-[#6366f1]/40 transition-colors"
                />
              </div>
            ))}

            <div>
              <label className="text-sm font-medium text-white/60 block mb-1.5">Tipo de estabelecimento</label>
              <select
                value={form.type}
                onChange={(e) => update('type', e.target.value)}
                className="w-full h-11 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white text-sm focus:outline-none focus:border-[#6366f1]/60 transition-colors"
              >
                <option value="barbershop" className="bg-[#0A0A0F]">Barbearia</option>
                <option value="salon" className="bg-[#0A0A0F]">Salão de beleza</option>
                <option value="studio" className="bg-[#0A0A0F]">Studio</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold rounded-xl text-sm transition-colors disabled:opacity-50 mt-2"
            >
              {loading ? 'Criando conta...' : 'Criar conta grátis →'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-white/30 mt-4">
          Já tem conta?{' '}
          <a href="/login" className="text-[#6366f1] font-medium hover:text-[#818cf8] transition-colors">
            Entrar
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