#!/usr/bin/env python3
"""
Wardrobe Manager & Auto-Stylist Engine
Menyimpan dan mengelola lemari pakaian virtual karakter di SQLite,
serta memilih baju secara otomatis dan cerdas sesuai konsep video/foto.
"""

import sqlite3
import datetime
import uuid
import json
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "operations" / "production.sqlite"

def get_connection():
    return sqlite3.connect(DB_PATH)

def add_outfit(character_id, name, category, color_palette, vibe_tags, 
               hijab_type, top_desc, bottom_desc, footwear_accessories, 
               closeup_photo_path, fullbody_photo_path):
    """Menambahkan outfit baru ke database lemari pakaian virtual."""
    conn = get_connection()
    c = conn.cursor()
    outfit_id = f"outfit_{character_id}_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()

    # Pastikan folder wardrobe karakter ada
    wardrobe_dir = BASE_DIR / "characters" / character_id / "wardrobe" / outfit_id
    wardrobe_dir.mkdir(parents=True, exist_ok=True)

    # Salin file master foto ke direktori lemari karakter jika belum di sana
    stored_closeup = wardrobe_dir / "master_closeup.png"
    stored_fullbody = wardrobe_dir / "master_fullbody.png"

    if os.path.exists(closeup_photo_path) and str(closeup_photo_path) != str(stored_closeup):
        shutil.copy2(closeup_photo_path, stored_closeup)
    if os.path.exists(fullbody_photo_path) and str(fullbody_photo_path) != str(stored_fullbody):
        shutil.copy2(fullbody_photo_path, stored_fullbody)

    tags_json = json.dumps(vibe_tags if isinstance(vibe_tags, list) else [vibe_tags])

    c.execute("""
        INSERT INTO character_wardrobe (
            id, character_id, name, category, color_palette, vibe_tags,
            hijab_type, top_description, bottom_description, footwear_accessories,
            closeup_photo_path, fullbody_photo_path, times_used, last_used_at, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, 'active', ?)
    """, (
        outfit_id, character_id, name, category, color_palette, tags_json,
        hijab_type, top_desc, bottom_desc, footwear_accessories,
        str(stored_closeup), str(stored_fullbody), now
    ))

    conn.commit()
    conn.close()
    return outfit_id

def select_best_outfit(character_id, concept_title, context_tags=None):
    """
    Sistem Auto-Stylist Otonom:
    Memilih baju yang paling cocok dengan konsep video/foto secara otomatis.
    Mempertimbangkan relevansi konsep dan rotasi baju (least recently used) agar tidak monoton.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, category, color_palette, vibe_tags, hijab_type,
               top_description, bottom_description, closeup_photo_path, 
               fullbody_photo_path, times_used, last_used_at
        FROM character_wardrobe
        WHERE character_id = ? AND status = 'active'
    """, (character_id,))
    outfits = c.fetchall()

    if not outfits:
        conn.close()
        return None

    search_text = (concept_title + " " + " ".join(context_tags or [])).lower()

    scored_outfits = []
    for o in outfits:
        oid, oname, ocat, opalette, otags_json, ohijab, otop, obottom, oclose, ofull, otimes, olast = o
        
        # Validasi fisik keberadaan file referensi 9:16 di disk
        if not (oclose and ofull and os.path.isfile(oclose) and os.path.isfile(ofull)):
            c.execute("UPDATE character_wardrobe SET status = 'incomplete' WHERE id = ?", (oid,))
            conn.commit()
            continue

        score = 0

        # Cocokkan tag / kategori
        otags = json.loads(otags_json) if otags_json else []
        for tag in otags:
            if tag.lower() in search_text:
                score += 5

        if ocat.lower() in search_text:
            score += 10

        # Cocokkan konteks umum
        if any(w in search_text for w in ["ngopi", "cafe", "coffee", "senja", "sore"]):
            if ocat in ["casual_cafe", "daily_hangout"]:
                score += 8
        elif any(w in search_text for w in ["sarapan", "pasar", "kuliner", "makan"]):
            if ocat in ["street_market", "casual_walk", "kuliner"]:
                score += 8
        elif any(w in search_text for w in ["kerja", "kantor", "office", "meeting"]):
            if ocat in ["smart_casual", "formal_office"]:
                score += 8

        # Prioritas rotasi & formula anti-monoton (Arsitektur §3.1)
        # Score(O_i) = W_tag * M_tag + W_cat * M_cat - lambda * U(O_i) - R(O_i)
        usage_penalty = otimes * 2.0
        
        # Recency Penalty R(O_i) = infinity (1,000,000) jika dipakai dalam 24 jam terakhir
        recency_penalty = 0.0
        if olast:
            try:
                last_dt = datetime.datetime.fromisoformat(olast)
                now_dt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
                delta_hours = (now_dt - last_dt).total_seconds() / 3600.0
                if delta_hours < 24.0:
                    recency_penalty = 1000000.0
            except Exception:
                pass

        final_score = score - usage_penalty - recency_penalty

        scored_outfits.append({
            "id": oid,
            "name": oname,
            "category": ocat,
            "color": opalette,
            "closeup_photo": oclose,
            "fullbody_photo": ofull,
            "times_used": otimes,
            "score": final_score
        })

    # Urutkan dari skor tertinggi
    scored_outfits.sort(key=lambda x: x["score"], reverse=True)
    chosen = scored_outfits[0]

    # Update pemakaian di database
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()
    c.execute("""
        UPDATE character_wardrobe
        SET times_used = times_used + 1, last_used_at = ?
        WHERE id = ?
    """, (now, chosen["id"]))

    conn.commit()
    conn.close()

    return chosen

