---
name: math-review-queue-activate
description: Move an explicitly requested number of indexed math questions from an unscheduled pool into a dated review queue. Use when a user asks to draw, activate, or schedule questions already recorded in a pending JSON file; not for OCR, new question entry, or automatic backlog migration.
---

# Activate pending math questions

This skill handles one deliberate transfer from a pending index to a dated review queue. It is a portable Agent Skills folder: use ordinary file and shell capabilities, with no Codex-specific API or metadata. The bundled Python helper is optional but preferred for the JSON layout described below.

## Establish the local contract

1. Read the host project's recording/scheduling instructions. The user's requested count, date, and ordering take priority. Do not infer authorization for future dates, extra questions, Git operations, or review-result changes.
2. Locate the pending pool, the canonical question-record file, and the schedule file. In this repository they are `workbook_880_unscheduled.json`, `880-record.json`, and `review_schedule.json`. Resolve paths from the project root, never from the skill's installation directory.
3. Resolve “today” in the schedule's timezone. Require a positive integer count and an actual calendar date. Select exactly the first `count` items in the pending array's existing order, not by grade or page number. Never skip an invalid item.
4. Confirm that each selected ID has at most one canonical record, has no active `history` entry, and is absent from all dated queues, plans, release buffers, and backlog. Where a record exists, confirm its identifiers, display fields, page, order, and grade agree with pending. Where no record exists, create a metadata-only record from the pending index and the project's explicit defaults; do not invent question text. Missing or conflicting required metadata requires repair or user direction; do not silently skip ahead to reach the requested count.

For this repository's schema, the transfer removes the selected objects from `items`, appends lightweight entries copied from existing or newly created records to `history`, and inserts `workbook_880:<question_id>` into both `buckets[date]` and `daily_plans[date]`. New items go before existing items on that date; existing relative order is retained. Existing full `records` and `review_state.json` stay unchanged. New metadata-only records contain the display ID as a heading, not a transcription of the problem. Do not OCR or invent question text.

## Execute and verify

If Python 3.9+ and local filesystem access are available, run the helper in two phases. Use the explicit date and project root; replace the example values with the user's request:

```text
python3 <skill-folder>/scripts/transfer.py plan --root <project-root> --date 2026-09-28 --count 10
python3 <skill-folder>/scripts/transfer.py apply --root <project-root> --date 2026-09-28 --count 10 --token <token-from-plan>
```

The plan is read-only and lists exact IDs. The token binds the apply step to the three file contents, date, and count, so a stale plan cannot silently consume the next batch. Apply stages and verifies all three outputs before replacing originals. If files change during transfer or a write fails, stop and inspect the reported recovery copies; do not blindly rerun with a fresh token. The helper requires the three files to be in one directory, uses a local lock, and edits only the affected JSON arrays/fields.

If the helper is unavailable or the local schema differs, perform the same semantic checks and a minimal edit with the host's file tools. Never force the helper onto an unfamiliar schema. Preserve unrelated fields and the existing queue order.

Verify JSON parsing, exactly the requested number of new queue keys, one history entry and one canonical record per selected ID, absence of those IDs from pending, no duplicate queue keys, and preservation of pre-existing dated items. Report the exact IDs or page/type ranges, added count, remaining pending count, the target day's queue count, and how many metadata-only records were created. Do not commit or push unless asked.

## Recovery boundaries

- A repeated completed request with the original token must fail; a newly planned request targets the next pending items. Confirm the user actually wants another batch before making a new plan.
- If the target date has already passed, treat it as the user's explicit date; do not substitute a later date.
- If the user asks only for a candidate list, stop after the read-only plan.
- Multi-file JSON cannot be made fully atomic without a transactional store. The helper checks for concurrent edits and keeps recovery copies if replacement fails; inspect current files before any retry.
