---
name: locate-and-replicate-file
description: Locate a user-specified file on device storage and ensure a copy exists in the Hermes workspace (.hermes20). If file not found, create an empty placeholder.
---

**Trigger**: User asks to find or copy a specific file from phone storage to Hermes directory.

**Steps**:
- Clarify with user if they have a specific path or just filename. If user says the file is 'out there' or external but cannot specify exact location, ask for the exact directory or a more precise filename pattern before proceeding to search.
2. Search common storage locations (`/storage/emulated/0/Download`, `/storage/emulated/0`, etc.) for the file by name.
3. If found, copy the file to `~/.hermes20/` preserving name.
4. If not found, create an empty file with the given name in `~/.hermes20/`.
5. Verify the file exists and report its path and size.

**Pitfalls**:
- Assuming the file is in the current directory; always search storage.
- Not handling spaces or special characters in filename; use proper quoting.
- Overwriting existing file without warning; consider checking if user wants to overwrite.

**References**:
- See `references/session-2026-10-17.md` for an example session.