"""
setup_frontend.py
Cria toda a estrutura do frontend Next.js automaticamente.
Rodar na raiz do projeto: python setup_frontend.py
"""

import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

files = {}

# ── package.json ──────────────────────────────────────────────
files['package.json'] = '''{
  "name": "beauti-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "^18",
    "react-dom": "^18",
    "next-pwa": "^5.6.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-switch": "^1.0.3",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "lucide-react": "^0.383.0",
    "axios": "^1.7.2",
    "zustand": "^4.5.2",
    "react-hook-form": "^7.51.5",
    "zod": "^3.23.8",
    "@hookform/resolvers": "^3.6.0",
    "date-fns": "^3.6.0",
    "react-day-picker": "^8.10.1",
    "recharts": "^2.12.7",
    "sonner": "^1.5.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.4.1",
    "eslint": "^8",
    "eslint-config-next": "14.2.3"
  }
}
'''

# ── next.config.js ────────────────────────────────────────────
files['next.config.js'] = """/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
})

const nextConfig = {
  images: {
    domains: ['softwaresalao.onrender.com', 'res.cloudinary.com'],
  },
}

module.exports = withPWA(nextConfig)
"""

# ── tsconfig.json ─────────────────────────────────────────────
files['tsconfig.json'] = '''{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
'''

# ── postcss.config.js ─────────────────────────────────────────
files['postcss.config.js'] = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

# ── tailwind.config.ts ────────────────────────────────────────
files['tailwind.config.ts'] = """import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border:     'hsl(var(--border))',
        input:      'hsl(var(--input))',
        ring:       'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT:    'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT:    'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        beauti: {
          50:  '#eef2ff',
          500: '#6366f1',
          600: '#4f46e5',
          900: '#312e81',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
"""

# ── .env.local ────────────────────────────────────────────────
files['.env.local'] = """NEXT_PUBLIC_API_URL=https://softwaresalao.onrender.com
"""

# ── app/globals.css ───────────────────────────────────────────
files['app/globals.css'] = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background:          0 0% 98%;
    --foreground:          222 47% 11%;
    --card:                0 0% 100%;
    --card-foreground:     222 47% 11%;
    --popover:             0 0% 100%;
    --popover-foreground:  222 47% 11%;
    --primary:             239 84% 67%;
    --primary-foreground:  0 0% 100%;
    --secondary:           220 14% 96%;
    --secondary-foreground: 222 47% 11%;
    --muted:               220 14% 96%;
    --muted-foreground:    220 9% 46%;
    --accent:              239 84% 67%;
    --accent-foreground:   0 0% 100%;
    --destructive:         0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --border:              220 13% 91%;
    --input:               220 13% 91%;
    --ring:                239 84% 67%;
    --radius:              0.75rem;
  }

  * { @apply border-border; }

  body {
    @apply bg-background text-foreground antialiased;
    font-family: 'Inter', system-ui, sans-serif;
  }

  * { -webkit-tap-highlight-color: transparent; }
}

@layer components {
  .status-pending    { @apply bg-amber-100 text-amber-700 border-amber-200; }
  .status-confirmed  { @apply bg-indigo-100 text-indigo-700 border-indigo-200; }
  .status-completed  { @apply bg-emerald-100 text-emerald-700 border-emerald-200; }
  .status-cancelled  { @apply bg-red-100 text-red-700 border-red-200; }
  .status-no-show    { @apply bg-slate-100 text-slate-600 border-slate-200; }
  .status-in-comanda { @apply bg-purple-100 text-purple-700 border-purple-200; }
  .beauti-card       { @apply bg-card rounded-xl border border-border shadow-sm; }
}
"""

# ── app/layout.tsx ────────────────────────────────────────────
files['app/layout.tsx'] = """import type { Metadata, Viewport } from 'next'
import { Toaster } from 'sonner'
import './globals.css'

export const metadata: Metadata = {
  title: { default: 'Beauti', template: '%s | Beauti' },
  description: 'Sistema de gestão para barbearias e salões.',
  manifest: '/manifest.json',
  appleWebApp: { capable: true, statusBarStyle: 'default', title: 'Beauti' },
}

