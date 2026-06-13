# Project Overview

**Taiwan Stock Simulation Game Backend**

This repository implements a multi‑agent system powered by **CrewAI** that automatically generates a PostgreSQL schema for a stock‑trading simulation game. The workflow consists of:

1. **Principal Systems Architect** – researches (max 2 Google searches) and writes a System Design Document (SDD) in Markdown.
2. **Senior Backend & Database Engineer** – reads the SDD, generates production‑ready PostgreSQL DDL, runs a systematic SQL review, and saves the result as `init_schema.sql`.
3. **Discord Progress Reporter** – sends status updates to a Discord channel for the project manager.
4. **Systematic Code Reviewer** – checks generated SQL for anti‑patterns (SELECT *, missing NOT NULL, unsafe DROP TABLE, etc.).

---

## ✅ Completed
- CrewAI agents and tasks defined.
- Built‑in Discord reporting and SQL review tools.
- Automatic generation of `system_design_doc.md` and `init_schema.sql`.

## 🚧 In Progress
- Front‑end UI (React/Next.js).
- Unit & integration tests.
- CI/CD pipeline.

## ⏳ To‑Do
- Add `pytest` test suite under `tests/`.
- Create GitHub Actions workflow for linting, type‑checking, and testing.
- Refactor file paths to consistently use the `src/` directory.
- Centralise configuration (model, base URL) in `.env` or `config.yaml`.
- Implement robust error handling for Discord webhooks and LLM calls.

---

*All sensitive keys must be stored in a `.env` file and never committed.*