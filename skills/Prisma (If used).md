# Prisma Patterns & Best Practices
Use for this: Writing safe, efficient Prisma schemas, queries, and migrations.

Constraints: Always use parameterized queries (Prisma handles this). Never run destructive migrations without a backup.
Agent note: Verify DB provider before suggesting features. Never include real connection strings.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Schema Conventions

### Naming
```prisma
// Models: PascalCase, singular
model User {}
model ProjectMember {}

// Fields: camelCase
id        String
createdAt DateTime

// Enums: PascalCase
enum Role { ADMIN MEMBER VIEWER }
```

### Base Model Pattern
```prisma
model Project {
  id        String   @id @default(cuid())
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  name        String   @db.VarChar(100)
  description String?  @db.Text
  visibility  Visibility @default(PRIVATE)

  // Relations
  authorId String
  author   User   @relation(fields: [authorId], references: [id], onDelete: Cascade)
  members  ProjectMember[]

  // Indexes for common queries
  @@index([authorId])
  @@index([createdAt])
}

enum Visibility {
  PRIVATE
  PUBLIC
}
```

### Soft Delete Pattern
```prisma
model Post {
  // ... other fields
  deletedAt DateTime?  // null = active, set = deleted
  @@index([deletedAt])
}
```

### Many-to-Many (explicit join table — preferred)
```prisma
model ProjectMember {
  id        String   @id @default(cuid())
  projectId String
  userId    String
  role      Role     @default(MEMBER)
  joinedAt  DateTime @default(now())

  project Project @relation(fields: [projectId], references: [id], onDelete: Cascade)
  user    User    @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([projectId, userId])  // prevent duplicates
  @@index([userId])
}
```

## Query Patterns

### Always select what you need
```ts
// ❌ Over-fetches everything
const user = await db.user.findUnique({ where: { id } })

// ✅ Select only needed fields
const user = await db.user.findUnique({
  where: { id },
  select: { id: true, name: true, email: true },
})
```

### Prevent N+1 with include
```ts
// ❌ N+1: 1 query for projects + N queries for members
const projects = await db.project.findMany()
for (const p of projects) {
  p.members = await db.projectMember.findMany({ where: { projectId: p.id } })
}

// ✅ Single query with join
const projects = await db.project.findMany({
  include: {
    members: { include: { user: { select: { id: true, name: true } } } },
    _count: { select: { members: true } },
  },
})
```

### Safe filtering with type-checked where
```ts
const projects = await db.project.findMany({
  where: {
    authorId: session.user.id,           // ownership check
    visibility: 'PUBLIC',
    name: { contains: search, mode: 'insensitive' },
    deletedAt: null,                     // soft delete filter
  },
  orderBy: { updatedAt: 'desc' },
  take: limit,
  skip: (page - 1) * limit,
})
```

### Pagination (cursor-based — preferred for large tables)
```ts
const projects = await db.project.findMany({
  where: { authorId: userId },
  take: limit + 1,                       // fetch one extra to check hasMore
  cursor: cursor ? { id: cursor } : undefined,
  orderBy: { createdAt: 'desc' },
})

const hasMore = projects.length > limit
const items = hasMore ? projects.slice(0, -1) : projects
const nextCursor = hasMore ? items[items.length - 1].id : null
```

### Transaction (for multi-step operations)
```ts
const result = await db.$transaction(async (tx) => {
  const project = await tx.project.create({ data: { name, authorId } })
  await tx.projectMember.create({ data: { projectId: project.id, userId: authorId, role: 'ADMIN' } })
  await tx.activityLog.create({ data: { action: 'PROJECT_CREATED', projectId: project.id } })
  return project
})
```

## Migration Commands
```bash
# Create migration (development)
npx prisma migrate dev --name add_projects_table

# Apply migrations (production)
npx prisma migrate deploy

# Reset DB (development only — destructive!)
npx prisma migrate reset

# Push schema without migration (prototype only)
npx prisma db push

# Explore data
npx prisma studio

# Regenerate client after schema change
npx prisma generate
```

## Prisma Client Singleton (Next.js)
```ts
// lib/db.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient }

export const db = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'error'] : ['error'],
})

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db
```

## Performance Checklist
- [ ] Every foreign key has an `@@index`
- [ ] `findMany` uses `take` (no unbounded queries)
- [ ] Multi-step writes use `$transaction`
- [ ] `select` used instead of full model select for list views
- [ ] `_count` used instead of fetching full relations just to count
- [ ] Soft-deleted rows excluded with `deletedAt: null` filter
