'use client'
// components/agenda/AppointmentSheet.tsx
// Bottom sheet de detalhes e ações do agendamento

import { useState } from 'react'
import {
  X, Check, XCircle, Clock, Phone, Scissors,
  User, AlertTriangle, ChevronRight, DollarSign
} from 'lucide-react'
import { appointmentsApi } from '@/lib/api'
import { usePermissions } from '@/lib/hooks/usePermissions'
import { toast } from 'sonner'

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending:    { label: 'Aguardando confirmação', color: 'text-amber-400'  },
  confirmed:  { label: 'Confirmado',             color: 'text-indigo-400' },
  in_comanda: { label: 'Em atendimento',          color: 'text-purple-400' },
  completed:  { label: 'Realizado',              color: 'text-emerald-400'},
  cancelled:  { label: 'Cancelado',              color: 'text-red-400'    },
  no_show:    { label: 'Não compareceu',          color: 'text-slate-400'  },
}

export default function AppointmentSheet({
  appointment, onClose, onUpdated
}: {
  appointment: any
  onClose: () => void
  onUpdated: () => void
}) {
  const { isStaff, isOwner } = usePermissions()
  const [loading, setLoading] = useState(false)
  const [step,    setStep]    = useState<'detail' | 'cancel' | 'checkout'>('detail')
  const [paymentMethod, setPaymentMethod] = useState('pix')

  const status = STATUS_LABELS[appointment.status] || { label: appointment.status, color: 'text-white/50' }
  const canConfirm  = isStaff && appointment.status === 'pending'
  const canComplete = isStaff && appointment.status === 'confirmed'
  const canCancel   = isStaff && !['completed','cancelled','no_show'].includes(appointment.status)
  const canNoShow   = isStaff && appointment.status === 'confirmed'
  const isDone      = ['completed','cancelled','no_show'].includes(appointment.status)

  async function handleConfirm() {
    setLoading(true)
    try {
      await appointmentsApi.confirm(appointment.id)
      toast.success('Agendamento confirmado!')
      onUpdated()
    } catch { toast.error('Erro ao confirmar.') }
    finally { setLoading(false) }
  }

  async function handleCancel() {
    setLoading(true)
    try {
      await appointmentsApi.cancel(appointment.id, { reason: 'Cancelado pelo barbeiro' })
      toast.success('Agendamento cancelado.')
      onUpdated()
    } catch { toast.error('Erro ao cancelar.') }
    finally { setLoading(false) }
  }

  async function handleNoShow() {
    setLoading(true)
    try {
      await appointmentsApi.noShow(appointment.id)
      toast.success('Marcado como não compareceu.')
      onUpdated()
    } catch { toast.error('Erro.') }
    finally { setLoading(false) }
  }

  async function handleCheckout() {
    setLoading(true)
    try {
      await import('@/lib/api').then(({ financialApi }) =>
        financialApi.checkout(appointment.id, { payment_method: paymentMethod })
      )
      toast.success('Atendimento concluído! 🎉')
      onUpdated()
    } catch { toast.error('Erro ao finalizar.') }
    finally { setLoading(false) }
  }

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
      />

      {/* Sheet */}
      <div
        className="fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-96 z-50 bg-[#0D0D14] border border-white/10 rounded-t-3xl md:rounded-2xl animate-slide-in-bottom shadow-2xl"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        {/* Handle (mobile) */}
        <div className="md:hidden flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 bg-white/20 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-start justify-between px-5 pt-4 pb-3 border-b border-white/[0.06]">
          <div>
            <h3 className="text-white font-bold text-lg leading-tight">{appointment.client_name}</h3>
            <span className={`text-sm font-medium ${status.color}`}>{status.label}</span>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center text-white/30 hover:text-white rounded-lg hover:bg-white/[0.06] transition-all ml-2 flex-shrink-0">
            <X size={18} />
          </button>
        </div>

        {/* Detail view */}
        {step === 'detail' && (
          <div className="px-5 py-4">
            {/* Info */}
            <div className="space-y-3 mb-5">
              <InfoRow icon={Scissors} label="Serviço" value={`${appointment.service_name} · ${appointment.service_duration}min`} />
              <InfoRow icon={User}     label="Profissional" value={appointment.professional_name} />
              <InfoRow icon={Clock}    label="Horário"
                value={`${formatTime(appointment.starts_at)} – ${formatTime(appointment.ends_at)}`}
                sub={formatDate(appointment.starts_at)}
              />
              {appointment.client_phone && (
                <InfoRow icon={Phone} label="Telefone"
                  value={appointment.client_phone}
                  action={{ label: 'Ligar', href: `tel:${appointment.client_phone}` }}
                />
              )}
              <InfoRow icon={DollarSign} label="Valor" value={`R$ ${Number(appointment.price_snapshot || 0).toFixed(2)}`} />
            </div>

            {/* Ações */}
            {!isDone && (
              <div className="space-y-2.5">
                {canConfirm && (
                  <ActionBtn
                    label="Confirmar agendamento"
                    icon={Check}
                    color="bg-[#6366f1] hover:bg-[#4f46e5] text-white"
                    onClick={handleConfirm}
                    loading={loading}
                  />
                )}
                {canComplete && (
                  <ActionBtn
                    label="Finalizar atendimento"
                    icon={Check}
                    color="bg-emerald-600 hover:bg-emerald-500 text-white"
                    onClick={() => setStep('checkout')}
                    loading={false}
                  />
                )}
                {canNoShow && (
                  <ActionBtn
                    label="Não compareceu"
                    icon={AlertTriangle}
                    color="bg-white/[0.06] hover:bg-white/10 text-white/60 border border-white/[0.08]"
                    onClick={handleNoShow}
                    loading={loading}
                  />
                )}
                {canCancel && (
                  <ActionBtn
                    label="Cancelar agendamento"
                    icon={XCircle}
                    color="bg-red-500/10 hover:bg-red-500/15 text-red-400 border border-red-500/20"
                    onClick={() => setStep('cancel')}
                    loading={false}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* Checkout view */}
        {step === 'checkout' && (
          <div className="px-5 py-4">
            <h4 className="text-white font-semibold mb-4">Finalizar atendimento</h4>
            <p className="text-white/40 text-sm mb-4">
              {appointment.client_name} · {appointment.service_name}
            </p>

            <div className="mb-5">
              <label className="text-white/50 text-sm block mb-2">Forma de pagamento</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { value: 'pix',    label: '💸 Pix'      },
                  { value: 'cash',   label: '💵 Dinheiro' },
                  { value: 'credit', label: '💳 Crédito'  },
                  { value: 'debit',  label: '💳 Débito'   },
                ].map(({ value, label }) => (
                  <button
                    key={value}
                    onClick={() => setPaymentMethod(value)}
                    className={`py-3 rounded-xl text-sm font-medium transition-all active:scale-95 ${
                      paymentMethod === value
                        ? 'bg-[#6366f1] text-white'
                        : 'bg-white/[0.06] text-white/50 border border-white/[0.08] hover:bg-white/10'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between bg-white/[0.04] rounded-xl px-4 py-3 mb-5">
              <span className="text-white/60 text-sm">Total</span>
              <span className="text-white font-bold text-lg">
                R$ {Number(appointment.price_snapshot || 0).toFixed(2)}
              </span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setStep('detail')}
                className="flex-1 py-3 rounded-xl bg-white/[0.06] text-white/50 text-sm font-medium border border-white/[0.08] hover:bg-white/10 transition-all"
              >
                Voltar
              </button>
              <button
                onClick={handleCheckout}
                disabled={loading}
                className="flex-[2] py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold transition-all disabled:opacity-50 active:scale-[0.98]"
              >
                {loading ? 'Finalizando...' : 'Confirmar pagamento'}
              </button>
            </div>
          </div>
        )}

        {/* Cancel confirm */}
        {step === 'cancel' && (
          <div className="px-5 py-4">
            <div className="text-center mb-5">
              <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-3">
                <XCircle size={22} className="text-red-400" />
              </div>
              <h4 className="text-white font-semibold text-lg">Cancelar agendamento?</h4>
              <p className="text-white/40 text-sm mt-1">
                {appointment.client_name} — {formatTime(appointment.starts_at)}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setStep('detail')}
                className="flex-1 py-3 rounded-xl bg-white/[0.06] text-white/50 text-sm font-medium border border-white/[0.08]"
              >
                Voltar
              </button>
              <button
                onClick={handleCancel}
                disabled={loading}
                className="flex-[2] py-3 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-bold transition-all disabled:opacity-50"
              >
                {loading ? 'Cancelando...' : 'Sim, cancelar'}
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function InfoRow({ icon: Icon, label, value, sub, action }: {
  icon: any; label: string; value: string; sub?: string
  action?: { label: string; href: string }
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon size={15} className="text-white/40" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-white/30 text-xs">{label}</div>
        <div className="text-white text-sm font-medium truncate">{value}</div>
        {sub && <div className="text-white/30 text-xs capitalize">{sub}</div>}
      </div>
      {action && (
        <a href={action.href} className="text-[#6366f1] text-xs font-medium border border-[#6366f1]/30 px-2.5 py-1.5 rounded-lg hover:bg-[#6366f1]/10 transition-all flex-shrink-0">
          {action.label}
        </a>
      )}
    </div>
  )
}

function ActionBtn({ label, icon: Icon, color, onClick, loading }: {
  label: string; icon: any; color: string; onClick: () => void; loading: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl font-semibold text-sm transition-all active:scale-[0.98] disabled:opacity-50 ${color}`}
    >
      <Icon size={18} />
      <span className="flex-1 text-left">{label}</span>
      {!loading && <ChevronRight size={16} className="opacity-50" />}
    </button>
  )
}