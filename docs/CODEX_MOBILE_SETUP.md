# How to use the Codex mobile new-task screen

This document is written for the iPhone screen that says: "Nueva tarea" and "Describe una tarea de programación".

## What each visible control means in practice

- `Cancelar`: exits without starting the task.
- Text area: write the programming task for Codex.
- `+`: attach files, screenshots, specifications or code fragments when the task needs them.
- `1 veces`: run-count / attempts selector. Keep it at 1 for normal work. Raise it only when you intentionally want several attempts or variants. Four runs can consume more usage and may create parallel alternatives.
- Computer/workspace icon: choose or inspect the execution environment or repository/workspace when available.
- Branch/Git icon: connect/select GitHub context when available. If it is greyed out, no repo/environment is selected or GitHub context is not ready.
- Microphone: dictate the task.
- `Comenzar`: starts the Codex task.

## Minimal safe first run

Paste the contents of `docs/CODEX_PROMPT_MASTER.md` into the text area and press `Comenzar`.

## What to attach

Attach only material that Codex needs:

1. A ZIP of this repository if Codex does not already see it.
2. Screenshots of the desired visual style.
3. A short brand file if you have one.
4. Existing code only if you want it modified.

Do not attach passwords, tokens, API keys, INE/passports, bank data or private family documents.

## When to choose 4 runs

Use 4 only for exploration, for example:

- four landing page directions;
- four architecture options;
- four prompt-engine variants;
- four visual identity routes.

Do not use 4 for a precise repository edit unless you are prepared to compare outputs and choose one.
