# Math Test Records

这是一个数学错题与复盘记录仓库，只保存题目记录、错题分级、复盘状态和进度索引。

配合 [dashboard ](https://github.com/Ymy333137/math-test-dashboard)使用

配套的本地 dashboard/app 会读取本仓库的数据做可视化和复盘队列(但本仓库本身不包含 app 代码)

## 仓库结构

```text
.
├── math_records.json              # 总索引：当前题册、题册状态、记录文件入口
├── 660-record.json                # 660 题册的完整记录
├── 800-record.json                # 800 题册历史归档
├── review_state.json              # 每道错题的复盘历史与下一次到期日
├── review_schedule.json           # 按日期组织的复盘队列
├── workbook_660_error_abc.md      # 660 题册 ABC 错题索引
├── workbook_660_progress.md       # 660 题册当前进度
├── workbook_800_error_abc.md      # 800 题册 ABC 错题索引
├── workbook_800_progress.md       # 800 题册历史进度
├── unit_*_outline.md              # 单元大纲
└── *_coverage.md / dashboard.md   # 阶段性分析与覆盖记录
```

## 核心文件

### `math_records.json`

总入口文件，记录当前 active workbook、题册对应的 record 文件，以及每个题册/单元的状态。

关键字段：

- `active_workbook`: 当前正在记录的题册，例如 `workbook_660`
- `units`: 单元与题册状态
- `record_files`: 题册到明细文件的映射

### `660-record.json`

当前主要题册的明细记录，包含两层数据：

- `history`: 轻量摘要，供 dashboard 快速统计
- `records`: 完整记录，保存题目 markdown、错因、分数分级、掌握度等

### `review_state.json`

保存每道错题的复盘状态，例如：

- 已复盘次数
- 最近一次复盘结果
- 当前错误等级
- 下一次复盘日期

### `review_schedule.json`

按日期 bucket 保存复盘队列。新增错题通常会被排到次日。

## 记录格式示例

### `history` 示例

```json
{
  "question_id": "660-190",
  "mastery": 0.94,
  "performance_level": "优秀",
  "unit": "unit_1",
  "target_score_tier": 90,
  "required_for_scores": [90, 110, 135],
  "error_level": null
}
```

### `records` 示例

```json
{
  "timestamp": "2026-06-15T03:30:00Z",
  "unit": "workbook_660",
  "curriculum_unit": "unit_1",
  "question_id": "660-190",
  "source_label": "题册660",
  "assessment_basis": "self_report",
  "question_md": "### 190.\\n设 ...",
  "target_score_tier": 90,
  "required_for_scores": [90, 110, 135],
  "error_level": null,
  "correctness": 1.0,
  "thinking_quality": 0.85,
  "missing_steps": [],
  "error_tags": [],
  "weakness_focus": [],
  "student_answer_summary": "按用户记录：本题做对。",
  "mastery": 0.94,
  "performance_level": "优秀",
  "difficulty_adjustment_suggestion": "up",
  "next_expected_target_score_tier": 90
}
```

## 字段说明

- `question_id`: 题号，例如 `660-190`
- `unit`: 在 `history` 中表示课程单元，如 `unit_1`
- `curriculum_unit`: 在完整记录中表示课程单元，如 `unit_1`
- `target_score_tier`: 分数分级，常见为 `90`、`110`、`135`
- `required_for_scores`: 该题对哪些目标分数是必做题
- `error_level`: 错题等级；`A` 为会做但计算/细节错，`B` 为有思路但卡住，`C` 为无从下手；做对时为 `null`
- `mastery`: 当前掌握度估计
- `performance_level`: 人类可读表现等级
- `missing_steps`: 具体错因或缺失步骤
- `weakness_focus`: 归纳出的薄弱考点

## 更新约定

新增题目时通常需要同步更新：

1. `660-record.json`
   - 追加 `history[]`
   - 追加 `records[]`
   - 更新 `recorded_range`、`recorded_count`、`curriculum_unit`
2. `math_records.json`
   - 更新当前题册的 `recorded_range`、`recorded_count`、`curriculum_unit`
3. `workbook_660_error_abc.md`
   - 只记录错题题号，按单元和 A/B/C 分类
4. `workbook_660_progress.md`
   - 更新当前单元、记录范围、累计题量、下一题建议编号
5. `review_schedule.json`
   - 新错题通常排到次日复盘

更新后建议至少运行：

```bash
jq empty math_records.json
jq empty 660-record.json
jq empty review_schedule.json
jq empty review_state.json
```

## 为什么用 JSON

目前题目记录量较小,也没有频繁检索的需求,在“若无必要，勿增实体”的理念下JSON 已经足够了.
