# Beauti Frontend

Frontend do sistema de gestão para barbearias e salões, desenvolvido com Next.js 15, React 18 e TypeScript. Preparado para funcionar como PWA (Progressive Web App).

---

## Stack tecnológica

| Categoria | Tecnologia | Versão |
|---|---|---|
| Framework | Next.js | 15.5.18 |
| UI | React + React DOM | 18.3.1 |
| Linguagem | TypeScript | ^5 |
| Estilização | Tailwind CSS | 3.4 |
| Componentes | Radix UI | latest |
| Ícones | Lucide React | latest |
| Formulários | React Hook Form + Zod | latest |
| Estado global | Zustand | latest |
| HTTP | Axios | latest |
| Datas | date-fns | latest |
| Gráficos | Recharts | latest |
| Notificações | Sonner | latest |
| PWA | Serwist + @serwist/next | latest |
| Linting | ESLint | 9.39.4 |

---

## Estrutura de pastas

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout + PWA meta tags
│   ├── page.tsx                # Redirect → /painel ou /login
│   ├── globals.css             # Design system + variáveis CSS
│   │
│   ├── (auth)/                 # Grupo sem layout do painel
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── cadastro/
│   │       └── page.tsx
│   │
│   ├── setup/                  # Wizard de primeiro acesso (4 passos)
│   │   └── page.tsx
│   │
│   ├── painel/                 # Painel do barbeiro (owner/manager)
│   │   ├── layout.tsx          # Sidebar desktop + BottomNav mobile
│   │   ├── page.tsx            # Dashboard
│   │   ├── agenda/
│   │   │   ├── page.tsx        # Agenda do dia / semana
│   │   │   └── novo/
│   │   │       └── page.tsx    # Novo agendamento
│   │   ├── clientes/
│   │   │   ├── page.tsx        # Lista + insights CRM
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Perfil do cliente
│   │   ├── financeiro/
│   │   │   └── page.tsx        # Caixa, relatório, comissões
│   │   ├── produtos/
│   │   │   └── page.tsx        # Estoque e produtos
│   │   └── configuracoes/
│   │       └── page.tsx        # Estabelecimento, agente, plano
│   │
│   ├── profissional/           # Tela do profissional (mobile-first)
│   │   ├── layout.tsx
│   │   └── page.tsx            # Minha agenda do dia
│   │
│   └── b/                      # Área pública do cliente final
│       ├── page.tsx            # Discovery — busca barbearias
│       └── [slug]/
│           ├── page.tsx        # Perfil da barbearia
│           ├── agendar/
│           │   └── page.tsx    # Fluxo de agendamento
│           └── minha-conta/
│               └── page.tsx    # Meus agendamentos
│
├── components/
│   ├── ui/                     # Shadcn/UI components
│   ├── layout/
│   │   ├── Sidebar.tsx         # Navegação desktop
│   │   ├── BottomNav.tsx       # Navegação mobile (tab bar)
│   │   └── Header.tsx
│   ├── agenda/
│   │   ├── AgendaDay.tsx
│   │   ├── AppointmentCard.tsx
│   │   └── NewAppointmentModal.tsx
│   ├── comanda/
│   │   ├── CommandaSheet.tsx   # Drawer da comanda
│   │   └── CheckoutModal.tsx
│   ├── dashboard/
│   │   ├── DashboardStats.tsx
│   │   └── RevenueChart.tsx
│   └── public/
│       ├── BarbershopCard.tsx
│       └── BookingFlow.tsx
│
├── lib/
│   ├── api.ts                  # Cliente HTTP (Axios) + endpoints
│   ├── store.ts                # Estado global (Zustand)
│   └── utils.ts                # Helpers
│
├── public/
│   ├── manifest.json           # PWA manifest
│   └── icons/                  # Ícones PWA (192x192, 512x512)
│
├── next.config.js              # Next.js + Serwist (PWA)
├── tailwind.config.ts          # Design system Beauti
├── tsconfig.json
├── postcss.config.js
└── .env.local                  # Variáveis de ambiente
```

---

## Interfaces do sistema

```
/login              → Autenticação do barbeiro
/cadastro           → Cadastro novo tenant (trial 14 dias)
/setup              → Wizard de configuração inicial (4 passos)

