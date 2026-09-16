# 每日文学精选推送系统 V1.0

Python batch pipeline for selecting one literary work or excerpt four times a
day, generating a mobile-first static site, optionally generating a Gemini TTS
MP3, deploying to GitHub Pages, and notifying WeChat via PushPlus only after
deployment. Telegram remains an optional compatible provider.

This subsystem is deliberately isolated from the existing Next.js literature
reader. It has no long-running server, database, Flask/Django/FastAPI app, or
client framework.

## Architecture

```text
collectors -> normalize/filter -> deduplicate -> Gemini/rules rank
           -> contiguous excerpt -> editorial JSON -> Gemini TTS MP3
           -> data + static HTML -> Pages deploy -> PushPlus/Telegram notification
```

The standalone project's `library/` directory is the default local fallback
source. Network RSS and webpage collectors are present but disabled by default
in `config/settings.yaml`. This project does not read the private literature
room's `content/` directory.

Gemini is the only AI path. `GEMINI_API_KEY` is read only from the environment;
it is never written to generated JSON, HTML, logs, or workflow files. Gemini
structured JSON uses the `generateContent` endpoint. Gemini TTS uses the
`interactions` audio endpoint and converts returned 24 kHz PCM to MP3 with
`ffmpeg`. TTS is retried twice; if it still fails, the article is published
with `audio: null` and the notification remains readable.

## Local setup

```bash
cd literary-daily
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY` and, for WeChat notification, `PUSHPLUS_TOKEN` in the
ignored `.env` or the shell environment. `TELEGRAM_BOT_TOKEN` and
`TELEGRAM_CHAT_ID` are optional compatibility credentials. Do not put secrets
in `config/`, `data/`, or GitHub-tracked files.

Run a non-writing evaluation:

```bash
python -m src.main --dry-run --debug
```

Run a local publication (writes `data/` and `site/`, and generates `audio/` if
Gemini TTS is configured):

```bash
python -m src.main
```

Serve the generated site locally:

```bash
python -m http.server 8765 --directory site
```

## Configuration

All scheduling, selection, model, TTS, source, and site settings live under
`config/`. The files use JSON-compatible YAML syntax so the pipeline still
supports a dependency-light dry run; installing `PyYAML` enables normal YAML
parsing for future hand edits.

- `settings.yaml`: schedule and operational limits.
- `categories.yaml`: soft category weights, never a fixed rotation.
- `sources.yaml`: local, RSS, and webpage source switches and URLs.
- `prompts.yaml`: prompt copy kept out of Python logic.

The local source defaults to `library/`, which belongs only to this project.
Add independently curated Markdown works there. Every selected excerpt is
validated as a contiguous substring of the original candidate text.

## GitHub Actions and Pages

`.github/workflows/publish.yml` runs at 08:30, 12:30, 18:30, and 22:30 in
`Asia/Shanghai`, and also supports `workflow_dispatch` inputs for `category`,
`force`, `dry_run`, and `skip_tts`. GitHub Pages must be configured to use
GitHub Actions as its source. Add these repository secrets:

- `GEMINI_API_KEY`
- `PUSHPLUS_TOKEN` (PushPlus user token; delivers to the personal WeChat bound to PushPlus)
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (optional)

Add the repository variable `PAGES_BASE_URL`, for example
`https://wisely88.github.io/literary-daily`.

The workflow deploys `literary-daily/site` first and runs the PushPlus/Telegram
notifier only after `actions/deploy-pages` succeeds. Generated HTML and JSON remain
inspectable in the artifact; audio is intentionally ignored in Git because
the current V1 retention policy is 60 days.

### PushPlus / 微信配置

1. 在 PushPlus 获取个人用户 token，并确认已绑定微信接收渠道。
2. 在仓库 `Settings → Secrets and variables → Actions → Secrets` 中新增
   `PUSHPLUS_TOKEN`。
3. 在 `Settings → Pages` 将构建来源设为 GitHub Actions，并设置
   `PAGES_BASE_URL` repository variable 为 Pages 站点根地址。

通知只会在 Pages 部署成功后发送；PushPlus 失败会让 workflow 明确失败，
但不会回滚已经部署的静态站点。

## Tests

```bash
python -m compileall -q src scripts
python -m unittest discover -s tests -v
```

The test suite covers normalization/filtering, exact-text deduplication,
author cooldown, contiguous excerpt selection, HTML escaping, audio asset
copying, and the PushPlus Markdown request payload. Live Gemini, PushPlus, and
Telegram calls are not made by tests.
