---
name: file-retrieval-from-android-storage
description: Locate and copy user files from Android internal/external storage into Hermes workspace.
category: file-operations
---

# Find and Copy User Files from Android Storage to Hermes

## When to Use
Use this skill when you need to locate a file that the user believes exists on their device (outside Hermes directories) and copy it into the Hermes workspace (`~/.hermes20/` or a subdirectory) for further processing.

## Steps
1. **Confirm the expected filename** – ask the user for the exact name or a pattern if unsure.
2. **Check Hermes directories first** – look in `~/.hermes20/` and any relevant subdirectories (e.g., `skills/`, `plugins/`).
3. **Search common Android storage locations** – if not found, search:
   - `/storage/emulated/0/Download`
   - `/storage/emulated/0/Documents`
   - `/storage/emulated/0/DCIM`
   - `/storage/emulated/0/Pictures`
   - Use `find` with `-iname` for case-insensitive matching, limiting depth to avoid scanning entire filesystem.
4. **Handle multiple matches** – if more than one candidate is found, present the list to the user and ask which to use.
5. **Copy the file** – once the correct file is identified, copy it to the target location within `~/.hermes20/` (preserving the base name unless the user specifies otherwise).
6. **Verify** – confirm the file exists at the destination and report its size or a preview if appropriate.

## Pitfalls
- Assuming the file is already inside Hermes directories; always verify with a quick search before concluding it is missing.
- Scanning the entire filesystem can be slow and may hit permission barriers; limit searches to user‑accessible storage directories.
- Forgetting to check for case‑insensitive variants on Android filesystems.

## Verification
After copying, run `ls -lh <destination>` and optionally `head -n 5 <destination>` to ensure the file is not empty and contains expected content.

## Example
User: “I have a file called `autonomous_trading_controller` in my Downloads folder.”
Agent:
1. Check `~/.hermes20/` → not found.
2. Search `/storage/emulated/0/Download` → finds `/storage/emulated/0/Download/autonomous_trading_controller`.
3. Copy to `~/.hermes20/autonomous_trading_controller`.
4. Confirm copy succeeded.