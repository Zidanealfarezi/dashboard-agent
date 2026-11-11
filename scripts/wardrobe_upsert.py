#!/usr/bin/env python3
"""Upsert baris wardrobe dari file JSON (dipakai daily_pinterest_wardrobe_job.js).

Kenapa file JSON: menyisipkan SQL lewat `python3 -c "..."` membuat escaping
rapuh dan dulu gagal tanpa jejak. Skrip ini menerima path JSON berisi
{"db": "...", "rows": [{...}]} dan melakukan INSERT OR REPLACE per baris.

Pakai: python3 scripts/wardrobe_upsert.py /path/to/payload.json
"""

import json
import os
import sqlite3
import sys

COLUMNS = (
    "id", "character_id", "name", "category", "color_palette", "vibe_tags",
    "hijab_type", "top_description", "bottom_description", "footwear_accessories",
    "closeup_photo_path", "fullbody_photo_path", "times_used", "last_used_at",
    "status", "created_at",
)


def main(argv):
    if len(argv) != 2:
        raise SystemExit("pakai: wardrobe_upsert.py <payload.json>")
    payload = json.loads(open(argv[1], encoding="utf-8").read())
    rows = payload.get("rows") or []
    if not rows:
        raise SystemExit("payload tidak berisi rows")
    conn = sqlite3.connect(payload["db"])
    try:
        with conn:
            for row in rows:
                missing = [c for c in ("id", "character_id", "name", "category", "created_at") if not row.get(c)]
                if missing:
                    raise SystemExit(f"baris kehilangan kolom wajib: {missing}")
                row.setdefault("vibe_tags", "[]")
                closeup = (row.get("closeup_photo_path") or "").strip()
                fullbody = (row.get("fullbody_photo_path") or "").strip()
                row["closeup_photo_path"] = closeup
                row["fullbody_photo_path"] = fullbody
                row.setdefault("times_used", 0)

                # Kebijakan Autopilot: Outfit hanya sah 'active' bila kedua file foto referensi benar-benar ada di disk
                has_files = (
                    bool(closeup and fullbody)
                    and os.path.isfile(closeup)
                    and os.path.isfile(fullbody)
                )
                if not has_files:
                    row["status"] = "incomplete"
                else:
                    row.setdefault("status", "active")

                values = [row.get(c) for c in COLUMNS]
                conn.execute(
                    f"INSERT OR REPLACE INTO character_wardrobe ({', '.join(COLUMNS)}) "
                    f"VALUES ({', '.join(['?'] * len(COLUMNS))})",
                    values,
                )
        count = conn.execute("SELECT COUNT(*) FROM character_wardrobe").fetchone()[0]
    finally:
        conn.close()
    print(f"wardrobe upsert ok: {len(rows)} baris, total {count}")


if __name__ == "__main__":
    main(sys.argv)
