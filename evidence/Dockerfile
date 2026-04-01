# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — Evidence
# Base: Node.js 20 LTS
# ── Rede ─────────────────────────────────────────────────────────────────────
# Este container opera na rede "compras_network" definida no docker-compose.yml
# Acessa o PostgreSQL pelo hostname "postgres" (não localhost)
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim

WORKDIR /app

COPY package.json ./

RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["./node_modules/.bin/evidence", "dev", "--host", "0.0.0.0", "--port", "3000"]