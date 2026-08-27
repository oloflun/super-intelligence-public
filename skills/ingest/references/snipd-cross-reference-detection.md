# Snipd Cross-Reference Detection

When `ingest-pending.sh all` times out (common on Windows OneDrive vaults) or the status-based grep returns false positives, use this Python method to detect truly unprocessed Snipd files.

## Method

Compare every Snipd file under Snipd/Data/<show>/ against every existing page in wiki/sources/. A file is "unprocessed" if no source page references its episode title.

```python
import os

VAULT = r"{{VAULT_PATH}}"
snipd_dir = os.path.join(VAULT, "Snipd", "Data")
sources_dir = os.path.join(VAULT, "wiki", "sources")

snipd_files = []
for show in sorted(os.listdir(snipd_dir)):
    show_dir = os.path.join(snipd_dir, show)
    if os.path.isdir(show_dir):
        for f in sorted(os.listdir(show_dir)):
            if f.endswith(".md"):
                snipd_files.append((show, f))

source_files = [f for f in os.listdir(sources_dir) if f.endswith(".md")]

missing = []
for show, filename in snipd_files:
    rel_path = f"Snipd/Data/{show}/{filename}"
    episode_key = filename.replace(".md", "").strip()[:50]
    episode_lower = episode_key.lower()
    
    matched = False
    for sf in source_files:
        sf_path = os.path.join(sources_dir, sf)
        try:
            with open(sf_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read(2000)
                if episode_lower in content.lower():
                    matched = True
                    break
        except:
            pass
    
    if not matched:
        missing.append(rel_path)

print(f"Files with existing source pages: {len(snipd_files) - len(missing)}")
print(f"Files MISSING source pages: {len(missing)}")
for m in sorted(missing):
    print(m)
```

## How it works

- Iterates all Snipd show directories
- For each .md file, takes the first 50 chars of the filename as the episode key
- Reads the first 2000 chars of each wiki/sources/ page (enough to catch frontmatter and section headers)
- Case-insensitive comparison against the episode key
- Reports files with no match as "missing" (truly unprocessed)

## When to use

- After `ingest-pending.sh all` times out
- When you need a definitive list before initializing a batch
- Before running --strays to double-check what graph-stray-audit missed
