'use client'
// app/painel/planos/page.tsx
// Página de planos — exibida quando trial expira ou usuário clica "Ver planos"

import { useAuthStore } from '@/lib/store'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { Check, Zap, Crown, Building2, Rocket } from 'lucide-react'

const PLANS = [
  {
    key:         'starter',
    name:        'Starter',
    price:       99.90,
    profs:       '1 profissional',
    color:       'from-slate-600 to-slate-700',
    badge:       'bg-slate-500/20 text-slate-300 border-slate-500/30',
    icon:        Zap,
    description: 'Ideal para barbeiros autônomos',
    features: [
      'Agenda online ilimitada',
      'Link público de agendamento',
      'Agente WhatsApp IA',
      'Lembretes automáticos',
      'PWA — app no celular',
    ],
    notIncluded: ['CRM de clientes', 'Financeiro', 'Comissões', 'Relatórios'],
  },
  {
    key:         'pro',
    name:        'Pro',
    price:       149.90,
    profs:       'Até 5 profissionais',
    color:       'from-[#6366f1] to-[#8B5CF6]',
    badge:       'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    icon:        Crown,
    description: 'Para barbearias em crescimento',
    highlight:   true,
    features: [
      'Tudo do Starter',
      'CRM completo de clientes',
      'Financeiro e caixa do dia',
      'Comissões dos profissionais',
      'Relatórios mensais',
      'Pacotes e assinaturas',
      'Produtos e estoque',
      'Gestão de equipe',
    ],
    notIncluded: ['Insights IA', 'Domínio customizado'],
  },
  {
    key:         'advanced',
    name:        'Advanced',
    price:       199.90,
    profs:       'Até 15 profissionais',
    color:       'from-purple-600 to-pink-600',
    badge:       'bg-purple-500/20 text-purple-300 border-purple-500/30',
    icon:        Rocket,
    description: 'Para redes de barbearias',
    features: [
      'Tudo do Pro',
      'Insights com IA',
      'Blast de promoções',
      'Domínio customizado',
      'Relatórios avançados',
      'Suporte prioritário',
    ],
    notIncluded: [],
  },
  {
    key:         'enterprise',
    name:        'Enterprise',
    price:       279.90,
    profs:       'Profissionais ilimitados',
    color:       'from-emerald-600 to-teal-600',
    badge:       'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    icon:        Building2,
    description: 'Para grandes operações',
    features: [
      'Tudo do Advanced',
      'SLA garantido',
      'Onboarding assistido',
      'Suporte dedicado',
      'Treinamento da equipe',
      'Integrações customizadas',
    ],
    notIncluded: [],
  },
]

