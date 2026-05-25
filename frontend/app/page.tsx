'use client'
// frontend/app/page.tsx
// Landing page do Beauti — substitui o redirect simples
// Mostra o produto e converte novos clientes

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Scissors, MessageCircle, Calendar, Users, TrendingUp,
  Package, Star, ChevronRight, Check, Menu, X,
  Smartphone, Zap, Shield, Clock, BarChart3, Sparkles,
  ArrowRight, Play
} from 'lucide-react'

// ── Dados ──────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: MessageCircle,
    title: 'Agente WhatsApp com IA',
    desc: 'Seu assistente inteligente agenda, cancela e responde clientes 24h — sem você precisar digitar nada.',
    highlight: true,
    badge: 'Exclusivo',
    color: '#25D366',
  },
  {
    icon: Calendar,
    title: 'Agenda online inteligente',
    desc: 'Clientes agendam pelo link, WhatsApp ou painel. Slots calculados pela duração real do serviço.',
    highlight: false,
    color: '#6366F1',
  },
  {
    icon: Users,
    title: 'CRM de clientes',
    desc: 'Histórico completo, aniversariantes da semana, clientes inativos e programa de fidelidade.',
    highlight: false,
    color: '#8B5CF6',
  },
  {
    icon: TrendingUp,
    title: 'Financeiro completo',
    desc: 'Caixa do dia, relatório mensal, comissões automáticas e controle de estoque integrado.',
    highlight: false,
    color: '#10B981',
  },
  {
    icon: Package,
    title: 'Comanda digital',
    desc: 'Abertura automática ao atender. Adicione produtos, aplique descontos e feche com 1 toque.',
    highlight: false,
    color: '#F59E0B',
  },
  {
    icon: Smartphone,
    title: 'PWA — funciona como app',
    desc: 'Instale na tela do celular sem App Store. Funciona no Android, iPhone e notebook da recepção.',
    highlight: false,
    color: '#EC4899',
  },
]

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    desc: 'Para começar',
    price: 99.90,
    professionals: 1,
    features: [
      'Agendamento online',
      'Agente WhatsApp IA',
      'Link público',
      'Lembretes automáticos',
      'Histórico de clientes',
      'Comanda digital',
    ],
    recommended: false,
    cta: 'Começar grátis',
  },
  {
    id: 'pro',
    name: 'Pro',
    desc: 'Mais popular',
    price: 149.90,
    professionals: 5,
    features: [
      'Tudo do Starter',
      'Até 5 profissionais',
      'Lista de espera',
      'Pacotes e assinaturas',
      'Financeiro completo',
      'Comissões automáticas',
      'CRM completo',
      'Relatórios avançados',
    ],
    recommended: true,
    cta: 'Começar grátis',
  },
  {
    id: 'advanced',
    name: 'Advanced',
    desc: 'Para crescer',
    price: 199.90,
    professionals: 15,
    features: [
      'Tudo do Pro',
      'Até 15 profissionais',
      'Disparo de promoções',
      'Insights com IA',
      'Domínio customizado',
    ],
    recommended: false,
    cta: 'Começar grátis',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    desc: 'Redes e franquias',
    price: 279.90,
    professionals: 999,
    features: [
      'Tudo do Advanced',
      'Profissionais ilimitados',
      'Suporte dedicado',
      'Onboarding assistido',
      'SLA garantido',
    ],
    recommended: false,
    cta: 'Falar com especialista',
  },
]