export const viewport: Viewport = {
  themeColor:   '#6366F1',
  width:        'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit:  'cover',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {children}
        <Toaster position="top-center" richColors />
      </body>
    </html>
  )
}
"""

# ── app/page.tsx ──────────────────────────────────────────────
files['app/page.tsx'] = """'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('beauti_token')
    router.replace(token ? '/painel' : '/login')
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-8 h-8 border-2 border-[#6366f1] border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
"""

# ── app/(auth)/login/page.tsx ─────────────────────────────────
files['app/(auth)/login/page.tsx'] = """'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { authApi, setAuthTokens } from '@/lib/api'
import { toast } from 'sonner'

export default function LoginPage() {
  const router   = useRouter()
  const setAuth  = useAuthStore((s) => s.setAuth)
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [loading,  setLoading]  = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await authApi.login({ email, password })
      setAuthTokens(data.tokens.access, data.tokens.refresh)
      setAuth(data.user, data.tenant, data.role)
      toast.success('Bem-vindo de volta!')
      router.replace(data.tenant.setup_completed ? '/painel' : '/setup')
    } catch (err: any) {
      toast.error(err.response?.data?.error || 'E-mail ou senha incorretos.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#6366f1] mb-4">
            <span className="text-white text-2xl font-bold">B</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Beauti</h1>
          <p className="text-muted-foreground text-sm mt-1">Gestão de barbearias</p>
        </div>

        {/* Form */}
        <div className="beauti-card p-6">
          <h2 className="text-lg font-semibold mb-4">Entrar na sua conta</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Senha</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full h-10 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-medium rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-4">
          Não tem conta?{' '}
          <a href="/cadastro" className="text-[#6366f1] font-medium hover:underline">
            Criar agora
          </a>
        </p>
      </div>
    </div>
  )
}
"""

# ── app/(auth)/cadastro/page.tsx ──────────────────────────────
files['app/(auth)/cadastro/page.tsx'] = """'use client'
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
    business_name: '',
    phone:         '',
    email:         '',
    password:      '',
    type:          'barbershop',
  })

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.register(form)
      toast.success('Conta criada! Fazendo login...')
      const { data } = await authApi.login({ email: form.email, password: form.password })
      setAuthTokens(data.tokens.access, data.tokens.refresh)
      setAuth(data.user, data.tenant, data.role)
      router.replace('/setup')
    } catch (err: any) {
      const errors = err.response?.data
      const msg = errors?.email?.[0] || errors?.error || 'Erro ao criar conta.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#6366f1] mb-4">
            <span className="text-white text-2xl font-bold">B</span>
          </div>
          <h1 className="text-2xl font-bold">Criar conta gratuita</h1>
          <p className="text-muted-foreground text-sm mt-1">14 dias grátis, sem cartão</p>
        </div>

        <div className="beauti-card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-1.5">Nome da barbearia</label>
              <input
                value={form.business_name}
                onChange={(e) => update('business_name', e.target.value)}
                placeholder="Barbearia do Carlão"
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">Telefone (WhatsApp)</label>
              <input
                value={form.phone}
                onChange={(e) => update('phone', e.target.value)}
                placeholder="19999999999"
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">E-mail</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                placeholder="seu@email.com"
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">Senha</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                placeholder="Mínimo 8 caracteres"
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">Tipo</label>
              <select
                value={form.type}
                onChange={(e) => update('type', e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="barbershop">Barbearia</option>
                <option value="salon">Salão de beleza</option>
                <option value="studio">Studio</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full h-10 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-medium rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Criando conta...' : 'Criar conta grátis'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-4">
          Já tem conta?{' '}
          <a href="/login" className="text-[#6366f1] font-medium hover:underline">Entrar</a>
        </p>
      </div>
    </div>
  )
}
"""

# ── lib/api.ts ────────────────────────────────────────────────
files['lib/api.ts'] = """import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://softwaresalao.onrender.com'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('beauti_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('beauti_refresh')
        if (!refresh) throw new Error('no refresh')
        const { data } = await axios.post(`${API_URL}/api/token/refresh/`, { refresh })
        localStorage.setItem('beauti_token', data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const clientApi = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

clientApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('beauti_client_token')
    if (token) config.headers.Authorization = `ClientBearer ${token}`
  }
  return config
})

