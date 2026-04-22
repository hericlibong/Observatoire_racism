from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from src.assemblee_contextualization.io_v2 import read_outputs_v2, summarize_output_file, write_outputs_v2
from src.assemblee_contextualization.processing_journal import (
    JOURNAL_PATH,
    append_processing_journal_entry,
    read_processing_journal,
)
from src.assemblee_contextualization.paths import INTERIM_DIR, ROOT_DIR, display_path, session_slug
from src.assemblee_contextualization.providers import ContextualReviewProvider
from src.assemblee_contextualization.review_engine import (
    DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES,
    review_candidates_v2,
)
from src.assemblee_contextualization.runners.run_pilot_v2 import (
    build_provider,
    load_interventions_for_source,
)
from src.assemblee_contextualization.sources.source_manifest import MANIFEST_PATH


OUTPUT_DIR = INTERIM_DIR


class IncrementalSessionError(ValueError):
    pass


def build_dry_run_status(
    source_file: str,
    *,
    provider_name: str,
    manifest_path: Path = MANIFEST_PATH,
    journal_path: Path = JOURNAL_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    session = resolve_incremental_target(source_file, manifest, journal_path=journal_path)
    output_path, summary_path = incremental_output_paths(source_file, provider_name, output_dir)
    return {
        "dry_run": True,
        "source_file": session["source_file"],
        "seance_id": session["seance_id"],
        "seance_date": session["seance_date"],
        "seance_date_label": session["seance_date_label"],
        "available_status": session["available_status"],
        "already_processed": session["already_processed"],
        "journal_status": session["journal_status"],
        "local_path": session["local_path"],
        "output_jsonl": str(display_path(output_path)),
        "summary_json": str(display_path(summary_path)),
        "provider": provider_name,
        "will_call_provider": False,
        "message": "Aucun appel provider, aucun appel Mistral, aucun traitement V2 lance.",
    }


def run_incremental_session(
    source_file: str,
    *,
    provider_name: str,
    confirm: bool,
    manifest_path: Path = MANIFEST_PATH,
    journal_path: Path = JOURNAL_PATH,
    output_dir: Path = OUTPUT_DIR,
    window: int = 2,
    sample_size_when_no_candidates: int = DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES,
    provider: ContextualReviewProvider | None = None,
    interventions_loader: Callable[[str], list[dict[str, Any]]] = load_interventions_for_source,
) -> dict[str, Any]:
    if not confirm:
        raise PermissionError("--confirm est requis pour lancer le traitement incremental V2.")

    manifest = load_manifest(manifest_path)
    session = resolve_incremental_target(source_file, manifest, journal_path=journal_path)
    output_path, summary_path = incremental_output_paths(source_file, provider_name, output_dir)
    provider_instance = provider or build_provider(provider_name)

    try:
        interventions = interventions_loader(source_file)
        outputs = review_candidates_v2(
            interventions,
            provider_instance,
            source_file=source_file,
            window=window,
            sample_size_when_no_candidates=sample_size_when_no_candidates,
        )
        write_outputs_v2(outputs, output_path)
        read_outputs_v2(output_path)
        summary = write_incremental_summary(
            output_path,
            summary_path,
            session=session,
            provider_name=provider_name,
            provider=provider_instance,
        )
        journal_entry = _journal_entry(
            session=session,
            provider_name=provider_name,
            provider=provider_instance,
            outputs=[output_path, summary_path],
            status="success",
            reviewed_items=int(summary["reviewed_items"]),
            fallback_count=int(summary["fallback_technical"]),
            error="",
        )
        append_processing_journal_entry(journal_entry, journal_path)
        return {
            "source_file": source_file,
            "status": "success",
            "output_jsonl": str(display_path(output_path)),
            "summary_json": str(display_path(summary_path)),
            "journal_entry": journal_entry,
            "reviewed_items": int(summary["reviewed_items"]),
            "fallback_count": int(summary["fallback_technical"]),
        }
    except Exception as exc:
        journal_entry = _journal_entry(
            session=session,
            provider_name=provider_name,
            provider=provider_instance,
            outputs=[],
            status="error",
            reviewed_items=0,
            fallback_count=0,
            error=str(exc),
        )
        append_processing_journal_entry(journal_entry, journal_path)
        raise


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_incremental_target(
    source_file: str,
    manifest: dict[str, Any],
    *,
    journal_path: Path = JOURNAL_PATH,
) -> dict[str, Any]:
    sessions = [
        session
        for session in manifest.get("sessions", [])
        if session.get("source_file") == source_file
    ]
    if not sessions:
        raise IncrementalSessionError(f"Seance absente du manifest : {source_file}")
    if len(sessions) > 1:
        raise IncrementalSessionError(f"Seance dupliquee dans le manifest : {source_file}")

    session = dict(sessions[0])
    available_status = str(session.get("available_status", ""))
    if available_status != "available":
        raise IncrementalSessionError(
            f"Seance non eligible : {source_file} a le statut manifest {available_status}."
        )

    start_date = date.fromisoformat(str(manifest["initialization_from_date"]))
    seance_date = date.fromisoformat(str(session["seance_date"]))
    if seance_date < start_date:
        raise IncrementalSessionError(f"Seance avant le seuil d'initialisation : {source_file}")

    local_path = _resolve_local_path(str(session["local_path"]))
    if not local_path.exists():
        raise IncrementalSessionError(f"XML local introuvable : {session['local_path']}")

    journal_entry = _matching_journal_entry(session, journal_path)
    if journal_entry is not None:
        raise IncrementalSessionError(
            f"Seance deja journalisee : {source_file}, statut {journal_entry.get('status')}."
        )

    if session.get("already_processed") or session.get("journal_status") != "not_processed":
        raise IncrementalSessionError(
            f"Seance deja marquee traitee dans le manifest : {source_file}."
        )

    return session


def incremental_output_paths(
    source_file: str,
    provider_name: str,
    output_dir: Path = OUTPUT_DIR,
) -> tuple[Path, Path]:
    slug = session_slug(source_file)
    base = f"contextual_reviews_incremental_{slug}_v2_{provider_name}"
    return output_dir / f"{base}.jsonl", output_dir / f"{base}_summary.json"


def write_incremental_summary(
    output_path: Path,
    summary_path: Path,
    *,
    session: dict[str, Any],
    provider_name: str,
    provider: ContextualReviewProvider,
) -> dict[str, Any]:
    output_summary = summarize_output_file(output_path)
    payload = {
        "summary_type": "assemblee_contextual_reviews_v2_incremental_session",
        "source_file": session["source_file"],
        "seance_id": session["seance_id"],
        "seance_date": session["seance_date"],
        "seance_date_label": session["seance_date_label"],
        "provider": _journal_provider_name(provider_name, provider),
        "model_name": _journal_model_name(provider_name, provider),
        "output_path": str(display_path(output_path)),
        "fallbacks_excluded_from_substantive_metrics": True,
        **output_summary,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _journal_entry(
    *,
    session: dict[str, Any],
    provider_name: str,
    provider: ContextualReviewProvider,
    outputs: list[Path],
    status: str,
    reviewed_items: int,
    fallback_count: int,
    error: str,
) -> dict[str, Any]:
    return {
        "seance_id": session["seance_id"],
        "source_file": session["source_file"],
        "seance_date": session["seance_date"],
        "seance_date_label": session["seance_date_label"],
        "processed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "provider": _journal_provider_name(provider_name, provider),
        "model_name": _journal_model_name(provider_name, provider),
        "status": status,
        "outputs": [str(display_path(path)) for path in outputs],
        "fallback_count": fallback_count,
        "reviewed_items": reviewed_items,
        "error": error,
    }


def _matching_journal_entry(session: dict[str, Any], journal_path: Path) -> dict[str, Any] | None:
    for entry in read_processing_journal(journal_path):
        if entry.get("seance_id") == session.get("seance_id"):
            return entry
        if entry.get("source_file") == session.get("source_file"):
            return entry
    return None


def _journal_provider_name(provider_name: str, provider: ContextualReviewProvider) -> str:
    return str(getattr(provider, "model_provider", f"{provider_name}_v2"))


def _journal_model_name(provider_name: str, provider: ContextualReviewProvider) -> str:
    if provider_name == "mistral":
        return str(getattr(provider, "model", ""))
    return str(getattr(provider, "model_name", provider_name))


def _resolve_local_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Assemblee incremental V2 session.")
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--provider", choices=["mock", "mistral"], default="mock")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--journal", type=Path, default=JOURNAL_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--window", type=int, default=2)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES)
    args = parser.parse_args()

    try:
        if args.dry_run:
            print(
                json.dumps(
                    build_dry_run_status(
                        args.source_file,
                        provider_name=args.provider,
                        manifest_path=args.manifest,
                        journal_path=args.journal,
                        output_dir=args.output_dir,
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        result = run_incremental_session(
            args.source_file,
            provider_name=args.provider,
            confirm=args.confirm,
            manifest_path=args.manifest,
            journal_path=args.journal,
            output_dir=args.output_dir,
            window=args.window,
            sample_size_when_no_candidates=args.sample_size,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (IncrementalSessionError, PermissionError) as exc:
        print(json.dumps({"status": "refused", "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
