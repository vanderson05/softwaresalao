# softwaresalao
Plataforma de Gestão com Atendimento Inteligente por WhatsApp

# Frontend - Software Salão

Frontend do projeto Software Salão desenvolvido com Next.js, React, TypeScript e preparado para funcionamento como PWA (Progressive Web App).

---

# Stack Tecnológica

## Framework

- Next.js 15.5.18
- React 18.3.1
- React DOM 18.3.1
- TypeScript 5.x

## UI e Componentes

- Radix UI
- Lucide React
- Tailwind CSS 3.4
- Tailwind Merge
- Class Variance Authority (CVA)

## Formulários e Validação

- React Hook Form
- Zod
- @hookform/resolvers

## Estado Global

- Zustand

## Integração HTTP

- Axios

## Datas

- date-fns

## Gráficos

- Recharts

## Notificações

- Sonner

## Qualidade de Código

- ESLint 9
- eslint-config-next 15

## PWA

- Serwist
- Manifest Web App
- Service Worker

---

# Versões Homologadas

```json
{
  "next": "15.5.18",
  "react": "18.3.1",
  "react-dom": "18.3.1",
  "typescript": "^5",
  "eslint": "9.39.4",
  "eslint-config-next": "15.5.18",
  "serwist": "latest",
  "@serwist/next": "latest"
}
```

---

# Estrutura do Projeto

```text
frontend/
│
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── sw.ts
│
├── lib/
│
├── public/
│   ├── manifest.json
│   ├── sw.js
│   └── icons/
│       ├── icon-192.png
│       └── icon-512.png
│
├── node_modules/
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── package-lock.json
```

---

# Organização Recomendada

Conforme o projeto evoluir:

```text
app/
│
├── (auth)/
│   ├── login/
│   └── recuperar-senha/
│
├── dashboard/
│
├── agenda/
│   ├── agendamentos/
│   ├── bloqueios/
│   ├── profissionais/
│   └── servicos/
│
├── clientes/
│
├── financeiro/
│
├── estoque/
│
├── fidelidade/
│
├── configuracoes/
│
└── agent/
```

---

# Estrutura Recomendada para Crescimento

```text
frontend/
│
├── app/
│
├── components/
│   ├── ui/
│   ├── forms/
│   ├── layout/
│   ├── dashboard/
│   ├── agenda/
│   └── clientes/
│
├── hooks/
│
├── services/
│   ├── api.ts
│   ├── auth.ts
│   ├── agenda.ts
│   ├── clientes.ts
│   ├── profissionais.ts
│   └── agent.ts
│
├── store/
│
├── types/
│
├── utils/
│
├── lib/
│
└── public/
```

---

# Integração com Backend Django

Backend principal:

```text
https://softwaresalao.onrender.com
```

API:

```text
https://softwaresalao.onrender.com/api
```

Estrutura recomendada:

```text
services/
└── api.ts
```

Exemplo:

```typescript
import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});
```

Arquivo:

```env
NEXT_PUBLIC_API_URL=https://softwaresalao.onrender.com/api
```

---

# Progressive Web App (PWA)

O frontend foi preparado para funcionar como aplicativo instalável.

Recursos:

- Instalação Android
- Instalação iPhone
- Funcionamento em tela cheia
- Ícone na tela inicial
- Service Worker
- Cache local
- Manifest Web App

Arquivos envolvidos:

```text
public/manifest.json
app/sw.ts
public/sw.js
next.config.js
```

---

# Comandos do Projeto

Instalar dependências:

```bash
npm install
```

Executar ambiente local:

```bash
npm run dev
```

Build produção:

```bash
npm run build
```

Executar build local:

```bash
npm run start
```

Lint:

```bash
npm run lint
```

---

# Roadmap Frontend

## Fase 1

- Login JWT
- Dashboard
- Profissionais
- Serviços
- Agenda

## Fase 2

- Clientes
- Histórico
- Financeiro
- Comissões

## Fase 3

- Estoque
- Fidelidade
- Relatórios

## Fase 4

- Aplicativo Cliente
- Agendamento Online
- Pagamento Online

## Fase 5

- Agent IA
- WhatsApp
- Automações
- Confirmação automática de agendamentos

---

# Arquitetura

```text
Frontend (Next.js)
        │
        ▼
API Gateway
        │
        ▼
Backend Django
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
Tenant Agenda Agent
        │
        ▼
 PostgreSQL
```

---

# Objetivo

Construir uma plataforma SaaS multi-tenant para:

- Barbearias
- Salões de beleza
- Clínicas estéticas
- Studios de beleza

com:

- Gestão completa
- Agenda online
- Aplicativo PWA
- Inteligência Artificial
- WhatsApp integrado
- Modelo SaaS por assinatura