/painel             → Dashboard do barbeiro
/painel/agenda      → Agenda do dia / semana + comanda
/painel/clientes    → CRM: lista, perfil, insights
/painel/financeiro  → Caixa do dia, relatório mensal, comissões
/painel/produtos    → Estoque e produtos
/painel/configuracoes → Dados, agente WhatsApp, plano

/profissional       → Tela do profissional (mobile-first)

/b                  → Discovery público (busca barbearias)
/b/[slug]           → Perfil público da barbearia
/b/[slug]/agendar   → Agendamento pelo link
/b/[slug]/minha-conta → Área do cliente final
```

---

## Configuração

### 1. Instalar dependências

```bash
cd frontend
npm install
```

### 2. Variáveis de ambiente

Crie o arquivo `.env.local` na pasta `frontend/`:

```env
NEXT_PUBLIC_API_URL=https://softwaresalao.onrender.com
```

Para desenvolvimento local com backend local:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Rodar em desenvolvimento

```bash
npm run dev
```

Acesse: [http://localhost:3000](http://localhost:3000)

### 4. Build para produção

```bash
npm run build
npm start
```

---

## PWA

O projeto usa **Serwist** (`@serwist/next`) para Progressive Web App.

- Service Worker registrado automaticamente no build
- Manifest configurado em `public/manifest.json`
- Tema: `#6366F1` (indigo)
- Start URL: `/painel`
- Display: `standalone` (sem barra do navegador)

### Instalar como app

**Android (Chrome):** banner automático aparece após a primeira visita.

**iPhone (Safari):** toque em "Compartilhar" → "Adicionar à Tela de Início".

**Desktop (Chrome/Edge):** ícone de instalação na barra de endereços.

---

## Conexão com o backend

O frontend se conecta à API Django em `NEXT_PUBLIC_API_URL`.

Dois tokens JWT são usados:

| Token | Header | Quem usa |
|---|---|---|
| `beauti_token` | `Bearer {token}` | Barbeiro (owner/manager) |
| `beauti_client_token` | `ClientBearer {token}` | Cliente final |

Refresh automático: quando o token expira, o interceptor do Axios renova automaticamente usando o `beauti_refresh`.

---

## Design system

Cores principais:

| Nome | Hex | Uso |
|---|---|---|
| Primary | `#6366F1` | Botões, links, destaques |
| Background | `#F8FAFC` | Fundo das páginas |
| Card | `#FFFFFF` | Cards e painéis |
| Border | `hsl(220 13% 91%)` | Bordas e divisores |

Status de agendamentos:

| Status | Cor |
|---|---|
| pending | Amber |
| confirmed | Indigo |
| in_comanda | Purple |
| completed | Emerald |
| cancelled | Red |
| no_show | Slate |

---

## Backend (API)

Repositório do backend Django: `softwaresalao/`

Documentação da API: consultar os arquivos de teste:
- `test_api.py` — Etapas 1, 2, 3 e 4
- `test_agent.py` — Agente WhatsApp
- `test_m3.py` — Perfil público + Auth cliente
- `test_crm.py` — CRM e assinaturas
- `test_m5.py` — Financeiro, comanda e estoque

---

## Sprints de desenvolvimento

- [x] Sprint 0 — Setup inicial, PWA, design system
- [ ] Sprint 1 — Login, cadastro, setup wizard
- [ ] Sprint 2 — Painel: dashboard e agenda
- [ ] Sprint 3 — Painel: comanda, CRM, financeiro
- [ ] Sprint 4 — Tela do profissional
- [ ] Sprint 5 — Discovery público + área do cliente