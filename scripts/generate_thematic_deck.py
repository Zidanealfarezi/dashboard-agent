#!/usr/bin/env python3
"""
generate_thematic_deck.py
Builds the upgraded, high-theme "Cyber-Executive Autonomous Studio" PowerPoint deck.
Features:
- Unified Obsidian Slate Dark Theme across all 10 slides
- Distinct Brand Identity colors for Dinda Kemala (Rose/Coral) and PT ISK (Industrial Amber/Gold)
- Visual Metric Callout Bars (Big stats: 89.5%, 25 KG, 0% Emoji, 10s, 30 Kredit, 2 Jam)
- High-contrast alert/solution cards with colored top-accent stripes
- Photo embedding (Dinda portrait & Paku Cap Keris box reference)
- Cohesive header, slide index counter (01/10 .. 10/10), divider lines, and boardroom footers
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
OUTPUT_PPTX = os.path.join(DOCS_DIR, "Laporan_Evaluasi_Akun_dan_Masalah_Operasional.pptx")

DINDA_PORTRAIT = os.path.join(BASE_DIR, "FOTO_KARAKTER", "Dinda", "snaptik-app-7622957837660032277-slide-1.jpg_b841cd5b.jpg")
DINDA_HORIZONTAL = os.path.join(BASE_DIR, "FOTO_KARAKTER", "Dinda", "dinda.jpg")
ISK_IMG = os.path.join(BASE_DIR, "characters", "isk", "assets", "brand", "paku_cap_keris_box_reference.jpg")

# =============================================================================
# THEME COLOR PALETTE (Cyber-Executive Boardroom)
# =============================================================================
COLOR_BG_VOID = RGBColor(11, 15, 25)          # Obsidian Slate #0B0F19
COLOR_SURFACE_CARD = RGBColor(17, 24, 39)     # Deep Card Surface #111827
COLOR_SURFACE_ELEVATED = RGBColor(26, 36, 54) # Elevated Chip #1A2436
COLOR_BORDER_SUBTLE = RGBColor(31, 41, 55)    # Card Border #1F2937
COLOR_BORDER_LIGHT = RGBColor(51, 65, 85)     # Lighter Border #334155
COLOR_DIVIDER = RGBColor(30, 41, 59)          # Subtle Divider #1E293B

COLOR_TEXT_PRIMARY = RGBColor(248, 250, 252)  # Pure White #F8FAFC
COLOR_TEXT_SECONDARY = RGBColor(203, 213, 225)# Crisp Light Slate #CBD5E1
COLOR_TEXT_MUTED = RGBColor(148, 163, 184)    # Cool Grey #94A3B8
COLOR_TEXT_DARK_MUTED = RGBColor(100, 116, 139) # Dim Footer Grey #64748B

# Thematic Accents
ACCENT_DINDA = RGBColor(244, 63, 94)          # Rose Coral #F43F5E
ACCENT_DINDA_GLOW = RGBColor(251, 113, 133)   # Soft Rose #FB7185

ACCENT_ISK = RGBColor(245, 158, 11)           # Industrial Amber #F59E0B
ACCENT_ISK_GOLD = RGBColor(251, 191, 36)      # Keris Gold #FBBF24

ACCENT_SYSTEM = RGBColor(14, 165, 233)        # Cyber Cyan #0EA5E9
ACCENT_SYSTEM_INDIGO = RGBColor(99, 102, 241) # Tech Indigo #6366F1

ACCENT_ALERT = RGBColor(239, 68, 68)          # Crimson Alert #EF4444
ACCENT_SUCCESS = RGBColor(16, 185, 129)       # Emerald Verified #10B981
ACCENT_PURPLE = RGBColor(168, 85, 247)        # Quantum Purple #A855F7

FONT_HEADING = "Helvetica"
FONT_BODY = "Arial"


def add_cyber_background(slide, prs, top_accent_color):
    """Draws full slide dark background and top glowing accent band."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BG_VOID
    bg.line.fill.background()

    # Top accent band (3pt)
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.06))
    band.fill.solid()
    band.fill.fore_color.rgb = top_accent_color
    band.line.fill.background()


def add_slide_header(slide, eyebrow_text, title_text, subtitle_text, slide_index, total_slides=10, accent_color=ACCENT_SYSTEM):
    """Unified header for all slides with category pill, slide counter, and title."""
    left = Inches(0.8)
    top = Inches(0.38)

    # Eyebrow Pill
    eyebrow_w = Inches(2.8)
    eyebrow_h = Inches(0.28)
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, eyebrow_w, eyebrow_h)
    pill.fill.solid()
    pill.fill.fore_color.rgb = COLOR_SURFACE_ELEVATED
    pill.line.color.rgb = accent_color
    pill.line.width = Pt(1)

    tf_p = pill.text_frame
    tf_p.word_wrap = True
    tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
    p = tf_p.paragraphs[0]
    p.text = eyebrow_text.upper()
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_HEADING
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = accent_color

    # Slide Number Tracker (Top Right)
    counter_w = Inches(1.5)
    counter_h = Inches(0.28)
    counter_left = Inches(11.033)
    c_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, counter_left, top, counter_w, counter_h)
    c_box.fill.solid()
    c_box.fill.fore_color.rgb = COLOR_SURFACE_ELEVATED
    c_box.line.color.rgb = COLOR_BORDER_SUBTLE
    c_box.line.width = Pt(1)

    tf_c = c_box.text_frame
    tf_c.word_wrap = True
    tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
    p_c = tf_c.paragraphs[0]
    p_c.text = f"SLIDE {slide_index:02d} / {total_slides:02d}"
    p_c.alignment = PP_ALIGN.CENTER
    p_c.font.name = FONT_HEADING
    p_c.font.size = Pt(8.5)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_TEXT_MUTED

    # Title & Subtitle
    tb = slide.shapes.add_textbox(left, top + Inches(0.34), Inches(11.733), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_title = tf.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(20)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_PRIMARY

    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED
        p_sub.space_before = Pt(2)

    # Fine Divider Line
    div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top + Inches(1.15), Inches(11.733), Pt(1))
    div.fill.solid()
    div.fill.fore_color.rgb = COLOR_DIVIDER
    div.line.fill.background()


