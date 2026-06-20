# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

IOPtics is a Python package for testing and evaluating a wide range of IOP
(inherent optical properties) algorithms. The goal is to generate metrics and
diagnostics to share with the ocean optics community.

## Package layout

- `ioptics/` — the Python package source.
- `claude_prompts/` — prompts and task definitions that drive this work.

## Environment

- Use the `ocean14` conda environment for running Python.

## Conventions

- Write clear, well-documented Python with docstrings.

## Git

- **The user (J. Xavier Prochaska) performs all git commands.** Do not run
  `git add`, `git commit`, `git push`, or any other git command that changes
  repository state unless explicitly asked. You may run read-only git commands
  (e.g. `git status`, `git diff`, `git log`) when helpful.
