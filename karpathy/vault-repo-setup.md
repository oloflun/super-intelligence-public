# Building the vault as a git repo

Agent instructions for standing up the knowledge base this stack expects. The
vault is a **git repository of markdown files** — nothing else. No Obsidian, no
sync client, no database. Obsidian can be pointed at the checkout if you want a
nicer editor, but nothing here depends on it, and the stack never reads through
it.

This is the repo-based counterpart to `wiki-setup.md`, which describes the same
structure on a synced folder. Prefer this one. A folder owned by a sync client
can silently roll a file back to an older version mid-edit; a git repo cannot,
and `git log` tells you what happened either way.

## Why a repo and not a synced folder

Three properties the stack actually relies on:

1. **One reachable address on every surface.** Working locally, an agent reads
   files from the checkout. Working in a cloud session or a chat with a GitHub
   connector, the same agent reads the same paths out of the same repo over the
   network. One structure, two access methods, no divergence.
2. **History.** Retrieval quality regressions are usually a content change, not a
   code change. `git log -p` on a knowledge file answers "when did this get
   worse" in seconds.
3. **No silent overwrite.** A conflicting write is a merge conflict you must
   resolve, not a file that quietly reverted.

Make it **private** unless the knowledge in it is genuinely publishable. It will
accumulate client names, pricing and half-formed opinions faster than you expect.

## Structure

```
<vault-repo>/
├── wiki/
│   ├── concepts/          # reusable ideas, one per file
│   ├── entities/          # people, tools, systems, companies
│   ├── projects/
│   │   ├── _index/
│   │   │   └── portfolio.md      # every project, status, one line each
│   │   └── <slug>/
│   │       ├── <slug>.md         # the hub — see below
│   │       └── GOALS.md          # what done means, sub-goals in order
│   ├── sources/           # one page per ingested conversation/article
│   └── domains/           # long-lived reference KBs, split into sections
├── raw/                   # unprocessed captures, before ingestion
├── memory/
│   ├── MEMORY.md          # environment facts, hard cap ~2 000 chars
│   ├── USER.md            # preferences and corrections, hard cap ~1 400 chars
│   └── BLOCKS.md          # why work stopped, and what unstuck it
├── session-logs/          # one file per session, YYYY-MM-DD-session-log.md
└── plans/                 # YYYY-MM-DD-<slug>.md, one per work stream
```

Two rules keep this from rotting:

**The hub carries frontmatter, and agents read the frontmatter, not the prose.**

```yaml
---
title: <Project name>
type: project
status: active            # active | parked | reference — anything but active is not available work
project_slug: <slug>
repo: <path or URL>
goal: "<one sentence: what this is and for whom>"
next_milestone: "<the next thing that would count as progress>"
milestone_blockers:
  - "<what is actually in the way>"
updated: YYYY-MM-DD
---
```

`status` is what stops an agent proposing work on something you deliberately
parked. `updated` is what tells it the rest of the file may be stale. Both are
worth more than the prose beneath them.

**The hot memory files have hard caps and they are load-bearing.** They are
injected into context every session, so an uncapped `MEMORY.md` is a slow tax on
every conversation. When one hits its cap, move the oldest resolved entries to a
`-FULL.md` beside it rather than deleting them. Only write to these at session
end, never mid-session — an agent that edits its own live context mid-task
produces confusing results.

## Access: local when local, remote when remote

The agent must resolve *where* the vault is rather than assume it. Resolution
order, most explicit first:

1. `CLAUDE_VAULT` environment variable, if set — the override for anyone whose
   checkout is somewhere unusual.
2. A conventional local path, if it exists on this machine.
3. `CLAUDE_PROJECT_DIR`, when the vault repo *is* the project being worked on.
4. A sibling directory of the project — cloud sessions with several repos
   attached place them side by side under a common parent.
5. Nothing resolved → **say so and read over the network instead.** Name the repo
   and branch explicitly.

That last step matters more than it looks. An agent given a bare relative path
with no root will guess a root, and a wrong guess costs tool calls and can
silently read a stale copy. Emit an absolute path when you can resolve one, and
when you cannot, say which repo to fetch from — never a naked relative path.

For the remote case, the GitHub MCP server (`https://api.githubcopilot.com/mcp/`)
gives read and write against a private repo from chat and cloud sessions alike.
Connect it once at the account level and it reaches every surface.

## Splitting large reference files

A knowledge base file over ~50 KB is unreadable over a connector — fetching it
burns the context it was supposed to inform. Keep the canonical file as the write
target, and generate section mirrors as a build step:

```
wiki/domains/<domain>/<domain>.md              # canonical, written by ingestion
wiki/domains/<domain>/sections/NN-<slug>.md    # generated, one per H2
wiki/domains/<domain>/sections/INDEX.md        # section number → title → filename
```

Agents read `INDEX.md` first, then fetch exactly one section. Never point them at
the canonical file. Regenerate the mirrors whenever the canonical file changes —
if regeneration is manual it will drift, so wire it into whatever already runs on
a schedule.

## Ingestion

Captured material lands in `raw/` and becomes a `wiki/sources/` page. Extraction,
not summary: pull out the problem, the solution, what worked, what didn't, the
key insight, where it applies, and the date it was true. A summary of an article
is worth little; the claim you can act on is worth keeping.

Keep a ledger (`.ingest-ledger.json`) of what has been processed so re-runs are
idempotent, and link every new page to at least one existing page. An orphan page
is one nothing will ever retrieve.

## Bootstrapping checklist

1. Create the repo, private, one default branch. Do not reuse a repo that holds
   code — the churn patterns are different and the ignore rules will fight.
2. Create the directory skeleton above with a `.gitkeep` in each empty directory.
3. Write `wiki/projects/_index/portfolio.md` with one line per project. This is
   the cheapest possible answer to "what am I working on" and the first thing an
   agent should read on a broad question.
4. Create a hub and a `GOALS.md` for each active project, with real frontmatter.
5. Create the three memory files with their caps stated in a comment at the top.
6. `.gitignore`: editor state, OS junk, caches, anything a sync client writes,
   and any vendored subtree over a few MB. Check nothing above ~20 MB is tracked
   before the first push — a knowledge repo that grew to gigabytes has something
   in it that does not belong.
7. Connect the GitHub MCP server at the account level so the same repo is
   reachable from chat and cloud sessions, not only from the checkout.

## What not to do

- **Do not put the vault inside a sync-client folder.** If you must, relocate the
  git directory outside it with `git init --separate-git-dir`.
- **Do not `git add -A`.** Ingestion and generation touch many files; a blanket
  add sweeps unreviewed content into a commit. Stage explicit paths.
- **Do not let an agent write to the hot memory files mid-session.**
- **Do not skip `status:`.** Without it, every parked project comes back as a
  suggestion, forever.
