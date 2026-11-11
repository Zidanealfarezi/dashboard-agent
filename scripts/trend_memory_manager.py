#!/usr/bin/env python3
"""
Trend Memory Manager & Continuous Learning Engine
Menyimpan dan mengelola bank data tren serta memori pembelajaran agen secara permanen.
"""

import sqlite3
import datetime
import uuid
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'operations', 'production.sqlite')

def get_connection():
    return sqlite3.connect(DB_PATH)

def save_trend(character_id, category, topic, hook_text, script_outline, viral_sound_title="", viral_sound_url="", source_evidence="", viral_score=8.5):
    """Menyimpan ide tren baru ke dalam bank memori."""
    conn = get_connection()
    c = conn.cursor()
    trend_id = f"trend_{uuid.uuid4().hex[:10]}"
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()
    
    c.execute("""
        INSERT INTO trend_memory (
            id, character_id, category, topic, hook_text, script_outline, 
            viral_sound_title, viral_sound_url, source_evidence, status, 
            viral_score, times_used, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?, 0, ?)
    """, (trend_id, character_id, category, topic, hook_text, script_outline, viral_sound_title, viral_sound_url, source_evidence, viral_score, now))
    
    conn.commit()
    conn.close()
    return trend_id

def log_learning(character_id, content_topic, insight, what_worked, what_to_avoid="", confidence_score=1.0):
    """Mencatat pelajaran (learning) agar agen makin pintar membuat konten berikutnya."""
    conn = get_connection()
    c = conn.cursor()
    learning_id = f"learn_{uuid.uuid4().hex[:10]}"
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()
    
    c.execute("""
        INSERT INTO content_learning_log (
            id, character_id, content_topic, insight, what_worked, what_to_avoid, confidence_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (learning_id, character_id, content_topic, insight, what_worked, what_to_avoid, confidence_score, now))
    
    conn.commit()
    conn.close()
    return learning_id

def get_top_learnings(character_id, limit=5):
    """Mengambil pelajaran teratas untuk karakter tertentu."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT content_topic, insight, what_worked, what_to_avoid 
        FROM content_learning_log 
        WHERE character_id = ? 
        ORDER BY created_at DESC LIMIT ?
    """, (character_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{"topic": r[0], "insight": r[1], "what_worked": r[2], "what_to_avoid": r[3]} for r in rows]

def get_fresh_trends(character_id, limit=3):
    """Mengambil tren segar yang belum pernah digunakan atau memiliki skor tertinggi."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, category, topic, hook_text, script_outline, viral_sound_title, viral_score 
        FROM trend_memory 
        WHERE character_id = ? AND status = 'discovered'
        ORDER BY viral_score DESC, created_at DESC LIMIT ?
    """, (character_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0], "category": r[1], "topic": r[2], "hook": r[3], 
        "script": r[4], "sound": r[5], "score": r[6]
    } for r in rows]

def seed_initial_memory():
    """Menginisialisasi memori awal dengan data tren & pelajaran yang terbukti berhasil."""
    # 1. Catat Pelajaran Nyata
    log_learning(
        character_id="dinda",
        content_topic="Vlog Pagi Tepi Sungai Musi",
        insight="Format 2-Shot 16 Detik (8s + 8s) menghasilkan alur vlog yang matang dan ritme berbicara yang tenang.",
        what_worked="Pencahayaan jam 6 pagi alami, 3 lembar referensi identitas konsisten, lip-sync bahasa Indonesia natural, volume vokal 100% dan musik akustik 15%.",
        what_to_avoid="Jangan posting video latar malam di waktu pagi, hindari emoji pada caption."
    )
    log_learning(
        character_id="dinda",
        content_topic="Pilihan Angle & Latar Palembang",
        insight="Jembatan Ampera dan Sungai Musi adalah landmark paling kuat untuk membangun trust audiens lokal Palembang.",
        what_worked="Medium shot berdiri di pagar pembatas dermaga dengan latar pilar merah Ampera.",
        what_to_avoid="Hindari background generik yang tidak khas kota Palembang."
    )
    log_learning(
        character_id="nara",
        content_topic="Office GRWM & Daily Beauty Medan",
        insight="Kombinasi ring light dan pakaian kantor pastel meningkatkan kredibilitas sebagai pekerja kantoran muda Medan.",
        what_worked="POV 5 menit persiapan sebelum ngantor, tips sunscreen anti keringat iklim tropis.",
        what_to_avoid="Hindari tutorial makeup terlalu rumit yang tidak cocok untuk sehari-hari."
    )
    log_learning(
        character_id="rania",
        content_topic="Wisata Alam & Pantai Lampuuk Aceh",
        insight="Traveler muslimah santun sangat diminati audiens modest lifestyle.",
        what_worked="Eksplorasi hidden gem pantai berpasir putih, outfit gamis/tunik outdoor praktis bernuansa emerald.",
        what_to_avoid="Hindari destinasi wisata yang terlalu komersil atau tidak terverifikasi keindahannya."
    )

    # 2. Bank Data Tren Segar Dinda (Palembang)
    save_trend(
        character_id="dinda",
        category="kuliner",
        topic="Berburu Sarapan Celimpungan & Laksan Pasar 26 Ilir",
        hook_text="Kalo ke Palembang, jangan cuma cari pempek! Kuah celimpungan kuning santan di sini juaranya.",
        script_outline="Shot 1: Dinda menyapa dari warung sarapan 26 Ilir sambil menunjukkan kuah kuning mengepul. Shot 2: Dinda menyeruput kuah santan gurih dan memberikan rating jujur.",
        viral_sound_title="Palembang Morning Chill Acoustic",
        source_evidence="TikTok Creator Search: #kulinerpalembang #celimpungan trend +45% minggu ini",
        viral_score=9.2
    )
    save_trend(
        character_id="dinda",
        category="spot_nongkrong",
        topic="Sunset Ngopi di Dermaga Point Benteng Kuto Besak",
        hook_text="Spot terbaik nikmati angin sore Palembang sambil lihat kapal ketek lewat di Musi.",
        script_outline="Shot 1: Dinda duduk santai memegang es kopi susu dengan angin mengibaskan ujung jilbab. Shot 2: Kamera menyorot senja keemasan memantul di air Sungai Musi.",
        viral_sound_title="Sore Santai Lofi Vibes",
        source_evidence="Instagram Reels & TikTok FYP Palembang sore hari",
        viral_score=8.8
    )
    save_trend(
        character_id="dinda",
        category="lifestyle_belanja",
        topic="Belanja Camilan Kemplang Panggang Asli Palembang",
        hook_text="Sensasi wangi kemplang dipanggang di atas bara arang, cocolan sambal terasinya nagih!",
        script_outline="Shot 1: Dinda memilih kemplang bantat gurih langsung dari tempat pemanggangan. Shot 2: Reaksi menikmati kerenyahan kemplang hangat.",
        viral_sound_title="Happy Cooking & Snack Time",
        source_evidence="Review jajanan oleh-oleh viral Palembang",
        viral_score=8.5
    )

    # 3. Bank Data Tren Segar Nara (Medan)
    save_trend(
        character_id="nara",
        category="beauty",
        topic="5 Menit Touch-up Anti Longsor Panas Terik Medan",
        hook_text="Panasnya Kota Medan ga bakal bikin makeup geser kalau kalian pakai trik setting spray ini.",
        script_outline="Shot 1: Nara di depan cermin ring light menunjukkan cara tap-tap cushion. Shot 2: Hasil flawless matte siap beraktivitas di kantor.",
        viral_sound_title="Clean Girl Aesthetic Upbeat",
        source_evidence="Tren TikTok Beauty Indonesia: #beautytips #medanlifestyle",
        viral_score=9.0
    )

    # 4. Bank Data Tren Segar Rania (Aceh)
    save_trend(
        character_id="rania",
        category="wisata_alam",
        topic="Hidden Gem Tebing Karang Pantai Ujong Batee",
        hook_text="Siapa sangka tebing seindah ini cuma 25 menit dari pusat Kota Banda Aceh?",
        script_outline="Shot 1: Rania berjalan di tepi pantai berangin sejuk dengan latar tebing karang. Shot 2: Menatap laut biru lepas samudra Hindia yang tenang.",
        viral_sound_title="Peaceful Cinematic Travel Ambient",
        source_evidence="TikTok Travel Aceh: #wisataaceh #ujongbatee",
        viral_score=9.1
    )

    print("Initial trend memory & continuous learning logs successfully seeded!")

if __name__ == '__main__':
    seed_initial_memory()
