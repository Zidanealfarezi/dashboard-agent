#!/usr/bin/env python3
"""
Riset tren TikTok -> bank topik -> 1 topik terpilih (otonom) -> SQLite.

Aturan yang dipegang skrip ini:
- Bukti tren harus nyata: brief riset berisi >= 2 sumber yang benar-benar dibaca
  (verification_status = source_read) dan punya evidence non-kosong. Kalau tidak,
  skrip berhenti (fail closed) daripada mengarang topik.
- Owner tidak memilih. Skrip hanya mencetak keputusan; TIDAK ada panggilan jaringan,
  TIDAK ada pengiriman opsi A/B/C ke Telegram.
- Skor viral dihitung dari faktor eksplisit (momentum, relevansi lokal, kebaruan,
  kecocokan format, kekuatan bukti, risiko), bukan angka yang ditulis tangan.
- Satu keputusan per karakter per hari, disimpan di tabel trend_selections.

Pakai: python3 scripts/generate_content_options.py [--brief PATH] [--dry-run]
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from shared.sanitizer import clean_emojis, has_emojis

DB_PATH = BASE_DIR / "operations" / "production.sqlite"
REPORTS_DIR = BASE_DIR / "operations" / "reports"
BRIEF_DIR = BASE_DIR / "operations" / "research-briefs"
WIB = timezone(timedelta(hours=7))

MIN_SOURCES = 2
REQUIRED_SOURCE_STATUS = "source_read"

# Bobot faktor penilai potensi viral (total 1.0).
WEIGHTS = {
    "momentum": 0.25,
    "local_relevance": 0.20,
    "novelty": 0.20,
    "format_fit": 0.15,
    "evidence_strength": 0.15,
    "risk_safety": 0.05,
}


def now_wib():
    return datetime.now(WIB)


def load_brief(brief_path):
    """Memuat brief riset dan menolak brief yang buktinya tidak layak pakai."""
    if not brief_path or not Path(brief_path).exists():
        raise SystemExit(
            "STOP: brief riset tidak ada. Jalankan riset tren dulu dan simpan bukti "
            "ke operations/research-briefs/ sebelum membuat topik."
        )
    data = json.loads(Path(brief_path).read_text(encoding="utf-8"))
    candidates = data.get("candidates") or []
    readable = [
        c for c in candidates
        if c.get("verification_status") == REQUIRED_SOURCE_STATUS
        and str(c.get("evidence") or "").strip()
        and str(c.get("url") or "").startswith("https://")
        and (c.get("observed_at") or c.get("published_at"))
    ]
    if len(readable) < MIN_SOURCES:
        raise SystemExit(
            f"STOP: bukti tren terlalu lemah ({len(readable)} sumber terbaca, "
            f"minimal {MIN_SOURCES}). Tunda slot, jangan mengarang tren."
        )
    return data, readable


def get_available_wardrobe(character_id="dinda"):
    """Mengambil koleksi busana dari database wardrobe."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            SELECT name, category, color_palette, closeup_photo_path, fullbody_photo_path
            FROM character_wardrobe
            WHERE character_id = ? AND status = 'active'
            ORDER BY created_at DESC
            """,
            (character_id,),
        )
        rows = c.fetchall()
        conn.close()
        valid = [
            r for r in rows
            if r[3] and r[4] and Path(r[3]).is_file() and Path(r[4]).is_file()
        ]
        if valid:
            return [f"{r[0]} ({r[1]}, {r[2]})" for r in valid[:5]]
    except Exception:
        pass
    profile_path = BASE_DIR / "characters" / character_id / "profile.json"
    if profile_path.is_file():
        try:
            sig = json.loads(profile_path.read_text(encoding="utf-8")).get("signature_wardrobe")
            if sig:
                return [sig]
        except Exception:
            pass
    if character_id == "dinda":
        return ["Striped Taupe Knit Cardigan & Cream Palazzo (casual, earth-tone)"]
    return ["Pakaian kerja rapi sesuai profil karakter"]


def _tokens(text):
    return {w for w in re.findall(r"[a-z]{4,}", str(text).lower())}


def novelty_score(title, hook, previous_topics):
    """Penalti topik yang terlalu mirip dengan bank topik yang sudah ada."""
    new = _tokens(title) | _tokens(hook)
    if not new:
        return 5.0, []
    if not previous_topics:
        return 9.0, []
    overlaps = []
    worst = 0.0
    for topic in previous_topics:
        old = _tokens(topic)
        if not old:
            continue
        ratio = len(new & old) / len(new | old)
        if ratio >= 0.18:
            overlaps.append((round(ratio, 2), topic[:60]))
        worst = max(worst, ratio)
    return round(max(0.0, 10.0 - worst * 14.0), 2), overlaps


REQUIRED_CANDIDATE_FIELDS = ("code", "title", "hook", "caption", "sources", "factors")


def _candidates_from_brief(brief, fallback_outfit):
    """Kandidat topik yang ditulis langsung di brief riset, bila ada.

    Memungkinkan riset harian menyegarkan ide (bukan tiga topik tetap di kode). Brief
    tanpa `topic_candidates` tetap jalan dengan kandidat bawaan.
    """
    provided = brief.get("topic_candidates") or []
    if not provided:
        return []
    candidates = []
    codes = set()
    for raw in provided:
        missing = [f for f in REQUIRED_CANDIDATE_FIELDS if not raw.get(f)]
        if missing:
            raise SystemExit(f"STOP: topic_candidates kehilangan field wajib: {missing}")
        code = str(raw["code"]).upper()
        if code in codes:
            raise SystemExit(f"STOP: topic_candidates memakai kode ganda: {code}")
        codes.add(code)
        candidates.append(
            {
                "code": code,
                "title": raw["title"],
                "pillar": raw.get("pillar") or brief.get("pillar") or "Kuliner Khas Palembang",
                "hook": raw["hook"],
                "shots": raw.get("shots") or [],
                "sound": raw.get("sound") or "",
                "outfit": raw.get("outfit") or fallback_outfit,
                "caption": raw["caption"],
                "sources": raw["sources"],
                "near_duplicate_ids": raw.get("near_duplicate_ids") or [],
                "factors": raw["factors"],
                "why": raw.get("why") or "",
            }
        )
    return candidates


def _candidates_from_trend_memory(character_id, readable_sources, fallback_outfit):
    """Membaca bank ide dari tabel trend_memory untuk karakter non-Dinda (mis. bang_ray)."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(trend_memory)").fetchall()}
        select_extra = ", times_used, learnings" if {"times_used", "learnings"}.issubset(cols) else ""
        order_clause = (
            "ORDER BY COALESCE(times_used, 0) ASC, COALESCE(viral_score, 0.0) DESC, created_at DESC"
            if "times_used" in cols
            else "ORDER BY COALESCE(viral_score, 0.0) DESC, created_at DESC"
        )
        rows = conn.execute(
            f"""
            SELECT id, category, topic, hook_text, script_outline, viral_sound_title,
                   source_evidence, viral_score{select_extra}
            FROM trend_memory
            WHERE character_id = ?
              AND status IN ('discovered', 'drafted')
            {order_clause}
            LIMIT 10
            """,
            (character_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    source_urls = [s["url"] for s in readable_sources[:3]]
    candidates = []
    for idx, row in enumerate(rows):
        base_score = float(row["viral_score"] or 8.0)
        base_score = max(5.0, min(9.8, base_score))
        code = chr(ord("A") + idx)
        title = row["topic"]
        hook = row["hook_text"]
        outline = row["script_outline"] or ""
        caption = clean_emojis(
            f"{hook} Simpan tips ini biar kerja bangunan makin rapi dan aman. "
            f"#tipsbangunan #tukangbangunan #ilmubangunan #bandaaceh"
        )
        candidates.append(
            {
                "code": code,
                "existing_trend_id": row["id"],
                "title": title,
                "pillar": row["category"] or "Tips Bangunan",
                "hook": hook,
                "shots": [outline] if outline else [],
                "sound": row["viral_sound_title"] or "Suara asli lapangan tanpa musik mengganggu",
                "outfit": fallback_outfit,
                "caption": caption,
                "sources": source_urls,
                "near_duplicate_ids": [],
                "factors": {
                    "momentum": round(base_score, 2),
                    "local_relevance": 9.0,
                    "format_fit": 9.0,
                    "evidence_strength": min(9.5, 6.5 + 1.0 * len(source_urls)),
                    "risk_safety": 9.5,
                },
                "why": (row["learnings"] if "learnings" in row.keys() and row["learnings"] else f"Topik dari bank memori {character_id} ({row['id']})."),
            }
        )
    return candidates


def build_candidates(character_id, brief):
    """Menyusun kandidat topik. Tiap kandidat menempel ke sumber yang benar-benar dibaca."""
    sources = {c["url"]: c for c in brief["candidates"]}
    wardrobe = get_available_wardrobe(character_id)
    primary_outfit = wardrobe[0]

    def src(url):
        if url not in sources:
            raise SystemExit(f"STOP: kandidat merujuk sumber yang tidak ada di brief: {url}")
        return sources[url]

    candidates = _candidates_from_brief(brief, primary_outfit)
    if candidates:
        pass
    elif character_id == "dinda":
        bmkg = "https://staklim-sumsel.bmkg.go.id/prediksi-musim-hujan-tahun-2026-2027/"
        lagitren_today = "https://lagitren.id/tiktok"
        lagitren_musteat = "https://lagitren.id/tiktok/musteatinmycity"
        rri_asinan = ("https://rri.co.id/palembang/regional/2562968/"
                      "viral-di-tiktok-asinan-padat-raya-raup-omzet-rp8-juta-sehari")
        kompas_musteat = ("https://kompas.com/food/read/2026/11/01/075200375/"
                          "cara-pakai-fitur-must-eat-tiktok-mudah-temukan-tempat-makan-viral-dan-fine")

        candidates = [
            {
                "code": "A",
                "title": "Mie Celor Pertama di Musim Hujan: Sarapan Berkuah yang Bikin Palembang Betah",
                "pillar": "Kuliner Khas Palembang",
                "hook": "Palembang masuk musim hujan minggu ini, dan sarapan yang paling pas ya yang kuahnya masih ngebul.",
                "shots": [
                    "Shot 1 (8s): Dinda duduk di bangku kayu warung mie celor pagi, uap kuah udang mengepul di depan kamera, ia menyeruput santan kental lalu tersenyum puas.",
                    "Shot 2 (8s): Dinda menunjuk genangan hujan di jalan di balik warung, lalu menoleh ke kamera dan bertanya sarapan kuah favorit warga Palembang saat hujan.",
                ],
                "sound": "Lofi Akustik Pagi Hujan (format kuliner lokal, bukan klaim angka)",
                "outfit": primary_outfit,
                "caption": "Palembang baru mau masuk musim hujan minggu ini, jadi sarapan berkuah mulai balik jadi prioritas. Mie celor kuah udangnya kental, hangatnya nempel sampai siang. Kalau hujan pagi begini kalian pilih mie celor atau tekwan? #palembang #kulinerpalembang #miecelor #sarapanpalembang #musimhujan #dailyvlog",
                "sources": [bmkg, lagitren_today, kompas_musteat, rri_asinan],
                "factors": {
                    "momentum": 8.5,
                    "local_relevance": 9.5,
                    "format_fit": 9.0,
                    "evidence_strength": 9.0,
                    "risk_safety": 9.5,
                },
                "why": "BMKG memprediksi Palembang masuk musim hujan pada dasarian II November 2026, jadi kebutuhan sarapan berkuah relevan tepat minggu depan. Mie celor ikon Palembang tapi jarang jadi topik utama dibanding pempek.",
            },
            {
                "code": "B",
                "title": "Asinan Buah Viral yang Bikin Orang Luar Kota Pesan ke Palembang",
                "pillar": "Kuliner Khas Palembang",
                "hook": "Asinan buah di Palembang ini viral sampai pembelinya datang dari luar kota, dan ada sepuluh varian rasa.",
                "shots": [
                    "Shot 1 (8s): Dinda memilih cup asinan buah berwarna-warni di gerai, kamera menyorot mangga, jambu kristal dan salak yang basah kuah asam pedas.",
                    "Shot 2 (8s): Dinda mencicipi satu suapan, matanya membelalak kaget karena pedasnya, lalu tertawa dan menyebut varian mana yang paling worth it.",
                ],
                "sound": "Upbeat Jajanan Nusantara (format review kuliner lokal)",
                "outfit": "Casual earth-tone outer & cream palazzo",
                "caption": "Awalnya cuma penasaran karena asinan ini sering muncul di FYP, ternyata variannya ada sepuluh dan pedasnya beda-beda. Yang bikin ramai katanya banyak pembeli datang dari luar kota setelah lihat review di TikTok. Kalian tim asinan mangga pedas atau jambu kristal? #palembang #kulinerpalembang #asinanbuah #jajananviral #kulinerviral #dailyvlog",
                "sources": [rri_asinan, lagitren_musteat, kompas_musteat],
                "factors": {
                    "momentum": 6.0,
                    "local_relevance": 9.0,
                    "format_fit": 9.0,
                    "evidence_strength": 7.5,
                    "risk_safety": 7.5,
                },
                "why": "Bukti kuat bahwa review kuliner lokal Palembang di TikTok menggerakkan kunjungan nyata, tetapi artikel pendukungnya terbit Juli 2026 dan tagar #musteatinmycity sudah tidak aktif sejak 6 November 2026.",
            },
            {
                "code": "C",
                "title": "POV Kehujanan Pulang Kerja, Mampir Warung Tekwan di Pinggir Jalan",
                "pillar": "Daily Vlog Palembang",
                "hook": "POV: hujan deras pas pulang kerja, dan satu-satunya penyelamat adalah warung tekwan di pinggir jalan.",
                "shots": [
                    "Shot 1 (8s): Dinda berlari kecil menembus hujan sambil menutupi kepala dengan tas, lalu duduk di warung tekwan pinggir jalan dan menghela napas lega.",
                    "Shot 2 (8s): Dinda menyeruput kuah tekwan hangat, kamera menangkap rintik hujan di terpal warung, lalu ia tersenyum ke kamera.",
                ],
                "sound": "Rainy Day Ambient (format POV hujan)",
                "outfit": "Casual hoodie earth-tone & celana kulot",
                "caption": "Hujan turun pas banget jam pulang kerja, jadi rencana masak dibatalkan dan mendarat di warung tekwan pinggir jalan. Kuahnya hangat, harganya tetap ramah. Kalian kalau kehujanan di jalan paling sering mampir ke mana? #palembang #dailyvlog #tekwan #kulinerpalembang #povhujan #streetfood",
                "sources": [bmkg, lagitren_today],
                "near_duplicate_ids": ["trend_a08e0087a7"],
                "factors": {
                    "momentum": 7.5,
                    "local_relevance": 7.0,
                    "format_fit": 8.0,
                    "evidence_strength": 6.0,
                    "risk_safety": 9.0,
                },
                "why": "Momentum hujan kuat, tetapi format POV pulang kerja sudah dipakai topik lain di bank memori dan tidak punya bukti permintaan kuliner spesifik.",
            },
        ]
    else:
        readable_sources = [c for c in brief["candidates"] if c.get("verification_status") == REQUIRED_SOURCE_STATUS]
        candidates = _candidates_from_trend_memory(character_id, readable_sources or brief["candidates"], primary_outfit)
        if not candidates:
            raise SystemExit(
                f"STOP: belum ada topic_candidates di brief atau bank ide trend_memory untuk karakter '{character_id}'."
            )

    for cand in candidates:
        cand["source_evidence"] = [
            {
                "url": u,
                "title": src(u)["title"],
                "observed_at": src(u).get("observed_at") or src(u).get("published_at"),
                "evidence": src(u)["evidence"],
            }
            for u in cand["sources"]
        ]
    return candidates


def get_topic_by_id(trend_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT topic FROM trend_memory WHERE id=?", (trend_id,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def get_produced_topics(character_id, exclude_day=None):
    """Topik yang benar-benar sudah dipakai produksi (punya versi di daily_slots).

    Kebaruan harus dihitung terhadap konten yang nyata-nyata dibuat, bukan terhadap
    seluruh bank ide. Kalau dihitung terhadap trend_memory, setiap run menuliskan tiga
    topiknya sendiri sehingga skor kebaruan kolaps ke 0 dan ranking harian membeku.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT m.topic || ' ' || COALESCE(m.hook_text, '')
            FROM trend_selections s
            JOIN daily_slots d
              ON d.day = s.day AND d.character_id = s.character_id
            JOIN trend_memory m ON m.id = s.trend_id
            WHERE s.character_id = ?
              AND d.version_id IS NOT NULL
              AND (? IS NULL OR s.day < ?)
            """,
            (character_id, exclude_day, exclude_day),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def get_unproduced_selections(character_id, exclude_day):
    """Topik yang sudah dipilih di hari lain tetapi belum pernah diproduksi.

    Dipakai untuk penalti ringan: ide yang belum jadi konten memang masih layak dipakai,
    tetapi memilih topik yang sama berulang hari tetap harus terlihat di skor.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT m.topic || ' ' || COALESCE(m.hook_text, '')
            FROM trend_selections s
            JOIN trend_memory m ON m.id = s.trend_id
            WHERE s.character_id = ?
              AND s.day < ?
              AND NOT EXISTS (
                  SELECT 1 FROM daily_slots d
                  WHERE d.day = s.day AND d.character_id = s.character_id
                    AND d.version_id IS NOT NULL
              )
            """,
            (character_id, exclude_day),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def score_candidates(candidates, produced_topics, unproduced_topics=None):
    unproduced_topics = unproduced_topics or []
    for cand in candidates:
        novelty, overlaps = novelty_score(cand["title"], cand["hook"], produced_topics)

        # Penalti ringan untuk topik yang sudah dipilih di hari lain tetapi belum
        # pernah diproduksi. Maksimal -2.0 supaya ide yang belum jadi konten tetap bisa
        # menang bila memang paling kuat, tidak dikunci mati seperti bank ide statis.
        repeat = novelty_score(cand["title"], cand["hook"], unproduced_topics)[1]
        repeat_penalty = min(2.0, 1.0 * len(repeat)) if repeat else 0.0
        if repeat_penalty:
            novelty = round(max(0.0, novelty - repeat_penalty), 2)

        # Penalti duplikat yang diklaim eksplisit oleh penulis kandidat. ID harus
        # benar-benar ada di bank memori, jadi klaim tidak bisa dikarang.
        near_dups = []
        for trend_id in cand.get("near_duplicate_ids", []):
            topic = get_topic_by_id(trend_id)
            if not topic:
                raise SystemExit(f"STOP: near_duplicate_ids merujuk id yang tidak ada: {trend_id}")
            near_dups.append({"id": trend_id, "topic": topic})
        if near_dups:
            novelty = round(max(0.0, novelty - 1.5 * len(near_dups)), 2)

        factors = dict(cand["factors"])
        factors["novelty"] = novelty
        total = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
        cand["score_breakdown"] = {k: round(factors[k], 2) for k in WEIGHTS}
        cand["viral_score"] = round(total, 2)
        cand["overlaps"] = overlaps
        cand["near_duplicates"] = near_dups
    return sorted(candidates, key=lambda c: c["viral_score"], reverse=True)


def save_to_db(character_id, ranked, day, decided_at, slot="morning"):
    now_iso = decided_at.isoformat()
    best = ranked[0]
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(trend_memory)").fetchall()}
        with conn:
            trend_ids = {}
            for cand in ranked:
                if cand.get("existing_trend_id"):
                    trend_id = cand["existing_trend_id"]
                    trend_ids[cand["code"]] = trend_id
                    conn.execute(
                        "UPDATE trend_memory SET viral_score = ? WHERE id = ?",
                        (cand["viral_score"], trend_id),
                    )
                    continue
                trend_id = f"opt_{character_id}_{cand['code']}_{int(decided_at.timestamp())}"
                trend_ids[cand["code"]] = trend_id
                conn.execute(
                    """
                    INSERT INTO trend_memory (
                        id, character_id, category, topic, hook_text, script_outline,
                        viral_sound_title, source_evidence, status, viral_score, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?, ?)
                    """,
                    (
                        trend_id,
                        character_id,
                        cand["pillar"],
                        cand["title"],
                        cand["hook"],
                        json.dumps(cand["shots"], ensure_ascii=False),
                        cand["sound"],
                        json.dumps(cand["source_evidence"], ensure_ascii=False),
                        cand["viral_score"],
                        now_iso,
                    ),
                )
            if best.get("existing_trend_id") and {"times_used", "last_used_at"}.issubset(cols):
                conn.execute(
                    "UPDATE trend_memory SET times_used = COALESCE(times_used, 0) + 1, last_used_at = ? WHERE id = ?",
                    (now_iso, best["existing_trend_id"]),
                )
            conn.execute(
                """
                INSERT INTO trend_selections (
                    id, day, character_id, slot, trend_id, title, viral_score, rationale,
                    source_urls, score_breakdown, decided_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pm_autonomous', ?)
                ON CONFLICT(day, character_id, slot) DO UPDATE SET
                    trend_id=excluded.trend_id, title=excluded.title,
                    viral_score=excluded.viral_score, rationale=excluded.rationale,
                    source_urls=excluded.source_urls,
                    score_breakdown=excluded.score_breakdown, created_at=excluded.created_at
                """,
                (
                    f"sel_{character_id}_{day}_{slot}",
                    day,
                    character_id,
                    slot,
                    trend_ids[best["code"]],
                    best["title"],
                    best["viral_score"],
                    best["why"],
                    json.dumps(best["sources"], ensure_ascii=False),
                    json.dumps(best["score_breakdown"], ensure_ascii=False),
                    now_iso,
                ),
            )
    finally:
        conn.close()
    return best, trend_ids


def resolve_brief_path(character_id, day_iso, brief_arg=None):
    if brief_arg:
        return Path(brief_arg)
    slugs = [character_id]
    alt = character_id.replace("_", "-")
    if alt not in slugs:
        slugs.append(alt)
    for slug in slugs:
        candidate = BRIEF_DIR / f"tiktok-trend-{slug}-{day_iso}.json"
        if candidate.exists():
            return candidate
    if BRIEF_DIR.is_dir():
        cutoff = now_wib().timestamp() - 72 * 3600
        recent = []
        for slug in slugs:
            for p in BRIEF_DIR.glob(f"tiktok-trend-{slug}-*.json"):
                if p.stat().st_mtime >= cutoff:
                    recent.append(p)
        if recent:
            recent.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return recent[0]
    return BRIEF_DIR / f"tiktok-trend-{character_id}-{day_iso}.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", default=None, help="path brief riset JSON")
    parser.add_argument("--character", default="dinda")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--day",
        default=None,
        help="tanggal slot tujuan (YYYY-MM-DD). Default hari ini; run malam pakai besok "
             "supaya keputusan hari ini tidak tertimpa.",
    )
    parser.add_argument(
        "--slot",
        default=None,
        choices=["morning", "evening"],
        help="Slot riset (morning atau evening). Otomatis ditentukan dari brief/jam jika tidak diset.",
    )
    args = parser.parse_args()

    decided_at = now_wib()
    brief_path = resolve_brief_path(args.character, decided_at.date().isoformat(), args.brief)

    print("[RISET] Memuat bukti tren yang sudah dibaca:")
    brief, readable = load_brief(brief_path)
    for c in readable:
        print(f"  - {c['title']} ({len(c['evidence'])} char bukti)")

    slot = args.slot or brief.get("slot") or ("evening" if decided_at.hour >= 15 else "morning")

    target_day = args.day or decided_at.date().isoformat()
    try:
        datetime.strptime(target_day, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"STOP: --day tidak valid: {target_day}")
    produced_topics = get_produced_topics(args.character, exclude_day=target_day)
    unproduced_topics = get_unproduced_selections(args.character, target_day)
    candidates = build_candidates(args.character, brief)
    ranked = score_candidates(candidates, produced_topics, unproduced_topics)
    print(
        f"[MEMORI] topik sudah diproduksi: {len(produced_topics)}, "
        f"sudah dipilih tapi belum diproduksi: {len(unproduced_topics)}"
    )

    print("\n[SKOR] Potensi viral:")
    for cand in ranked:
        print(f"  {cand['code']}. {cand['viral_score']:.2f}  {cand['title']}")

    best = ranked[0]
    print(
        f"\n[KEPUTUSAN OTONOM] {best['code']} dipilih dengan skor "
        f"{best['viral_score']:.2f} (runner-up {ranked[1]['viral_score']:.2f})"
    )
    print(f"  Alasan: {best['why']}")
    if best["overlaps"]:
        print(f"  Catatan kemiripan topik lama: {best['overlaps']}")
    for dup in ranked[0].get("near_duplicates", []):
        print(f"  [PENALTI DUPLIKAT] mirip {dup['id']}: {dup['topic']}")

    caption = clean_emojis(best["caption"])
    if has_emojis(caption):
        raise SystemExit("STOP: caption masih memuat emoji, kebijakan caption melarang.")

    # Owner rule: tidak ada pengiriman opsi ke Telegram. Skrip ini offline.
    print("[TELEGRAM] Tidak ada opsi yang dikirim. Owner tidak memilih; keputusan final oleh PM/AI.")

    report_path = REPORTS_DIR / f"content-options-{int(decided_at.timestamp())}.json"
    report = {
        "timestamp": decided_at.isoformat(),
        "character_id": args.character,
        "brief": str(brief_path),
        "target_day": target_day,
        "slot": slot,
        "selection_mode": "autonomous",
        "selected": {
            "code": best["code"],
            "title": best["title"],
            "viral_score": best["viral_score"],
            "rationale": best["why"],
            "sources": best["sources"],
            "score_breakdown": best["score_breakdown"],
        },
        "candidates": [
            {
                "code": c["code"],
                "title": c["title"],
                "viral_score": c["viral_score"],
                "score_breakdown": c["score_breakdown"],
                "overlaps": c["overlaps"],
                "near_duplicates": c.get("near_duplicates", []),
            }
            for c in ranked
        ],
    }

    if args.dry_run:
        print("[DRY RUN] Tidak menulis ke database.")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    best, trend_ids = save_to_db(args.character, ranked, target_day, decided_at, slot=slot)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[DB] trend_memory: {len(ranked)} topik tersimpan, terpilih id={trend_ids[best['code']]}")
    print(f"[DB] trend_selections: 1 keputusan tercatat untuk {target_day} (slot: {slot})")
    print(f"[REPORT] {report_path}")


if __name__ == "__main__":
    main()
