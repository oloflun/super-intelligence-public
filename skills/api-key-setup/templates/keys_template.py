"""Nyckelhantering — TEMPLATE. Kopiera till <projekt>/scripts/keys.py och
fyll i ROOT-relativa TARGET_FILES + KEYS för det aktuella projektet.

Referensimplementation: project-b/scripts/keys.py (2026-08-07).

    python "<absolut sökväg>\\scripts\\keys.py"          # sätt + verifiera
    python .../scripts/keys.py --check                    # bara verifiera
    python .../scripts/keys.py --pull                      # hämta från deploy-mål
    python .../scripts/keys.py --push                      # skicka till deploy-mål

Sökvägar löses ur __file__, ALDRIG ur cwd (se SKILL.md Pitfall 1 — en
relativ env_file-sökväg i den konsumerande appens Settings-klass går sönder
tyst så fort något körs från en annan katalog). Värden läses med getpass
(syns aldrig, hamnar aldrig i shell-historiken) och skrivs bara till
gitignorerade filer.

Nycklar hör ALDRIG hemma i databasen — cirkulärt (appen behöver ändå en
databasnyckel i env för att läsa dem) och exponerar en läsbehörighet på en
tabell till mer än den borde nå.
"""

from __future__ import annotations

import argparse
import getpass
import subprocess
import sys
from pathlib import Path

# --- FYLL I: projektets rot och de faktiska env-filerna ------------------
ROOT = Path(__file__).resolve().parent.parent  # justera antal .parent efter var scriptet hamnar
BACKEND_ENV = ROOT / "backend" / ".env"          # exempel — döp om/lägg till fler
FRONTEND_ENV = ROOT / ".env.local"               # exempel — ta bort om projektet saknar frontend


class Key:
    def __init__(self, name, files, blurb, *, required, where):
        self.name, self.files, self.blurb = name, files, blurb
        self.required, self.where = required, where


# --- FYLL I: en Key per upptäckt nyckel -----------------------------------
# files = lista av Path — VILKA filer den ska skrivas till. En nyckel som
# bara backend läser ska INTE ligga i FRONTEND_ENV (se SKILL.md Pitfall 5).
KEYS = [
    Key(
        "EXAMPLE_REQUIRED_KEY",
        [BACKEND_ENV],
        "En rad: vad den driver, vad som händer utan den.",
        required=True,
        where="https://example.com/api-keys",
    ),
    # Key("EXAMPLE_OPTIONAL_KEY", [BACKEND_ENV], "...", required=False, where="..."),
]

# --- FYLL I: konfiguration som är en direkt konsekvens av en satt nyckel --
FIXED: dict[Path, dict[str, str]] = {
    # BACKEND_ENV: {"LLM_PROVIDER": "example", "MODEL": "example-model"},
}


def looks_placeholder(value: str) -> bool:
    """Matcha den konsumerande appens egen is_simulation()-heuristik om den har en."""
    return len(value) < 20 or "..." in value or "din-" in value or "your-" in value


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def upsert(path: Path, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def guard_gitignored(target_files: list[Path]) -> None:
    for path in target_files:
        relative = path.relative_to(ROOT).as_posix()
        result = subprocess.run(
            ["git", "check-ignore", relative], cwd=ROOT, capture_output=True, text=True
        )
        if result.returncode != 0:
            sys.exit(f"AVBRYTER: {relative} är inte gitignorerad — nycklar kunde committas.")


def cmd_check() -> bool:
    print(f"Repo: {ROOT}\n")
    ok = True
    for key in KEYS:
        value = read_env(key.files[0]).get(key.name, "")
        if not value:
            status = "SAKNAS" if key.required else "tom (valfri)"
            ok = ok and not key.required
        elif looks_placeholder(value):
            status = "PLATSHÅLLARE — appen kör troligen i simuleringsläge"
            ok = False
        else:
            status = f"OK (len={len(value)}, ...{value[-4:]})"
        flag = "KRÄVS" if key.required else "valfri"
        print(f"  {key.name:28} [{flag:6}] {status}")
    print("\nKLART." if ok else "\nBLOCKERAT — se SAKNAS/PLATSHÅLLARE ovan.")
    return ok


def cmd_set() -> None:
    all_files = sorted({f for key in KEYS for f in key.files} | set(FIXED))
    guard_gitignored(all_files)
    print(f"Repo: {ROOT}")
    print("Lämna tomt för att hoppa över (befintligt värde behålls).\n")

    for key in KEYS:
        current = read_env(key.files[0]).get(key.name, "")
        marker = " [redan satt]" if current and not looks_placeholder(current) else ""
        print(f"{key.name}{marker}\n  {key.blurb}\n  Hämtas här: {key.where}")
        value = getpass.getpass("  Klistra in (syns inte): ").strip()
        if not value:
            print("  -> hoppar över\n")
            continue
        for path in key.files:
            upsert(path, key.name, value)
        print(f"  -> sparad i {', '.join(p.name for p in key.files)}\n")

    for path, pairs in FIXED.items():
        for name, value in pairs.items():
            upsert(path, name, value)
    cmd_check()


def cmd_pull() -> None:
    """FYLL I: hämta env från projektets deploy-mål (Vercel/Render/Fly/...) om relevant."""
    print("--pull inte konfigurerat för det här projektet ännu — fyll i templaten.")


def cmd_push() -> None:
    """FYLL I: skicka till deploy-mål. Bara nycklar vars files-lista faktiskt
    inkluderar MÅLETS env-fil — se SKILL.md Pitfall 5."""
    print("--push inte konfigurerat för det här projektet ännu — fyll i templaten.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Nyckelhantering.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()

    if args.check:
        sys.exit(0 if cmd_check() else 1)
    if args.pull:
        cmd_pull()
    elif args.push:
        cmd_push()
    else:
        cmd_set()


if __name__ == "__main__":
    main()
