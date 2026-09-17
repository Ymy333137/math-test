# Math Records Agent Instructions

This repository is used only for two workflows:

1. Record new math questions from user-provided text or images.
2. Make temporary review schedules when the user explicitly requests one.

Before either workflow, read `RECORDING_GUIDE.md` and follow it as the source of truth.

## 当前 880 批量待排期模式（最高优先级）

当用户正在批量录入 880，并明确要先存入待排期队列、以后每日按顺序取题时，以下规则优先于本文件中的历史默认值：

- 只写入 `workbook_880_unscheduled.json`；不得改动 `880-record.json`、`review_state.json`、`review_schedule.json`、`math_records.json`、任何 ABC 汇总或进度索引。
- 每张卡只保存物理页码、题型、题号（必要时含用户明确指定的小问）和等级；不录题干、不 OCR、不写 LaTex、不解题。
- 用户手写勾号或明确说“对了”表示做对，不建卡。用户口头给出的 A/B/C 优先于图片中的任何笔记。
- 没有明确等级且无法从用户标记安全判断时，只问一个简短问题；不要猜测，不要通过计算或 OCR 推断。
- 默认一题对应一张卡；仅当用户明确要求按小问拆分时才拆分。
- 图片批次先在当前图片中核对页码、题型、题号和等级，再一次性写入。禁止为查找旧卡、题干或答案进行反复搜索。
- 写入后仅做最小校验：JSON 可解析、ID 不重复、写入数量正确。回复只报告新增数量和待排期总数。

## Hard Boundaries

- Do not develop or modify the dashboard app from this repository.
- Do not redesign the review algorithm unless the user explicitly asks for a discussion.
- Do not solve questions or add standard answers unless explicitly requested.
- 只有用户明确要求完整 OCR 记录时，OCR 输出才包含题号和题干；省略书名、页眉和装饰标题。
- 完整记录流程中新错题默认激活到 `history`，并排到次日。当前 880 批量待排期模式不激活、不排期。
- If the user explicitly says `不排期`, requests manual splitting, or provides a later schedule plan, keep those records out of `history` and dated queues until activation is requested.
- Do not modify `review_state.json` while recording or manually scheduling questions.
- Do not start the app, run Pixi, use the app API, or perform broad tests for ordinary recording or scheduling work.
- Do not commit or push unless the user explicitly asks.
- Preserve unrelated local changes. Never rewrite or normalize whole data files unnecessarily.

## Context And Tool Discipline

- Read only the relevant workbook file, one representative record, the required metadata, and the target schedule slice.
- Never print or load an entire large JSON file when a narrow `jq` query is sufficient.
- Perform one structured update and one minimal validation. Avoid experimental write methods.
- 对索引式图片批次，先完成题号和等级核对再一次写入；只有完整记录流程才进行 OCR。
- Ask only when the page, section, question type, handwritten ABC grade, or subquestion relationship cannot be determined safely.

## Defaults

- Active workbook: 880 unless the user names another workbook.
- 880 section: `基础题` unless the user says `综合题` or `拓展题`.
- 880 score tier: `120以下` unless the user explicitly says `120+`.
- 880 curriculum unit: `unit_unassigned` when the user does not specify a unit.
- 完整记录流程中的新错题默认次日复习，用户指定日期优先；待排期索引模式不设日期。

## Minimal Verification

For recording: JSON parses, question IDs are unique, and the added count is correct.

For scheduling: the requested date contains the requested new questions in the intended order, existing items are preserved unless the user asks otherwise, and the remaining unscheduled count is correct.