const FAQS = [
  {
    q: 'Preciso baixar algum aplicativo?',
    a: 'Não. O Beauti funciona direto no navegador em qualquer dispositivo. Você pode "instalar" como app na tela do celular com 1 toque — sem App Store, sem Google Play.',
  },
  {
    q: 'Como funciona o agente WhatsApp?',
    a: 'O agente é uma IA que responde seus clientes no WhatsApp, mostra horários disponíveis, cria e cancela agendamentos automaticamente. Você configura o nome, o tom e ele trabalha por você 24h.',
  },
  {
    q: 'Posso testar sem cartão de crédito?',
    a: 'Sim. 14 dias grátis com todas as funcionalidades liberadas. Sem cartão, sem compromisso.',
  },
  {
    q: 'Funciona para salão de beleza e studio?',
    a: 'Sim. O Beauti foi desenvolvido para barbearias, salões de beleza e studios. Cada tipo tem configurações específicas.',
  },
  {
    q: 'E se eu já usar o AppBarber ou outro sistema?',
    a: 'A migração é simples. Nossa equipe te ajuda a importar clientes e configurar tudo. O período de trial existe exatamente para você comparar sem pressão.',
  },
  {
    q: 'Quantos profissionais posso cadastrar?',
    a: 'Depende do plano. Starter: 1. Pro: até 5. Advanced: até 15. Enterprise: ilimitado.',
  },
]

const DIFFERENTIALS = [
  { icon: Zap,     title: 'IA nativa',        desc: 'Agente WhatsApp com GPT-4 — não é um bot simples' },
  { icon: Shield,  title: 'Sem app obrigatório', desc: 'Cliente agenda pelo link ou WhatsApp. Sem fricção.' },
  { icon: Clock,   title: '14 dias grátis',    desc: 'Teste tudo sem cartão. Decida depois.' },
  { icon: BarChart3, title: 'Gestão completa', desc: 'Do agendamento ao financeiro em um lugar só' },
]

// ── Componentes ────────────────────────────────────────────────

