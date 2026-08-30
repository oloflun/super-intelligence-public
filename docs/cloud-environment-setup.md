# Cloud environment setup script

Agent instructions for making this stack work in Claude Code cloud sessions
(claude.ai/code, and scheduled routines). Everything here is a workaround for one
fact: **a cloud session is a fresh VM that knows nothing about your setup**, and
several of the mechanisms that configure it locally do not run there.

The fixes go in the environment's **Setup script** field, not in a repo. Find it
at claude.ai/code → the cloud icon above the message box → hover the environment
→ the gear icon → *Setup script* → Save. It runs as root, before Claude Code
starts, and its result is cached for roughly a week or until the script changes.

Everything below was measured in a live cloud VM, not inferred from docs. Where a
behaviour is surprising, the measurement is stated so you can re-check it rather
than trust this file.

## Why a repo can't configure itself here

A cloud session with **one** repo attached gets `cwd` inside that repo, and
`<repo>/.claude/settings.json` applies as you'd expect.

Attach **two or more** repos and the working directory moves up to their common
parent. Measured layout:

```
pwd  = /home/user            <- the working directory
HOME = /root                 <- NOT the same directory
repos = /home/user/<repo-a>, /home/user/<repo-b>
/home/user/<repo-a>/.claude/settings.json   exists, and is never loaded
```

Claude Code searches upward from `cwd`, and the common parent sits *above* both
repos — so nothing inside either repo applies. A `CLAUDE.md` in a repo root does
not fix this either; it is on the wrong side of `cwd`.

What always applies is the user level under `$HOME`. The setup script can write
there, which is what makes it the right place for anything that must hold on
every surface.

Note that `HOME` and `cwd` are different directories. A script that assumes they
are the same will write to a path nothing reads.

## Three things worth doing

### 1. Neutralise the auto-push Stop hook

Cloud images ship `~/.claude/stop-hook-git-check.sh`, which on every Stop demands
that untracked files be committed **and pushed**. It is not configurable
([anthropics/claude-code#50481](https://github.com/anthropics/claude-code/issues/50481)),
and it will push to the default branch on its own.

If your workflow is "the human decides what gets committed", that is a
correctness problem, not a preference. Replace the file's contents with a no-op
rather than deleting it — deleting can make the registration itself fail — and
keep the original beside it:

```bash
if [ -f "$HOME/.claude/stop-hook-git-check.sh" ]; then
  cp "$HOME/.claude/stop-hook-git-check.sh" \
     "$HOME/.claude/stop-hook-git-check.sh.orig" 2>/dev/null || true
  printf '#!/bin/bash\n# Neutralised by the environment setup script.\nexit 0\n' \
    > "$HOME/.claude/stop-hook-git-check.sh"
  chmod +x "$HOME/.claude/stop-hook-git-check.sh" 2>/dev/null || true
fi
```

Verify by running a session that leaves an untracked file: no feedback line, no
commit, no push.

### 2. Install plugins at the user level

Headless sessions **never register marketplaces on their own** — you get "No
marketplaces configured" even though the network path works fine, because the
trust flow that normally registers them does not run. The plugins must be
installed actively.

Two traps here, both of which produce misleading errors:

**Do not pre-declare the marketplace in `settings.json`.** If a name is already
declared pointing somewhere else, `marketplace add` refuses:

> `Cannot add marketplace "<name>": its network source differs from the one
> declared for it in settings`

This reads like an access failure and is not one — it never attempts the fetch.
Let `marketplace add` write the declaration itself, and keep `settings.json` to
`enabledPlugins` only.

**A plugin installed from a newly added marketplace is disabled by default**
("This plugin is disabled by default — enable it with: …"), so `enabledPlugins`
is not sufficient on its own. Call `plugin enable` explicitly.

```bash
mkdir -p "$HOME/.claude" 2>/dev/null || true

if [ ! -f "$HOME/.claude/settings.json" ]; then
  cat > "$HOME/.claude/settings.json" <<'SETTINGS'
{
  "enabledPlugins": {
    "<plugin>@<marketplace>": true
  }
}
SETTINGS
fi

if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add <owner>/<marketplace-repo> >/dev/null 2>&1 || true
  claude plugin install <plugin>@<marketplace> --yes        >/dev/null 2>&1 || true
  claude plugin enable  <plugin>@<marketplace>              >/dev/null 2>&1 || true
fi
```

**Private repositories work as marketplaces.** A cloud VM clones a private repo
over HTTPS with the session's own credentials — no token needs to go in the
script. If you keep a private source and a public mirror, try the private one
first and fall back, so a session is never left with no plugin at all:

```bash
if ! claude plugin marketplace add <owner>/<private-repo> >/dev/null 2>&1; then
  claude plugin marketplace add <owner>/<public-mirror> >/dev/null 2>&1 || true
fi
```

Never put a token or API key in this script. Environment scripts and routine
prompts are visible to anyone who can list them, and they are not a secret store.

### 3. Write user-level instructions that survive any working directory

Hooks are the precise mechanism — a `UserPromptSubmit` hook can route to an exact
knowledge-base section for a couple of hundred tokens. But hooks registered in a
repo stop applying the moment `cwd` moves above that repo, and they do not exist
at all in chat.

So put the *policy* in `$HOME/.claude/CLAUDE.md`, where it loads regardless of
`cwd`, and let the hook remain the precise path when it can fire. The two
compose: the file states the rule, the hook supplies the specifics.

```bash
cat > "$HOME/.claude/CLAUDE.md" <<'MEMORY'
# <your rules that must hold on every surface>
MEMORY
```

Keep it short. Unlike a hook, this is loaded on **every** prompt whether it is
relevant or not, so it should carry rules and pointers, never content. If you
find yourself pasting knowledge into it, that knowledge belongs in a skill or a
repo the agent can fetch on demand.

## Ordering and caching

The script runs before Claude Code starts, so anything it writes is in place for
the first prompt. The result is cached — editing the script invalidates the
cache, but pushing new content to a marketplace repo does **not**. If you change
the plugin and want a session to pick it up, the session must re-run the install,
which it does on a fresh environment.

Sequence when changing both: push the marketplace repo first, then re-save the
setup script. Doing it the other way round gives you a session or two running the
old content.

## Verifying it worked

Ask a session to report, and read the raw output rather than a summary:

```bash
head -5 ~/.claude/CLAUDE.md
cat ~/.claude/settings.json
claude plugin list
head -3 ~/.claude/stop-hook-git-check.sh
pwd && echo "$HOME"
```

A useful signal beyond the file contents: count the hook events in the session
log. A multi-repo session where user-level config is working shows an order of
magnitude more `hook_started` events than one where only repo-level config was
declared — that difference is the fix landing, and it is visible without asking
the session to introspect.
