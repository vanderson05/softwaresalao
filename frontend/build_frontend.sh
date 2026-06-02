#!/usr/bin/env bash
# build_frontend.sh — Next.js frontend no Render
# Colocar na raiz de softwaresalao/frontend/
set -o errexit

echo "==> Instalando dependências Node..."
npm install

echo "==> Build do Next.js..."
npm run build

echo "==> Build frontend concluído!"