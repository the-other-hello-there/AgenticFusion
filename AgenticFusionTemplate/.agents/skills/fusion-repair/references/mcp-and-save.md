## MCP output, timeout, and crash

- **`The operation timed out.`** The script can still be running in Fusion, with later calls queued behind it. Wait, then poll with a read-only script; do not blindly rerun the build. Split future heavy builds into batches and log progress to a scratchpad file.
- **Empty MCP output mid-session:** scripts may return an empty message even while `sys.stdout` works. Write results to a scratchpad file and read it with Bash for the rest of that session.
- **Save collision or `ECONNRESET`:** a scripted `doc.save()` started in the same second as an autosave and crashed Fusion with heap corruption `0xc0000374` after `NEUTRON_BUG_ALERT` floods in `BinaryBulkSaveVisitor`. The version was not saved; its crash-recovery backup was `not a valid zip package`. Follow the autosave timing and version checks in the [modeling MCP workflow](../../fusion-model/references/mcp.md) before another save.
- **Startup recovery dialog after a crash:** it blocks every MCP call, including read-only calls, with `The operation timed out.` Ask the user to dismiss the dialog.
- **Export timeout during save upload:** an export can return `The operation timed out.` and still finish; check output-file timestamps before retrying.
