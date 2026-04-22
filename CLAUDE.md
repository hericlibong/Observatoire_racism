# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python 3.12+ data pipeline for analyzing French parliamentary debates (Assemblée nationale, Syceron XML corpus). Detects hate speech, racism, xenophobia, discrimination, and problematic group-targeting signals. Contextualizes via Mistral LLM.

Scope is strictly limited to discriminatory signals. This project must not become a general political-tension or civic-climate observatory.

Key reference docs:
- `docs/assemblee_roadmap.md` — planning source of truth
- `docs/assemblee_contextualization_contract_v2.md` — V2 contract reference
- `docs/audit_architecture.md` — architecture audit and Phase G refactoring roadmap

## Commands

```bash
# Install (editable, with dev deps)
python -m pip install -e '.[dev]'

# Test
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/assemblee_contextualization/test_review_engine.py -v

# Lint (check)
python -m ruff check src tests

# Format
python -m ruff format src tests

# Type check
python -m mypy src tests
```

## Architecture

**Data flow:**
```
ZIP archive → source_acquisition → XML files (data/raw/)
    → build_assemblee_pilot (parse XML, detect lexical signals) → CSV + D3 JSON
    → context_builder (windowed context payload)
    → provider V2 (Mistral or Mock)
    → review_engine (orchestrate, validate contracts, journal)
    → JSONL reviews (data/interim/) + heatmap export (data/exports/d3/)
```

**Main layers:**

1. **Acquisition & Parsing** — `src/build_assemblee_pilot.py`, `src/assemblee_contextualization/sources/` (`source_acquisition.py`, `source_inventory.py`, `source_manifest.py`, `xml_parser.py`)
   - Downloads/imports ZIP archives, extracts and validates Syceron XML
   - Parses interventions, applies rule-based lexical signal detection

2. **Contracts** — `src/assemblee_contextualization/contracts.py`
   - Frozen dataclasses and enums: `ScopeLevel`, `SignalCategory`, `Confidence`, `ContextPayload`
   - Enforces allowed combinations and fallback invariants (see "Invariants" below)

3. **Review Engine** — `src/assemblee_contextualization/review_engine.py`
   - `review_candidates_v2()`: selects candidates, builds context, calls provider, validates output
   - Anti-duplicate tracking via `processing_journal.py`

4. **Providers** — `src/assemblee_contextualization/providers/`
   - `providers/__init__.py`: exposes the `ContextualReviewProvider` ABC
   - `providers/mistral_provider_v2.py`: real Mistral API (reads `MISTRAL_API_KEY` from `.env`)
   - `providers/mock_provider_v2.py`: offline deterministic mock for tests
   - V1 files live in `src/assemblee_contextualization/legacy/` (`reviewer.py`, `mock_provider.py`, `mistral_provider.py`, `run_pilot.py`) — preserved for history, do not modify

4b. **Runners** — `src/assemblee_contextualization/runners/`
   - `run_pilot_v2.py`, `run_phase_c_lot_v2.py`, `run_incremental_session_v2.py`: CLI entry points orchestrating the V2 pipeline

5. **I/O & Export** — `src/assemblee_contextualization/io_v2.py`, `heatmap_export.py`
   - JSONL read/write, result summaries, D3 heatmap generation

6. **Paths & Utilities** — `src/assemblee_contextualization/paths.py`, `env.py`
   - Centralized constants: `ROOT_DIR`, `SOURCE_DIR`, `INTERIM_DIR`, `EXPORTS_D3_DIR`
   - `.env` loading for `MISTRAL_API_KEY` and `MISTRAL_MODEL`

## Code conventions

- `from __future__ import annotations` at the top of every module
- Strict type annotations on all function signatures
- Absolute imports for modules outside the package; relative imports allowed within `assemblee_contextualization`
- Prefer pure functions and `frozen=True` dataclasses over classes
- Use `logging` for all new code; do not convert existing `print()` calls unless the task requires it
- No new dependencies without explicit justification

## Tests

- Mirror structure: `tests/assemblee/` ↔ `src/build_assemblee_*.py`, `tests/assemblee_contextualization/` ↔ `src/assemblee_contextualization/`
- No real filesystem, network, or Mistral API access in tests — use `tmp_path`, fixtures, and mocks
- Every new or modified function must have a corresponding test; never mark a step complete until its tests pass

## Contract invariants (V2)

Never modify `ScopeLevel`, `SignalCategory`, or `Confidence` enums, or the allowed-combination table, without a documented roadmap decision.

- `is_fallback=True` only allowed for `hors_perimetre / ambiguous` with `needs_human_review=True` and `confidence=low`
- `is_fallback=True` records are always excluded from substantive metrics
- `needs_human_review=False` only allowed for `hors_perimetre / no_signal / confidence=high`

## Working method

One atomic sub-step at a time: write the code, verify the tests, commit, then move on. Never modify more than one module at once without explicit reason. Do not anticipate Phase G refactorings in unrelated tasks — apply each refactoring as an isolated step with its own tests.
