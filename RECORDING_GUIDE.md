# 错题记录与临时排期规范

本规范用于新任务中的两类工作：

1. 从用户提供的文字或图片中录入新错题。
2. 按用户指定日期和数量临时安排复盘题目。

它不负责 Dashboard 开发，也不负责重新设计复盘算法。

## 1. 工作原则

- 用户提供的是学习记录，不要求解出标准答案。
- OCR 只手写题号与题目正文，不写书名、章节题头、题组标题或答案解析。
- 以用户明确说明为最高优先级；图片上的印刷内容和手写标注只用于识别题目、题型和 ABC 等级。
- 新增记录默认立即激活到 `history[]`；其中错题默认排入次日首次复盘。
- 只有用户明确说“不排期”、要求手动拆分大批量题目，或另行给出排期方案时，才暂缓激活和排期。
- 用户没有要求 Git 时，不提交、不推送。
- 普通数据更新不启动 App、不运行 Pixi、不调用本地网页接口。

## 2. 文件职责

### `math_records.json`

题册总索引。维护当前题册、记录文件映射，以及题册的页码、范围和数量等摘要。

### `660-record.json` / `880-record.json`

- `records[]`：完整题目与评估记录，是题目内容的事实来源。
- `history[]`：Dashboard 和复盘系统使用的轻量激活索引。

重要约定：

- OCR 新增题目时追加到 `records[]`。
- 默认同步追加轻量摘要到 `history[]`，供 Dashboard 和复盘系统读取。
- `error_level` 非空的新错题默认排入次日首次复盘；做对的题只进入 `history[]`，不进入复盘日期。
- 用户明确说“不排期”或要求手动拆分大批量题目时，本批题目暂不进入 `history[]` 和日期队列，等待后续激活。

### `workbook_*_error_abc.md`

保存全部错题的 ABC 索引，与是否已经排期无关。

### `workbook_*_progress.md`

保存当前页码、记录范围、累计卡片数、默认分数档和下一步记录提示。

### `review_schedule.json`

保存临时复盘日期：

- `buckets[date]`：该日实际复盘题号。
- `daily_plans[date]`：该日计划快照。
- key 格式：`book_id:question_id`。

除非用户明确要求，不修改 `release_buffer`、`backlog` 或 `forced_releases`。

### `review_state.json`

保存真实复盘反馈与历史。新增题、激活和手工排期时不修改；用户在 App 中反馈“对了/仍错”后再由 App 更新。

## 3. ABC 错因等级

- `A`：会做，主要是计算、抄写、公式细节或漏项错误。
- `B`：有思路并尝试过，但中途卡住或未能完成。
- `C`：没有有效入口、完全不会，或题型第一次见且无法展开。
- 做对：`error_level: null`。

用户给出的具体错因必须优先写入 `missing_steps`、`error_tags` 和 `student_answer_summary`；没有具体错因时才使用“依据图片手写分级记录，未提供详细错因”。

当前一致性默认值：

| 结果 | correctness | thinking_quality | mastery | performance_level | difficulty_adjustment_suggestion |
| --- | ---: | ---: | ---: | --- | --- |
| 做对 | 1.0 | 0.85 | 0.94 | 优秀 | up |
| A | 0.65 | 0.60 | 0.49 | 不佳 | down |
| B | 0.70 | 0.50 | 0.62 | 合格 | keep |
| C | 0.20 | 0.40 | 0.28 | 不佳 | down |

## 4. 660 题册规则

- `question_id`：`660-题号`，例如 `660-297`。
- `unit`：完整记录中固定为 `workbook_660`。
- `curriculum_unit`：使用用户给出的 `unit_n`。
- 分数档为数字 `90`、`110`、`135`。
- `target_score_tier` 取最低必做分数档。
- `required_for_scores` 从目标档向上包含，例如 90 分必做题为 `[90, 110, 135]`。
- 未明确单元时不要猜测，向用户确认；只有用户明确允许时才使用未分配单元。

660 完整记录至少包含：

```json
{
  "timestamp": "2026-07-09T00:18:00Z",
  "unit": "workbook_660",
  "curriculum_unit": "unit_7",
  "question_id": "660-297",
  "source_label": "题册660",
  "assessment_basis": "self_report",
  "question_md": "### 297\n题目正文",
  "target_score_tier": 90,
  "required_for_scores": [90, 110, 135],
  "error_level": "A"
}
```

## 5. 880 题册规则

### 5.1 默认值

- 板块：未说明时为 `基础题`。
- 题型：必须识别为 `选择题`、`填空题` 或 `解答题`。
- 分数档：未明确说 `120+` 时一律为 `120以下`。
- `required_for_scores`：`120以下` 题为 `["120以下", "120+"]`；`120+` 题为 `["120+"]`。
- 单元：用户未说明或表示不再精确维护时使用 `unit_unassigned`，不得自行猜单元。

### 5.2 页码题号

显示题号示例：

- `P1-(1)`
- `P2-(2)-(II)`

同一页可能同时存在选择题、填空题和解答题的相同序号，因此内部 ID 必须包含题型。

题型代码：

- 选择题：`choice`
- 填空题：`fill`
- 解答题：`solution`

内部 ID 示例：

```text
880-basic-choice-P1-(1)
880-basic-fill-P2-(1)
880-basic-solution-P2-(2)-(II)
```

板块代码：

- 基础题：`basic`
- 综合题：`comprehensive`
- 拓展题：`extended`

`display_label` 格式固定为：

```text
板块 · 题型 · display_id
```

例如：`基础题 · 解答题 · P2-(2)-(II)`。

### 5.3 小问拆卡

