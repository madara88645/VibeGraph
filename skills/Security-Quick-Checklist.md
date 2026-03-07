# Security Quick Checklist
Use for this: Pre-release security sanity-checks covering OWASP Top 10 essentials.

Constraints: This is a fast check, not a full audit. Flag uncertain items for a dedicated security review.
Agent note: Never output real secrets. Recommend rotating any exposed secrets immediately.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Pre-Release Security Checklist

### 1. Secrets & Environment Variables
```bash
# Check for hardcoded secrets
grep -r "sk_live\|sk_test\|api_key\|apiKey\|password\|secret" --include="*.ts" --include="*.tsx" src/

# .env should be in .gitignore
cat .gitignore | grep -E "^\.env"

# .env.example should have no real values
cat .env.example
```
- [ ] No secrets in source code
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has placeholder values only
- [ ] No secrets in git history (`git log -p | grep -i "api_key"`)

### 2. Input Validation (Injection Prevention)
```tsx
// FAIL: Using raw user input in queries
const user = await db.raw(`SELECT * FROM users WHERE id = ${userId}`)

// FIX: Parameterized / ORM
const user = await db.user.findUnique({ where: { id: userId } })

// FAIL: Rendering raw HTML (XSS)
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// FIX: Sanitize or avoid
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```
- [ ] All user inputs validated with Zod or equivalent before use
- [ ] No raw SQL string concatenation
- [ ] No `dangerouslySetInnerHTML` with unvalidated user content
- [ ] File upload types & sizes validated server-side

### 3. Authentication & Authorization
```tsx
// Every API route must verify session
export async function GET(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session) return new Response('Unauthorized', { status: 401 });
  // ... proceed
}

// Resource access must verify ownership
const post = await db.post.findUnique({ where: { id, authorId: session.user.id } });
if (!post) return new Response('Not Found', { status: 404 });
```
- [ ] Every protected API route checks session/JWT
- [ ] Resource access validates ownership (not just authentication)
- [ ] Admin routes have role check, not just auth check
- [ ] Password resets expire quickly (< 1 hour)
- [ ] Logout invalidates server-side session

### 4. HTTP Security Headers
```ts
// next.config.ts
const securityHeaders = [
  { key: 'X-DNS-Prefetch-Control', value: 'on' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self'" },
];
```
- [ ] `X-Frame-Options: SAMEORIGIN` (clickjacking)
- [ ] `X-Content-Type-Options: nosniff`
- [ ] CSP header configured
- [ ] HTTPS enforced (no mixed content)
- [ ] Cookies: `HttpOnly`, `Secure`, `SameSite=Lax`

### 5. Rate Limiting & Abuse Prevention
```ts
// API routes should have rate limiting
import { Ratelimit } from '@upstash/ratelimit';
const ratelimit = new Ratelimit({ limiter: Ratelimit.slidingWindow(10, '10 s') });
```
- [ ] Auth endpoints rate-limited (login, password reset)
- [ ] Public API endpoints rate-limited
- [ ] File upload endpoints size-limited
- [ ] No unbounded DB queries (always use `take`/`limit`)

### 6. Data Exposure
- [ ] API responses never include password hashes, tokens, or internal IDs
- [ ] Pagination uses cursor-based (not offset with total count)
- [ ] Error messages don't leak stack traces or DB schemas to clients
- [ ] Logs don't contain PII (emails, phone numbers, IP addresses without consent)

### 7. Dependency Vulnerabilities
```bash
npm audit --audit-level=high
# or
pnpm audit
```
- [ ] No critical or high severity vulnerabilities in dependencies
- [ ] Dependencies updated within last 3 months

## On Suspicious Finding
```
FINDING: [description]
FILE: [path]
LINE: [number]
RISK: Critical / High / Medium
ACTION: Rotate secret / Patch immediately / Monitor
```