export const getOwnerToken   = () => typeof window !== 'undefined' ? localStorage.getItem('beauti_token') : null
export const getRefreshToken = () => typeof window !== 'undefined' ? localStorage.getItem('beauti_refresh') : null
export const getClientToken  = () => typeof window !== 'undefined' ? localStorage.getItem('beauti_client_token') : null
export const setAuthTokens   = (access: string, refresh: string) => { localStorage.setItem('beauti_token', access); localStorage.setItem('beauti_refresh', refresh) }
export const setClientToken  = (token: string) => localStorage.setItem('beauti_client_token', token)
export const clearAuth       = () => { localStorage.removeItem('beauti_token'); localStorage.removeItem('beauti_refresh') }

export const authApi = {
  login:    (data: any) => api.post('/auth/login/', data),
  register: (data: any) => api.post('/auth/register/', data),
  me:       ()          => api.get('/auth/me/'),
}

export const setupApi = {
  status:             ()          => api.get('/setup/status/'),
  establishment:      ()          => api.get('/setup/establishment/'),
  updateEstablishment:(data: any) => api.patch('/setup/establishment/', data),
  complete:           ()          => api.post('/setup/complete/'),
}

export const professionalsApi = {
  list:         ()                       => api.get('/professionals/'),
  create:       (data: any)              => api.post('/professionals/', data),
  update:       (id: string, data: any)  => api.patch(`/professionals/${id}/`, data),
  delete:       (id: string)             => api.delete(`/professionals/${id}/`),
  scheduleBulk: (data: any)              => api.post('/schedules/bulk/', data),
  schedules:    (id: string)             => api.get(`/professionals/${id}/schedules/`),
}

export const servicesApi = {
  list:   ()                      => api.get('/services/'),
  create: (data: any)             => api.post('/services/', data),
  update: (id: string, data: any) => api.patch(`/services/${id}/`, data),
  delete: (id: string)            => api.delete(`/services/${id}/`),
}

export const appointmentsApi = {
  list:       (params?: any) => api.get('/appointments/', { params }),
  create:     (data: any)    => api.post('/appointments/', data),
  confirm:    (id: string)   => api.post(`/appointments/${id}/confirm/`),
  cancel:     (id: string, data?: any) => api.post(`/appointments/${id}/cancel/`, data),
  noShow:     (id: string)   => api.post(`/appointments/${id}/no-show/`),
  agendaDay:  (params?: any) => api.get('/agenda/day/', { params }),
  agendaWeek: (params?: any) => api.get('/agenda/week/', { params }),
}

export const slotsApi = {
  get:  (params: any) => api.get('/slots/', { params }),
  next: (params: any) => api.get('/slots/next/', { params }),
}

export const financialApi = {
  products:      (params?: any)              => api.get('/financial/products/', { params }),
  createProduct: (data: any)                 => api.post('/financial/products/', data),
  addStock:      (id: string, data: any)     => api.post(`/financial/products/${id}/stock/`, data),
  stockAlerts:   ()                          => api.get('/financial/stock/alerts/'),
  comanda:       (id: string)                => api.get(`/financial/appointments/${id}/comanda/`),
  addItem:       (id: string, data: any)     => api.post(`/financial/appointments/${id}/comanda/`, data),
  editItem:      (id: string, data: any)     => api.patch(`/financial/comanda/items/${id}/`, data),
  removeItem:    (id: string)                => api.delete(`/financial/comanda/items/${id}/`),
  checkout:      (id: string, data: any)     => api.post(`/financial/appointments/${id}/checkout/`, data),
  cashbox:       (params?: any)              => api.get('/financial/cashbox/', { params }),
  reportMonthly: (params?: any)              => api.get('/financial/report/monthly/', { params }),
  commissions:   (params?: any)              => api.get('/financial/commissions/', { params }),
}

