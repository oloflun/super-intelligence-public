# Installing the plugin

Step by step, per surface. Start with **A** — it is the one most people want, and
it takes about a minute.

Throughout: `<marketplace-repo>` is the GitHub repo holding the plugin
(`owner/name`). For this project that is `oloflun/super-intelligence-public`.

---

## A. Local Claude Code

Run these three commands. An agent can run them for you — they are ordinary CLI
calls, nothing interactive:

```bash
claude plugin marketplace add oloflun/super-intelligence-public
claude plugin install super-intelligence@super-intelligence --yes
claude plugin enable super-intelligence@super-intelligence
```

**Then restart Claude Code.** Skills and hooks are read when a session starts, so
the session you ran the install from will not see them. This is the single most
common reason people think the install failed.

Verify:

```bash
claude plugin list
```

You want `Status: ✔ enabled`. If it says `disabled`, run the `enable` line again —
a plugin installed from a newly added marketplace is disabled by default, and the
install output says so in a line that is easy to scroll past.

---

## B. Cloud sessions (claude.ai/code and scheduled routines)

A cloud session is a fresh VM every time, so the install has to run on each boot.
Put it in the environment's **Setup script** — see
[cloud-environment-setup.md](cloud-environment-setup.md) for the full script and
the reasoning behind each part.

Short version: claude.ai/code → cloud icon above the message box → hover the
environment → gear icon → *Setup script* → paste → Save.

Do **not** rely on a repo's `.claude/settings.json` alone. It works with one repo
attached and silently stops working with two, because the working directory moves
above both repos. That document explains the measurement.

---

## C. Chat and Cowork (claude.ai web and mobile)

These surfaces do not run hooks and have no filesystem, so they get skills only.

1. claude.ai → **Settings** → **Plugins**
2. **Add marketplace** → `oloflun/super-intelligence-public`
3. Enable the plugin

This step is **yours, not the agent's** — it is account configuration behind a UI
the agent cannot reach.

Skills carry their own trigger descriptions, so they activate on relevant
questions without being named. That activation is model judgment rather than a
deterministic hook, so it is less reliable here than in Claude Code. That is a
known and accepted difference, not a bug.

---

## Can the agent do this for me?

| Step | Who |
|---|---|
| `marketplace add` / `install` / `enable` locally | **Agent** — plain CLI commands |
| Restarting Claude Code | **You** |
| Pasting the cloud setup script | **You** — it is a field in the claude.ai UI |
| Adding the marketplace on your account | **You** — same reason |
| Connecting an MCP connector | **You** — OAuth or credential entry |

The rule of thumb: an agent can run anything that is a command. Anything that is
a **field in a web UI**, or that requires **entering a credential**, is yours. Do
not paste a token into a file and ask an agent to install it for you — put it in
the tool's own credential store instead.

---

## What happens to a setup you already have

Installing this plugin does not overwrite your existing configuration, but there
are three collisions worth knowing about before you install.

**1. One marketplace name, one source.** A marketplace name may be declared in
only one place. If `super-intelligence` is already declared pointing at a
different repo — in your user settings, or in a project's
`.claude/settings.json` — `marketplace add` refuses:

> `Cannot add marketplace "<name>": its network source differs from the one
> declared for it in settings`

This reads like a network or permission failure. It is not; the fetch is never
attempted. Fix it by making the two agree, or by removing the old declaration
first:

```bash
claude plugin marketplace remove super-intelligence
claude plugin marketplace add <the-source-you-actually-want>
```

Be deliberate about which source wins. If you maintain a private fork and a
public mirror, decide once and set every surface the same way — a project
declaring one source while your user settings declare another is the situation
that produces the error above, and it appears only when you open that project.

**2. The same plugin can be installed at several scopes.** User scope and project
scope are tracked separately, so `claude plugin list` can show the same plugin
three times at three different versions. It is not fatal, but it means "which
version is actually running here" has a non-obvious answer, and a stale project
scope can shadow a fresh user-scope install. Check with `claude plugin list`
before debugging behaviour that looks like an old version — because it is one.

**3. Hooks can fire twice.** If you previously copied any of this plugin's hooks
into `~/.claude/settings.json` by hand, remove those entries when you install the
plugin. The plugin registers its own hooks; leaving hand-added copies in place
means both run on every prompt, which usually shows up as duplicated injected
context rather than an error.

To check what is actually registered, look at the plugin's own `hooks.json`
inside its cache directory rather than at `settings.json` — and verify a hook by
its **effect** in the transcript, never by where it appears to be declared.

---

## Uninstalling

```bash
claude plugin disable super-intelligence@super-intelligence
claude plugin uninstall super-intelligence@super-intelligence
claude plugin marketplace remove super-intelligence
```

Restart afterwards. Nothing outside the plugin cache is touched, so anything you
wrote yourself stays where it is.
