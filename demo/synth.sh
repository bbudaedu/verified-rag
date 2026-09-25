#!/usr/bin/env bash
# Regenerate demo/wiki/*.md: one-shot, same prompt for both models. Aliases resolved to
# claude-sonnet-5 and claude-haiku-4-5-20251001 on 2026-09-25; output varies per run.
set -euo pipefail
cd "$(dirname "$0")"
for m in sonnet haiku; do
  cat synth_prompt.md synth_input.md | claude -p --model "$m" > "wiki/$m.md"
done