export const crmApi = {
  clients:            (params?: any)             => api.get('/crm/clients/', { params }),
  client:             (id: string)               => api.get(`/crm/clients/${id}/`),
  updateClient:       (id: string, data: any)    => api.patch(`/crm/clients/${id}/`, data),
  summary:            ()                         => api.get('/crm/insights/summary/'),
  inactive:           (params?: any)             => api.get('/crm/insights/inactive/', { params }),
  birthdays:          ()                         => api.get('/crm/insights/birthdays/'),
  top:                (params?: any)             => api.get('/crm/insights/top/', { params }),
  subscriptions:      (params?: any)             => api.get('/crm/subscriptions/', { params }),
  createSubscription: (data: any)                => api.post('/crm/subscriptions/', data),
  renewSubscription:  (id: string, data: any)    => api.post(`/crm/subscriptions/${id}/renew/`, data),
}

export const agentApi = {
  config:       ()          => api.get('/agent/config/'),
  updateConfig: (data: any) => api.patch('/agent/config/', data),
  test:         (msg: string) => api.post('/agent/test/', { message: msg }),
  conversations:(params?: any) => api.get('/agent/conversations/', { params }),
}

export const publicApi = {
  home:              (params?: any)          => clientApi.get('/b/', { params }),
  profile:           (slug: string)          => clientApi.get(`/b/${slug}/`),
  services:          (slug: string)          => clientApi.get(`/b/${slug}/services/`),
  professionals:     (slug: string)          => clientApi.get(`/b/${slug}/professionals/`),
  requestCode:       (slug: string, phone: string) => clientApi.post(`/b/${slug}/auth/request-code/`, { phone }),
  verifyCode:        (slug: string, data: any)     => clientApi.post(`/b/${slug}/auth/verify-code/`, data),
  slots:             (slug: string, params: any)   => clientApi.get(`/b/${slug}/slots/`, { params }),
  book:              (slug: string, data: any)     => clientApi.post(`/b/${slug}/book/`, data),
  myAppointments:    (slug: string)          => clientApi.get(`/b/${slug}/my-appointments/`),
  cancelAppointment: (slug: string, id: string) => clientApi.post(`/b/${slug}/my-appointments/${id}/cancel/`),
}

export default api
"""

# ── lib/store.ts ──────────────────────────────────────────────
files['lib/store.ts'] = """import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  user:        any | null
  tenant:      any | null
  role:        string | null
  setAuth:     (user: any, tenant: any, role: string) => void
  setTenant:   (tenant: any) => void
  clearAuth:   () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user:     null,
      tenant:   null,
      role:     null,
      setAuth:  (user, tenant, role) => set({ user, tenant, role }),
      setTenant:(tenant) => set({ tenant }),
      clearAuth:() => set({ user: null, tenant: null, role: null }),
    }),
    { name: 'beauti_auth' }
  )
)

interface AgendaState {
  selectedDate:         string
  selectedProfessional: string | null
  view:                 'day' | 'week'
  setDate:              (date: string) => void
  setProfessional:      (id: string | null) => void
  setView:              (view: 'day' | 'week') => void
}

export const useAgendaStore = create<AgendaState>()((set) => ({
  selectedDate:         new Date().toISOString().split('T')[0],
  selectedProfessional: null,
  view:                 'day',
  setDate:              (selectedDate) => set({ selectedDate }),
  setProfessional:      (selectedProfessional) => set({ selectedProfessional }),
  setView:              (view) => set({ view }),
}))
"""

# ── public/manifest.json ──────────────────────────────────────
files['public/manifest.json'] = """{
  "name": "Beauti",
  "short_name": "Beauti",
  "description": "Gestão de barbearias",
  "start_url": "/painel",
  "display": "standalone",
  "background_color": "#0F172A",
  "theme_color": "#6366F1",
  "icons": [
    { "src": "/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "lang": "pt-BR"
}
"""

# ── Criar arquivos ────────────────────────────────────────────
def write(rel_path, content):
    full = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {rel_path}")

print("\n🚀 Criando estrutura do frontend Beauti...\n")
for path, content in files.items():
    write(path, content)

print(f"\n✅ {len(files)} arquivos criados em {BASE}")
print("\nPróximos passos:")
print("  cd frontend")
print("  npm install")
print("  npx shadcn-ui@latest init")
print("  npm run dev\n")