def add_metric_bar(slide, left, top, total_width, height, metrics_list, accent_color=ACCENT_SYSTEM):
    """
    metrics_list: list of tuples (stat_big_text, label_text)
    Creates a row of high-impact metric boxes.
    """
    n = len(metrics_list)
    gap = Inches(0.18)
    box_w = (total_width - (gap * (n - 1))) / n

    for i, (big_stat, label) in enumerate(metrics_list):
        bx = left + i * (box_w + gap)
        
        # Background Box
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bx, top, box_w, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SURFACE_CARD
        card.line.color.rgb = COLOR_BORDER_SUBTLE
        card.line.width = Pt(1)

        # Top Accent Stripe on Metric Card
        top_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx + Inches(0.08), top, box_w - Inches(0.16), Pt(2.5))
        top_stripe.fill.solid()
        top_stripe.fill.fore_color.rgb = accent_color
        top_stripe.line.fill.background()

        # Text Box
        tb = slide.shapes.add_textbox(bx + Inches(0.1), top + Inches(0.08), box_w - Inches(0.2), height - Inches(0.12))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = big_stat
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = accent_color
        p1.alignment = PP_ALIGN.CENTER

        p2 = tf.add_paragraph()
        p2.text = label.upper()
        p2.font.name = FONT_BODY
        p2.font.size = Pt(8)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_TEXT_MUTED
        p2.alignment = PP_ALIGN.CENTER
        p2.space_before = Pt(1)


