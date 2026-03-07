# Database Query Patterns
Use for this: Write efficient, safe Prisma queries that avoid N+1s, over-fetching, and missing index issues.

Constraints: All queries go through the `db` singleton — never instantiate PrismaClient in components or route handlers. Always apply `take` limits on list queries.
Agent note: When debugging slow queries, check Prisma logs before adding indexes. Index the right columns, not all columns.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## The 5 Most Common Query Mistakes

| Mistake | Impact | Fix |
|---|---|---|
| N+1 (loop + query per item) | O(n) DB calls | Use `include` or `$transaction` |
| No `take` limit | Full table scan | Always add pagination |
| Select * (no explicit select) | Over-fetching | Use `select: { id, name }` |
| No index on filtered column | Full table scan | Add `@@index([column])` |
| Session check after query | Wasted DB call | Check auth first |

## Select Only What You Need

```ts
// ❌ Over-fetch: returns all 30+ User fields
const user = await db.user.findUnique({ where: { id } })

// ✅ Efficient: returns only what's needed
const user = await db.user.findUnique({
  where: { id },
  select: { id: true, name: true, email: true, image: true },
})
```

## N+1 Prevention

```ts
// ❌ N+1: 1 query for posts + N queries for each author
const posts = await db.post.findMany()
for (const post of posts) {
  const author = await db.user.findUnique({ where: { id: post.authorId } })
}

// ✅ Single query with include
const posts = await db.post.findMany({
  include: {
    author: { select: { id: true, name: true, image: true } },
  },
})

// ✅ For conditional includes or complex aggregation
const [posts, authorMap] = await db.$transaction([
  db.post.findMany({ select: { id: true, title: true, authorId: true } }),
  db.user.findMany({ select: { id: true, name: true } }),
])
```

## Pagination

### Cursor-based (preferred for large datasets)
```ts
async function listPosts(cursor?: string, limit = 20) {
  const posts = await db.post.findMany({
    take: limit + 1,   // fetch one extra to detect next page
    skip: cursor ? 1 : 0,
    cursor: cursor ? { id: cursor } : undefined,
    orderBy: { createdAt: 'desc' },
    select: { id: true, title: true, createdAt: true },
  })

  const hasNextPage = posts.length > limit
  return {
    items: hasNextPage ? posts.slice(0, -1) : posts,
    nextCursor: hasNextPage ? posts[limit - 1].id : null,
  }
}
```

### Offset-based (simple, but slower at large offsets)
```ts
async function listWithOffset(page = 1, limit = 20) {
  const [items, total] = await db.$transaction([
    db.post.findMany({
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    db.post.count(),
  ])
  return { items, total, pages: Math.ceil(total / limit) }
}
```

## Filtered Queries (safe from injection)

```ts
// Prisma is parameterized — never vulnerable to SQL injection
const results = await db.product.findMany({
  where: {
    AND: [
      { name: { contains: searchQuery, mode: 'insensitive' } },
      { price: { gte: minPrice } },
      { price: { lte: maxPrice } },
      { category: { in: selectedCategories } },
      { deletedAt: null },  // soft delete filter
    ],
  },
  orderBy: { createdAt: 'desc' },
  take: 50,
})
```

## Atomic Writes (transactions)

```ts
// Multiple writes that must all succeed or all fail
const order = await db.$transaction(async (tx) => {
  // Check inventory first
  const product = await tx.product.findUniqueOrThrow({ where: { id: productId } })
  if (product.stock < quantity) throw new Error('Insufficient stock')

  // Decrement stock
  await tx.product.update({
    where: { id: productId },
    data: { stock: { decrement: quantity } },
  })

  // Create order
  return tx.order.create({
    data: { userId, productId, quantity, totalPrice: product.price * quantity },
  })
})
```

## Indexing Guide

```prisma
model Post {
  id        String     @id @default(cuid())
  authorId  String
  status    PostStatus
  createdAt DateTime   @default(now())
  updatedAt DateTime   @updatedAt
  slug      String     @unique     // unique index auto-created

  // Compound index: matches query WHERE authorId=? AND status=?
  @@index([authorId, status])

  // Sort index: matches ORDER BY createdAt DESC
  @@index([createdAt(sort: Desc)])
}
```

### When to add an index
- Column used in `WHERE` filters on large tables
- Column used in `ORDER BY` for pagination
- Foreign key columns (Prisma does NOT auto-add by default)
- `@unique` constraint columns (index auto-created)

### When NOT to add an index
- Small tables (< 1000 rows) — full scan is fast enough
- Columns written to very frequently — index slows writes
- Boolean columns with few distinct values — low selectivity

## Useful Raw Queries (edge cases only)

```ts
// For complex SQL Prisma can't express cleanly
const results = await db.$queryRaw<{ id: string; rank: number }[]>`
  SELECT id, ts_rank(search_vector, plainto_tsquery(${query})) as rank
  FROM "Post"
  WHERE search_vector @@ plainto_tsquery(${query})
  ORDER BY rank DESC
  LIMIT ${limit}
`
// $queryRaw is safe — parameters are bound, not interpolated
```