function formatCurrency(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function PlanosPage() {
  const { tenant } = useAuthStore()
  const { plan, isTrial } = usePermissions()

  const trialDays = tenant?.trial_days_remaining ?? 0
  const trialExpired = trialDays <= 0 && isTrial

  return (
    <div className="px-4 py-6 md:px-6 max-w-5xl">
      {/* Header */}
      <div className="text-center mb-8">
        {trialExpired ? (
          <>
            <div className="inline-flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-full px-4 py-2 mb-4">
              <span className="text-red-400 text-sm font-medium">⚠️ Seu trial expirou</span>
            </div>
            <h1 className="text-white font-black text-3xl mb-2">
              Continue usando o Beauti
            </h1>
            <p className="text-white/40 text-base max-w-md mx-auto">
              Escolha um plano para reativar o acesso e continuar gerenciando sua barbearia.
            </p>
          </>
        ) : (
          <>
            <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-full px-4 py-2 mb-4">
              <span className="text-amber-400 text-sm font-medium">
                🕐 Trial — {trialDays} dia{trialDays !== 1 ? 's' : ''} restante{trialDays !== 1 ? 's' : ''}
              </span>
            </div>
            <h1 className="text-white font-black text-3xl mb-2">Escolha seu plano</h1>
            <p className="text-white/40 text-base max-w-md mx-auto">
              Planos a partir de R$99,90/mês. Cancele quando quiser.
            </p>
          </>
        )}
      </div>

      {/* Cards de planos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {PLANS.map(({ key, name, price, profs, color, badge, icon: Icon, description, highlight, features, notIncluded }) => {
          const isCurrent = plan === key

          return (
            <div
              key={key}
              className={`relative flex flex-col bg-white/[0.03] border rounded-2xl overflow-hidden transition-all ${
                highlight
                  ? 'border-[#6366f1]/50 shadow-[0_0_30px_rgba(99,102,241,0.15)]'
                  : isCurrent
                  ? 'border-white/20'
                  : 'border-white/[0.08]'
              }`}
            >
              {highlight && (
                <div className="bg-gradient-to-r from-[#6366f1] to-[#8B5CF6] text-white text-xs font-bold text-center py-1.5 tracking-wide">
                  ⭐ MAIS POPULAR
                </div>
              )}

              {/* Gradiente topo */}
              <div className={`h-1.5 bg-gradient-to-r ${color}`} />

              <div className="p-5 flex flex-col flex-1">
                {/* Header do plano */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-medium mb-2 ${badge}`}>
                      <Icon size={12} />
                      {name}
                    </div>
                    <div className="text-white font-black text-2xl">
                      {formatCurrency(price)}
                      <span className="text-white/30 text-sm font-normal">/mês</span>
                    </div>
                    <div className="text-white/40 text-xs mt-0.5">{profs}</div>
                  </div>
                  {isCurrent && (
                    <span className="text-xs bg-white/10 text-white/50 px-2.5 py-1 rounded-full border border-white/10">
                      Atual
                    </span>
                  )}
                </div>

                <p className="text-white/30 text-xs mb-4">{description}</p>

                {/* Features incluídas */}
                <div className="space-y-2 flex-1 mb-5">
                  {features.map(f => (
                    <div key={f} className="flex items-start gap-2">
                      <Check size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                      <span className="text-white/60 text-xs">{f}</span>
                    </div>
                  ))}
                  {notIncluded?.map(f => (
                    <div key={f} className="flex items-start gap-2 opacity-30">
                      <span className="text-white/30 text-xs w-3.5 flex-shrink-0 mt-0.5">✕</span>
                      <span className="text-white/30 text-xs line-through">{f}</span>
                    </div>
                  ))}
                </div>

                {/* Botão */}
                {isCurrent ? (
                  <div className="w-full py-3 rounded-xl bg-white/[0.05] border border-white/10 text-white/30 text-sm text-center font-medium">
                    Plano atual
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      // TODO: integrar Stripe
                      alert(`Em breve! Contato: contato@beautiapp.com.br`)
                    }}
                    className={`w-full py-3 rounded-xl text-white text-sm font-bold transition-all active:scale-[0.98] bg-gradient-to-r ${color} hover:opacity-90 shadow-lg`}
                  >
                    {trialExpired ? 'Ativar agora' : 'Fazer upgrade'}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* FAQ rápido */}
      <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6">
        <h3 className="text-white font-semibold mb-4">Dúvidas frequentes</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            {
              q: 'Posso cancelar a qualquer momento?',
              a: 'Sim. Sem fidelidade nem multa. Cancele quando quiser pelo painel.',
            },
            {
              q: 'Meus dados são mantidos se eu pausar?',
              a: 'Sim. Seus clientes, agendamentos e histórico ficam salvos por 90 dias.',
            },
            {
              q: 'Como funciona o pagamento?',
              a: 'Cobrança mensal automática via cartão de crédito. Integração com Stripe.',
            },
            {
              q: 'Posso mudar de plano depois?',
              a: 'Sim. Faça upgrade ou downgrade a qualquer momento, sem perda de dados.',
            },
          ].map(({ q, a }) => (
            <div key={q}>
              <div className="text-white/70 text-sm font-medium mb-1">{q}</div>
              <div className="text-white/30 text-xs">{a}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Contato */}
      <div className="text-center mt-6">
        <p className="text-white/30 text-sm">
          Dúvidas?{' '}
          <a href="mailto:contato@beautiapp.com.br" className="text-[#6366f1] hover:text-[#818cf8] transition-colors">
            contato@beautiapp.com.br
          </a>
        </p>
      </div>
    </div>
  )
}