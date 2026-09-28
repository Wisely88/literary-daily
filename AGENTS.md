# Literary Daily subsystem

## 八荣八耻（全局必遵）

- 以臆猜接口为耻，以查档求证为荣。
- 以模糊开工为耻，以对齐需求为荣。
- 以脑补业务为耻，以请示规则为荣。
- 以新增冗余为耻，以复用存量为荣。
- 以省略校验为耻，以完备测试为荣。
- 以乱改架构为耻，以恪守规范为荣。
- 以不懂装懂为耻，以坦承存疑为荣。
- 以批量乱改为耻，以分步迭代为荣。

This directory implements the user-requested Python + GitHub Actions + GitHub
Pages V1 pipeline. The repository root `AGENTS.md`,
`DEVELOPMENT_GOVERNANCE.md`, and the canonical company rules in
`/Volumes/wisely data/Projects/_company-standards/` remain authoritative.

Additional boundaries for this subsystem:

- Gemini is the only AI provider in V1. Keep `GEMINI_API_KEY` in Actions
  Secrets or an ignored local environment file; never log or commit it.
- The pipeline is batch-only. It must not introduce a long-running Python
  service, Flask/Django/FastAPI server, database, or client framework.
- Original candidate text is immutable. Any AI-selected excerpt must be a
  contiguous substring of that original text.
- Publishing and notification are separate stages: notify only after the
  Pages artifact has been deployed successfully.
- Prefer the existing repository's curated `content/` as a local fallback
  source; do not read from or copy the private literature-room library. This
  project owns its independent `library/` directory.

- For UI, card, interaction, or prompt design work, also read the synchronized
  copies of `docs/UI_UX_TERMINOLOGY.md`, `docs/UI_PROMPT_PLAYBOOK.md`, and
  `docs/UI_REFERENCE_SITES.md` under `/Volumes/wisely data/Projects/_company-standards/`;
  use them as reference only and preserve this project's batch pipeline and
  Pages boundaries.

Required local gates for this subsystem:

```bash
python -m unittest discover -s literary-daily/tests -v
python -m compileall -q literary-daily/src literary-daily/scripts
```

## GitHub 使用规范（2026.09）

本项目继承 `/Volumes/wisely data/Projects/DEVELOPMENT_GOVERNANCE.md` 与 `/Volumes/wisely data/Projects/_company-standards/standards/github/GITHUB_USAGE_STANDARD.md`。

涉及 GitHub 仓库、Actions、Runner、Artifact、Cache、Release、Package、Secrets、Environments、分支保护、规则集或部署时，先读取中央 GitHub 使用规范；概念、保留期、账单或存储边界不明确时，再读取 `/Volumes/wisely data/Projects/_company-standards/docs/GITHUB_CONCEPTS_AND_ACTIONS_GUIDE.md`。仓库可见性按数据与安全分类决定，Actions 默认最小权限（通常为 `contents: read`），必须设置必要的超时、并发和保留期；Artifact 仅存临时运行产物，Cache 仅存可再生加速数据，正式版本使用 Release，凭据只放 Secrets/Environment，禁止写入代码、日志、文档或示例。新增自动化前必须检查现有 workflow，避免重复或高频轮询；时效性 GitHub 限额、账单和安全能力以官方文档复核为准。