function NavBar() {
  const router  = useRouter()
  const [open, setOpen]   = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? 'bg-[#0A0A0F]/95 backdrop-blur-md border-b border-white/5' : 'bg-transparent'
    }`}>
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center">
            <Scissors size={16} className="text-white" />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">Beauti</span>
        </div>

        {/* Nav desktop */}
        <nav className="hidden md:flex items-center gap-8">
          {['Funcionalidades', 'Planos', 'FAQ'].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="text-white/60 hover:text-white text-sm font-medium transition-colors"
            >
              {item}
            </a>
          ))}
        </nav>

        {/* CTAs */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={() => router.push('/login')}
            className="text-white/70 hover:text-white text-sm font-medium transition-colors px-4 py-2"
          >
            Entrar
          </button>
          <button
            onClick={() => router.push('/cadastro')}
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-sm font-semibold px-5 py-2 rounded-lg transition-colors"
          >
            Testar grátis
          </button>
        </div>

        {/* Mobile menu */}
        <button onClick={() => setOpen(!open)} className="md:hidden text-white p-2">
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className="md:hidden bg-[#0A0A0F]/98 border-b border-white/5 px-4 pb-4">
          <nav className="flex flex-col gap-4 pt-4">
            {['Funcionalidades', 'Planos', 'FAQ'].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                onClick={() => setOpen(false)}
                className="text-white/70 text-base font-medium"
              >
                {item}
              </a>
            ))}
            <div className="flex flex-col gap-2 pt-2 border-t border-white/10">
              <button onClick={() => router.push('/login')} className="text-white/70 text-base py-2 text-left">
                Entrar na minha conta
              </button>
              <button
                onClick={() => router.push('/cadastro')}
                className="bg-[#6366F1] text-white text-base font-semibold py-3 rounded-lg"
              >
                Testar 14 dias grátis
              </button>
            </div>
          </nav>
        </div>
      )}
    </header>
  )
}

function HeroSection() {
  const router = useRouter()
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0A0A0F]">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:64px_64px]" />

      {/* Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-[#6366F1]/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/4 w-[300px] h-[300px] bg-[#8B5CF6]/15 rounded-full blur-[80px] pointer-events-none" />

      <div className="relative max-w-5xl mx-auto px-4 pt-24 pb-16 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 mb-8">
          <Sparkles size={14} className="text-[#6366F1]" />
          <span className="text-white/70 text-sm font-medium">Agente WhatsApp com IA nativo</span>
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-black text-white leading-[1.05] tracking-tight mb-6">
          Sua barbearia
          <br />
          <span className="bg-gradient-to-r from-[#6366F1] via-[#8B5CF6] to-[#EC4899] bg-clip-text text-transparent">
            no próximo nível.
          </span>
        </h1>

        {/* Subheadline */}
        <p className="text-white/60 text-xl md:text-2xl max-w-2xl mx-auto leading-relaxed mb-10">
          Agenda online, agente WhatsApp com IA e gestão completa.
          <br className="hidden md:block" />
          <strong className="text-white/80"> Sem app obrigatório. Sem complicação.</strong>
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <button
            onClick={() => router.push('/cadastro')}
            className="group flex items-center gap-2 bg-[#6366F1] hover:bg-[#4F46E5] text-white font-bold text-lg px-8 py-4 rounded-xl transition-all shadow-[0_0_40px_rgba(99,102,241,0.4)] hover:shadow-[0_0_60px_rgba(99,102,241,0.6)] hover:scale-[1.02]"
          >
            Testar 14 dias grátis
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </button>
          <button
            onClick={() => router.push('/b')}
            className="flex items-center gap-2 text-white/60 hover:text-white font-medium text-lg px-6 py-4 rounded-xl border border-white/10 hover:border-white/20 transition-all"
          >
            <Play size={18} />
            Ver demonstração
          </button>
        </div>

        {/* Social proof */}
        <div className="flex flex-wrap items-center justify-center gap-8 text-white/40 text-sm">
          <div className="flex items-center gap-2">
            <div className="flex -space-x-2">
              {['#6366F1','#8B5CF6','#EC4899','#10B981'].map((c, i) => (
                <div key={i} className="w-7 h-7 rounded-full border-2 border-[#0A0A0F]" style={{ background: c }} />
              ))}
            </div>
            <span>+500 estabelecimentos</span>
          </div>
          <div className="flex items-center gap-1">
            {[1,2,3,4,5].map(i => <Star key={i} size={14} className="fill-[#F59E0B] text-[#F59E0B]" />)}
            <span className="ml-1">4.9 de satisfação</span>
          </div>
          <div>14 dias grátis · Sem cartão</div>
        </div>
      </div>
    </section>
  )
}

function DifferentialsSection() {
  return (
    <section className="bg-[#0A0A0F] py-16 border-y border-white/5">
      <div className="max-w-5xl mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {DIFFERENTIALS.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="text-center">
              <div className="w-12 h-12 rounded-xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center mx-auto mb-3">
                <Icon size={22} className="text-[#6366F1]" />
              </div>
              <div className="text-white font-semibold text-sm mb-1">{title}</div>
              <div className="text-white/40 text-xs leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function FeaturesSection() {
  return (
    <section id="funcionalidades" className="bg-[#0D0D14] py-24">
      <div className="max-w-5xl mx-auto px-4">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-[#6366F1]/10 border border-[#6366F1]/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-[#6366F1] text-sm font-medium">Tudo que você precisa</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
            Gestão completa.<br />
            <span className="text-white/40">Sem complexidade.</span>
          </h2>
          <p className="text-white/50 text-lg max-w-xl mx-auto">
            Cada funcionalidade foi pensada para o dia a dia real de barbearias, salões e studios.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc, highlight, badge, color }) => (
            <div
              key={title}
              className={`relative rounded-2xl p-6 border transition-all duration-300 hover:-translate-y-1 ${
                highlight
                  ? 'bg-gradient-to-br from-[#6366F1]/20 to-[#8B5CF6]/10 border-[#6366F1]/40'
                  : 'bg-white/[0.03] border-white/[0.06] hover:border-white/10'
              }`}
            >
              {badge && (
                <span className="absolute top-4 right-4 bg-[#6366F1] text-white text-xs font-bold px-2.5 py-1 rounded-full">
                  {badge}
                </span>
              )}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                style={{ background: `${color}18`, border: `1px solid ${color}30` }}
              >
                <Icon size={22} style={{ color }} />
              </div>
              <h3 className="text-white font-bold text-lg mb-2">{title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function ComparisonSection() {
  return (
    <section className="bg-[#0A0A0F] py-24">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-white mb-3">
            Por que o Beauti?
          </h2>
          <p className="text-white/50">Comparado com as alternativas do mercado</p>
        </div>
        <div className="rounded-2xl border border-white/10 overflow-hidden">
          <div className="grid grid-cols-3 bg-white/[0.03] border-b border-white/10">
            <div className="p-4 text-white/40 text-sm font-medium">Funcionalidade</div>
            <div className="p-4 text-center">
              <div className="inline-flex items-center gap-1.5">
                <div className="w-5 h-5 rounded bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center">
                  <Scissors size={10} className="text-white" />
                </div>
                <span className="text-white font-bold text-sm">Beauti</span>
              </div>
            </div>
            <div className="p-4 text-white/30 text-sm font-medium text-center">Concorrentes</div>
          </div>
          {[
            ['Agente WhatsApp com IA nativa', true, false],
            ['Agenda sem app obrigatório',    true, false],
            ['Comanda digital integrada',     true, true],
            ['Controle de estoque',           true, true],
            ['PWA — instala sem App Store',   true, false],
            ['Link público de agendamento',   true, true],
            ['CRM com insights automáticos',  true, false],
            ['Trial sem cartão de crédito',   true, true],
          ].map(([feat, beauti, concorrente]) => (
            <div key={feat as string} className="grid grid-cols-3 border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02] transition-colors">
              <div className="p-4 text-white/60 text-sm">{feat as string}</div>
              <div className="p-4 flex justify-center">
                {beauti
                  ? <Check size={18} className="text-[#10B981]" />
                  : <X size={18} className="text-white/20" />}
              </div>
              <div className="p-4 flex justify-center">
                {concorrente
                  ? <Check size={18} className="text-white/30" />
                  : <X size={18} className="text-red-500/50" />}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function PlansSection() {
  const router = useRouter()
  return (
    <section id="planos" className="bg-[#0D0D14] py-24">
      <div className="max-w-5xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
            Planos e preços
          </h2>
          <p className="text-white/50 text-lg">
            14 dias grátis em qualquer plano. Sem cartão de crédito.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`relative rounded-2xl p-6 flex flex-col transition-all duration-300 hover:-translate-y-1 ${
                plan.recommended
                  ? 'bg-gradient-to-b from-[#6366F1] to-[#4F46E5] border border-[#6366F1]'
                  : 'bg-white/[0.03] border border-white/[0.07] hover:border-white/10'
              }`}
            >
              {plan.recommended && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#F59E0B] text-black text-xs font-black px-3 py-1 rounded-full whitespace-nowrap">
                  ⭐ Mais escolhido
                </div>
              )}

              <div className="mb-5">
                <div className={`text-sm font-medium mb-1 ${plan.recommended ? 'text-white/70' : 'text-white/40'}`}>
                  {plan.desc}
                </div>
                <div className={`text-2xl font-black ${plan.recommended ? 'text-white' : 'text-white'}`}>
                  {plan.name}
                </div>
                <div className="flex items-end gap-1 mt-3">
                  <span className={`text-xs ${plan.recommended ? 'text-white/70' : 'text-white/40'}`}>R$</span>
                  <span className={`text-4xl font-black leading-none ${plan.recommended ? 'text-white' : 'text-white'}`}>
                    {plan.price.toFixed(0)}
                  </span>
                  <span className={`text-sm pb-1 ${plan.recommended ? 'text-white/70' : 'text-white/40'}`}>/mês</span>
                </div>
                <div className={`text-xs mt-1 ${plan.recommended ? 'text-white/60' : 'text-white/30'}`}>
                  {plan.professionals === 999 ? 'Profissionais ilimitados' : `Até ${plan.professionals} profissional${plan.professionals > 1 ? 'is' : ''}`}
                </div>
              </div>

              <ul className="flex-1 space-y-2.5 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <Check size={14} className={`mt-0.5 flex-shrink-0 ${plan.recommended ? 'text-white' : 'text-[#6366F1]'}`} />
                    <span className={`text-sm ${plan.recommended ? 'text-white/80' : 'text-white/50'}`}>{f}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => router.push('/cadastro')}
                className={`w-full py-3 rounded-xl font-bold text-sm transition-all ${
                  plan.recommended
                    ? 'bg-white text-[#4F46E5] hover:bg-white/90'
                    : 'bg-white/[0.07] text-white hover:bg-white/10 border border-white/10'
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-white/30 text-sm mt-8">
          Planos semestrais e anuais com até 30% de desconto · Pagamento via PIX, boleto ou cartão
        </p>
      </div>
    </section>
  )
}

