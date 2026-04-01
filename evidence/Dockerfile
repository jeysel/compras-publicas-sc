# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — Evidence
#
# Base: Node.js 20 LTS (imagem oficial)
#
# ── Rede ─────────────────────────────────────────────────────────────────────
# Este container opera na rede "compras_network" definida no docker-compose.yml
# Acessa o PostgreSQL pelo hostname "postgres" (não localhost)
#
# Modos de uso:
#   dev   → npm run dev   (http://localhost:3000) — desenvolvimento local
#   build → npm run build (gera /app/build)       — antes de publicar no Pages
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim

WORKDIR /app

# Copia dependências primeiro (cache de layer)
COPY package.json ./

RUN npm install --legacy-peer-deps

# Copia o projeto Evidence
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]