# Literary Daily subsystem

This directory implements the user-requested Python + GitHub Actions + GitHub
Pages V1 pipeline. The repository root `AGENTS.md`,
`DEVELOPMENT_GOVERNANCE.md`, and the canonical company rules in
`/private/tmp/ai-frontend-rules` remain authoritative.

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

Required local gates for this subsystem:

```bash
python -m unittest discover -s literary-daily/tests -v
python -m compileall -q literary-daily/src literary-daily/scripts
```