function FAQSection() {
  const [open, setOpen] = useState<number | null>(null)
  return (
    <section id="faq" className="bg-[#0A0A0F] py-24">
      <div className="max-w-2xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-black text-white mb-3">Dúvidas frequentes</h2>
          <p className="text-white/50">Tudo que você precisa saber antes de começar</p>
        </div>
        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className="rounded-xl border border-white/[0.07] overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between p-5 text-left hover:bg-white/[0.03] transition-colors"
              >
                <span className="text-white font-medium text-sm pr-4">{faq.q}</span>
                <ChevronRight
                  size={16}
                  className={`flex-shrink-0 text-white/40 transition-transform duration-200 ${open === i ? 'rotate-90' : ''}`}
                />
              </button>
              {open === i && (
                <div className="px-5 pb-5 text-white/50 text-sm leading-relaxed border-t border-white/[0.05] pt-4">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTASection() {
  const router = useRouter()
  return (
    <section className="bg-[#0D0D14] py-24">
      <div className="max-w-3xl mx-auto px-4 text-center">
        <div className="relative rounded-3xl overflow-hidden p-12 bg-gradient-to-br from-[#6366F1]/30 via-[#8B5CF6]/20 to-[#EC4899]/10 border border-[#6366F1]/30">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff06_1px,transparent_1px),linear-gradient(to_bottom,#ffffff06_1px,transparent_1px)] bg-[size:32px_32px]" />
          <div className="relative">
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              Comece hoje.<br />É grátis.
            </h2>
            <p className="text-white/60 text-lg mb-8 max-w-lg mx-auto">
              14 dias com todas as funcionalidades liberadas. Sem cartão de crédito. Cancele quando quiser.
            </p>
            <button
              onClick={() => router.push('/cadastro')}
              className="group inline-flex items-center gap-2 bg-white text-[#4F46E5] font-black text-lg px-10 py-4 rounded-xl hover:bg-white/90 transition-all shadow-[0_0_60px_rgba(99,102,241,0.4)] hover:scale-[1.02]"
            >
              Criar conta gratuita
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <p className="text-white/30 text-sm mt-4">
              Barbearias · Salões de beleza · Studios
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="bg-[#0A0A0F] border-t border-white/5 py-12">
      <div className="max-w-5xl mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center">
              <Scissors size={14} className="text-white" />
            </div>
            <span className="text-white font-bold">Beauti</span>
            <span className="text-white/20 text-sm">Sistema de gestão para o setor beauty</span>
          </div>
          <div className="flex items-center gap-6 text-white/30 text-sm">
            <a href="#" className="hover:text-white/60 transition-colors">Termos de uso</a>
            <a href="#" className="hover:text-white/60 transition-colors">Privacidade</a>
            <a href="/login" className="hover:text-white/60 transition-colors">Entrar</a>
          </div>
        </div>
        <div className="text-center text-white/20 text-xs mt-8">
          © 2026 Beauti. Todos os direitos reservados.
        </div>
      </div>
    </footer>
  )
}

// ── Page ───────────────────────────────────────────────────────

export default function LandingPage() {
  return (
    <main>
      <NavBar />
      <HeroSection />
      <DifferentialsSection />
      <FeaturesSection />
      <ComparisonSection />
      <PlansSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </main>
  )
}