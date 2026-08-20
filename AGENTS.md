# Math Records Agent Instructions

This repository is used only for two workflows:

1. Record new math questions from user-provided text or images.
2. Make temporary review schedules when the user explicitly requests one.

Before either workflow, read `RECORDING_GUIDE.md` and follow it as the source of truth.

## Hard Boundaries

- Do not develop or modify the dashboard app from this repository.
- Do not redesign the review algorithm unless the user explicitly asks for a discussion.
- Do not solve questions or add standard answers unless explicitly requested.
- OCR output must contain the question number and question body only; omit book headers and decorative headings.
- New records are activated in `history` by default, and new wrong questions are scheduled for their first review on the next calendar day.
- If the user explicitly says `不排期`, requests manual splitting, or provides a later schedule plan, keep those records out of `history` and dated queues until activation is requested.
- Do not modify `review_state.json` while recording or manually scheduling questions.
- Do not start the app, run Pixi, use the app API, or perform broad tests for ordinary recording or scheduling work.
- Do not commit or push unless the user explicitly asks.
- Preserve unrelated local changes. Never rewrite or normalize whole data files unnecessarily.

## Context And Tool Discipline

- Read only the relevant workbook file, one representative record, the required metadata, and the target schedule slice.
- Never print or load an entire large JSON file when a narrow `jq` query is sufficient.
- Perform one structured update and one minimal validation. Avoid experimental write methods.
- For image batches, finish OCR and card splitting before writing, then write the batch once.
- Ask only when the page, section, question type, handwritten ABC grade, or subquestion relationship cannot be determined safely.

## Defaults

- Active workbook: 880 unless the user names another workbook.
- 880 section: `基础题` unless the user says `综合题` or `拓展题`.
- 880 score tier: `120以下` unless the user explicitly says `120+`.
- 880 curriculum unit: `unit_unassigned` when the user does not specify a unit.
- New wrong records default to next-day scheduling. An explicit user date overrides the default.

## Minimal Verification

For recording: JSON parses, question IDs are unique, and the added count is correct.

For scheduling: the requested date contains the requested new questions in the intended order, existing items are preserved unless the user asks otherwise, and the remaining unscheduled count is correct.