def add_cyber_card(slide, left, top, width, height, accent_stripe_color=None, border_color=COLOR_BORDER_SUBTLE):
    """Creates a dark slate surface card with an optional colored top-accent line."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_SURFACE_CARD
    card.line.color.rgb = border_color
    card.line.width = Pt(1)

    if accent_stripe_color:
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.12), top, width - Inches(0.24), Pt(3))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = accent_stripe_color
        stripe.line.fill.background()

    return card


def add_slide_footer(slide, current_date="NOVEMBER 2026"):
    """Boardroom footer across the bottom of every slide."""
    left = Inches(0.8)
    top = Inches(7.1)
    width = Inches(11.733)

    tb = slide.shapes.add_textbox(left, top, width, Inches(0.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = "PT INTAN SUAR KARTIKA • AUTONOMOUS MEDIA ECOSYSTEM"
    p.font.name = FONT_HEADING
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK_MUTED

    run2 = p.add_run()
    run2.text = "   |   VIRTUAL OFFICE: kantor-ai-intan.vercel.app   |   "
    run2.font.name = FONT_BODY
    run2.font.size = Pt(8.5)
    run2.font.bold = False
    run2.font.color.rgb = COLOR_DIVIDER

    run3 = p.add_run()
    run3.text = f"{current_date} // STRICT 0% EMOJI // CONFIDENTIAL"
    run3.font.name = FONT_BODY
    run3.font.size = Pt(8.5)
    run3.font.bold = True
    run3.font.color.rgb = COLOR_TEXT_DARK_MUTED


def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: COVER (CYBER-EXECUTIVE THEME)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s1, prs, ACCENT_SYSTEM)

    # Eyebrow Chip
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.1), Inches(3.6), Inches(0.32))
    pill.fill.solid()
    pill.fill.fore_color.rgb = COLOR_SURFACE_ELEVATED
    pill.line.color.rgb = ACCENT_SYSTEM
    pill.line.width = Pt(1)
    p = pill.text_frame.paragraphs[0]
    p.text = "AUTONOMOUS MEDIA INTELLIGENCE // 2026"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_HEADING
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SYSTEM

    # Main Headline
    tb_title = s1.shapes.add_textbox(Inches(1.0), Inches(1.55), Inches(11.333), Inches(2.2))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0

    p_t1 = tf_title.paragraphs[0]
    p_t1.text = "Evaluasi Portfolio Akun AI &\nPemetaan Masalah Operasional"
    p_t1.font.name = FONT_HEADING
    p_t1.font.size = Pt(32)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_TEXT_PRIMARY

    p_t2 = tf_title.add_paragraph()
    p_t2.text = "Analisis Dual-Engine (@dinda.kemala_ & @intansuarkartika), Arsitektur Pipeline Otonom, dan Resolusi Kendala Lapangan"
    p_t2.font.name = FONT_BODY
    p_t2.font.size = Pt(12)
    p_t2.font.color.rgb = COLOR_TEXT_MUTED
    p_t2.space_before = Pt(8)

    # Dual-Engine Hero Cards
    card_w = Inches(5.5)
    card_h = Inches(2.6)

    # Dinda Cover Card
    add_cyber_card(s1, Inches(1.0), Inches(4.0), card_w, card_h, accent_stripe_color=ACCENT_DINDA)
    tb_c1 = s1.shapes.add_textbox(Inches(1.25), Inches(4.2), card_w - Inches(0.5), card_h - Inches(0.4))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    
    p = tf_c1.paragraphs[0]
    p.text = "ENGINE 1: DINDA KEMALA (@dinda.kemala_)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA

    bullets_c1 = [
        ("Niche & Sektor", "B2C Lifestyle, Budaya, Kuliner Palembang & Mahasiswi Hijab"),
        ("Format Visual", "9:16 Vertical AI Video (1080x1920) Talking-Head Flow Omni"),
        ("Frekuensi", "2x Sehari (07:00 Pagi & 19:00 Malam WIB)"),
        ("Status Operasi", "Aktif Berjalan dengan Pengawasan Telegram Gatekeeper")
    ]
    for lbl, val in bullets_c1:
        p = tf_c1.add_paragraph()
        p.text = f"• {lbl}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        r = p.add_run()
        r.text = val
        r.font.name = FONT_BODY
        r.font.size = Pt(9.5)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(4)

    # ISK Cover Card
    add_cyber_card(s1, Inches(6.833), Inches(4.0), card_w, card_h, accent_stripe_color=ACCENT_ISK)
    tb_c2 = s1.shapes.add_textbox(Inches(7.083), Inches(4.2), card_w - Inches(0.5), card_h - Inches(0.4))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    
    p = tf_c2.paragraphs[0]
    p.text = "ENGINE 2: PT INTAN SUAR KARTIKA (@intansuarkartika)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK_GOLD

    bullets_c2 = [
        ("Niche & Sektor", "B2B/B2C Manufaktur Bahan Bangunan, Paku Cap Keris & Kawat"),
        ("Format Visual", "Field Test Uji Ketahanan Ekstrem + Kinetic Hardsub ASS (M=850)"),
        ("Frekuensi", "Produksi 09:00 WIB, Publikasi 12:00 WIB"),
        ("Brand Anchor", "Strict 0% Emoji, Kardus Cokelat Kraft, Konversi Langsung WA")
    ]
    for lbl, val in bullets_c2:
        p = tf_c2.add_paragraph()
        p.text = f"• {lbl}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        r = p.add_run()
        r.text = val
        r.font.name = FONT_BODY
        r.font.size = Pt(9.5)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(4)

    add_slide_footer(s1)

    # =========================================================================
    # SLIDE 2: PROFIL AKUN 1 - DINDA KEMALA (ROSE PALETTE)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s2, prs, ACCENT_DINDA)
    add_slide_header(s2, "// PERSONA KREATIF B2C", "Akun 1: Dinda Kemala (@dinda.kemala_)",
                     "Persona Kreator Digital Palembang: Lifestyle, Gastronomi, dan Kebudayaan Lokal",
                     slide_index=2, total_slides=10, accent_color=ACCENT_DINDA)

    # Metric Callout Bar
    metrics_dinda = [
        ("2x / HARI", "Jadwal Tayang (07:00 & 19:00 WIB)"),
        ("9:16 VERTICAL", "Format Standar Google Flow"),
        ("10s TALK-HEAD", "Durasi Native Voice AI"),
        ("100% HIJAB", "Karakter Santun Mahasiswi")
    ]
    add_metric_bar(s2, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.72), metrics_dinda, accent_color=ACCENT_DINDA)

    # Left Column: Image Card
    col_img_w = Inches(3.4)
    col_img_h = Inches(4.35)
    add_cyber_card(s2, Inches(0.8), Inches(2.6), col_img_w, col_img_h, accent_stripe_color=ACCENT_DINDA)
    
    # Embed Photo
    if os.path.exists(DINDA_PORTRAIT):
        s2.shapes.add_picture(DINDA_PORTRAIT, Inches(1.05), Inches(2.8), width=Inches(2.9))
    elif os.path.exists(DINDA_HORIZONTAL):
        s2.shapes.add_picture(DINDA_HORIZONTAL, Inches(0.95), Inches(2.8), width=Inches(3.1))

    # Badge under image
    tb_badge = s2.shapes.add_textbox(Inches(1.0), Inches(6.35), Inches(3.0), Inches(0.45))
    tf_b = tb_badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = "IDENTITAS: @dinda.kemala_\nPalembang, Sumatera Selatan"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.name = FONT_HEADING
    p_b.font.size = Pt(8.5)
    p_b.font.bold = True
    p_b.font.color.rgb = ACCENT_DINDA_GLOW

    # Right Column: 3 Structured Pillar Cards
    right_x = Inches(4.45)
    right_w = Inches(8.083)
    card_r_h = Inches(1.35)
    card_gap = Inches(0.15)

    # Card 1: Content Pillars
    add_cyber_card(s2, right_x, Inches(2.6), right_w, card_r_h, accent_stripe_color=ACCENT_DINDA)
    tb = s2.shapes.add_textbox(right_x + Inches(0.2), Inches(2.72), right_w - Inches(0.4), card_r_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "PILAR KONTEN & POSITIONING STRATEGIS"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA
    d_pillars = [
        "Wisata Kuliner Palembang: Eksplorasi pempek bingen, martabak HAR, tekwan, kue gandus, dan gulo palu.",
        "Destinasi & Kebudayaan: Narasi Sungai Musi, Benteng Kuto Besak, Museum SMB II, dan tradisi lokal.",
        "Daily Vlog Mahasiswi: OOTD hijab casual, persiapan kuliah, dan interaksi hangat ramah publik."
    ]
    for dp in d_pillars:
        p = tf.add_paragraph()
        p.text = "• " + dp
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    # Card 2: Brand Voice & Safety
    add_cyber_card(s2, right_x, Inches(2.6) + card_r_h + card_gap, right_w, card_r_h, accent_stripe_color=ACCENT_DINDA)
    tb = s2.shapes.add_textbox(right_x + Inches(0.2), Inches(2.72) + card_r_h + card_gap, right_w - Inches(0.4), card_r_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "TONE OF VOICE & KEBIJAKAN ENGAGEMENT"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA
    d_voice = [
        "Bahasa & Dialek: Bahasa Indonesia santun dengan selipan kosakata Palembang halus ('dulur-dulur', 'mangcek').",
        "Keterbukaan AI: Transparan menjawab bahwa Dinda adalah persona AI karya kreator lokal jika ditanya.",
        "Batasan Keamanan (Guardrails): Dilarang membuat janji temu fisik, relasi fiktif, atau nomor kontak pribadi."
    ]
    for dv in d_voice:
        p = tf.add_paragraph()
        p.text = "• " + dv
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    # Card 3: Production Mechanics
    add_cyber_card(s2, right_x, Inches(2.6) + 2 * (card_r_h + card_gap), right_w, card_r_h, accent_stripe_color=ACCENT_DINDA)
    tb = s2.shapes.add_textbox(right_x + Inches(0.2), Inches(2.72) + 2 * (card_r_h + card_gap), right_w - Inches(0.4), card_r_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "WORKFLOW PRODUKSI OTONOM & APPROVAL"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_DINDA
    d_prod = [
        "Auto-Stylist Wardrobe: Kurasi OOTD harian dari database busana hijab untuk menjaga konsistensi visual.",
        "Google Flow Generatif: Pembuatan video talking-head 10 detik rasio 9:16 resolusi tinggi tanpa watermark.",
        "Gatekeeper Telegram: Pengiriman kartu review & naskah ke Telegram Owner sebelum publikasi CDP."
    ]
    for dpr in d_prod:
        p = tf.add_paragraph()
        p.text = "• " + dpr
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    add_slide_footer(s2)

    # =========================================================================
    # SLIDE 3: PROFIL AKUN 2 - PT INTAN SUAR KARTIKA (AMBER/GOLD PALETTE)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s3, prs, ACCENT_ISK)
    add_slide_header(s3, "// MANUFAKTUR & OTOMATISASI B2B", "Akun 2: PT Intan Suar Kartika (@intansuarkartika)",
                     "Strategi Konten Edukasi Industri Konstruksi, Uji Ketahanan Material & Corong Sales Toko Bangunan",
                     slide_index=3, total_slides=10, accent_color=ACCENT_ISK)

    # Metric Callout Bar
    metrics_isk = [
        ("89.5% INTENT", "Dominasi Pencarian Organik TikTok"),
        ("25 KG NETTO", "Standar Ekspor SNI 0194-78"),
        ("0% EMOJI", "Strict Professionalism Policy"),
        ("4.07s OUTRO", "Closing Bumper Resmi PT ISK")
    ]
    add_metric_bar(s3, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.72), metrics_isk, accent_color=ACCENT_ISK)

    # Left Column: Image Card
    add_cyber_card(s3, Inches(0.8), Inches(2.6), col_img_w, col_img_h, accent_stripe_color=ACCENT_ISK)
    if os.path.exists(ISK_IMG):
        s3.shapes.add_picture(ISK_IMG, Inches(0.95), Inches(3.0), width=Inches(3.1))

    tb_badge3 = s3.shapes.add_textbox(Inches(1.0), Inches(5.0), Inches(3.0), Inches(1.6))
    tf_b3 = tb_badge3.text_frame
    tf_b3.word_wrap = True
    p_b3 = tf_b3.paragraphs[0]
    p_b3.text = "PACKAGING ANCHOR RESMI:\nKardus Cokelat Kraft Horisontal\nTipografi Hijau Tua SNI 0194-78\nPaku Curah Lepas TANPA Plastik"
    p_b3.alignment = PP_ALIGN.CENTER
    p_b3.font.name = FONT_HEADING
    p_b3.font.size = Pt(8.5)
    p_b3.font.bold = True
    p_b3.font.color.rgb = ACCENT_ISK_GOLD

    # Right Column: 3 Structured Cards
    # Card 1: Search Intent & Pillars
    add_cyber_card(s3, right_x, Inches(2.6), right_w, card_r_h, accent_stripe_color=ACCENT_ISK)
    tb = s3.shapes.add_textbox(right_x + Inches(0.2), Inches(2.72), right_w - Inches(0.4), card_r_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "EKSPLOITASI 89.5% SEARCH INTENT & PILAR PRODUK"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK
    isk_pil = [
        "Paku Cap Keris: Standar SNI 0194-78, ekspor quality, paku lurus anti bengkok, timbangan pas 25 kg.",
        "Kawat Duri Diamond: Spesialis pagar kebun sawit, cabai, dan lahan proyek (views organik tertinggi).",
        "Kereta Sorong Five Star & Kawat Bendrat: Uji beban ekstrem 200+ kg dan kekuatan ikat tulangan beton."
    ]
    for ip in isk_pil:
        p = tf.add_paragraph()
        p.text = "• " + ip
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    # Card 2: Production Formula & Subtitling
    add_cyber_card(s3, right_x, Inches(2.6) + card_r_h + card_gap, right_w, card_r_h, accent_stripe_color=ACCENT_ISK)
    tb = s3.shapes.add_textbox(right_x + Inches(0.2), Inches(2.72) + card_r_h + card_gap, right_w - Inches(0.4), card_r_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "FORMULA PRODUKSI & POST-PRODUCTION KHUSUS"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK
    isk_form = [
        "Hook 0-3s Visual Nyata: Aksi banting tang, hantaman palu baja, dan uji beban langsung di lapangan.",
        "Kinetic Yellow Hardsub: Faster-Whisper alignment, warna kuning (#FFE600), font tebal outline hitam.",
        "Safe-Zone MarginV=850: Posisi vertikal y=1070 menjamin subtitle 100% aman dari tutupan UI TikTok.",
        "Official Outro Bumper: Concat FFmpeg video penutup resmi PT Intan Suar Kartika utuh 4.07 detik."
    ]
    for iform in isk_form:
        p = tf.add_paragraph()
        p.text = "• " + iform
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    # Card 3: Strict Policy & Conversion
    add_cyber_card(s3, right_x, Inches(2.6) + 2 * (card_r_h + card_gap), right_w, card_r_h, accent_stripe_color=ACCENT_ISK)
    tb = s3.shapes.add_textbox(right_x + Inches(0.2), Inches(2.72) + 2 * (card_r_h + card_gap), right_w - Inches(0.4), card_r_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "STRICT 0% EMOJI POLICY & FUNNEL PENJUALAN"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ISK
    isk_pol = [
        "Strict 0% Emoji Policy: Seluruh naskah, caption, dan balasan chat bebas emoji demi wibawa industri berat.",
        "Tone Bicara Lapangan: Lugas, ringkas, menghormati kalkulasi biaya mandor dan pemilik toko bangunan.",
        "3 Hashtag Terfokus: Maksimal 3 tag resmi (#pakucapkeris #intansuarkartika #tokobangunan).",
        "Direct CTA WhatsApp: Arahkan setiap pertanyaan grosir langsung ke wa.me/62819889350."
    ]
    for ipol in isk_pol:
        p = tf.add_paragraph()
        p.text = "• " + ipol
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    add_slide_footer(s3)

    # =========================================================================
    # SLIDE 4: MATRIKS KOMPARASI STRATEGIS (CYBER TABLE)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s4, prs, ACCENT_SYSTEM)
    add_slide_header(s4, "// ANALISIS KOMPARATIF DUAL-ENGINE", "Matriks Komparasi Strategis Antar Akun",
                     "Perbandingan Parameter, Persona, Arsitektur Konten, dan Funnel Konversi",
                     slide_index=4, total_slides=10, accent_color=ACCENT_SYSTEM)

    # Table Card Container
    add_cyber_card(s4, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.25), accent_stripe_color=ACCENT_SYSTEM)

    # Create Table
    rows, cols = 8, 3
    t_shape = s4.shapes.add_table(rows, cols, Inches(1.0), Inches(1.85), Inches(11.333), Inches(4.8))
    table = t_shape.table

    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(4.416)
    table.columns[2].width = Inches(4.416)

    # Header Row
    headers = [
        ("PARAMETER STRATEGIS", COLOR_SURFACE_ELEVATED, COLOR_TEXT_PRIMARY),
        ("DINDA KEMALA (@dinda.kemala_)", RGBColor(76, 5, 25), ACCENT_DINDA_GLOW),
        ("PT INTAN SUAR KARTIKA (@intansuarkartika)", RGBColor(69, 26, 3), ACCENT_ISK_GOLD)
    ]
    for col_idx, (htext, bg_col, txt_col) in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = htext
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg_col
        p = cell.text_frame.paragraphs[0]
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = txt_col
        p.alignment = PP_ALIGN.CENTER

    matrix_rows = [
        ("Segmen Audiens", "B2C Konsumen umum, generasi muda, pecinta budaya Palembang", "B2B / B2C Kontraktor, mandor proyek, pemilik toko bangunan"),
        ("Persona Karakter", "Mahasiswi berhijab santun, ramah, tutur kata lokal Palembang", "Representatif teknis pabrik manufaktur, lugas, profesional"),
        ("Gaya Visual AI", "Talking-head lifestyle 9:16, natural look, kurasi busana OOTD", "Field test, uji banting ketahanan, kemasan karton paku curah"),
        ("Audio & Post-Prod", "Native Flow voice tanpa subtitle bakar, musik lokal santun", "Faster-Whisper alignment, Hardsub ASS Kuning (M=850), Outro Bumper"),
        ("Kebijakan Bahasa", "Bahasa Indonesia luwes dengan selipan kosakata daerah halus", "Strict 0% Emoji Policy, narasi langsung tanpa basa-basi"),
        ("Branding & Outro", "Signature watermark halus personal brand Dinda Kemala", "Official outro bumper PT Intan Suar Kartika utuh 4.07 detik"),
        ("Tujuan Akhir (Goal)", "Engagement komunitas, awareness budaya lokal & UMKM", "Penetrasi pasar grosir, edukasi ketahanan, leads WA Distributor")
    ]

    for r_idx, (param, dinda_val, isk_val) in enumerate(matrix_rows, start=1):
        row_bg = COLOR_SURFACE_CARD if r_idx % 2 == 1 else RGBColor(22, 30, 49)
        vals = [param, dinda_val, isk_val]
        for c_idx in range(3):
            cell = table.cell(r_idx, c_idx)
            cell.text = vals[c_idx]
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_HEADING if c_idx == 0 else FONT_BODY
            p.font.size = Pt(9.5)
            p.font.bold = (c_idx == 0)
            if c_idx == 0:
                p.font.color.rgb = COLOR_TEXT_PRIMARY
            elif c_idx == 1:
                p.font.color.rgb = COLOR_TEXT_SECONDARY
            else:
                p.font.color.rgb = COLOR_TEXT_SECONDARY

    add_slide_footer(s4)

    # =========================================================================
    # SLIDE 5: ARSITEKTUR PIPELINE 6-STAGE AUTONOMOUS ENGINE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s5, prs, ACCENT_SYSTEM)
    add_slide_header(s5, "// ARSITEKTUR SISTEM OTONOM", "Arsitektur End-to-End Autonomous Pipeline",
                     "Integrasi 6 Modul Otonom: Riset Tren, Generasi AI, Post-Production, hingga Publikasi CDP",
                     slide_index=5, total_slides=10, accent_color=ACCENT_SYSTEM)

    # 6 Step Cards
    stages = [
        ("01", "Riset & Tren", "Analisis kueri 89.5% search intent TikTok Studio & tren lokal harian.", ACCENT_PURPLE),
        ("02", "Brief & Naskah", "Penyusunan hook 0-3 detik, verifikasi OOTD fisik, penegakan 0% emoji.", ACCENT_SYSTEM),
        ("03", "Generasi AI", "Google Flow 1.2 Flash merender video rasio 9:16 durasi 10 detik HD.", ACCENT_DINDA),
        ("04", "Post-Production", "Whisper timing, hardsub kuning ASS (MarginV=850), & outro bumper.", ACCENT_ISK),
        ("05", "Telegram Gate", "Kirim kartu preview & naskah ke Telegram Owner (Window 2 jam ACC).", RGBColor(13, 148, 136)),
        ("06", "CDP Publisher", "Headless Chrome via DevTools Protocol mengunggah draf ke TikTok Studio.", ACCENT_SUCCESS)
    ]

    card_w = Inches(1.8)
    gap = Inches(0.18)
    left_start = Inches(0.8)
    top_stage = Inches(1.7)
    height_stage = Inches(3.7)

    for idx, (num, title, desc, acc_col) in enumerate(stages):
        x = left_start + idx * (card_w + gap)
        add_cyber_card(s5, x, top_stage, card_w, height_stage, accent_stripe_color=acc_col)

        tb = s5.shapes.add_textbox(x + Inches(0.12), top_stage + Inches(0.18), card_w - Inches(0.24), height_stage - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p_num = tf.paragraphs[0]
        p_num.text = num
        p_num.font.name = FONT_HEADING
        p_num.font.size = Pt(22)
        p_num.font.bold = True
        p_num.font.color.rgb = acc_col

        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(11)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_PRIMARY
        p_title.space_before = Pt(4)

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = FONT_BODY
        p_desc.font.size = Pt(9.5)
        p_desc.font.color.rgb = COLOR_TEXT_MUTED
        p_desc.space_before = Pt(8)

    # Bottom Architectural Highlights Card
    add_cyber_card(s5, Inches(0.8), Inches(5.6), Inches(11.733), Inches(1.3), accent_stripe_color=ACCENT_SYSTEM)
    tb_b = s5.shapes.add_textbox(Inches(1.0), Inches(5.72), Inches(11.333), Inches(1.1))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True

    p = tf_b.paragraphs[0]
    p.text = "PRINSIP DESAIN SISTEM (SEPARATION OF CONCERNS & SAFETY):"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SYSTEM

    arch_pts = [
        "Desentralisasi Sub-Agent: AI Orchestrator, Growth Engine, Media Engine, dan Publisher beroperasi secara modular diatur SQLite State Machine.",
        "Zero Human Overhead untuk Formatting: Whisper otomatis menghitung word-level timing, memotong subtitle menjadi 3 baris aman dari tutupan UI TikTok.",
        "Fail-Safe Security Gate: Konten tidak akan dipublikasikan tanpa adanya record persetujuan sah (APPROVED) di tabel approvals SQLite."
    ]
    for ap in arch_pts:
        p = tf_b.add_paragraph()
        p.text = "• " + ap
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_before = Pt(2)

    add_slide_footer(s5)

    # =========================================================================
    # SLIDE 6: MASALAH 1 - TIKTOK STUDIO DRAFTEDITOR LEAK
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s6, prs, ACCENT_ALERT)
    add_slide_header(s6, "// KENDALA OPERASIONAL 01", "Bug TikTok Studio: Filename Placeholder Leak",
                     "Desinkronisasi Virtual DOM React Mengakibatkan Nama File Menimpa Caption Naratif Video",
                     slide_index=6, total_slides=10, accent_color=ACCENT_ALERT)

    # Metric Badges Bar
    metrics_m1 = [
        ("STATUS: FIXED", "Telah Diperbaiki Live 9 & 10 Nov"),
        ("REACT COMPONENT", ".public-DraftEditor-content"),
        ("METODE BARU", "CDP Physical Keystroke Injection"),
        ("PRE-FLIGHT GUARD", "Validasi Teks Sebelum Upload")
    ]
    add_metric_bar(s6, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.72), metrics_m1, accent_color=ACCENT_ALERT)

    # 2 Big Cards: Root Cause (Red) vs Solution (Green)
    half_w = Inches(5.75)
    half_h = Inches(4.35)

    # Left Card: Root Cause
    add_cyber_card(s6, Inches(0.8), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_ALERT)
    tb_l = s6.shapes.add_textbox(Inches(1.05), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    p = tf_l.paragraphs[0]
    p.text = "DIAGNOSIS & AKAR MASALAH (ROOT CAUSE)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ALERT

    pts_m1_l = [
        ("Gejala Lapangan", "Video Dinda Kemala yang terbit 9 & 10 November menampilkan caption placeholder mentah seperti 'final_vlog_morning' atau 'final_vlog' tanpa narasi budaya/kuliner."),
        ("Komponen React", "TikTok Studio menggunakan React DraftEditor. Saat file diupload, TikTok menginjeksi nama file secara default ke editor state."),
        ("Kegagalan Manipulasi DOM", "Perintah 'document.execCommand(insertText)' atau manipulasi DOM langsung hanya mengubah tampilan visual browser, namun GAGAL memicu React synthetic events."),
        ("Dampak Payload", "Form submission TikTok membaca internal Virtual DOM state lama (nama file), sehingga narasi persetujuan hilang saat dipublikasikan.")
    ]
    for title, desc in pts_m1_l:
        p = tf_l.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    # Right Card: Technical Solution & Live Verification
    add_cyber_card(s6, Inches(6.783), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_SUCCESS)
    tb_r = s6.shapes.add_textbox(Inches(7.033), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.text = "SOLUSI TEKNIS & HASIL VERIFIKASI (RESOLVED)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SUCCESS

    pts_m1_r = [
        ("CDP Physical Keystroke", "Beralih ke simulasi keyboard nyata via Chrome DevTools Protocol (Input.dispatchKeyEvent / Input.insertText) untuk mengemulasikan ketukan pengguna asli."),
        ("Clearing & Typing", "Eksekusi Select All (Meta+A / Ctrl+A) -> Backspace fisik -> Pengetikan ulang narasi karakter per karakter secara bersih."),
        ("Synthetic isDirty Activation", "Pemicuan event sintetis focus, space, backspace, dan blur pada node editor sehingga tombol Simpan aktif (aria-disabled='false')."),
        ("Verifikasi Sukses Live", "Dua video terdampak berhasil diperbaiki di TikTok Studio: Video 10 Nov Pagi (Museum SMB II) dan Video 9 Nov Malam (Gulo Palu)."),
        ("Pre-Flight Guard", "Penambahan modul pembaca innerText editor sebelum klik simpan/post: proses langsung dibatalkan jika masih memuat teks '.mp4' atau 'final_vlog'.")
    ]
    for title, desc in pts_m1_r:
        p = tf_r.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(5)

    add_slide_footer(s6)

    # =========================================================================
    # SLIDE 7: MASALAH 2 - INKONSISTENSI LEMARI PAKAIAN AUTO-STYLIST
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s7, prs, ACCENT_ALERT)
    add_slide_header(s7, "// KENDALA OPERASIONAL 02", "Inkonsistensi Lemari Pakaian Auto-Stylist",
                     "Scraping OOTD Pinterest Tanpa Verifikasi Foto Fisik Lokal Mengakibatkan Inkonsistensi Visual",
                     slide_index=7, total_slides=10, accent_color=ACCENT_ALERT)

    # Metric Badges Bar
    metrics_m2 = [
        ("STATUS: RESOLVED", "Guard Aktif di 3 Modul Script"),
        ("ASSET FORMAT", "Wajib 9:16 Vertical HD Busana"),
        ("DEFAULT STATUS", "Kini Ditetapkan 'Incomplete'"),
        ("INTEGRITY CHECK", "os.path.isfile Enforcement")
    ]
    add_metric_bar(s7, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.72), metrics_m2, accent_color=ACCENT_ALERT)

    # Left Card: Akar Masalah Scraping
    add_cyber_card(s7, Inches(0.8), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_ALERT)
    tb_l7 = s7.shapes.add_textbox(Inches(1.05), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_l7 = tb_l7.text_frame
    tf_l7.word_wrap = True

    p = tf_l7.paragraphs[0]
    p.text = "DIAGNOSIS & AKAR MASALAH (ROOT CAUSE)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ALERT

    pts_m2_l = [
        ("Gejala di Video", "Karakter Dinda kadang tampil dengan busana yang tidak konsisten atau berubah model antar adegan, mengurangi koherensi persona kreator."),
        ("Bug daily_pinterest_wardrobe_job.js", "Skrip otomatis merayapi Pinterest dan langsung menandai record busana baru sebagai status='active' di database character_wardrobe."),
        ("File Fisik Belum Terunduh", "URL Pinterest sering memiliki token CDN sementara yang cepat kedaluwarsa, sementara berkas gambar fisik lokal di /characters/dinda/wardrobe/ belum diunduh."),
        ("Silent Fallback", "Saat engine Google Flow mencari file gambar dan gagal menemukannya, pipeline melakukan fallback diam-diam ke prompt teks generik tanpa panduan visual OOTD.")
    ]
    for title, desc in pts_m2_l:
        p = tf_l7.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    # Right Card: Solusi & SOP Standarisasi
    add_cyber_card(s7, Inches(6.783), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_SUCCESS)
    tb_r7 = s7.shapes.add_textbox(Inches(7.033), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_r7 = tb_r7.text_frame
    tf_r7.word_wrap = True

    p = tf_r7.paragraphs[0]
    p.text = "PERBAIKAN YANG DIIMPLEMENTASIKAN (FIXED)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SUCCESS

    pts_m2_r = [
        ("Default Status 'Incomplete'", "Skrip crawling kini secara default menetapkan status busana baru sebagai 'incomplete' hingga file gambar terbukti tersimpan secara lokal."),
        ("Pemeriksaan os.path.isfile()", "Pada 'scripts/wardrobe_upsert.py', status hanya dapat dinaikkan menjadi 'active' jika file foto fisik lolos uji keberadaan di disk lokal."),
        ("Guard Pemilihan Konten", "Modul 'wardrobe_manager.py' dan 'generate_content_options.py' difilter ketat: hanya outfit dengan aset fisik terverifikasi yang dapat diajukan ke Google Flow."),
        ("Standarisasi Aset OOTD", "Setiap foto busana wajib memiliki rasio vertikal 9:16 (min 1080x1920), hijab rapi, dan checksum SHA-256 tercatat dalam ledger produksi."),
        ("Rotasi Outfit Cerdas", "Algoritma mencegah pemilihan outfit yang sama dalam kurun 5 hari terakhir untuk mempertahankan variasi visual yang segar bagi penonton.")
    ]
    for title, desc in pts_m2_r:
        p = tf_r7.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(5)

    add_slide_footer(s7)

    # =========================================================================
    # SLIDE 8: MASALAH 3 - LIMITASI PLATFORM TIKTOK & DOUBLE HASHTAG
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s8, prs, ACCENT_ALERT)
    add_slide_header(s8, "// KENDALA OPERASIONAL 03", "Limitasi Kebijakan TikTok & Sanitasi Tag",
                     "Batas Edit Caption 1x/24 Jam, Kedaluwarsa 7 Hari, dan Penanganan Spam Double Hashtag",
                     slide_index=8, total_slides=10, accent_color=ACCENT_ALERT)

    # Metric Callout Bar
    metrics_m3 = [
        ("1x / 24 JAM", "Batas Pengubahan Caption TikTok"),
        ("7 HARI", "Maksimal Window Edit Pasca-Publish"),
        ("0% SPAM", "Filter Regex Deduplikasi Tag"),
        ("ZERO-DEFECT", "Filosofi Upload Pertama Sempurna")
    ]
    add_metric_bar(s8, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.72), metrics_m3, accent_color=ACCENT_ALERT)

    # Left Card: Kebijakan TikTok
    add_cyber_card(s8, Inches(0.8), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_ALERT)
    tb_l8 = s8.shapes.add_textbox(Inches(1.05), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_l8 = tb_l8.text_frame
    tf_l8.word_wrap = True

    p = tf_l8.paragraphs[0]
    p.text = "REGULASI KETAT PLATFORM TIKTOK STUDIO"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_ALERT

    pts_m3_l = [
        ("Batas Edit 1 Kali per 24 Jam", "TikTok menerapkan aturan keras: deskripsi video hanya dapat disunting 1 kali dalam 24 jam. Percobaan edit kedua langsung ditolak dengan pesan 'Something went wrong. Please try again'."),
        ("Jendela Waktu 7 Hari", "Fitur 'Edit post' di TikTok Studio hanya aktif pada video berusia < 7 hari. Setelah melewati hari ke-7, tombol edit dikunci permanen oleh TikTok."),
        ("Risiko Patching Pasca-Upload", "Mengandalkan perbaikan caption setelah video tayang memiliki tingkat risiko kegagalan tinggi jika kuota harian video tersebut telah terpakai."),
        ("Konsekuensi Desain", "Sistem TIDAK BOLEH mengandalkan skrip perbaikan belakangan (post-publishing patch). Caption wajib 100% sempurna saat pengunggahan pertama.")
    ]
    for title, desc in pts_m3_l:
        p = tf_l8.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    # Right Card: Double Hashtag & Sanitizer
    add_cyber_card(s8, Inches(6.783), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_SUCCESS)
    tb_r8 = s8.shapes.add_textbox(Inches(7.033), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_r8 = tb_r8.text_frame
    tf_r8.word_wrap = True

    p = tf_r8.paragraphs[0]
    p.text = "ARTEFAK DOUBLE HASHTAG & SOLUSI SANITASI"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SUCCESS

    pts_m3_r = [
        ("Artefak Video Tanggal 7-8 Nov", "Pada sejumlah postingan lawas ditemukan penumpukan hashtag ganda di akhir caption (contoh: '#fyp #palembang #kuliner #fyp #palembang')."),
        ("Penyebab Skrip Lama", "Skrip pembuatan naskah lama menambahkan daftar hashtag bawaan, kemudian modul uploader menambahkan hashtag cadangan lagi tanpa pemeriksaan duplikasi."),
        ("Bahaya Penalti Algoritma FYP", "Penumpukan tag berulang dibaca sebagai perilaku spam oleh sistem moderasi TikTok dan dapat menurunkan rekomendasi video di halaman For You (FYP)."),
        ("Implementasi Regex Deduplicator", "Penambahan fungsi pembersih teks otomatis: memisahkan seluruh hashtag, menyaring nilai unik secara berurutan, dan membatasi maksimal 3-5 hashtag resmi."),
        ("Audit Riwayat di SQLite", "Pencatatan status publikasi dan hash caption ke SQLite untuk mencegah pemicuan ulang postingan yang sudah tervalidasi.")
    ]
    for title, desc in pts_m3_r:
        p = tf_r8.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(5)

    add_slide_footer(s8)

    # =========================================================================
    # SLIDE 9: MASALAH 4 & 5 - RESOURCE LIMITS & TELEGRAM ACC
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s9, prs, ACCENT_SYSTEM)
    add_slide_header(s9, "// KENDALA OPERASIONAL 04 & 05", "Manajemen Kredit Google Flow & Gatekeeping Telegram",
                     "Efisiensi Kredit Komputasi Generatif dan Penanganan Antrean Human-in-the-Loop",
                     slide_index=9, total_slides=10, accent_color=ACCENT_SYSTEM)

    # Metric Callout Bar
    metrics_m4 = [
        ("~30 KREDIT", "Biaya Komputasi per Video 10s"),
        ("5-10 MENIT", "Latensi Render Cloud Google"),
        ("2 JAM", "Jendela Konfirmasi ACC Telegram"),
        ("BUFFER 50", "Ambang Batas Keamanan Kredit")
    ]
    add_metric_bar(s9, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.72), metrics_m4, accent_color=ACCENT_SYSTEM)

    # Left Card: Google Flow Limits
    add_cyber_card(s9, Inches(0.8), Inches(2.6), half_w, half_h, accent_stripe_color=ACCENT_PURPLE)
    tb_l9 = s9.shapes.add_textbox(Inches(1.05), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_l9 = tb_l9.text_frame
    tf_l9.word_wrap = True

    p = tf_l9.paragraphs[0]
    p.text = "KONSUMSI KREDIT & LATENSI GOOGLE FLOW"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_PURPLE

    pts_m4_l = [
        ("Biaya Komputasi Tinggi", "Google Flow Omni 1.2 Flash menghabiskan ~30 kredit per video 10 detik. Percobaan multi-take atau render gagal dapat menguras kuota harian akun."),
        ("Fluktuasi Latensi Render", "Waktu antrean komputasi di cloud Google bervariasi antara 3 hingga 10 menit. Jika automasi browser mengalami timeout, pipeline berisiko terhenti (hang)."),
        ("Two-Phase Commit Ledger", "Pencatatan kredit menggunakan model reservasi kuota terlebih dahulu, dan pemotongan saldo baru dikonfirmasi saat file MP4 tervalidasi utuh di disk."),
        ("Credit Ceiling Safeguard", "Sistem secara otomatis menolak permintaan generasi video baru jika saldo kredit harian tersisa kurang dari 50 kredit untuk mencegah kegagalan di tengah jalan.")
    ]
    for title, desc in pts_m4_l:
        p = tf_l9.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    # Right Card: Telegram Gatekeeper
    add_cyber_card(s9, Inches(6.783), Inches(2.6), half_w, half_h, accent_stripe_color=RGBColor(13, 148, 136))
    tb_r9 = s9.shapes.add_textbox(Inches(7.033), Inches(2.75), half_w - Inches(0.5), half_h - Inches(0.3))
    tf_r9 = tb_r9.text_frame
    tf_r9.word_wrap = True

    p = tf_r9.paragraphs[0]
    p.text = "BOTTLENECK TIME-LOCK TELEGRAM GATEKEEPER"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(13, 148, 136)

    pts_m4_r = [
        ("Jendela Waktu Tunggu 2 Jam", "Demi keamanan brand, video hanya dipublikasikan jika status 'APPROVED' tercatat dalam tabel approvals sebelum slot tayang tiba (06:00 - 08:00 WIB)."),
        ("Resiko Unresponsive Owner", "Jika owner berhalangan merespons tepat waktu, sistem menahan konten di antrean demi mencegah terbitnya konten yang belum disetujui."),
        ("Potensi Antrean Menumpuk", "Konten yang tertahan berpotensi bertabrakan dengan jadwal produksi video siklus berikutnya jika tidak dikelola secara dinamis."),
        ("Solusi Adaptive Rescheduling", "Jika batas waktu 2 jam kedaluwarsa tanpa respons, video dipindahkan secara otomatis ke slot malam (19:00 WIB) tanpa memicu render ulang yang memboroskan kredit.")
    ]
    for title, desc in pts_m4_r:
        p = tf_r9.add_paragraph()
        p.text = f"• {title}: "
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        r = p.add_run()
        r.text = desc
        r.font.name = FONT_BODY
        r.font.size = Pt(9)
        r.font.bold = False
        r.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    add_slide_footer(s9)

    # =========================================================================
    # SLIDE 10: RENCANA AKSI & MONITORING BERKELANJUTAN
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_cyber_background(s10, prs, ACCENT_SUCCESS)
    add_slide_header(s10, "// STRATEGI & ROADMAP EKSEKUTIF", "Rencana Aksi Berkelanjutan & Pusat Kontrol 3D",
                     "Roadmap Mitigasi P0-P2 dan Pemantauan Operasional Real-Time via Virtual Office 3D HQ",
                     slide_index=10, total_slides=10, accent_color=ACCENT_SUCCESS)

    # 3 Priority Columns (P0, P1, P2)
    col_w = Inches(3.7)
    gap = Inches(0.28)
    top_col = Inches(1.65)
    h_col = Inches(4.05)

    priorities = [
        ("PRIORITAS P0 (IMMEDIATE)", "Pencegahan Bug Kritis", ACCENT_ALERT, [
            "Terapkan Pre-Flight Verification Guard pada seluruh skrip uploader CDP sebelum submit.",
            "Validasi fisik os.path.isfile() pada setiap entri busana di character_wardrobe.",
            "Enforce hard-guard subtitle kinetik kuning ASS MarginV=850 pada pipeline video ISK.",
            "Semua test runner suite (59 tests) wajib lulus 100% sebelum cron job dieksekusi."
        ]),
        ("PRIORITAS P1 (SHORT-TERM)", "Optimasi & Automasi", ACCENT_ISK, [
            "Otomatisasi pengunduhan gambar fisik Pinterest saat crawling OOTD berjalan.",
            "Sinkronisasi kuota Google Flow dengan single-ledger alerts jika sisa < 50 kredit.",
            "Fitur Quick ACC di Telegram (Inline Keyboard: 'Setujui', 'Revisi', 'Tunda').",
            "Penyempurnaan timing MarginV=850 hardsub ASS pada video uji lapangan ISK."
        ]),
        ("PRIORITAS P2 (MEDIUM-TERM)", "Skalabilitas Ekosistem", ACCENT_SYSTEM, [
            "Multi-account load balancing untuk Google Flow (rotasi token aman).",
            "Peningkatan interaksi otomatis komentar TikTok dengan NLP konteks lokal.",
            "Integrasi live dashboard analitik retensi penonton dari TikTok Studio ke SQLite.",
            "Ekspansi pipeline ke akun cabang dan platform short-video lain (Reels/Shorts)."
        ])
    ]

    for idx, (p_title, p_sub, col_accent, tasks) in enumerate(priorities):
        x = Inches(0.8) + idx * (col_w + gap)
        add_cyber_card(s10, x, top_col, col_w, h_col, accent_stripe_color=col_accent)

        tb = s10.shapes.add_textbox(x + Inches(0.18), top_col + Inches(0.18), col_w - Inches(0.36), h_col - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = p_title
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col_accent

        p_subt = tf.add_paragraph()
        p_subt.text = p_sub
        p_subt.font.name = FONT_BODY
        p_subt.font.size = Pt(9)
        p_subt.font.bold = True
        p_subt.font.color.rgb = COLOR_TEXT_MUTED
        p_subt.space_before = Pt(2)

        for t in tasks:
            pt = tf.add_paragraph()
            pt.text = "• " + t
            pt.font.name = FONT_BODY
            pt.font.size = Pt(9.5)
            pt.font.color.rgb = COLOR_TEXT_SECONDARY
            pt.space_before = Pt(6)

    # Bottom Dashboard Banner
    add_cyber_card(s10, Inches(0.8), Inches(5.85), Inches(11.733), Inches(1.1), accent_stripe_color=ACCENT_SYSTEM)
    tb_dash = s10.shapes.add_textbox(Inches(1.05), Inches(5.95), Inches(11.233), Inches(0.9))
    tf_dash = tb_dash.text_frame
    tf_dash.word_wrap = True

    p = tf_dash.paragraphs[0]
    p.text = "PUSAT PEMANTAUAN VIRTUAL OFFICE 3D CYBER HQ"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_SYSTEM

    p_d = tf_dash.add_paragraph()
    p_d.text = "Seluruh aktivitas agen, jadwal cron aktif (07:00 & 19:00 WIB Dinda, 09:00 & 12:00 WIB ISK), antrean Telegram, dan health check worker dipantau secara real-time melalui antarmuka 3D Virtual Office di https://kantor-ai-intan.vercel.app (Lounge 3D & Studio Mode)."
    p_d.font.name = FONT_BODY
    p_d.font.size = Pt(9)
    p_d.font.color.rgb = COLOR_TEXT_MUTED
    p_d.space_before = Pt(3)

    add_slide_footer(s10)

    # Save Presentation
    os.makedirs(DOCS_DIR, exist_ok=True)
    prs.save(OUTPUT_PPTX)
    print(f"Upgraded thematic presentation generated successfully at: {OUTPUT_PPTX}")
    return OUTPUT_PPTX


if __name__ == "__main__":
    out = build_deck()
    print("Done! File:", out)

