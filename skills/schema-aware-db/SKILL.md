---
name: schema-aware-db
description: Use WHENEVER writing, editing, or reviewing backend code that reads or writes a database — SQL (PostgreSQL, MySQL, SQLite) or NoSQL (MongoDB, DynamoDB, Redis): a query, ORM model, migration, repository/DAO, connection, adding/renaming a column or field, or a join — even if the user only says "add an endpoint," "fix this query," or "add a field." Stops schema guessing: introspect the real structure, map every usage across the codebase, then change it and trace the ripple so no column is invented and no query, serializer, or test goes stale.
---

# Schema-Aware Database Work

## Why this exists

The recurring failure when writing backend data code is not ignorance of SQL or query
syntax — it is acting on a **guessed** schema and a **local** view of the code. Concretely:

- **Invented columns/tables/fields** — writing `SELECT user_name FROM users` when the column is `username`, or referencing a collection field that doesn't exist.
- **Broken joins** — joining on the wrong key, joining tables with no real relationship, or fanning out rows because a one-to-many join wasn't aggregated.
- **Connection/session mishandling** — opening connections that never close, running queries outside a transaction that needs one, sharing a session across threads/requests, N+1 query loops.
- **Stale ripple** — changing a query or renaming a field in one place and missing the other files, migrations, serializers, and tests that use it.

Every one of these is prevented by the same discipline: **look before you write, and trace after you write.** Do not skip phases even when the change feels trivial. "Just add one field" is exactly the change that goes stale in five other files.

## The four phases

Work through these in order. Do not write query code until Phase 1 and 2 are done.

### Phase 1 — Discover the real schema (never guess)

Establish ground truth for every table/collection the task touches. Determine the engine first (check `settings.py`, `.env`, `docker-compose.yml`, `package.json`, connection strings, or ORM config), then introspect.

Read `references/sql.md` for SQL engines or `references/nosql.md` for NoSQL — they give the exact introspection commands and ORM-model-reading steps per engine. In short:

- **SQL**: get the actual column names, types, nullability, primary keys, foreign keys, indexes, and unique constraints. Prefer live introspection (`\d table`, `information_schema`, `PRAGMA table_info`) when a DB is reachable; otherwise read the migration history and ORM models as the source of truth. Never trust a single model file if migrations may have altered it — reconcile them.
- **NoSQL**: schemas are implicit, so sample real documents/items to learn the actual field shape, and read validators/indexes/access patterns. For DynamoDB, the partition/sort key and GSIs *are* the schema — you must know them before writing any access code.

Write down (in your working notes) the exact field names and key relationships you'll use. If you cannot confirm a name, say so and find it — do not fill it in from memory.

### Phase 2 — Map usage across the codebase (never edit locally)

Before changing anything, find **every** place the table/collection is referenced, so a change here doesn't leave stale code there. Read `references/ripple.md` for the full search recipe. In short: grep for the table/collection name, the ORM model/class name, raw query strings, migration files, serializers/schemas, and repository/DAO methods. Build a short map: "this entity is touched in models.py, three query sites, one serializer, two tests, one migration."

### Phase 3 — Write the change to industry standard

Now write the query or edit. Follow the standards in `references/standards.md` (parameterization, transactions, connection lifecycle, join correctness, indexing, N+1 avoidance, migration hygiene). Match the patterns already established in this codebase — if it uses a repository layer, add to it; don't scatter raw SQL. Reuse the exact field names confirmed in Phase 1.

### Phase 4 — Trace the ripple and reconcile

Go back to the map from Phase 2 and update every affected site: other queries on the same table, serializers, DTOs, type definitions, migrations (create one if the schema changed), and tests. Re-run a search for the old field name if you renamed something — zero stale references should remain. State explicitly what you changed and what you verified.

## Design the tables to industry standard

When the task is to create or improve the table/collection design itself (not just query it), apply the normalization, key, constraint, and indexing guidance in `references/standards.md` (SQL) and `references/nosql.md` (NoSQL, where you design around access patterns rather than normalize). Propose a migration; don't mutate a live schema ad hoc.

## Output discipline

At the end, briefly report: (1) the confirmed schema facts you relied on and how you got them (live introspection vs. migrations vs. models), (2) the usage map, (3) the change, (4) the ripple you reconciled. This makes it auditable and catches guesses before they ship.

If at any point you cannot verify a schema fact — no DB access, ambiguous migrations, no sample documents — do not proceed on an assumption. Say what you need (a connection string, a sample document, permission to run a read-only query) and stop there rather than guessing.

## Composes with (optional, never required)

Self-contained: nothing here is needed for this skill to work. When a companion is installed:

- **lsp**: in Phase 2, run `references` on the ORM model or class for precise call sites, instead of grepping a table name and drowning in false positives.
- **codebase-guardian**: governs the general edit and its Phase 4 verification. This skill specializes Phases 1–3 for the data layer.
- **memory**: confirmed schema facts and access patterns (keys, GSIs, reconciled migration state) go into `MEMORY.md`.
- **agents-dox**: a schema or migration change that alters a module's data contract triggers that subtree's DOX pass.
- **decision-maker**: in Phase 2, score every grep hit as real-usage-or-noise in one call, and check migration risk before Phase 3 (`decision-maker/references/use-cases.md` §5). It never replaces introspection.
