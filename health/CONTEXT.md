# health/ — does every layer actually work?

## Why this folder exists

The plugin updates itself on every upstream commit. That is only safe if a broken
commit is caught before anyone installs it, so the checks below are the thing that
makes auto-update acceptable rather than reckless.

They also answer a question the repo could not answer before: *installed* is not
the same as *working*. A skill file can exist and still have unparseable
frontmatter; a hook can be declared and point at a script that was never shipped;
a manifest can be valid JSON and still name a directory that does not exist.

## Inputs

Reference (every run):
- `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — the manifest
- `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/marketplace.json` — the self-marketplace
- `health/forbidden-patterns.txt` — identifiers that must never ship

Working (this run):
- Everything under `skills/`, `hooks/`, `agents/`

## Process

`python health/check-all.py` runs six checks in order. Each is independent and
reports its own PASS/FAIL; the run exits non-zero if any check fails.

| # | Check | Fails when |
|---|---|---|
| 1 | manifest | `plugin.json` is missing/invalid, or declares a directory that does not exist |
| 2 | skills | a `SKILL.md` lacks frontmatter, `name`, or `description`, or the folder name and `name:` disagree |
| 3 | hooks | `hooks.json` is invalid, names an unknown event, or points at a script that is not on disk |
| 4 | agents | an agent file has no frontmatter or no description |
| 5 | portability | an absolute home-directory path, a Windows drive letter, or an MSYS `/c/` path survives anywhere in shipped files |
| 6 | privacy | any pattern in `forbidden-patterns.txt` appears in a shipped file |

Checks 5 and 6 are the ones that matter most here. This plugin is extracted from a
private working repo, so sanitization is not a one-time cleanup that someone
remembers to redo — it is a test that runs on every commit and fails the build.

## Outputs

- stdout: one line per check, detail lines only for failures
- exit code: 0 = every layer verified, 1 = at least one failed
- `--json`: machine-readable result, for CI and for the assistant layer's own
  health sweep to consume

## The two checks this suite deliberately does not do

**`claude plugin validate .`** — the manifest contract as Claude Code itself parses
it. Kept separate on purpose: if the plugin format changes, it should surface as a
validator failure rather than quietly passing home-grown checks. It caught a real
error this suite missed (`repository` must be a string, not an object).

Note it runs **without** `--strict`. Strict fails on the missing `version` field —
which is exactly the design: no version means the commit SHA is the version, which
is what makes installs follow every commit. Passing strict would mean giving that up.

**The load smoke test** — the only check that proves *installed* equals *working*:

```bash
claude --plugin-dir /path/to/this/repo -p "reply with OK"
```

It needs credentials, so it cannot run in CI; run it by hand before publishing a
structural change. Everything above verifies that files resolve. This verifies that
Claude Code accepts them.

## Human check

Run `python health/check-all.py` after any structural change. A green run means the
plugin installs and every declared component resolves — it does not mean the skills
give good advice. That is what review is for.
