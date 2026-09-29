# 使用与分发

## 分发

打包整个 `math-review-queue-activate` 文件夹，保留原有目录结构。至少需要：

- `SKILL.md`：技能说明和操作规则
- `scripts/transfer.py`：预览与转入脚本

建议直接分发整个文件夹，连同 `scripts/test_transfer.py` 一起保留。它只用 Python 3.9+ 标准库，不需要额外安装 Python 包。不要把个人题库 JSON 数据放进分发包。

## 安装

把整个文件夹交给目标 agent，并告诉它：

> 请将这个文件夹作为 Agent Skill 安装，保留目录结构；安装后告诉我它的调用名称和发现状态。

如果 agent 支持 Agent Skills 规范并能安装本地 skill，它通常可以按自己的安装流程处理。并非所有 agent 或 harness 都支持该规范，也不是所有环境都能访问本地文件；不支持时，需要由使用者把 `SKILL.md` 内容作为项目指令提供，并让其按环境配置脚本路径。安装 skill 也不会安装或搬运题库数据。

## 使用

在支持 skill 的 agent 中，直接说：

> 用 `math-review-queue-activate` 从待排队列按原顺序取 10 题，加入今天的复习队列。先生成只读预览，核对无误后按我的请求执行。

agent 应先运行只读预览，核对将转入的题目；随后使用该预览令牌执行。用户已明确要求转入时，不需要额外确认。日期、数量和排序由用户的明确要求决定。需要兼容其他题库或不同 JSON 结构时，应先适配 `SKILL.md` 中的本地数据约定和脚本参数，不能直接假设文件结构相同。

## 手动运行

在有题库数据的项目目录，先预览：

```text
python3 /path/to/math-review-queue-activate/scripts/transfer.py plan --root /path/to/records --date YYYY-MM-DD --count 10
```

确认输出的题号后，用同一日期、数量和路径，将预览返回的令牌传给 `apply`：

```text
python3 /path/to/math-review-queue-activate/scripts/transfer.py apply --root /path/to/records --date YYYY-MM-DD --count 10 --token <预览令牌>
```

当前脚本默认使用 880 题库的文件名和字段约定。若文件名或元数据默认值不同，可查看 `--help`；结构不同则先适配脚本，不要直接执行。
