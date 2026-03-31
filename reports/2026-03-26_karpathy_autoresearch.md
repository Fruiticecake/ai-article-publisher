# GitHub 每日项目分析报告：karpathy/autoresearch

- 排行名次：Top 1
- 仓库链接：https://github.com/karpathy/autoresearch
- Star 趋势：https://www.star-history.com/?repos=karpathy%2Fautoresearch&type=date&legend=top-left
- Star：56965
- Fork：7922
- 语言：Python
- 主题：无

## 项目简介

AI agents running research on single-GPU nanochat training automatically

## README 解析

- 文档章节：autoresearch
- 文档章节：How it works
- 功能点：**`prepare.py`** — fixed constants, one-time data prep (downloads training data, trains a BPE tokenizer), and runtime utilities (dataloader, evaluation). Not modified.
- 功能点：**`train.py`** — the single file the agent edits. Contains the full GPT model, optimizer (Muon + AdamW), and training loop. Everything is fair game: architecture, hyperparameters, optimizer, batch size, etc. **This file is edited and iterated on by the agent**.
- 功能点：**`program.md`** — baseline instructions for one agent. Point your agent here and let it go. **This file is edited and iterated on by the human**.
- 文档章节：Quick start

## 预览与建议

- 建议先查看仓库首页的 Issue 与 Discussions，评估社区活跃度。
- 建议重点阅读 README 的快速开始与部署部分，验证可落地性。
- 可将该项目加入候选技术栈，后续结合业务场景做 PoC。
