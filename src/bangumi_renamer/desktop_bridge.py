"""JSON bridge used by the Tauri desktop application.

The bridge keeps filesystem and metadata-provider work in Python so the CLI and desktop
application continue to share the same planning and apply pipeline.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from .core import PlanItem, apply_plan, build_plan
from .matcher import force_match, search_candidates
from .metadata import MetadataClient
from .parser import extract_media_extension
from .scanner import scan
from .thetvdb import TheTvdbClient
from .tmdb import TmdbClient

_CONFIG_DIR = Path(user_config_dir("Bangumi Renamer", appauthor=False))
_CONFIG_PATH = _CONFIG_DIR / "settings.json"
_VALID_CONFLICT_POLICIES = {"skip", "suffix", "overwrite"}
_VALID_UI_LANGUAGES = {"zh-CN", "zh-TW", "en-US", "ja-JP"}
_VALID_THEMES = {"system", "light", "dark"}
_VALID_METADATA_PROVIDERS = {"thetvdb", "tmdb"}


def load_settings() -> dict[str, Any]:
    """Load desktop preferences without exposing stored credentials to the UI."""
    stored = _load_stored_settings()
    provider = _normalize_metadata_provider(stored.get("metadata_provider"))
    tmdb_key, tmdb_key_from_env = _credential_value(
        stored, "TMDB_API_KEY", "tmdb_api_key", "api_key"
    )
    thetvdb_key, thetvdb_key_from_env = _credential_value(
        stored, "THETVDB_API_KEY", "thetvdb_api_key"
    )
    thetvdb_pin, thetvdb_pin_from_env = _credential_value(
        stored, "THETVDB_PIN", "thetvdb_pin"
    )
    has_tmdb_api_key = bool(tmdb_key)
    has_thetvdb_api_key = bool(thetvdb_key)
    selected_has_key = has_thetvdb_api_key if provider == "thetvdb" else has_tmdb_api_key
    selected_env_key = thetvdb_key_from_env if provider == "thetvdb" else tmdb_key_from_env
    return {
        "metadata_provider": provider,
        "ui_language": _normalize_ui_language(stored.get("ui_language")),
        "conflict_policy": _normalize_conflict_policy(stored.get("conflict_policy")),
        "theme": _normalize_theme(stored.get("theme")),
        "has_api_key": selected_has_key,
        "api_key_from_environment": selected_env_key,
        "has_thetvdb_api_key": has_thetvdb_api_key,
        "thetvdb_api_key_from_environment": thetvdb_key_from_env,
        "has_thetvdb_pin": bool(thetvdb_pin),
        "thetvdb_pin_from_environment": thetvdb_pin_from_env,
        "has_tmdb_api_key": has_tmdb_api_key,
        "tmdb_api_key_from_environment": tmdb_key_from_env,
    }


def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist validated desktop preferences in the platform config directory."""
    stored = _load_stored_settings()
    ui_language = _normalize_ui_language(payload.get("ui_language", stored.get("ui_language")))
    conflict_policy = _normalize_conflict_policy(
        payload.get("conflict_policy", stored.get("conflict_policy"))
    )
    theme = _normalize_theme(payload.get("theme", stored.get("theme")))
    provider = _normalize_metadata_provider(
        payload.get("metadata_provider", stored.get("metadata_provider"))
    )

    # ``api_key`` is the legacy TMDB field and remains accepted during migration.
    _store_secret(stored, "tmdb_api_key", payload.get("tmdb_api_key", payload.get("api_key")))
    _store_secret(stored, "thetvdb_api_key", payload.get("thetvdb_api_key"))
    _store_secret(stored, "thetvdb_pin", payload.get("thetvdb_pin"))
    if payload.get("clear_tmdb_api_key") is True or payload.get("clear_api_key") is True:
        stored.pop("tmdb_api_key", None)
        stored.pop("api_key", None)
    if payload.get("clear_thetvdb_api_key") is True:
        stored.pop("thetvdb_api_key", None)
    if payload.get("clear_thetvdb_pin") is True:
        stored.pop("thetvdb_pin", None)
    stored.pop("language", None)
    stored.update(
        {
            "metadata_provider": provider,
            "ui_language": ui_language,
            "conflict_policy": conflict_policy,
            "theme": theme,
        }
    )

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = _CONFIG_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(stored, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.chmod(0o600)
    temp_path.replace(_CONFIG_PATH)
    return load_settings()


def scan_folder(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a non-destructive rename plan for a folder."""
    root = _require_directory(payload.get("path"))
    client = _make_client(payload)
    try:
        items = build_plan(
            files=scan(root),
            client=client,
            forced=None,
            on_conflict=_normalize_conflict_policy(payload.get("conflict_policy")),
            verbose=True,
        )
    finally:
        client.close()
    return {"root": str(root), "items": [_serialize_plan_item(item) for item in items]}


def search_matches(payload: dict[str, Any]) -> dict[str, Any]:
    """Return scored provider candidates for a parsed series title."""
    query = str(payload.get("query", "")).strip()
    if not query:
        raise ValueError("A non-empty candidate query is required.")
    client = _make_client(payload)
    try:
        candidates = search_candidates(query, client=client)
    finally:
        client.close()
    return {"candidates": [asdict(candidate) for candidate in candidates]}


def rebuild_matches(payload: dict[str, Any]) -> dict[str, Any]:
    """Rebuild selected rows using a user-selected provider series."""
    sources = [_require_file(path) for path in payload.get("sources", [])]
    if not sources:
        raise ValueError("At least one source file is required.")
    provider_id = int(payload.get("provider_id", payload.get("tmdb_id")))
    client = _make_client(payload)
    try:
        forced = force_match(provider_id, client=client)
        items = build_plan(
            files=sources,
            client=client,
            forced=forced,
            on_conflict=_normalize_conflict_policy(payload.get("conflict_policy")),
            verbose=True,
        )
    finally:
        client.close()
    return {"items": [_serialize_plan_item(item) for item in items]}


def apply_items(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply only validated, actionable rows returned by the planning pipeline."""
    root = _require_directory(payload.get("root")).resolve()
    items = [_deserialize_apply_item(raw, root=root) for raw in payload.get("items", [])]
    actionable = [item for item in items if item.status == "OK" and item.target is not None]
    renames, history_path = apply_plan(actionable, root=root)
    return {
        "renamed": len(renames),
        "renames": [{"source": str(source), "target": str(target)} for source, target in renames],
        "history_path": str(history_path) if history_path else None,
    }


def test_provider_connection(payload: dict[str, Any]) -> dict[str, Any]:
    """Test provider credentials without persisting draft values from the settings form."""
    stored = _load_stored_settings()
    provider = _normalize_metadata_provider(payload.get("metadata_provider"))
    language = str(payload.get("language") or "en-US")

    if provider == "thetvdb":
        api_key = _draft_or_saved_credential(
            payload, stored, "thetvdb_api_key", "THETVDB_API_KEY"
        )
        pin = _draft_or_saved_credential(payload, stored, "thetvdb_pin", "THETVDB_PIN")
        client: MetadataClient = TheTvdbClient(api_key=api_key, pin=pin, lang=language)
    else:
        api_key = _draft_or_saved_credential(
            payload, stored, "tmdb_api_key", "TMDB_API_KEY", "api_key"
        )
        client = TmdbClient(api_key=api_key, lang=language)

    try:
        client.test_connection()
    finally:
        client.close()
    return {"provider": provider, "connected": True}


def dispatch(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch one allow-listed desktop command."""
    handlers = {
        "settings.get": lambda _payload: load_settings(),
        "settings.save": save_settings,
        "settings.test_connection": test_provider_connection,
        "plan.scan": scan_folder,
        "plan.candidates": search_matches,
        "plan.rebuild": rebuild_matches,
        "plan.apply": apply_items,
    }
    handler = handlers.get(command)
    if handler is None:
        raise ValueError(f"Unsupported desktop command: {command}")
    return handler(payload)


def _load_stored_settings() -> dict[str, Any]:
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _normalize_conflict_policy(value: object) -> str:
    policy = str(value or "suffix")
    return policy if policy in _VALID_CONFLICT_POLICIES else "suffix"


def _normalize_ui_language(value: object) -> str:
    language = str(value or "en-US")
    return language if language in _VALID_UI_LANGUAGES else "en-US"


def _normalize_theme(value: object) -> str:
    theme = str(value or "system")
    return theme if theme in _VALID_THEMES else "system"


def _normalize_metadata_provider(value: object) -> str:
    provider = str(value or "thetvdb").lower()
    return provider if provider in _VALID_METADATA_PROVIDERS else "thetvdb"


def _store_secret(stored: dict[str, Any], key: str, value: object) -> None:
    if isinstance(value, str) and value.strip():
        stored[key] = value.strip()


def _credential_value(
    stored: dict[str, Any], environment_name: str, *stored_keys: str
) -> tuple[str, bool]:
    environment_value = os.environ.get(environment_name, "").strip()
    stored_value = next(
        (str(stored.get(key) or "").strip() for key in stored_keys if stored.get(key)),
        "",
    )
    return environment_value or stored_value, bool(environment_value)


def _draft_or_saved_credential(
    payload: dict[str, Any],
    stored: dict[str, Any],
    payload_key: str,
    environment_name: str,
    *legacy_stored_keys: str,
) -> str:
    draft = payload.get(payload_key)
    if isinstance(draft, str) and draft.strip():
        return draft.strip()
    value, _ = _credential_value(
        stored,
        environment_name,
        payload_key,
        *legacy_stored_keys,
    )
    return value


def _make_client(payload: dict[str, Any]) -> MetadataClient:
    stored = _load_stored_settings()
    provider = _normalize_metadata_provider(
        payload.get("metadata_provider", stored.get("metadata_provider"))
    )
    language = str(payload.get("language") or "en-US")
    if provider == "thetvdb":
        api_key, _ = _credential_value(stored, "THETVDB_API_KEY", "thetvdb_api_key")
        pin, _ = _credential_value(stored, "THETVDB_PIN", "thetvdb_pin")
        return TheTvdbClient(api_key=api_key, pin=pin, lang=language)

    api_key, _ = _credential_value(stored, "TMDB_API_KEY", "tmdb_api_key", "api_key")
    return TmdbClient(api_key=api_key, lang=language)


def _require_directory(value: object) -> Path:
    path = Path(str(value or "")).expanduser()
    if not path.is_dir():
        raise ValueError(f"Directory does not exist: {path}")
    return path.resolve()


def _require_file(value: object) -> Path:
    path = Path(str(value or "")).expanduser()
    if not path.is_file():
        raise ValueError(f"File does not exist: {path}")
    return path.resolve()


def _serialize_plan_item(item: PlanItem) -> dict[str, Any]:
    parsed = None
    if item.parsed is not None:
        parsed = {
            "title": item.parsed.title,
            "season": item.parsed.season,
            "episode": item.parsed.episode,
            "year": item.parsed.year,
        }
    match = asdict(item.match) if item.match is not None else None
    return {
        "source": str(item.source),
        "source_name": item.source.name,
        "target": str(item.target) if item.target else None,
        "target_name": item.target.name if item.target else None,
        "status": item.status,
        "detail": item.detail,
        "parsed": parsed,
        "match": match,
    }


def _deserialize_apply_item(raw: object, *, root: Path) -> PlanItem:
    if not isinstance(raw, dict):
        raise ValueError("Invalid plan item payload.")
    source = _require_file(raw.get("source"))
    target_value = raw.get("target")
    if not isinstance(target_value, str) or not target_value:
        raise ValueError(f"Missing target for {source.name}.")
    target = Path(target_value).expanduser().resolve()

    if source.parent != target.parent:
        raise ValueError("Rename targets must remain in the source directory.")
    if extract_media_extension(source) != extract_media_extension(target):
        raise ValueError("Rename targets must preserve the source extension.")
    if not source.is_relative_to(root) or not target.is_relative_to(root):
        raise ValueError("Rename paths must stay inside the selected root.")
    if raw.get("status") != "OK":
        raise ValueError(f"Refusing to apply a non-actionable row: {source.name}")

    return PlanItem(
        source=source,
        parsed=None,
        match=None,
        target=target,
        status="OK",
        detail=str(raw.get("detail", "")),
    )


def main() -> None:
    """Read one request from stdin and write one JSON response to stdout."""
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m bangumi_renamer.desktop_bridge <command>")
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("Desktop payload must be a JSON object.")
        result = dispatch(sys.argv[1], payload)
        response = {"ok": True, "data": result}
    except Exception as exc:  # noqa: BLE001 - serialized for the desktop error boundary
        response = {"ok": False, "error": str(exc)}
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
