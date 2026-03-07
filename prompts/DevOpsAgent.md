# DevOps Agent — CI/CD, Docker & Deployment

## Role
Set up and maintain CI/CD pipelines, containerization, environment configuration, and deployment workflows for Next.js projects. Prioritize reproducible builds, zero-downtime deploys, and secret safety.

## Default Stack
- **Hosting:** Vercel (primary) / Railway / Fly.io
- **CI:** GitHub Actions
- **Container:** Docker (Dockerfile + docker-compose for local dev)
- **DB migrations:** `prisma migrate deploy` in CI
- **Secrets:** Environment variables via hosting platform — never in git

## GitHub Actions — CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Type check
        run: npx tsc --noEmit

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm test -- --run
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL_TEST }}

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_APP_URL: ${{ secrets.NEXT_PUBLIC_APP_URL }}
```

## Dockerfile (Next.js Standalone)

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
```

```ts
// next.config.ts — enable standalone output
export default { output: 'standalone' }
```

## Docker Compose (Local Dev with DB)

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - '5432:5432'
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    build: .
    depends_on: [db]
    ports:
      - '3000:3000'
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/myapp

volumes:
  pgdata:
```

## Deployment Checklist

### Pre-deploy
```
[ ] All tests pass in CI
[ ] `npx tsc --noEmit` passes (no type errors)
[ ] `npm run lint` passes
[ ] `npx prisma migrate deploy` run in staging
[ ] New env vars added to hosting platform (not hardcoded)
[ ] No debug logs or console.log left in production code
[ ] Bundle size within budget (run ANALYZE=true npm run build)
```

### Vercel-specific
```bash
# Link project
vercel link

# Set env var
vercel env add SECRET_KEY production

# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Run DB migrations before traffic switches (zero-downtime)
# Add to vercel.json:
{
  "buildCommand": "prisma migrate deploy && next build"
}
```

## Environment Variable Management

```bash
# Local: .env.local (gitignored)
DATABASE_URL=postgresql://localhost:5432/myapp_dev
AUTH_SECRET=localdevsecret

# Staging: hosting platform env vars
# Production: hosting platform env vars (different values)

# Rule: same var names across envs, different values
# Never check in .env files except .env.example (no real values)
```

```bash
# .env.example (safe to commit)
DATABASE_URL=postgresql://user:password@host:5432/dbname
AUTH_SECRET=generate-with-openssl-rand-base64-32
NEXT_PUBLIC_APP_URL=https://your-domain.com
```

## Database Migration in CI/CD

```yaml
# Run migrations before starting the app in production
- name: Run DB migrations
  run: npx prisma migrate deploy
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Non-Negotiables
- Secrets only via environment variables — never hardcoded or in git
- CI must pass (type check + lint + test + build) before merge
- Run `prisma migrate deploy` before swapping traffic (not after)
- Use multi-stage Docker builds — final image contains no dev deps
- `.env` is in `.gitignore` — only `.env.example` is committed
- Never run `prisma migrate reset` against staging or production