- 同一证明或同一题干下相互依赖的 `(I)(II)` 保留为一张卡片，并在正文中同时记录。
- 彼此独立的计算小问分别记录为多个卡片，例如 `P2-(2)-(I)`、`P2-(2)-(II)`。
- 无法判断小问是否相关时，写入前必须询问用户。
- 不得仅因版面靠近就合并，也不得机械地把所有罗马数字小问拆开。

### 5.4 880 完整记录示例

```json
{
  "timestamp": "2026-08-19T05:34:00Z",
  "unit": "workbook_880",
  "curriculum_unit": "unit_unassigned",
  "question_id": "880-basic-choice-P17-(3)",
  "display_id": "P17-(3)",
  "display_label": "基础题 · 选择题 · P17-(3)",
  "page": 17,
  "section": "基础题",
  "question_type": "选择题",
  "record_order": 134,
  "target_score_tier": "120以下",
  "required_for_scores": ["120以下", "120+"],
  "error_level": "B",
  "source_label": "题册880",
  "assessment_basis": "image_annotation",
  "parent_display_id": null,
  "subquestion": null,
  "card_structure": "single",
  "question_md": "### P17-(3)\n题目正文"
}
```

`record_order` 从现有最大值依次递增，不以数组长度代替。

## 6. OCR 录入流程

1. 读取本规范、目标题册顶层元数据、最后一条同类型记录和已有 `question_id` 集合。
2. 从图片识别页码、板块、题型、题号、题目正文及用户手写 ABC 标注。
3. 忽略图片中的答案、解析、章节标题和与记录无关的手写演算。
4. 保留数学表达式并转换为 Markdown + LaTeX。
5. 按小问关系决定卡片拆分；不能确定时先询问。
6. 在内存中完成整批记录，检查 ID 冲突后一次写入。
7. 同步更新目标题册元数据、`math_records.json`、ABC 索引和进度文件。
8. 默认把全部新记录摘要同步到 `history[]`，并把其中错题排入次日的 `buckets` 与 `daily_plans`；不写 `review_state.json`。
9. 用户明确说“不排期”或要求手动拆分时，跳过第 8 步中的激活与排期，等待后续指定。

新增记录时需要同步的摘要：

- `recorded_pages`
- `recorded_range`
- `recorded_count`，应等于 `records | length`
- 当前板块、默认分数档和必要的单元摘要
- ABC 索引中的题号
- 进度文件中的页码、范围和累计卡片数

发现与本批无关的历史不一致时，不擅自大范围修复；先完成用户任务并在结果中指出。

## 7. 默认排期与临时调整

正常新增错题时默认直接执行激活，并以 `Asia/Shanghai` 的下一自然日作为首次复盘日期。用户明确给出的今日、明日或具体日期覆盖该默认值。

大批量新增本身不自动改变规则；只有用户明确要求“不排期”或手动拆分时，才先保存完整记录、暂缓以下激活步骤。

### 7.1 激活题目

从完整记录复制轻量摘要到 `history[]`，避免重复：

```json
{
  "question_id": "880-basic-choice-P17-(3)",
  "display_id": "P17-(3)",
  "display_label": "基础题 · 选择题 · P17-(3)",
  "page": 17,
  "section": "基础题",
  "question_type": "选择题",
  "record_order": 134,
  "target_score_tier": "120以下",
  "required_for_scores": ["120以下", "120+"],
  "error_level": "B",
  "unit": "unit_unassigned",
  "mastery": 0.62,
  "performance_level": "合格"
}
```

### 7.2 写入日期

同时更新：

```text
buckets[YYYY-MM-DD]
daily_plans[YYYY-MM-DD]
```

默认日期为记录日的下一自然日。保留该日已有题目，除非用户明确要求删除或替换。不要因为每日上限截断持久化队列。

### 7.3 临时选题顺序

默认顺序：

1. 尚未复盘过的新错题。
2. 最近一次仍错的题。
3. 普通到期题。
4. 已多次通过的维护题。

同组内：

- ABC：`A > B > C`。
- 660 分数档：`90 > 110 > 135`。
- 880 分数档：`120以下 > 120+`。

临时重新排期时，用户指定数量就严格按数量加入；未指定数量时先给出简短方案并等待确认，不自行大批迁移。正常 OCR 新增错题仍按次日直接排期。

过期 bucket 不自动迁移。用户此前采用手动迁移方式；是否删除、顺延或重新安排必须由用户决定。

## 8. 最小验证

### 新增错题

只验证：

1. 修改过的 JSON 可被 `jq empty` 解析。
2. `question_id` 无重复。
3. 新增卡片数量与用户提供的题目一致。
4. 元数据、ABC 索引和进度数量一致。
5. 默认流程下全部新记录已进入 `history`，错题已进入次日 bucket，做对题没有进入日期队列。
6. 用户明确要求“不排期/手动拆分”时，本批新题没有进入 `history` 或任何日期 bucket。

### 临时排期

只验证：

1. 指定日期新增数量正确。
2. 新题位于预期优先级位置。
3. 原有队列没有被意外删除。
4. 未排期新题数量变化正确。

普通记录或排期任务到此结束，不启动 App，不运行完整测试。

## 9. 新任务的最短指令

新增错题：

```text
按仓库规范记录这批 880 错题。图片如下。
```

指定元数据：

```text
按仓库规范记录这批 880 错题：P32，综合题，120+。图片如下。
```

大批量暂不排期：

```text
按仓库规范记录这批 880 错题，先不排期，后续由我手动拆分。图片如下。
```

临时排期：

```text
按仓库规范给 2026-08-22 排 8 道新题，新题优先，A > B > C。
```
