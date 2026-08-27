---
name: api-key-setup
description: "Use whenever a project needs API keys/secrets set up for local dev and deploy — generates a project-specific script that discovers required keys, writes them to the right gitignored env files (or, for apps that store credentials via their own authenticated API rather than env vars, a headless script against that API), verifies gitignore status, and pushes/pulls them to the actual deploy targets. Trigger on: 'set up the API key', 'I need to add a key', 'how do I configure this key', 'nycklar', 'sätta nycklar', or when a task is blocked on a missing credential."
version: 1.1.0
metadata:
  tags: [secrets, env, deploy, onboarding, developer-experience]
  category: dev-tools
---

# API Key Setup

## When to Use

Any time a task is blocked on a missing API key/secret, or a user asks to configure one:
- A new integration needs a credential (LLM provider, scraping service, vision/embeddings, etc.)
- Local `.env`/`.env.local` is missing values a codebase reads
- Deploy is failing because an env var isn't set on the host

Do NOT use this for account passwords, payment credentials, or anything that belongs in a
password manager — this is for developer-facing API keys that live in env files.

## Procedure

### 0. Confirm the credential is actually env-file-shaped before assuming it is

Some apps — especially CMS-style servers with their own admin UI — store provider credentials
encrypted in their own DB via an authenticated API, not an env var. Grep for the storage
mechanism, not just the read side: an admin-panel "AI provider" or "integrations" settings page
is a strong signal. If you find a credentials table/handler (e.g. `POST /admin/api/.../credentials`)
instead of an `os.environ`/`process.env` read, this is Case B below, not Case A. Doing this check
first avoids writing a `.env` script for a value the app will never read from there.

**Case A — env file.** Continue with steps 1-5 below.

**Case B — DB-stored via the app's own authenticated API.** The `.env`-file steps don't apply.
Instead:
1. Find how the app authenticates its own admin API (session cookie, API token, etc.) and
   whether it has a **local, no-password dev-auth path** — many local-dev servers can mint a
   valid session by inserting a row directly into the local dev DB (hash a random token, insert
   into the sessions table, done) rather than going through a login form. If one doesn't already
   exist as a script, write one; keep it gitignored, same as any other local secret material.
2. Write a small script that POSTs to the app's own credential-creation endpoint, reading the key
   from **stdin only** (never a CLI arg — arg lists land in shell history and process listings).
   Never print the key back; only print what the app's own response considers safe to return
   (label, provider, timestamps — never plaintext/ciphertext).
3. **Verify by calling the app's own test/validate endpoint for that credential**, if one exists
   (e.g. `POST .../credentials/:id/test`), not just by listing that a record was created. A
   record existing proves the write worked; it does not prove the key is valid. This is a
   sharper version of Pitfall 6 below — the DB-record layer adds a second place a smoke check
   can stop short of the real thing.
4. If the app's own UI is *also* broken (not just slow to set up) and that's *why* you're doing
   this headlessly, don't silently work around it — tell the user what you found (e.g. "the
   admin UI hangs indefinitely, likely a local proxy/VPN extension issue") so they can decide
   whether to fix the UI or keep using the script going forward.

### 1. Discover what's actually needed — don't ask blind

Grep the codebase for how config is read (`os.environ`, `getenv`, `process.env`,
`pydantic-settings` `Settings` classes, `.env.example` files). Build a list of:

- **Key name** (exact env var name)
- **Which file(s)** it must land in — a monorepo often has more than one runtime
  (e.g. a Python backend's own `.env` AND a Next.js `.env.local`). Don't assume one file.
- **Required vs optional** — does the app degrade gracefully without it (simulation mode,
  a specific feature disabled) or does everything break?
- **Where to obtain it** — the exact dashboard URL, not a guess
- **Free tier availability** — worth surfacing explicitly if relevant to the user's stated
  goal (e.g. "start on the free tier"). Verify this by checking the provider's own docs AND
  a live search if the docs page routes to a personalized dashboard instead of publishing
  numbers — say so honestly rather than presenting scraped blog-aggregator numbers as fact.

### 2. Verify gitignore BEFORE writing anything

Every target file must already match `.gitignore`. Check with
`git check-ignore <relative-path>` for each target file. If any file isn't ignored, **stop
and fix `.gitignore` first** — never write a secret into a file that could be committed.

### 3. Generate a project-specific script from the template

Copy `templates/keys_template.py` into the project's `scripts/` directory (or that
project's existing scripts location), rename to `keys.py`, and adapt:

- Fill in `ROOT`, `TARGET_FILES` (one `Path` per env-file the project actually has)
- Fill in `KEYS` — one entry per discovered key, using the `Key(name, files, blurb,
  required, where)` shape from the template
- Fill in `FIXED` for any config that's a fixed consequence of having a key (e.g. picking
  a provider name / default model once a key for it exists)
- Wire `--push`/`--pull` to whatever deploy target(s) the project actually has (Vercel CLI,
  Render CLI, flyctl, etc.) — **only** for keys that file targets include the *frontend*
  file (see Pitfall 5). If the project has no deploy CLI available, drop those subcommands
  rather than leaving them silently broken.

