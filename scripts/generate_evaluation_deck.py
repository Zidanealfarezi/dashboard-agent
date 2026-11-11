#!/usr/bin/env python3
"""
generate_evaluation_deck.py
Generates an executive presentation deck evaluating the two AI accounts:
1. @dinda.kemala_ (Dinda Kemala - B2C Lifestyle & Kuliner Palembang)
2. @intansuarkartika (PT Intan Suar Kartika - B2B/B2C Construction Manufacturer)
and analyzing all operational challenges encountered and their mitigation strategies.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
OUTPUT_PPTX = os.path.join(DOCS_DIR, "Laporan_Evaluasi_Akun_dan_Masalah_Operasional.pptx")

DINDA_IMG = os.path.join(BASE_DIR, "FOTO_KARAKTER", "Dinda", "dinda.jpg")
ISK_IMG = os.path.join(BASE_DIR, "characters", "isk", "assets", "brand", "paku_cap_keris_box_reference.jpg")

# Color Palette
BG_DARK = RGBColor(15, 23, 42)        # Midnight Slate #0F172A
BG_LIGHT = RGBColor(248, 250, 252)    # Slate 50 #F8FAFC
CARD_BG = RGBColor(255, 255, 255)     # Pure White
CARD_BORDER = RGBColor(226, 232, 240) # Slate 200 #E2E8F0
TEXT_MAIN = RGBColor(15, 23, 42)      # Slate 900
TEXT_MUTED = RGBColor(100, 116, 139)  # Slate 500
TEXT_WHITE = RGBColor(255, 255, 255)
TEXT_WHITE_MUTED = RGBColor(203, 213, 225) # Slate 300

# Accents
PRIMARY_BLUE = RGBColor(37, 99, 235)  # #2563EB
ACCENT_DINDA = RGBColor(225, 29, 72)  # Rose 600 #E11D48
ACCENT_DINDA_BG = RGBColor(255, 241, 242)
ACCENT_ISK = RGBColor(217, 119, 6)    # Amber 600 #D97706
ACCENT_ISK_BG = RGBColor(254, 243, 199)
ACCENT_ALERT = RGBColor(220, 38, 38)  # Red 600 #DC2626
ACCENT_ALERT_BG = RGBColor(254, 242, 242)
ACCENT_SUCCESS = RGBColor(16, 185, 129) # Emerald 500 #10B981
ACCENT_SUCCESS_BG = RGBColor(236, 253, 245)
ACCENT_PURPLE = RGBColor(124, 58, 237) # Purple 600
ACCENT_PURPLE_BG = RGBColor(245, 243, 255)

FONT_HEADING = "Helvetica"
FONT_BODY = "Arial"


def add_solid_bg(slide, prs, color):
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = color
    bg_shape.line.fill.background()
    return bg_shape


def add_header(slide, category_tag, title_text, subtitle_text=None, tag_color=PRIMARY_BLUE, tag_bg=None, dark_theme=False):
    left = Inches(0.8)
    top = Inches(0.5)

    # Category Pill
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(2.2), Inches(0.32)
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = tag_bg if tag_bg else (RGBColor(30, 41, 59) if dark_theme else RGBColor(239, 246, 255))
    pill.line.color.rgb = tag_color
    pill.line.width = Pt(1)

    tf_p = pill.text_frame
    tf_p.word_wrap = True
    tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf_p.paragraphs[0]
    p.text = category_tag.upper()
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_HEADING
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = tag_color

    # Title & Subtitle Box
    tb = slide.shapes.add_textbox(left, top + Inches(0.38), Inches(11.733), Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_title = tf.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE if dark_theme else TEXT_MAIN

    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_WHITE_MUTED if dark_theme else TEXT_MUTED


def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER, border_width=1):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(border_width)
    return card


def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: COVER SLIDE (DARK THEME)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s1, prs, BG_DARK)

    # Accent Top Stripe
    stripe = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = PRIMARY_BLUE
    stripe.line.fill.background()

    # Category Pill
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.4), Inches(3.2), Inches(0.38))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(30, 41, 59)
    pill.line.color.rgb = PRIMARY_BLUE
    p = pill.text_frame.paragraphs[0]
    p.text = "EXECUTIVE PORTFOLIO & AUDIT"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_HEADING
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(147, 197, 253)

    # Main Title
    tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(2.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p1 = tf.paragraphs[0]
    p1.text = "Evaluasi Portfolio Akun AI &\nPemetaan Masalah Operasional"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE

    p2 = tf.add_paragraph()
    p2.text = "Analisis Kinerja @dinda.kemala_ & @intansuarkartika, Arsitektur Autonomous Pipeline, serta Mitigasi Kendala Lapangan"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_WHITE_MUTED
    p2.space_before = Pt(12)

    # 2 Account Cards on Cover
    c1 = add_card(s1, Inches(1.0), Inches(4.5), Inches(5.4), Inches(2.1), bg_color=RGBColor(30, 41, 59), border_color=ACCENT_DINDA, border_width=1.5)
    tb_c1 = s1.shapes.add_textbox(Inches(1.2), Inches(4.65), Inches(5.0), Inches(1.8))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    p = tf_c1.paragraphs[0]
    p.text = "AKUN 1: DINDA KEMALA (@dinda.kemala_)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(253, 164, 175)

    bullets_c1 = [
        "Fokus: B2C Lifestyle, Kuliner & Budaya Palembang",
        "Format: 9:16 Vertical AI Video, Talking-Head Modest Hijab",
        "Jadwal: 2x Sehari (07:00 Pagi & 19:00 Malam WIB)",
        "Engine: Google Flow Omni 1.2 Flash + CDP TikTok Automation"
    ]
    for b in bullets_c1:
        p = tf_c1.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_WHITE_MUTED
        p.space_before = Pt(3)

    c2 = add_card(s1, Inches(6.8), Inches(4.5), Inches(5.5), Inches(2.1), bg_color=RGBColor(30, 41, 59), border_color=ACCENT_ISK, border_width=1.5)
    tb_c2 = s1.shapes.add_textbox(Inches(7.0), Inches(4.65), Inches(5.1), Inches(1.8))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p = tf_c2.paragraphs[0]
    p.text = "AKUN 2: PT INTAN SUAR KARTIKA (@intansuarkartika)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(252, 211, 77)

    bullets_c2 = [
        "Fokus: B2B/B2C Manufaktur Bahan Bangunan & Paku Cap Keris",
        "Format: Field Test, Uji Ekstrem Ketahanan Material + Hardsub ASS",
        "Jadwal: Produksi 06:00/09:00 WIB, Posting 08:00/12:00 WIB",
        "Brand Identity: 100% Tanpa Emoji, Konversi Langsung ke WhatsApp Sales"
    ]
    for b in bullets_c2:
        p = tf_c2.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_WHITE_MUTED
        p.space_before = Pt(3)

    # Footer
    tb_f = s1.shapes.add_textbox(Inches(1.0), Inches(6.85), Inches(11.3), Inches(0.4))
    tf_f = tb_f.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "Autonomous AI Influencer System | Kantor AI Intan (kantor-ai-intan.vercel.app) | Tanggal: 10 November 2026"
    p_f.font.name = FONT_BODY
    p_f.font.size = Pt(9)
    p_f.font.color.rgb = RGBColor(148, 163, 184)

    # =========================================================================
    # SLIDE 2: PROFIL AKUN 1 - DINDA KEMALA
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s2, prs, BG_LIGHT)
    add_header(s2, "Karakter & Profil Kreatif", "Akun 1: Dinda Kemala (@dinda.kemala_)", 
               "Persona Kreator Digital Lokal Palembang — Lifestyle, Budaya & Wisata Gastronomi",
               tag_color=ACCENT_DINDA, tag_bg=ACCENT_DINDA_BG)

    # Left Column: Image & Quick Stats
    add_card(s2, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.3))
    if os.path.exists(DINDA_IMG):
        s2.shapes.add_picture(DINDA_IMG, Inches(1.0), Inches(1.8), width=Inches(3.2))

    tb_d_meta = s2.shapes.add_textbox(Inches(1.0), Inches(4.3), Inches(3.2), Inches(2.4))
    tf_d_meta = tb_d_meta.text_frame
    tf_d_meta.word_wrap = True
    tf_d_meta.margin_left = tf_d_meta.margin_right = 0
    
    meta_dinda = [
        ("Platform", "TikTok Official (@dinda.kemala_)"),
        ("Domisili", "Palembang, Sumatera Selatan"),
        ("Format Visual", "9:16 Vertical Video (1080x1920)"),
        ("AI Persona", "Modest Hijab, Mahasiswi Ramah"),
        ("Jadwal Publikasi", "2x Sehari (07:00 Pagi & 19:00 WIB)"),
        ("Status Approval", "Telegram Review (chat_id: 7463982122)")
    ]
    for lbl, val in meta_dinda:
        p = tf_d_meta.add_paragraph() if tf_d_meta.paragraphs[0].text else tf_d_meta.paragraphs[0]
        p.text = f"{lbl}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        run = p.add_run()
        run.text = val
        run.font.name = FONT_BODY
        run.font.size = Pt(9.5)
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(4)

    # Right Column: Pillar, Voice, & Content Strategy Cards
    # Card 1: Content Pillars
    add_card(s2, Inches(4.6), Inches(1.6), Inches(7.9), Inches(1.65))
    tb_cp = s2.shapes.add_textbox(Inches(4.8), Inches(1.75), Inches(7.5), Inches(1.4))
    tf_cp = tb_cp.text_frame
    tf_cp.word_wrap = True
    p = tf_cp.paragraphs[0]
    p.text = "PILAR KONTEN & POSITIONING STRATEGIS"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA

    pillars = [
        "Wisata Kuliner Palembang: Eksplorasi pempek bingen, martabak HAR, tekwan, kue gandus, dan gulo palu.",
        "Destinasi & Kebudayaan: Cerita Sungai Musi, Benteng Kuto Besak, Museum SMB II, tradisi perahu bidar.",
        "Daily Vlog Mahasiswi: OOTD hijab casual, persiapan ke kampus, interaksi hangat dengan masyarakat lokal.",
        "Pemberdayaan UMKM: Mengangkat pedagang kaki lima dan warung tradisional khas Palembang ke audiens muda."
    ]
    for pil in pillars:
        p = tf_cp.add_paragraph()
        p.text = "• " + pil
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(2)

    # Card 2: Tone of Voice & Engagement Policy
    add_card(s2, Inches(4.6), Inches(3.4), Inches(7.9), Inches(1.65))
    tb_tv = s2.shapes.add_textbox(Inches(4.8), Inches(3.55), Inches(7.5), Inches(1.4))
    tf_tv = tb_tv.text_frame
    tf_tv.word_wrap = True
    p = tf_tv.paragraphs[0]
    p.text = "BRAND VOICE & REGULASI ENGAGEMENT"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA

    voice_points = [
        "Bahasa & Tutur Kata: Bahasa Indonesia santun dengan selipan kosakata Palembang halus ('dulur-dulur', 'mangcek', 'bikcek').",
        "Keterbukaan AI: Transparan dan jujur jika ditanya bahwa Dinda adalah persona AI karya kreator Palembang.",
        "Batasan Keamanan (Guardrails): Dilarang membuat relasi pribadi fiktif, janji temu fisik, atau membagikan nomor pribadi.",
        "Moderasi Komentar: Balas sapaan follower secara organik dan teruskan tawaran komersial/endorse ke pemilik akun."
    ]
    for vp in voice_points:
        p = tf_tv.add_paragraph()
        p.text = "• " + vp
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(2)

    # Card 3: Automation Mechanics
    add_card(s2, Inches(4.6), Inches(5.2), Inches(7.9), Inches(1.7))
    tb_am = s2.shapes.add_textbox(Inches(4.8), Inches(5.35), Inches(7.5), Inches(1.4))
    tf_am = tb_am.text_frame
    tf_am.word_wrap = True
    p = tf_am.paragraphs[0]
    p.text = "MEKANISME PRODUKSI OTONOM"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA

    auto_points = [
        "Auto-Stylist Wardrobe: Kurasi OOTD harian dari database busana hijab untuk menjaga konsistensi visual.",
        "Google Flow Generatif: Pembuatan video talking-head 10 detik rasio 9:16 resolusi tinggi tanpa watermark.",
        "Persetujuan Owner 2 Jam: Notifikasi preview video dan naskah ke Telegram sebelum jadwal publikasi.",
        "Otomasi Unggah CDP: Pengunggahan langsung ke TikTok Studio via headless Chrome dengan caption naratif tervalidasi."
    ]
    for ap in auto_points:
        p = tf_am.add_paragraph()
        p.text = "• " + ap
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 3: PROFIL AKUN 2 - PT INTAN SUAR KARTIKA
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s3, prs, BG_LIGHT)
    add_header(s3, "Manufaktur & Bisnis B2B", "Akun 2: PT Intan Suar Kartika (@intansuarkartika)", 
               "Strategi Konten Edukasi Industri Konstruksi, Uji Material & Konversi Distributor Toko Bangunan",
               tag_color=ACCENT_ISK, tag_bg=ACCENT_ISK_BG)

    # Left Column: Image & Quick Stats
    add_card(s3, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.3))
    if os.path.exists(ISK_IMG):
        s3.shapes.add_picture(ISK_IMG, Inches(1.0), Inches(1.8), width=Inches(3.2))

    tb_i_meta = s3.shapes.add_textbox(Inches(1.0), Inches(4.1), Inches(3.2), Inches(2.6))
    tf_i_meta = tb_i_meta.text_frame
    tf_i_meta.word_wrap = True
    tf_i_meta.margin_left = tf_i_meta.margin_right = 0
    
    meta_isk = [
        ("Platform", "TikTok (@intansuarkartika)"),
        ("Basis Pabrik", "Medan, Sumatera Utara"),
        ("Produk Utama", "Paku Cap Keris, Kawat Duri Diamond"),
        ("Format Konten", "Uji Lapangan, Hook 0-3s, Hardsub ASS"),
        ("Jadwal Publikasi", "Produksi 09:00 WIB, Posting 12:00 WIB"),
        ("Konversi Utama", "wa.me/62819889350 (Distributor Sales)")
    ]
    for lbl, val in meta_isk:
        p = tf_i_meta.add_paragraph() if tf_i_meta.paragraphs[0].text else tf_i_meta.paragraphs[0]
        p.text = f"{lbl}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        run = p.add_run()
        run.text = val
        run.font.name = FONT_BODY
        run.font.size = Pt(9.5)
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(4)

    # Right Column: Pillar, Strict Rules & Production Formula
    # Card 1: Product Pillars & Search Intent
    add_card(s3, Inches(4.6), Inches(1.6), Inches(7.9), Inches(1.65))
    tb_ip = s3.shapes.add_textbox(Inches(4.8), Inches(1.75), Inches(7.5), Inches(1.4))
    tf_ip = tb_ip.text_frame
    tf_ip.word_wrap = True
    p = tf_ip.paragraphs[0]
    p.text = "EKSPLOITASI 89.5% SEARCH INTENT & PILAR PRODUK"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK

    isk_pillars = [
        "Paku Cap Keris: Standar SNI 0194-78, ekspor quality, jaminan paku lurus tidak gampang patah/bengkok, timbangan pas 25 kg.",
        "Kawat Duri Diamond: Spesialis pagar kebun sawit, cabai, dan keamanan batas lahan proyek (performa views organik tertinggi).",
        "Kawat Licin & Bendrat: Uji fleksibilitas dan kekuatan ikat tulangan beton tanpa putus di lokasi proyek konstruksi.",
        "Kereta Sorong Five Star: Uji beban ekstrem 200+ kg pada jalur tanah berbatu untuk membuktikan ketangguhan sasis dan roda."
    ]
    for ip in isk_pillars:
        p = tf_ip.add_paragraph()
        p.text = "• " + ip
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(2)

    # Card 2: Packaging Anchor & Production Formula
    add_card(s3, Inches(4.6), Inches(3.4), Inches(7.9), Inches(1.65))
    tb_pf = s3.shapes.add_textbox(Inches(4.8), Inches(3.55), Inches(7.5), Inches(1.4))
    tf_pf = tb_pf.text_frame
    tf_pf.word_wrap = True
    p = tf_pf.paragraphs[0]
    p.text = "FORMULA PRODUKSI & INTEGRITAS BRAND (PACKAGING ANCHOR)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK

    formula_points = [
        "Packaging Anchor Tegas: Kardus cokelat kraft horisontal bertuliskan hijau 'PAKU EXPORT QUALITY / CAP KERIS'.",
        "Kondisi Paku: Paku curah lepas di dalam kardus TANPA bungkus plastik (karakteristik asli distribusi pabrik).",
        "Post-Production Spesifik: Ekstraksi audio WAV 16kHz, Faster-Whisper alignment, kinetic yellow sub (#FFE600).",
        "Outro Bumper Resmi: Penambahan video penutup resmi PT Intan Suar Kartika sepanjang 4.07 detik (total 14.07s / 24.07s)."
    ]
    for fp in formula_points:
        p = tf_pf.add_paragraph()
        p.text = "• " + fp
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(2)

    # Card 3: Strict Policy & Conversion
    add_card(s3, Inches(4.6), Inches(5.2), Inches(7.9), Inches(1.7))
    tb_pol = s3.shapes.add_textbox(Inches(4.8), Inches(5.35), Inches(7.5), Inches(1.4))
    tf_pol = tb_pol.text_frame
    tf_pol.word_wrap = True
    p = tf_pol.paragraphs[0]
    p.text = "STRICT 0% EMOJI POLICY & FUNNEL PENJUALAN"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK

    pol_points = [
        "Kebijakan Bahasa 0% Emoji: Seluruh naskah, caption, dan balasan chat bebas emoji demi wibawa industri manufaktur berat.",
        "Tone Bahasa Lapangan: Lugas, ringkas, solutif, menghormati kalkulasi biaya mandor, tukang proyek, dan pemilik toko bangunan.",
        "3 Hashtag Terarah: Maksimal 3 tag relevan tanpa spam (#pakucapkeris #intansuarkartika #tokobangunan).",
        "Direct CTA WhatsApp: Arahkan setiap pertanyaan grosir, harga distributor, dan katalog produk langsung ke sales resmi."
    ]
    for pp in pol_points:
        p = tf_pol.add_paragraph()
        p.text = "• " + pp
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 4: MATRIKS KOMPARASI KEDUA AKUN
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s4, prs, BG_LIGHT)
    add_header(s4, "Analisis Komparatif", "Matriks Perbandingan Strategis Antar Akun", 
               "Perbedaan Parameter, Persona, Arsitektur Konten, dan Funnel Konversi",
               tag_color=PRIMARY_BLUE)

    # Table Container Card
    add_card(s4, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.3))

    # Add Table
    rows, cols = 8, 3
    left, top, width, height = Inches(1.0), Inches(1.8), Inches(11.333), Inches(4.8)
    table_shape = s4.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(4.4)
    table.columns[2].width = Inches(4.4)

    headers = ["Parameter Komparasi", "Dinda Kemala (@dinda.kemala_)", "PT Intan Suar Kartika (@intansuarkartika)"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = BG_DARK
        p = cell.text_frame.paragraphs[0]
        p.font.name = FONT_HEADING
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.alignment = PP_ALIGN.CENTER

    matrix_data = [
        ("Segmen Audiens", "B2C Audiens Muda, Warga Palembang & Pecinta Budaya", "B2B / B2C Kontraktor, Mandor Proyek, Pemilik Toko Bangunan"),
        ("Persona Karakter", "Mahasiswi berhijab santun, ramah, hangat, bertutur lokal", "Representatif teknis pabrik manufaktur, lugas, profesional"),
        ("Gaya Visual AI", "Talking-head lifestyle 9:16, natural look, busana hijab OOTD", "Field test, banting material, kardus paku kraft tanpa plastik"),
        ("Audio & Teks", "Native flow voice, storytelling lokal halus, ambient sound", "Faster-Whisper alignment, Kinetic Yellow ASS hardsub (M=850)"),
        ("Kebijakan Bahasa", "Bahasa Indonesia luwes dengan selipan kosakata Palembang", "Strict 0% Emoji Policy, narasi langsung tanpa basa-basi"),
        ("Branding & Outro", "Logo overlay halus / signature Dinda Kemala", "Official bumper outro PT Intan Suar Kartika utuh 4.07 detik"),
        ("Tujuan Akhir (Goal)", "Brand building, engagement komunitas, kolaborasi UMKM lokal", "Penetrasi pasar grosir, edukasi ketahanan, leads WA Distributor")
    ]

    for row_idx, data in enumerate(matrix_data, start=1):
        bg_row = RGBColor(241, 245, 249) if row_idx % 2 == 1 else RGBColor(255, 255, 255)
        for col_idx in range(3):
            cell = table.cell(row_idx, col_idx)
            cell.text = data[col_idx]
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_row
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_HEADING if col_idx == 0 else FONT_BODY
            p.font.size = Pt(9.5)
            p.font.bold = (col_idx == 0)
            if col_idx == 0:
                p.font.color.rgb = TEXT_MAIN
            elif col_idx == 1:
                p.font.color.rgb = RGBColor(190, 24, 93) if row_idx == 1 else TEXT_MAIN
            else:
                p.font.color.rgb = RGBColor(180, 83, 9) if row_idx == 1 else TEXT_MAIN

    # =========================================================================
    # SLIDE 5: ARSITEKTUR AUTONOMOUS PIPELINE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s5, prs, BG_LIGHT)
    add_header(s5, "Teknologi & Otomasi", "Arsitektur End-to-End Autonomous Pipeline", 
               "Integrasi 6 Tahap Otonom: Riset Tren, Generasi AI, Post-Production, hingga Publikasi CDP",
               tag_color=PRIMARY_BLUE)

    pipeline_stages = [
        ("1. Riset & Tren", "Menganalisis kueri 89.5% search intent TikTok Studio & tren lokal harian.", ACCENT_PURPLE, ACCENT_PURPLE_BG),
        ("2. Brief & Naskah", "Penyusunan hook 0-3 detik, seleksi OOTD/kemasan fisik, penegakan 0% emoji.", PRIMARY_BLUE, RGBColor(239, 246, 255)),
        ("3. Generasi AI", "Google Flow Omni 1.2 Flash merender video resolusi 9:16 durasi 10 detik.", ACCENT_DINDA, ACCENT_DINDA_BG),
        ("4. Post-Production", "Whisper alignment, rendering hardsub kuning ASS (MarginV=850), & outro bumper.", ACCENT_ISK, ACCENT_ISK_BG),
        ("5. Telegram Gatekeeper", "Kirim kartu preview & berkas ke Telegram Owner dengan jendela approval 2 jam.", RGBColor(13, 148, 136), RGBColor(240, 253, 250)),
        ("6. CDP Publisher", "Headless Chrome via DevTools Protocol mengunggah draf & bypass modal TikTok.", ACCENT_SUCCESS, ACCENT_SUCCESS_BG)
    ]

    card_w = Inches(1.8)
    card_gap = Inches(0.18)
    start_left = Inches(0.8)

    for idx, (title, desc, color, bg) in enumerate(pipeline_stages):
        x = start_left + idx * (card_w + card_gap)
        card = add_card(s5, x, Inches(1.6), card_w, Inches(3.8), bg_color=bg, border_color=color, border_width=1.5)
        
        tb = s5.shapes.add_textbox(x + Inches(0.1), Inches(1.75), card_w - Inches(0.2), Inches(3.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = FONT_BODY
        p_desc.font.size = Pt(9.5)
        p_desc.font.color.rgb = TEXT_MAIN
        p_desc.space_before = Pt(8)

    # Bottom Architecture Summary Card
    add_card(s5, Inches(0.8), Inches(5.6), Inches(11.733), Inches(1.3), bg_color=CARD_BG, border_color=CARD_BORDER)
    tb_sum = s5.shapes.add_textbox(Inches(1.0), Inches(5.7), Inches(11.333), Inches(1.1))
    tf_sum = tb_sum.text_frame
    tf_sum.word_wrap = True
    
    p = tf_sum.paragraphs[0]
    p.text = "KEUNGGULAN DESAIN SISTEM (SEPARATION OF CONCERNS):"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    points_sum = [
        "Desentralisasi Sub-Agent: AI Orchestrator, Growth Engine, Media Engine, dan Publisher beroperasi secara modular diatur SQLite State Machine.",
        "Zero Human Overhead untuk Formatting: Whisper otomatis menghitung word-level timing, memotong subtitle menjadi 3 baris aman dari tutupan UI TikTok.",
        "Fail-Safe Security Gate: Konten tidak akan dipublikasikan tanpa adanya record persetujuan sah (APPROVED) di tabel approvals SQLite."
    ]
    for ps in points_sum:
        p = tf_sum.add_paragraph()
        p.text = "• " + ps
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 6: MASALAH 1 - TIKTOK STUDIO DRAFTEDITOR LEAK
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s6, prs, BG_LIGHT)
    add_header(s6, "Kendala Operasional 1", "Bug TikTok Studio DraftEditor: Filename Placeholder Leak", 
               "Kegagalan Sinkronisasi State React TikTok Menyebabkan Nama File Menimpa Caption Naratif",
               tag_color=ACCENT_ALERT, tag_bg=ACCENT_ALERT_BG)

    # 4 Structured Boxes: Gejala, Akar Masalah, Dampak, Solusi
    box_w = Inches(5.7)
    box_h = Inches(2.45)

    # Box 1: Gejala Lapangan
    add_card(s6, Inches(0.8), Inches(1.6), box_w, box_h, bg_color=CARD_BG, border_color=ACCENT_ALERT)
    tb = s6.shapes.add_textbox(Inches(1.0), Inches(1.75), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "GEJALA LAPANGAN (SYMPTOM)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ALERT

    pts = [
        "Video Dinda Kemala yang terbit pada 9 & 10 November menampilkan caption placeholder mentah seperti 'final_vlog_morning' atau 'final_vlog'.",
        "Narasi budaya dan kuliner yang sudah disetujui owner di Telegram tidak muncul di TikTok publik.",
        "Hanya hashtag di bagian ekor yang berhasil masuk, sementara bodi teks utama hilang."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # Box 2: Akar Masalah Teknis
    add_card(s6, Inches(6.8), Inches(1.6), box_w, box_h, bg_color=CARD_BG, border_color=CARD_BORDER)
    tb = s6.shapes.add_textbox(Inches(7.0), Inches(1.75), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "AKAR MASALAH TEKNIS (ROOT CAUSE)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    pts = [
        "TikTok Studio menggunakan React DraftEditor (.public-DraftEditor-content).",
        "Saat file diupload, TikTok menginjeksi nama file secara default ke editor.",
        "Manipulasi DOM standar (document.execCommand('insertText') / .value=) hanya mengubah teks di layar tetapi GAGAL mengupdate internal virtual state React.",
        "Form submission tetap mengirim state default lama (nama file)."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # Box 3: Mitigasi & Perbaikan Langsung
    add_card(s6, Inches(0.8), Inches(4.3), box_w, box_h, bg_color=ACCENT_SUCCESS_BG, border_color=ACCENT_SUCCESS)
    tb = s6.shapes.add_textbox(Inches(1.0), Inches(4.45), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "SOLUSI & MITIGASI TEKNIS (RESOLVED)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SUCCESS

    pts = [
        "Ganti DOM injection dengan Chrome DevTools Protocol Keystrokes asli (Input.dispatchKeyEvent / Input.insertText).",
        "Simulasikan keyboard nyata: Select All (Meta+A / Ctrl+A) -> Backspace -> Ketik narasi baru karakter demi karakter.",
        "Trigger synthetic focus, space, backspace, dan blur events untuk mengaktifkan state 'isDirty' React sehingga tombol Simpan aktif (aria-disabled='false').",
        "Video 10 Nov Pagi & 9 Nov Malam berhasil diperbaiki langsung di TikTok Studio."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # Box 4: Rekomendasi Preventif
    add_card(s6, Inches(6.8), Inches(4.3), box_w, box_h, bg_color=CARD_BG, border_color=CARD_BORDER)
    tb = s6.shapes.add_textbox(Inches(7.0), Inches(4.45), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "PRE-FLIGHT VERIFICATION GUARD (PREVENTIF)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_MAIN

    pts = [
        "Tambahkan guard wajib sebelum tombol Post diklik: Baca innerText seluruh editor via querySelector.",
        "Verifikasi exact match antara teks editor dengan naskah Telegram yang di-ACC.",
        "Jika terdeteksi kata placeholder (seperti 'final_vlog' atau '.mp4'), ABORT proses pengunggahan dan kirim alert darurat.",
        "Blokir pengiriman buta jika live_sending_ready belum bernilai True."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # =========================================================================
    # SLIDE 7: MASALAH 2 - WARDROBE AUTO-STYLIST INCONSISTENCY
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s7, prs, BG_LIGHT)
    add_header(s7, "Kendala Operasional 2", "Inkonsistensi Lemari Pakaian Auto-Stylist Dinda", 
               "Crawling Pinterest Memasukkan Entri Busana Tanpa Foto Fisik Lokal yang Valid",
               tag_color=ACCENT_ALERT, tag_bg=ACCENT_ALERT_BG)

    # 4 Structured Boxes
    # Box 1: Gejala
    add_card(s7, Inches(0.8), Inches(1.6), box_w, box_h, bg_color=CARD_BG, border_color=ACCENT_ALERT)
    tb = s7.shapes.add_textbox(Inches(1.0), Inches(1.75), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "GEJALA LAPANGAN (SYMPTOM)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ALERT

    pts = [
        "Karakter Dinda kadang-kadang tampil dengan pakaian yang tidak konsisten atau berubah model di tengah adegan.",
        "Generator konten memilih ID busana dari database tetapi file gambar referensi tidak dapat dimuat oleh Google Flow.",
        "Pipeline mengalami fallback diam-diam ke deskripsi generik teks saja tanpa panduan visual OOTD yang presisi."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # Box 2: Akar Masalah Teknis
    add_card(s7, Inches(6.8), Inches(1.6), box_w, box_h, bg_color=CARD_BG, border_color=CARD_BORDER)
    tb = s7.shapes.add_textbox(Inches(7.0), Inches(1.75), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "AKAR MASALAH TEKNIS (ROOT CAUSE)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    pts = [
        "Skrip daily_pinterest_wardrobe_job.js melakukan scraping tren Pinterest dan langsung menuliskan status='active' ke database character_wardrobe.",
        "URL gambar di Pinterest seringkali kadaluarsa (expired CDN token) atau belum diunduh ke folder lokal /characters/dinda/wardrobe/.",
        "Tidak ada validasi fisik (os.path.isfile) saat status busana dinyatakan siap pakai ('active')."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # Box 3: Perbaikan yang Telah Dilakukan
    add_card(s7, Inches(0.8), Inches(4.3), box_w, box_h, bg_color=ACCENT_SUCCESS_BG, border_color=ACCENT_SUCCESS)
    tb = s7.shapes.add_textbox(Inches(1.0), Inches(4.45), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "PERBAIKAN YANG TELAH DILAKUKAN (FIXED)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SUCCESS

    pts = [
        "Update script daily_pinterest_wardrobe_job.js: Entri hasil crawling baru kini diberi status='incomplete' secara default.",
        "Audit berkas fisik di wardrobe_upsert.py: Wajib lolos os.path.isfile(reference_path) sebelum diizinkan beralih ke status 'active'.",
        "Penambahan filter ketat pada wardrobe_manager.py dan generate_content_options.py sehingga hanya outfit dengan file lokal terverifikasi yang dapat dipilih pipeline."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # Box 4: Standar Aset Visual Wardrobe
    add_card(s7, Inches(6.8), Inches(4.3), box_w, box_h, bg_color=CARD_BG, border_color=CARD_BORDER)
    tb = s7.shapes.add_textbox(Inches(7.0), Inches(4.45), box_w - Inches(0.4), box_h - Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "STANDARISASI ASET VISUAL OOTD (SOP)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_MAIN

    pts = [
        "Format Gambar Wajib: Rasio vertikal 9:16 (minimal 1080x1920 piksel), pencahayaan studio bersih, hijab rapi.",
        "Penamaan Terstruktur: [kategori]_[warna]_[musim]_[hash].jpg untuk memudahkan seleksi algoritma.",
        "Rotasi Busana Otomatis: Batasi pemakaian busana maksimal 1 kali dalam rentang 5 hari untuk mencegah kebosanan audiens.",
        "Pencatatan SHA256: Setiap gambar pakaian divalidasi checksum-nya dalam ledger produksi."
    ]
    for pt in pts:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(3)

    # =========================================================================
    # SLIDE 8: MASALAH 3 - PLATFORM CONSTRAINTS TIKTOK
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s8, prs, BG_LIGHT)
    add_header(s8, "Kendala Operasional 3", "Limitasi Kebijakan TikTok: Edit Cooldown & Duplikasi Tag", 
               "Aturan Ketat Edit Pasca-Publish TikTok Serta Artefak Duplikasi Hashtag dari Skrip Lawas",
               tag_color=ACCENT_ALERT, tag_bg=ACCENT_ALERT_BG)

    # Left Column: TikTok Platform Policy Limits
    add_card(s8, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_l = s8.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.3), Inches(5.0))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    
    p = tf_l.paragraphs[0]
    p.text = "KEBIJAKAN KETAT EDIT CAPTION TIKTOK"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ALERT

    tiktok_limits = [
        ("Limitasi 1x per 24 Jam", "TikTok hanya mengizinkan pengubahan judul/caption video sebanyak 1 kali dalam rentang 24 jam. Percobaan edit kedua akan ditolak sistem dengan pesan error 'Something went wrong. Please try again'."),
        ("Jendela Waktu 7 Hari", "Fitur 'Edit post' di TikTok Studio hanya tersedia dalam 7 hari pertama sejak video dipublikasikan. Setelah hari ke-7, tombol edit dikunci permanen."),
        ("Dampak Operasional", "Koreksi manual pasca-posting memiliki risiko kegagalan tinggi jika video sudah pernah diedit sebelumnya."),
        ("Prinsip 'Zero-Defect Upload'", "Caption WAJIB 100% sempurna saat pertama kali diunggah oleh bot CDP. Tidak boleh mengandalkan skrip perbaikan belakangan (post-publish patching).")
    ]
    for title, desc in tiktok_limits:
        p = tf_l.add_paragraph()
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(8)

        p2 = tf_l.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(2)

    # Right Column: Double Hashtag Artifact & Sanitization
    add_card(s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_r = s8.shapes.add_textbox(Inches(7.0), Inches(1.75), Inches(5.3), Inches(5.0))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    
    p = tf_r.paragraphs[0]
    p.text = "ARTEFAK DOUBLE HASHTAG & SANITASI TEKS"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    hashtag_points = [
        ("Temuan pada Video Lama", "Pada video tanggal 7 & 8 November (misal ID 77057809392...), ditemukan penumpukan hashtag ganda di akhir caption (contoh: '#fyp #palembang #kuliner #fyp #palembang')."),
        ("Penyebab Skrip Lawas", "Skrip generasi naskah lama menambahkan hashtag bawaan, kemudian modul publisher menambahkan daftar hashtag cadangan lagi tanpa pemeriksaan deduplikasi."),
        ("Risiko Shadowban / Algoritma", "Penumpukan hashtag berulang dapat dianggap spam oleh algoritma rekomendasi For You Page (FYP) TikTok dan menurunkan jangkauan organik."),
        ("Solusi Regex Sanitizer", "Implementasi fungsi regex deduplikasi pada text cleaner sebelum proses injeksi caption: split kata -> filter unik berurutan -> pertahankan maksimal 3-5 hashtag resmi.")
    ]
    for title, desc in hashtag_points:
        p = tf_r.add_paragraph()
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(8)

        p2 = tf_r.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(2)

    # =========================================================================
    # SLIDE 9: MASALAH 4 & 5 - RESOURCE LIMITS & TELEGRAM ACC
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s9, prs, BG_LIGHT)
    add_header(s9, "Kendala Operasional 4 & 5", "Manajemen Kredit Google Flow & Gatekeeping Telegram", 
               "Tantangan Kuota Komputasi Generatif dan Penanganan Antrean Human-in-the-Loop",
               tag_color=ACCENT_ALERT, tag_bg=ACCENT_ALERT_BG)

    # Left Column: Google Flow Resource Limits
    add_card(s9, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_flow = s9.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.3), Inches(5.0))
    tf_flow = tb_flow.text_frame
    tf_flow.word_wrap = True

    p = tf_flow.paragraphs[0]
    p.text = "KONSUMSI KREDIT & LATENSI GOOGLE FLOW"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE

    flow_challenges = [
        ("Biaya Komputasi Tinggi", "Google Flow Omni 1.2 Flash menghabiskan ~30 kredit per video generasi 10 detik. Percobaan multi-take atau render berulang dapat menghabiskan kuota harian akun dalam hitungan jam."),
        ("Latensi Render 5-10 Menit", "Waktu antrean render video AI di cloud Google berfluktuasi antara 3 hingga 10 menit. Jika terjadi timeout pada browser automation, pipeline berisiko mengalami kebuntuan (hang)."),
        ("Two-Phase Commit Ledger", "Pencatatan konsumsi kredit kini dikunci dalam sistem single-ledger: reservasi kuota sebelum render, dan commit hanya saat file MP4 terverifikasi utuh di disk."),
        ("Credit Ceiling Safeguard", "Penerapan batas harian (daily ceiling cap): sistem menolak permintaan render baru jika sisa kredit mencapai batas ambang darurat (buffer 50 kredit).")
    ]
    for title, desc in flow_challenges:
        p = tf_flow.add_paragraph()
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(8)

        p2 = tf_flow.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(2)

    # Right Column: Telegram Approval Gatekeeper
    add_card(s9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    tb_tg = s9.shapes.add_textbox(Inches(7.0), Inches(1.75), Inches(5.3), Inches(5.0))
    tf_tg = tb_tg.text_frame
    tf_tg.word_wrap = True

    p = tf_tg.paragraphs[0]
    p.text = "BOTTLENECK TIME-LOCK TELEGRAM GATEKEEPER"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = RGBColor(13, 148, 136)

    tg_challenges = [
        ("Jendela Review 2 Jam (Time-Lock)", "Pipeline dirancang aman: video hanya diunggah jika status 'APPROVED' tercatat di SQLite approvals dalam rentang waktu tunggu 2 jam (06:00 - 08:00 WIB)."),
        ("Resiko Unresponsive Owner", "Jika owner berhalangan atau terlambat membalas Telegram saat slot posting tiba, sistem otomatis menahan (hold) posting agar reputasi brand tidak terancam."),
        ("Penumpukan Antrean (Queue Clogging)", "Konten yang tertahan sebelumnya berpotensi bertabrakan dengan jadwal produksi video berikutnya jika tidak ada mekanisme auto-reschedule."),
        ("Solusi Adaptive Rescheduling", "Jika window review kedaluwarsa tanpa ACC, konten dipindahkan secara otomatis ke slot alternatif malam (19:00 WIB) tanpa memicu render ulang yang memboroskan kredit.")
    ]
    for title, desc in tg_challenges:
        p = tf_tg.add_paragraph()
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.space_before = Pt(8)

        p2 = tf_tg.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(2)

    # =========================================================================
    # SLIDE 10: RENCANA AKSI & MONITORING BERKELANJUTAN
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_solid_bg(s10, prs, BG_DARK)

    # Top Stripe
    stripe10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    stripe10.fill.solid()
    stripe10.fill.fore_color.rgb = ACCENT_SUCCESS
    stripe10.line.fill.background()

    add_header(s10, "Rencana Aksi & Roadmap", "Strategi Mitigasi Berkelanjutan & Monitoring Terpusat", 
               "Matriks Prioritas Tindakan Sistematis untuk Menjamin Stabilitas Publikasi Otonom 24/7",
               tag_color=ACCENT_SUCCESS, tag_bg=RGBColor(6, 78, 59), dark_theme=True)

    # 3 Priority Columns (P0, P1, P2)
    col_w = Inches(3.7)
    gap = Inches(0.28)

    priorities = [
        ("PRIORITAS P0 (IMMEDIATE)", "Pencegahan Bug Kritis", ACCENT_ALERT, RGBColor(69, 10, 10), [
            "Terapkan Pre-Flight Verification Guard pada seluruh skrip uploader CDP sebelum submit.",
            "Validasi fisik os.path.isfile() pada setiap entri busana di character_wardrobe.",
            "Aktifkan regex deduplikasi hashtag untuk mencegah spam penalti TikTok FYP.",
            "Semua test runner suite (56 tests) wajib lulus 100% sebelum cron job dieksekusi."
        ]),
        ("PRIORITAS P1 (SHORT-TERM)", "Optimasi & Automasi", ACCENT_ISK, RGBColor(69, 26, 3), [
            "Otomatisasi pengunduhan gambar fisik Pinterest saat crawling OOTD berjalan.",
            "Sinkronisasi kuota Google Flow dengan single-ledger alerts jika sisa < 50 kredit.",
            "Fitur Quick ACC di Telegram (Inline Button: 'Setujui', 'Revisi', 'Tunda').",
            "Penyempurnaan timing MarginV=850 hardsub ASS pada video uji lapangan ISK."
        ]),
        ("PRIORITAS P2 (MEDIUM-TERM)", "Skalabilitas & Ekosistem", PRIMARY_BLUE, RGBColor(30, 58, 138), [
            "Multi-account load balancing untuk Google Flow (rotasi token aman).",
            "Peningkatan interaksi otomatis komentar TikTok dengan NLP konteks lokal.",
            "Integrasi live dashboard analitik retensi penonton dari TikTok Studio ke SQLite.",
            "Ekspansi pipeline ke akun cabang dan platform short-video lain (Reels/Shorts)."
        ])
    ]

    for idx, (p_title, p_sub, border_col, fill_col, tasks) in enumerate(priorities):
        x = Inches(0.8) + idx * (col_w + gap)
        add_card(s10, x, Inches(1.6), col_w, Inches(4.0), bg_color=RGBColor(24, 33, 47), border_color=border_col, border_width=1.5)
        
        tb = s10.shapes.add_textbox(x + Inches(0.15), Inches(1.75), col_w - Inches(0.3), Inches(3.7))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = border_col

        p_subt = tf.add_paragraph()
        p_subt.text = p_sub
        p_subt.font.name = FONT_BODY
        p_subt.font.size = Pt(9)
        p_subt.font.color.rgb = TEXT_WHITE_MUTED
        p_subt.space_before = Pt(2)

        for t in tasks:
            pt = tf.add_paragraph()
            pt.text = "• " + t
            pt.font.name = FONT_BODY
            pt.font.size = Pt(9.5)
            pt.font.color.rgb = TEXT_WHITE
            pt.space_before = Pt(6)

    # Bottom Dashboard Monitoring Card
    add_card(s10, Inches(0.8), Inches(5.8), Inches(11.733), Inches(1.2), bg_color=RGBColor(30, 41, 59), border_color=PRIMARY_BLUE)
    tb_dash = s10.shapes.add_textbox(Inches(1.0), Inches(5.9), Inches(11.333), Inches(1.0))
    tf_dash = tb_dash.text_frame
    tf_dash.word_wrap = True

    p = tf_dash.paragraphs[0]
    p.text = "PUSAT PEMANTAUAN VIRTUAL OFFICE 3D CYBER HQ"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(147, 197, 253)

    p_d = tf_dash.add_paragraph()
    p_d.text = "Seluruh aktivitas agen, status jadwal cron (Produksi 07:00 & 19:00 WIB Dinda, 09:00 & 12:00 WIB ISK), antrean Telegram, dan health check server dipantau secara visual melalui Virtual Office 3D di https://kantor-ai-intan.vercel.app (Lounge 3D & Studio Mode)."
    p_d.font.name = FONT_BODY
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_WHITE_MUTED
    p_d.space_before = Pt(4)

    # Save presentation
    os.makedirs(DOCS_DIR, exist_ok=True)
    prs.save(OUTPUT_PPTX)
    print(f"Presentation successfully generated at: {OUTPUT_PPTX}")
    return OUTPUT_PPTX


if __name__ == "__main__":
    out = build_deck()
    print("Done! Output file:", out)

