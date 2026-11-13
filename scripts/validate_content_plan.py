#!/usr/bin/env python3
"""Validasi paket rencana konten (operations/plans/*.json) sebelum ACC.

Aturan yang ditegakkan, semuanya dibaca dari config (bukan hardcode):
- caption tanpa emoji/emotikon (config/project.json caption_policy.no_emoji)
- hashtag tanpa nama diri karakter
  (config/autopilot.json caption_policy.hashtag_policy.prohibit_character_self_name_tag)
- durasi video ada di video_policy.allowed_durations_seconds
- prompt visual menyebut rasio 9:16 dan memakai referensi identitas master
- field wajib paket lengkap

Pemakaian:
    python3 scripts/validate_content_plan.py operations/plans/*.json
Exit code 0 = semua lolos, 1 = ada pelanggaran.

Skrip ini hanya membaca file; tidak menyentuh DB, Flow, atau media.
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.autopilot import max_video_duration_for, validate_isk_video_plan
from app.review import ReviewError

REQUIRED_PLAN_KEYS = ("plan_date", "status", "slots")
REQUIRED_SLOT_KEYS = (
    "id",
    "day",
    "character_id",
    "kind",
    "title",
    "hook",
    "story",
    "caption",
    "hashtags",
    "shots",
    "new_biography_facts",
    "promotional",
    "trend_sources",
)


NEGATIONS = ("no ", "not ", "without ", "avoid ", "zero ", "no-", "non-")


def prohibited_hits(prompt_lowered: str, term: str) -> bool:
    """True bila `term` muncul TANPA negasi di depannya.

    Klausa wajib Anti-AI Slop sendiri memakai bentuk negatif ("no glass skin",
    "no artificial golden glow"), jadi pencarian naif akan melaporkan false positive.
    """
    start = 0
    while True:
        index = prompt_lowered.find(term, start)
        if index == -1:
            return False
        window = prompt_lowered[max(0, index - 32):index]
        if not any(neg in window for neg in NEGATIONS):
            return True
        start = index + 1


def is_emoji_like(ch: str) -> bool:
    cp = ord(ch)
    return (
        cp >= 0x1F000
        or 0x2600 <= cp <= 0x27BF
        or 0xFE00 <= cp <= 0xFE0F
        or 0x1F1E6 <= cp <= 0x1F1FF
        or cp in (0x2B50, 0x2B55)
        or unicodedata.category(ch) == "So"
    )


def name_tokens(char: dict) -> set[str]:
    tokens = {str(char.get("id", "")).lower()}
    for field in ("name", "tiktok_account"):
        value = char.get(field)
        if isinstance(value, str):
            cleaned = value.lstrip("@").replace("_", " ").replace(".", " ")
            tokens.update(part for part in cleaned.lower().split() if len(part) > 1)
            tokens.add(cleaned.replace(" ", "").lower())
    return {t for t in tokens if t}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    plan = load_json(path)
    if plan.get("status") == "superseded":
        return []  # riwayat: tidak dipakai produksi, jangan kotori hasil validasi aktif
    if "slots" not in plan and plan.get("purpose"):
        return []  # format pilot teknis lama (single plan_json), bukan rencana harian
    project = load_json(ROOT / "config/project.json")
    autopilot = load_json(ROOT / "config/autopilot.json")
    allowed_durations = set(project["video_policy"]["allowed_durations_seconds"])
    # Anti-AI Slop tinggal di config/autopilot.json (video_policy), dengan fallback ke project.json.
    slop = (
        autopilot.get("video_policy", {}).get("anti_ai_slop_policy")
        or project.get("video_policy", {}).get("anti_ai_slop_policy")
        or {}
    )
    prohibited_terms = [t.lower() for t in slop.get("prohibited_prompt_terms", [])]
    mandatory_clauses = [t.lower() for t in slop.get("mandatory_prompt_clauses", [])]
    slop_required = bool(slop.get("mandatory", False))
    self_name_banned = bool(
        autopilot["caption_policy"].get("hashtag_policy", {}).get(
            "prohibit_character_self_name_tag", False
        )
    )

    for key in REQUIRED_PLAN_KEYS:
        if key not in plan:
            errors.append(f"plan: field wajib '{key}' tidak ada")

    for slot in plan.get("slots", []):
        label = slot.get("id", "<tanpa id>")
        for key in REQUIRED_SLOT_KEYS:
            if key not in slot:
                errors.append(f"{label}: field wajib '{key}' tidak ada")

        caption = str(slot.get("caption", ""))
        hits = sorted({ch for ch in caption if is_emoji_like(ch)})
        if hits:
            errors.append(f"{label}: caption memuat emoji/emotikon {hits}")
        if not caption.strip():
            errors.append(f"{label}: caption kosong")

        character_id = slot.get("character_id")
        profile_path = ROOT / "characters" / str(character_id) / "profile.json"
        char = load_json(profile_path) if profile_path.exists() else {"id": character_id}
        banned = name_tokens(char)
        hashtags = slot.get("hashtags", [])
        if not hashtags:
            errors.append(f"{label}: hashtags kosong")
        for tag in hashtags:
            if not str(tag).startswith("#"):
                errors.append(f"{label}: hashtag '{tag}' tidak diawali '#'")
            if self_name_banned and any(token in str(tag).lstrip("#").lower() for token in banned):
                errors.append(
                    f"{label}: hashtag '{tag}' memuat nama diri karakter (dilarang)"
                )

        if slot.get("kind") == "video":
            duration = slot.get("duration_seconds")
            char_max = max_video_duration_for(project, character_id)
            if character_id == "isk":
                try:
                    validate_isk_video_plan(slot, max_final_duration=char_max)
                except ReviewError as exc:
                    errors.append(f"{label}: {exc}")
            elif character_id == "pak_vincent" and (type(duration) is not int or not 10 <= duration <= char_max):
                errors.append(
                    f"{label}: durasi {duration}s Pak Vincent harus antara 10 sampai {char_max}s (minimal 10s, maksimal {char_max}s)"
                )
            elif type(duration) is not int or duration > char_max:
                errors.append(
                    f"{label}: durasi {duration}s melebihi batas maksimal karakter ({char_max}s)"
                )
            elif duration not in allowed_durations:
                errors.append(
                    f"{label}: durasi {duration} tidak ada di allowed_durations_seconds {sorted(allowed_durations)}"
                )
            shots = slot.get("shots", [])
            if not shots:
                errors.append(f"{label}: video tanpa shots")
            for index, shot in enumerate(shots):
                prompt = str(shot.get("prompt", ""))
                lowered = prompt.lower()
                if "9:16" not in prompt:
                    errors.append(f"{label}: prompt shot {index} tidak menyebut 9:16")
                if "reference" not in lowered:
                    errors.append(
                        f"{label}: prompt shot {index} tidak merujuk referensi identitas"
                    )
                if slop_required:
                    for term in prohibited_terms:
                        if prohibited_hits(lowered, term):
                            errors.append(
                                f"{label}: prompt shot {index} memuat istilah Anti-AI Slop yang dilarang: '{term}'"
                            )
                    missing = [c for c in mandatory_clauses if c not in lowered]
                    if missing:
                        errors.append(
                            f"{label}: prompt shot {index} kehilangan klausa wajib Anti-AI Slop: {missing}"
                        )
        elif slot.get("kind") == "photo":
            if not slot.get("shots"):
                errors.append(f"{label}: foto tanpa prompt")
        else:
            errors.append(f"{label}: kind '{slot.get('kind')}' tidak dikenal")

        if slot.get("trend_sources") and not autopilot.get("research_enabled"):
            errors.append(
                f"{label}: klaim tren dipakai padahal research_enabled false"
            )

    return errors


def main(argv: list[str]) -> int:
    targets = [Path(arg) for arg in argv[1:]]
    if not targets:
        targets = sorted((ROOT / "operations/plans").glob("*.json"))
    if not targets:
        print("tidak ada file rencana untuk divalidasi")
        return 1

    failed = 0
    for path in targets:
        errors = validate(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {path}")
    print(f"\n{len(targets) - failed}/{len(targets)} file lolos")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