Resolve every path from `Path(__file__).resolve()`, never from `cwd` — see Pitfall 1.

### 4. Run `--check` and show the user exactly what it reports

Never claim a key is "set" without having the script re-read the file and confirm. Report
length + last 4 characters only — never the full value, even to the user who owns it, since
chat transcripts get logged/searched.

### 5. Point the user at the exact dashboard, let them run the script themselves

The key must be created by the user in the provider's own dashboard — never attempt to
generate, request, or infer an API key yourself. Give the exact command
(`python "<absolute path>\scripts\keys.py"`) and the exact URL for each key.

## Pitfalls

Each of these cost real debugging time in production use of this skill. Don't skip them.

1. **Relative `env_file` paths silently break as soon as anything runs from a different
   `cwd`.** A Python `pydantic-settings` `Settings.model_config` with `env_file=".env"`
   resolves against the process's current directory, not the file's own location. A script
   or service run from the repo root instead of the backend's own directory will read *zero*
   keys and fail with a generic auth error that looks like a bad key, not a bad path. Always
   use `env_file=str(Path(__file__).resolve().parent / ".env")` or equivalent.

2. **`monkeypatch.delenv` does not override a value that lives in the `.env` FILE, only
   the process environment.** If a test wants to simulate "key missing" and the key is
   actually sourced from an `.env` file (common with pydantic-settings, dotenv, etc.),
   `delenv(key, raising=False)` on a variable that was never in `os.environ` is a no-op —
   the library still reads it from the file. Use `monkeypatch.setenv(key, "")` instead,
   which genuinely overrides (env vars outrank `.env` file values in precedence). This
   caused a test to make a real network call by accident.

3. **A test suite that passed before real keys existed can silently stop being hermetic
   the moment real keys land on the machine.** If tests rely on `is_simulation()`-style
   fallback behavior, that fallback quietly stops firing once a real key is present, and
   tests that were never designed to hit the network start doing so. Add an
   autouse fixture (`conftest.py`) that forces empty/fake credentials for the whole suite,
   so test behavior never depends on what happens to be in the developer's environment.

4. **Don't presume all keys are needed to start.** If one key unlocks the whole system and
   others only unlock secondary features (e.g. a vision/embeddings sidecar, an optional
   scraping tool), say so explicitly and let the user start with just the one that matters.
   Don't make onboarding feel bigger than it is.

5. **Don't push every discovered key to every deploy target.** In a project with both a
   backend host (Render, Fly, etc.) and a frontend host (Vercel), a key that's only consumed
   by the backend does not belong pushed to the frontend project just because a `--push`
   command exists. Scope `--push` to keys whose `files` list actually includes that target's
   env file — otherwise it either does nothing useful or pollutes an unrelated project with
   secrets it doesn't read. Verify this with an actual dry run, not by assumption.

6. **A single trivial API call proves the key works, not that the feature works.** Don't
   let a smoke test ("is the key valid") stand in for a real evaluation of output quality —
   especially for anything involving model behavior toggles (reasoning/thinking modes,
   temperature, etc.). If the user is deciding between two configurations, they need
   comparison data from real task output, not a synthetic ping.

7. **Record-exists is not the same claim as record-works, and Case B makes the gap wider.**
   A DB-stored credential can be created successfully (valid schema, valid auth, 201 response)
   while still holding a typo'd or expired key — the write path and the provider-auth path are
   fully independent. Never report a Case B credential as "configured" without having called
   the app's own test endpoint against it; if none exists, make a minimal real call yourself
   (e.g. the provider's models-list endpoint) rather than trusting creation success.

## Verification

- `git check-ignore` returns 0 for every target file before the script ever writes to it.
- `python scripts/keys.py --check` (or equivalent) reports each key's status without ever
  printing the full value.
- The consuming app's own settings-loader confirms the key resolved (e.g. a one-line
  `is_simulation()`-style check), run from a *different* `cwd` than the script itself, to
  catch Pitfall 1.
- Test suite still passes with real keys present on the machine (catches Pitfall 3).
- **Case B specifically:** the app's own credential-test endpoint returns a live success (not
  just a 2xx on creation) — e.g. a real provider API call proxied through the app, with a
  concrete result value (model count, account info) printed, not just `ok: true`.

## Changelog
- 2026-08-15 v1.1.0 — Added Case B (DB-stored credentials via the app's own authenticated API,
  not an env var) and Pitfall 7 (record-exists ≠ record-works). From `project-a-next`/ExampleCMS: the
  admin UI was unreachable (client-side, likely a VPN extension hanging `localhost` fetches
  indefinitely with no error), so a DeepSeek `openai-compatible` credential was added via a
  headless script — locally-minted session cookie (zero password contact), key via stdin only,
  verified live against the app's own `POST .../credentials/:id/test` endpoint
  (`{ ok: true, modelCount: 2 }`), not just confirmed-created.
- 2026-08-07 v1.0.0 — Initial creation, generalized from a same-session incident: a
  hand-rolled two-script key setup on `project-b` (Anthropic/DeepSeek/Gemini/ScrapeGraphAI
  keys for the `snajp-support` backend) that hit five of the six pitfalls above before
  landing on the pattern this skill now captures.
