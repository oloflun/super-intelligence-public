---

name: search-memory

description: Search across saved plans and session history

---



\# Search Memory



Search across Project memory (`\~/.agents/memory/<project-slug>`) to find past sessions, decisions, errors, handoffs and plans.



\## Usage



User invokes with: `/search-memory <query>`

or `/search-memory <query> --plans`

or `/search-memory <query> --sessions`



\## Steps



1\. Run the search script:



\~/.agents/scripts/search-memory.sh "<query>" \[--plans|--sessions|--all]



Default scope is `--all` (searches all categories).



2\. Present results clearly:

\- \*\*Plans:\*\* Show filename, title, modification date, and matching

&#x20; context lines. Include the full file path so the user can ask

&#x20; to read a specific plan.

\- \*\*Sessions:\*\* Show date, first message text, and session ID.

&#x20; Note that `/resume <sessionId>` can reopen a session.



3\. If the user wants to dig deeper into a specific plan, `Read`

the file and summarize its contents.



4\. If no results found, suggest alternative search terms.

