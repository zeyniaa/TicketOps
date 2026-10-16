# Arsitektur TicketOps

## Runtime dan data flow

React → FastAPI → PostgreSQL (Docker) atau SQLite WAL (quickstart) → satu worker → classifier → routing rules → BM25 policy retrieval → Ollama → validasi → draf → review operator.

Ticket creation and job insertion occur in one transaction. PostgreSQL claims use `FOR UPDATE SKIP LOCKED`; SQLite uses a compare-and-swap status update and supports a single worker. A job lease expires after 480 seconds. Interrupted jobs retry up to three claims. Run only one worker on the supported laptop profile. There is no browser-to-Ollama connection.

The UI polls every two seconds while a job is active. Classifier output is committed before generation, so it remains visible if Ollama is slow. The UI displays real stages rather than an invented percentage. Model output has provenance (`inference`, `ollama`, `template`, or `stored_example`).

## Review lifecycle

Ticket states: `baru`, `ditinjau`, `disetujui`, `selesai`. Changes to category, team, or priority increment the analysis revision and mark previous drafts stale. Every draft records the revision of the ticket it used. Editing a draft increments its version and removes approval. Approval checks the latest draft, ticket revision, optimistic version, and active jobs. Completing a ticket requires an approved current draft. Newer ticket revisions prevent older jobs from publishing a new draft.

AI categories, final operator categories, rule priorities, and operator corrections are stored separately in analysis/feedback/audit history. Feedback is not online training. Example seed analyses explicitly have no prediction score.

## Policies and orders

24 fictional, versioned policies. BM25 returns at most three policies with a category boost. Citation references are validated against supplied IDs and versions. Drafts retain full source snapshots. Reference validation is not a factuality guarantee. Order lookups are read-only and scoped to the current demo workspace; all facts are simulated.

## Access boundaries

Opaque HttpOnly SameSite cookies identify isolated demo workspaces. Mutation endpoints check session CSRF tokens and Origin. API responses are no-store. Resource lookups enforce workspace ownership, including indirectly owned drafts and jobs. Session creation itself checks Origin but requires no existing CSRF token. This is a local portfolio demo, not a complete multi-user authentication system.

Request metadata logs exclude ticket contents. Demo limits are 20 tickets and five outstanding jobs per workspace. They are demo limits, not a distributed abuse-prevention system. There is no public live-input backend in the hosted showcase.

## Delivery modes

Local mode uses a live backend and actual inference. The hosted static showcase reads curated synthetic scenarios from a generated snapshot. Its edits and approvals only change browser session storage, and new free-form analysis is disabled. This distinction is visible in the UI.

## Validation boundary

SQLite integration and real Ollama smoke checks run on the current machine. Docker/PostgreSQL configuration is supplied; Docker is unavailable here, so that deployment has not been executed. IndoBERT training requires a separate Colab run. Human-quality evaluation is pending.