def list_wardrobe(character_id):
    """Menampilkan seluruh isi lemari baju karakter."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, category, color_palette, times_used, last_used_at, created_at
        FROM character_wardrobe
        WHERE character_id = ? AND status = 'active'
        ORDER BY created_at DESC
    """, (character_id,))
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0], "name": r[1], "category": r[2], "color": r[3],
        "times_used": r[4], "last_used_at": r[5], "created_at": r[6]
    } for r in rows]

def seed_default_wardrobe():
    """Mengisi lemari pakaian awal Dinda dengan outfit signature & OOTD kasual."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM character_wardrobe WHERE character_id = 'dinda'")
    count = c.fetchone()[0]
    conn.close()

    if count > 0:
        return

    # 1. Signature Red Iconic Outfit
    add_outfit(
        character_id="dinda",
        name="Signature Red Blouse & Modern Pashmina",
        category="casual_walk",
        color_palette="merah elegan, hitam, denim biru",
        vibe_tags=["iconic", "sungaimusi", "ampera", "daily", "merah"],
        hijab_type="pashmina hitam modern",
        top_desc="Baju lengan panjang warna merah elegan dengan kalung cincin kecil",
        bottom_desc="Celana jeans biru kasual",
        footwear_accessories="Sneakers putih bersih, cincin liontin kecil",
        closeup_photo_path=str(BASE_DIR / "characters/dinda/identity/master_closeup_red.png"),
        fullbody_photo_path=str(BASE_DIR / "FOTO_KARAKTER/Dinda/dinda.jpg")
    )

    # 2. Casual Cafe Sage Green
    add_outfit(
        character_id="dinda",
        name="Sage Green Crinkle Blouse & Cream Culottes",
        category="casual_cafe",
        color_palette="sage green, cream gading, beige",
        vibe_tags=["cafe", "ngopi", "sore", "santai", "aesthetic", "lofi"],
        hijab_type="pashmina krem muda rapi",
        top_desc="Blouse linen crinkle airflow warna sage green dengan kancing kayu minimalis",
        bottom_desc="Celana kulot bahan katun warna krem gading longgar sopan",
        footwear_accessories="Mules shoes krem, tote bag kanvas natural",
        closeup_photo_path=str(BASE_DIR / "characters/dinda/identity/master_closeup_sage.png"),
        fullbody_photo_path=str(BASE_DIR / "characters/dinda/identity/master_fullbody_sage.png")
    )

    # 3. Market & Morning Street Mocha Earth-Tone
    add_outfit(
        character_id="dinda",
        name="Mocha Earth-Tone Oversized Shirt & Ivory Trousers",
        category="street_market",
        color_palette="mocha cokelat hangat, ivory putih gading",
        vibe_tags=["sarapan", "pasar", "kuliner", "pagi", "belanja", "mie celor"],
        hijab_type="segi empat voal mocha hangat",
        top_desc="Kemeja oversized katun warna mocha hangat dipadukan manset putih",
        bottom_desc="Celana panjang lurus bahan twill warna ivory",
        footwear_accessories="Slip-on sandal kulit cokelat muda, sling bag rajut",
        closeup_photo_path=str(BASE_DIR / "characters/dinda/identity/master_closeup_mocha.png"),
        fullbody_photo_path=str(BASE_DIR / "characters/dinda/identity/master_fullbody_mocha.png")
    )
    print("Seeded default wardrobe for Dinda successfully.")

if __name__ == '__main__':
    seed_default_wardrobe()
    print("Dinda's Wardrobe:")
    for w in list_wardrobe("dinda"):
        print(f"- [{w['category']}] {w['name']} (Color: {w['color']}, Used: {w['times_used']}x)")
