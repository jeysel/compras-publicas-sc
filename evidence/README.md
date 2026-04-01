

# 1. Desenvolvimento — visualiza em tempo real
docker compose --profile evidence up evidence
# acessa: http://localhost:3000

# 2. Build local — valida antes de publicar
docker compose run --rm evidence npm run build
# gera: evidence/build/

# 3. Commit + push → GitHub Actions publica no Pages
git add evidence/build
git push