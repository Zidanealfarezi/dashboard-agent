#!/usr/bin/env python3
"""
Generate KLYRO-Style Presentation with 100% Guaranteed Image Loading & 3D Office Photo
Outputs:
1. AI_INFLUENCER_END_TO_END_PRESENTATION.pptx (Embedded photos in PowerPoint)
2. index.html (Self-contained HTML deck with Base64 embedded images)
"""
import os
import sys
import base64
from pathlib import Path
from PIL import Image
import pptx
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

PROJECT_DIR = Path("/Users/zidane/Documents/ChatGPT/AI INFLUENCER")
OUTPUT_DIR = PROJECT_DIR / "output" / "presentation"
ASSETS_DIR = OUTPUT_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

PPTX_PATH = OUTPUT_DIR / "AI_INFLUENCER_END_TO_END_PRESENTATION.pptx"
HTML_PATH = OUTPUT_DIR / "index.html"

# Color Palette Constants (Exact Match to KLYRO Template)
LIME = RGBColor(162, 232, 48)       # #A2E830 Vibrant Acid Lime
DEEP_TEAL = RGBColor(7, 45, 51)     # #072D33 Deep Petrol Teal
MID_TEAL = RGBColor(16, 71, 80)     # #104750 Medium Petrol Teal
WHITE = RGBColor(255, 255, 255)     # #FFFFFF Pure White
LIGHT_BG = RGBColor(245, 248, 245)  # #F5F8F5 Off-White
BORDER_GRAY = RGBColor(205, 218, 208) # #CDDAD0 Subtle Border

def get_base64_img(file_path):
    """Converts an image file to Base64 data URL so it never fails to load."""
    p = Path(file_path)
    if not p.exists():
        return ""
    suffix = p.suffix.lower().replace(".", "")
    mime = "image/png" if suffix == "png" else "image/jpeg"
    with open(p, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"

def set_slide_background(slide, prs, color):
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = color
    bg_shape.line.color.rgb = color
    return bg_shape

def add_header_pill(slide, slide_num_str, dark_bg=False, lime_bg=False):
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.35), Inches(11.733), Inches(0.42))
    pill.fill.solid()
    if dark_bg:
        pill.fill.fore_color.rgb = DEEP_TEAL
        pill.line.color.rgb = MID_TEAL
    elif lime_bg:
        pill.fill.fore_color.rgb = LIME
        pill.line.color.rgb = DEEP_TEAL
    else:
        pill.fill.fore_color.rgb = WHITE
        pill.line.color.rgb = BORDER_GRAY
    pill.line.width = Pt(1)

    tf = pill.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)

    p = tf.paragraphs[0]
    p.text = ""

    r1 = p.add_run()
    r1.text = "●  AI INFLUENCER"
    r1.font.name = "Arial"
    r1.font.size = Pt(9.5)
    r1.font.bold = True
    r1.font.color.rgb = WHITE if dark_bg else DEEP_TEAL

    r_space = p.add_run()
    r_space.text = "                                                         "
    r_space.font.size = Pt(9)

    r2 = p.add_run()
    r2.text = "PRESENTATION"
    r2.font.name = "Arial"
    r2.font.size = Pt(8.5)
    r2.font.bold = True
    r2.font.color.rgb = LIME if dark_bg else (DEEP_TEAL if lime_bg else MID_TEAL)

    r_space2 = p.add_run()
    r_space2.text = "                                                         "
    r_space2.font.size = Pt(9)

    r3 = p.add_run()
    r3.text = f"/{slide_num_str}"
    r3.font.name = "Arial"
    r3.font.size = Pt(9.5)
    r3.font.bold = True
    r3.font.color.rgb = WHITE if dark_bg else DEEP_TEAL

def add_rounded_card(slide, left, top, width, height, bg_color=WHITE, border_color=BORDER_GRAY):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card

def add_bullet_point(tf, bold_prefix, text, pt_size=9.5, font_color=DEEP_TEAL):
    p = tf.add_paragraph()
    p.space_before = Pt(3)
    p.space_after = Pt(3)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix + (" " if bold_prefix else "")
    r1.font.bold = True
    r1.font.name = "Arial"
    r1.font.size = Pt(pt_size)
    r1.font.color.rgb = font_color
    
    r2 = p.add_run()
    r2.text = text
    r2.font.bold = False
    r2.font.name = "Arial"
    r2.font.size = Pt(pt_size)
    r2.font.color.rgb = font_color

def build_klyro_pptx():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Assets
    dinda_img = ASSETS_DIR / "dinda.jpg"
    nara_img = ASSETS_DIR / "nara.jpg"
    rania_img = ASSETS_DIR / "rania.jpg"
    f1_img = ASSETS_DIR / "frame-1.jpg"
    f2_img = ASSETS_DIR / "frame-2.jpg"
    f3_img = ASSETS_DIR / "frame-3.jpg"
    office_img = ASSETS_DIR / "office_3d.png"

    # =========================================================================
    # SLIDE 1: Cover Slide (/01)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, prs, LIGHT_BG)
    add_header_pill(s1, "01")

    stripe = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.1), Inches(13.333), Inches(0.4))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = LIME
    stripe.line.fill.background()

    tb_left = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(6.8), Inches(4.5))
    tf1 = tb_left.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "AI CREATIVE"
    p0.font.name = "Impact"
    p0.font.size = Pt(56)
    p0.font.color.rgb = DEEP_TEAL

    p1 = tf1.add_paragraph()
    r_star = p1.add_run()
    r_star.text = "✤ "
    r_star.font.size = Pt(52)
    r_star.font.color.rgb = LIME
    r_ag = p1.add_run()
    r_ag.text = "AGENCY"
    r_ag.font.name = "Impact"
    r_ag.font.size = Pt(56)
    r_ag.font.color.rgb = DEEP_TEAL
    p1.space_after = Pt(16)

    p2 = tf1.add_paragraph()
    p2.text = "Autonomous virtual influencer pipeline that fuels continuous storytelling, high-fidelity generation, and full creative control."
    p2.font.name = "Arial"
    p2.font.size = Pt(13)
    p2.font.color.rgb = MID_TEAL
    p2.space_after = Pt(24)

    p3 = tf1.add_paragraph()
    p3.text = "⚡ DEEPSEEK FLASH  |  🎬 GOOGLE FLOW (OMNI 1.1)  |  🔒 TELEGRAM APPROVAL BOT"
    p3.font.name = "Arial"
    p3.font.size = Pt(10)
    p3.font.bold = True
    p3.font.color.rgb = DEEP_TEAL

    # Arch Card with Dinda Photo
    add_rounded_card(s1, Inches(8.3), Inches(1.3), Inches(4.2), Inches(5.5), bg_color=WHITE, border_color=BORDER_GRAY)
    if dinda_img.exists():
        s1.shapes.add_picture(str(dinda_img), Inches(8.5), Inches(1.5), width=Inches(3.8), height=Inches(5.1))

    # =========================================================================
    # SLIDE 2: Lime Quote Slide (/02)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, prs, LIME)
    add_header_pill(s2, "02", lime_bg=True)

    tb_prop = s2.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(2.5), Inches(2.5))
    tf_pr = tb_prop.text_frame
    p_pr = tf_pr.paragraphs[0]
    p_pr.text = "✤"
    p_pr.font.size = Pt(110)
    p_pr.font.color.rgb = DEEP_TEAL

    tb_quote = s2.shapes.add_textbox(Inches(3.8), Inches(1.8), Inches(8.5), Inches(4.8))
    tf_q = tb_quote.text_frame
    tf_q.word_wrap = True

    for txt in ["AUTONOMY AND —", "CONSISTENCY ARE THE", "SPARK THAT FUELS", "VIRTUAL TALENTS"]:
        p = tf_q.add_paragraph() if tf_q.paragraphs[0].text else tf_q.paragraphs[0]
        p.text = txt
        p.font.name = "Impact"
        p.font.size = Pt(46)
        p.font.color.rgb = DEEP_TEAL
        p.space_after = Pt(4)

    pq5 = tf_q.add_paragraph()
    pq5.text = "Mengubah beban pembuatan konten harian menjadi ekosistem cerdas: Riset Tren otomatis → Generasi video Google Flow → QA Otomatis → Review Telegram."
    pq5.font.name = "Arial"
    pq5.font.size = Pt(13)
    pq5.font.color.rgb = DEEP_TEAL
    pq5.space_before = Pt(14)

    # =========================================================================
    # SLIDE 3: Statement (/03)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, prs, DEEP_TEAL)
    add_header_pill(s3, "03", dark_bg=True)

    tb_teal = s3.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(11.0), Inches(5.0))
    tf_t = tb_teal.text_frame
    tf_t.word_wrap = True

    for txt in ["THE STRENGTH OF", "MULTI-AGENT AI AND THE", "JOY OF VIRTUAL"]:
        p = tf_t.add_paragraph() if tf_t.paragraphs[0].text else tf_t.paragraphs[0]
        p.text = txt
        p.font.name = "Impact"
        p.font.size = Pt(56)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    pt4 = tf_t.add_paragraph()
    r_p1 = pt4.add_run()
    r_p1.text = "✤ "
    r_p1.font.size = Pt(52)
    r_p1.font.color.rgb = LIME
    r_tx = pt4.add_run()
    r_tx.text = "STORYTELLING"
    r_tx.font.name = "Impact"
    r_tx.font.size = Pt(56)
    r_tx.font.color.rgb = LIME
    r_p2 = pt4.add_run()
    r_p2.text = " ✤"
    r_p2.font.size = Pt(52)
    r_p2.font.color.rgb = LIME
    pt4.alignment = PP_ALIGN.CENTER
    pt4.space_after = Pt(20)

    pt5 = tf_t.add_paragraph()
    pt5.text = "Dinda Kemala • Nara Adelia • Rania Meutia • Hermes Multi-Agent Framework"
    pt5.font.name = "Arial"
    pt5.font.size = Pt(13)
    pt5.font.color.rgb = LIME
    pt5.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 4: Team / 3 Talent Cards (/04)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, prs, LIGHT_BG)
    add_header_pill(s4, "04")

    talents = [
        ("DINDA KEMALA", "LIFESTYLE & PALEMBANG VLOG", dinda_img, WHITE, BORDER_GRAY, DEEP_TEAL, [
            ("Persona:", "Gadis hangat, berhijab santun Palembang."),
            ("Fokus:", "Kuliner pempek, outfit kasual, jalan-jalan."),
            ("Status:", "Pilot teknis 100% sukses hingga TikTok Studio.")
        ]),
        ("NARA ADELIA", "BEAUTY & OFFICE LOOK MEDAN", nara_img, LIME, DEEP_TEAL, DEEP_TEAL, [
            ("Persona:", "Modern, profesional, rambut panjang cokelat."),
            ("Fokus:", "Makeup tutorial, office look, keseharian di ISK."),
            ("Aturan:", "Pekerjaan sesuai profil resmi tanpa mengarang.")
        ]),
        ("RANIA MEUTIA", "WISATA & TEMPAT BAGUS ACEH", rania_img, WHITE, BORDER_GRAY, DEEP_TEAL, [
            ("Persona:", "Anggun, santun, ramah, berhijab syar'i modern."),
            ("Fokus:", "Wisata alam, pantai Sabang, hidden gems & kuliner Aceh."),
            ("Aturan:", "Rekomendasi tempat nyata, estetik & ramah wisata.")
        ])
    ]

    card_w = Inches(3.75)
    card_h = Inches(5.9)
    top_y = Inches(1.05)

    for i, (name, role, img_f, bg_col, bdr_col, text_col, bullets) in enumerate(talents):
        left_x = Inches(0.8) + i * Inches(3.95)
        add_rounded_card(s4, left_x, top_y, card_w, card_h, bg_color=bg_col, border_color=bdr_col)

        if img_f.exists():
            s4.shapes.add_picture(str(img_f), left_x + Inches(0.2), top_y + Inches(0.2), width=Inches(3.35), height=Inches(2.7))

        tb = s4.shapes.add_textbox(left_x + Inches(0.2), top_y + Inches(3.05), Inches(3.35), Inches(2.7))
        tf = tb.text_frame
        tf.word_wrap = True

        pn = tf.paragraphs[0]
        pn.text = name
        pn.font.name = "Impact"
        pn.font.size = Pt(17)
        pn.font.color.rgb = text_col
        pn.space_after = Pt(4)

        pr = tf.add_paragraph()
        pr.text = f"{role}  ●"
        pr.font.name = "Arial"
        pr.font.size = Pt(8.5)
        pr.font.bold = True
        pr.font.color.rgb = DEEP_TEAL if bg_col == LIME else MID_TEAL
        pr.space_after = Pt(10)

        for bk, bv in bullets:
            add_bullet_point(tf, bk, bv, pt_size=8.8, font_color=text_col)

    # =========================================================================
    # SLIDE 5: 4 Architecture Pillars (/05)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, prs, DEEP_TEAL)
    add_header_pill(s5, "05", dark_bg=True)

    tb_top5 = s5.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.733), Inches(1.3))
    tf5 = tb_top5.text_frame
    tf5.word_wrap = True

    p5_0 = tf5.paragraphs[0]
    r_ic = p5_0.add_run()
    r_ic.text = "✤  "
    r_ic.font.size = Pt(26)
    r_ic.font.color.rgb = LIME
    r_t5 = p5_0.add_run()
    r_t5.text = "WE CREATE IMPACTFUL CONTENT WITH AUTONOMOUS PIPELINE"
    r_t5.font.name = "Impact"
    r_t5.font.size = Pt(24)
    r_t5.font.color.rgb = WHITE

    cards5 = [
        ("01. TREND RESEARCH", "Pencarian audio tren TikTok & topik viral dengan validasi minimal 2 sumber kredibel."),
        ("02. FLOW GENERATION", "Model Google Flow Omni 1.1 Flash 720p vertikal 9:16 durasi native 6 detik."),
        ("03. LOCAL FFMPEG QA", "Normalisasi MP4, ekstraksi frame 0.25s, 2.75s, 5.5s, dan penguncian hash SHA-256."),
        ("04. TELEGRAM APPROVAL", "Pengiriman video review interaktif dengan tombol ACC sebelum disimpan ke SQLite.")
    ]

    c5_w = Inches(2.78)
    c5_h = Inches(4.5)
    c5_top = Inches(2.4)

    for i, (c_title, c_desc) in enumerate(cards5):
        left_c = Inches(0.8) + i * Inches(2.95)
        add_rounded_card(s5, left_c, c5_top, c5_w, c5_h, bg_color=WHITE, border_color=None)

        tb_c = s5.shapes.add_textbox(left_c + Inches(0.2), c5_top + Inches(0.3), c5_w - Inches(0.4), c5_h - Inches(0.6))
        tfc = tb_c.text_frame
        tfc.word_wrap = True

        pc_0 = tfc.paragraphs[0]
        pc_0.text = "✤"
        pc_0.font.size = Pt(28)
        pc_0.font.color.rgb = DEEP_TEAL
        pc_0.space_after = Pt(8)

        pc_1 = tfc.add_paragraph()
        pc_1.text = c_title
        pc_1.font.name = "Impact"
        pc_1.font.size = Pt(13)
        pc_1.font.color.rgb = DEEP_TEAL
        pc_1.space_after = Pt(12)

        pc_2 = tfc.add_paragraph()
        pc_2.text = c_desc
        pc_2.font.name = "Arial"
        pc_2.font.size = Pt(10)
        pc_2.font.color.rgb = MID_TEAL

    # =========================================================================
    # SLIDE 6: Principles (/06)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, prs, LIME)
    add_header_pill(s6, "06", lime_bg=True)

    cpill = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.0), Inches(0.95), Inches(3.333), Inches(0.45))
    cpill.fill.solid()
    cpill.fill.fore_color.rgb = WHITE
    cpill.line.color.rgb = DEEP_TEAL
    cpill.line.width = Pt(1.5)
    tf_cp = cpill.text_frame
    p_cp = tf_cp.paragraphs[0]
    p_cp.text = "OUR PRINCIPLE"
    p_cp.font.name = "Impact"
    p_cp.font.size = Pt(14)
    p_cp.font.color.rgb = DEEP_TEAL
    p_cp.alignment = PP_ALIGN.CENTER

    principles = [
        ("PROJECT MANAGER", DEEP_TEAL, WHITE, LIME, "Mengatur dapur produksi pada board Kanban, mereview draf caption & mengawasi pagu kredit Flow."),
        ("GROUNDED RESEARCH", WHITE, DEEP_TEAL, DEEP_TEAL, "Riset tren & sound wajib menyertakan bukti 2 URL sumber kredibel; pisahkan fakta dari asumsi."),
        ("CONSISTENCY FIRST", DEEP_TEAL, WHITE, LIME, "33 foto master dikunci dengan hash SHA-256; identitas karakter tetap konsisten antar konten."),
        ("HUMAN APPROVAL", WHITE, DEEP_TEAL, DEEP_TEAL, "Persetujuan Telegram wajib sebelum publikasi; tidak ada auto-posting publik tanpa izin.")
    ]

    pr_w = Inches(2.78)
    pr_h = Inches(5.2)
    pr_top = Inches(1.6)

    for i, (pr_title, bg_c, txt_c, prop_c, pr_desc) in enumerate(principles):
        pr_left = Inches(0.8) + i * Inches(2.95)
        add_rounded_card(s6, pr_left, pr_top, pr_w, pr_h, bg_color=bg_c, border_color=DEEP_TEAL)

        tb_pr = s6.shapes.add_textbox(pr_left + Inches(0.2), pr_top + Inches(0.25), pr_w - Inches(0.4), pr_h - Inches(0.5))
        tf_pr = tb_pr.text_frame
        tf_pr.word_wrap = True

        p_ic = tf_pr.paragraphs[0]
        p_ic.text = "✤"
        p_ic.font.size = Pt(28)
        p_ic.font.color.rgb = prop_c
        p_ic.space_after = Pt(12)

        p_t = tf_pr.add_paragraph()
        p_t.text = pr_title
        p_t.font.name = "Impact"
        p_t.font.size = Pt(14)
        p_t.font.color.rgb = txt_c
        p_t.space_after = Pt(14)

        p_d = tf_pr.add_paragraph()
        p_d.text = pr_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = txt_c

    # =========================================================================
    # SLIDE 7: Metrics (/07)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, prs, LIME)
    add_header_pill(s7, "07", lime_bg=True)

    tb_head7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(5.5), Inches(4.5))
    tf7 = tb_head7.text_frame
    tf7.word_wrap = True

    p7_1 = tf7.paragraphs[0]
    p7_1.text = "TRUSTED RESULTS"
    p7_1.font.name = "Impact"
    p7_1.font.size = Pt(40)
    p7_1.font.color.rgb = DEEP_TEAL

    p7_2 = tf7.add_paragraph()
    r_p7 = p7_2.add_run()
    r_p7.text = "PROVEN BY ✤ PILOT"
    r_p7.font.name = "Impact"
    r_p7.font.size = Pt(40)
    r_p7.font.color.rgb = DEEP_TEAL
    p7_2.space_after = Pt(14)

    p7_3 = tf7.add_paragraph()
    p7_3.text = "Hasil eksekusi pilot terkontrol Dinda Kemala (5 November 2026) membuktikan seluruh alur berfungsi penuh dari prompt hingga TikTok Studio."
    p7_3.font.name = "Arial"
    p7_3.font.size = Pt(12)
    p7_3.font.color.rgb = DEEP_TEAL

    # Blocks
    add_rounded_card(s7, Inches(6.6), Inches(4.2), Inches(1.8), Inches(2.7), bg_color=WHITE, border_color=DEEP_TEAL)
    tb_b1 = s7.shapes.add_textbox(Inches(6.7), Inches(4.3), Inches(1.6), Inches(2.4))
    tf_b1 = tb_b1.text_frame
    tf_b1.paragraphs[0].text = "10"
    tf_b1.paragraphs[0].font.name = "Impact"
    tf_b1.paragraphs[0].font.size = Pt(38)
    tf_b1.paragraphs[0].font.color.rgb = DEEP_TEAL
    p_b1_l = tf_b1.add_paragraph()
    p_b1_l.text = "Kredit Flow"
    p_b1_l.font.name = "Arial"
    p_b1_l.font.size = Pt(10)
    p_b1_l.font.bold = True
    p_b1_l.font.color.rgb = MID_TEAL

    add_rounded_card(s7, Inches(8.6), Inches(3.2), Inches(1.8), Inches(3.7), bg_color=DEEP_TEAL, border_color=None)
    tb_b2 = s7.shapes.add_textbox(Inches(8.7), Inches(3.3), Inches(1.6), Inches(3.4))
    tf_b2 = tb_b2.text_frame
    tf_b2.paragraphs[0].text = "6s"
    tf_b2.paragraphs[0].font.name = "Impact"
    tf_b2.paragraphs[0].font.size = Pt(38)
    tf_b2.paragraphs[0].font.color.rgb = LIME
    p_b2_l = tf_b2.add_paragraph()
    p_b2_l.text = "Video 720p\n180 Frame"
    p_b2_l.font.name = "Arial"
    p_b2_l.font.size = Pt(10)
    p_b2_l.font.bold = True
    p_b2_l.font.color.rgb = WHITE

    add_rounded_card(s7, Inches(10.6), Inches(1.8), Inches(2.0), Inches(5.1), bg_color=WHITE, border_color=DEEP_TEAL)
    tb_b3 = s7.shapes.add_textbox(Inches(10.7), Inches(2.0), Inches(1.8), Inches(4.7))
    tf_b3 = tb_b3.text_frame
    tf_b3.paragraphs[0].text = "100%"
    tf_b3.paragraphs[0].font.name = "Impact"
    tf_b3.paragraphs[0].font.size = Pt(36)
    tf_b3.paragraphs[0].font.color.rgb = DEEP_TEAL
    p_b3_l = tf_b3.add_paragraph()
    p_b3_l.text = "Telegram ACC\n& TikTok Draft"
    p_b3_l.font.name = "Arial"
    p_b3_l.font.size = Pt(10)
    p_b3_l.font.bold = True
    p_b3_l.font.color.rgb = MID_TEAL

    # =========================================================================
    # SLIDE 8: Visual QA - 3 Frames (/08)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, prs, LIGHT_BG)
    add_header_pill(s8, "08")

    tb_t8 = s8.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.733), Inches(0.8))
    tf8 = tb_t8.text_frame
    p8 = tf8.paragraphs[0]
    p8.text = "VISUAL QUALITY CONTROL ✤ INSPECTION"
    p8.font.name = "Impact"
    p8.font.size = Pt(24)
    p8.font.color.rgb = DEEP_TEAL

    f_cards = [
        ("FRAME 1 (DETIK 0.25)", f1_img, [
            ("Inspeksi Wajah:", "Menghadap kamera, hijab rapi."),
            ("Pencahayaan:", "Natural soft light tanpa distorsi."),
            ("Aksesoris:", "Pendant/kalung terdeteksi sesuai master.")
        ]),
        ("FRAME 2 (DETIK 2.75)", f2_img, [
            ("Inspeksi Tengah:", "Gerakan alami, mata & bibir stabil."),
            ("Tekstur Kulit:", "Tekstur matte alami tanpa glossy AI."),
            ("Konsistensi Busana:", "Lipatan baju konsisten.")
        ]),
        ("FRAME 3 (DETIK 5.50)", f3_img, [
            ("Inspeksi Akhir:", "Transisi senyum konsisten."),
            ("Background:", "Latar belakang stabil tanpa warping."),
            ("Container Check:", "Video berakhir mulus 180 frame.")
        ])
    ]

    for i, (f_title, f_f, f_bullets) in enumerate(f_cards):
        f_left = Inches(0.8) + i * Inches(3.95)
        add_rounded_card(s8, f_left, Inches(1.75), Inches(3.75), Inches(5.1), bg_color=WHITE, border_color=BORDER_GRAY)

        if f_f.exists():
            s8.shapes.add_picture(str(f_f), f_left + Inches(0.2), Inches(1.95), width=Inches(3.35), height=Inches(2.5))

        tb_fc = s8.shapes.add_textbox(f_left + Inches(0.2), Inches(4.55), Inches(3.35), Inches(2.2))
        tff = tb_fc.text_frame
        tff.word_wrap = True

        p_ft = tff.paragraphs[0]
        p_ft.text = f_title
        p_ft.font.name = "Impact"
        p_ft.font.size = Pt(11)
        p_ft.font.color.rgb = DEEP_TEAL
        p_ft.space_after = Pt(4)

        for bk, bv in f_bullets:
            add_bullet_point(tff, bk, bv, pt_size=8.6, font_color=DEEP_TEAL)

    # =========================================================================
    # SLIDE 9: Safety (/09)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, prs, LIGHT_BG)
    add_header_pill(s9, "09")

    tb_s9 = s9.shapes.add_textbox(Inches(0.8), Inches(1.1), Inches(11.733), Inches(2.2))
    tf9 = tb_s9.text_frame
    tf9.word_wrap = True

    p9_1 = tf9.paragraphs[0]
    p9_1.text = "START WITH STRICT SAFETY GOALS, AND WHEN"
    p9_1.font.name = "Impact"
    p9_1.font.size = Pt(36)
    p9_1.font.color.rgb = DEEP_TEAL

    p9_2 = tf9.add_paragraph()
    r9_1 = p9_2.add_run()
    r9_1.text = "YOU ACCOMPLISH ✤ THEM, "
    r9_1.font.name = "Impact"
    r9_1.font.size = Pt(36)
    r9_1.font.color.rgb = DEEP_TEAL
    r9_2 = p9_2.add_run()
    r9_2.text = "SCALE FURTHER."
    r9_2.font.name = "Impact"
    r9_2.font.size = Pt(36)
    r9_2.font.color.rgb = LIME

    add_rounded_card(s9, Inches(0.8), Inches(3.5), Inches(5.7), Inches(3.4), bg_color=WHITE, border_color=BORDER_GRAY)
    tb_c1 = s9.shapes.add_textbox(Inches(1.1), Inches(3.7), Inches(5.1), Inches(3.0))
    tfc1 = tb_c1.text_frame
    tfc1.word_wrap = True
    tfc1.paragraphs[0].text = "100% ISOLATED"
    tfc1.paragraphs[0].font.name = "Impact"
    tfc1.paragraphs[0].font.size = Pt(30)
    tfc1.paragraphs[0].font.color.rgb = DEEP_TEAL
    tfc1.paragraphs[0].space_after = Pt(8)
    add_bullet_point(tfc1, "Akun Pribadi Terproteksi:", "Akun Google / Chrome Zidane · ISK dilarang disentuh oleh browser/agen manapun.", pt_size=9.5)
    add_bullet_point(tfc1, "use_real_profile=false:", "Browser otomasi diarahkan ke folder terisolasi.", pt_size=9.5)
    add_bullet_point(tfc1, "Zero Background Daemon:", "Tidak ada background worker atau scheduler liar.", pt_size=9.5)

    add_rounded_card(s9, Inches(6.8), Inches(3.5), Inches(5.7), Inches(3.4), bg_color=WHITE, border_color=BORDER_GRAY)
    tb_c2 = s9.shapes.add_textbox(Inches(7.1), Inches(3.7), Inches(5.1), Inches(3.0))
    tfc2 = tb_c2.text_frame
    tfc2.word_wrap = True
    tfc2.paragraphs[0].text = "0 AUTO-RETRY"
    tfc2.paragraphs[0].font.name = "Impact"
    tfc2.paragraphs[0].font.size = Pt(30)
    tfc2.paragraphs[0].font.color.rgb = DEEP_TEAL
    tfc2.paragraphs[0].space_after = Pt(8)
    add_bullet_point(tfc2, "Proteksi Saldo Ketat:", "Kegagalan render tidak memicu perulangan berbayar otomatis.", pt_size=9.5)
    add_bullet_point(tfc2, "ACC Telegram Bersidik Jari:", "Persetujuan mengikat hash SHA-256 media byte-per-byte.", pt_size=9.5)
    add_bullet_point(tfc2, "Draft-Only Publishing:", "Publikasi awal terbatas pada status 'Only you' berlabel AI.", pt_size=9.5)

    # =========================================================================
    # SLIDE 10: Virtual Office 3D & Access (/10) - With Real Office Photo!
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, prs, LIME)
    add_header_pill(s10, "10", lime_bg=True)

    # Left: Big Title + Office Photo Preview
    tb_l10 = s10.shapes.add_textbox(Inches(0.8), Inches(1.15), Inches(6.0), Inches(2.2))
    tf10 = tb_l10.text_frame
    tf10.word_wrap = True

    p10_1 = tf10.paragraphs[0]
    p10_1.text = "VISIT OUR VIRTUAL HQ OFFICE ✤"
    p10_1.font.name = "Impact"
    p10_1.font.size = Pt(32)
    p10_1.font.color.rgb = DEEP_TEAL

    p10_4 = tf10.add_paragraph()
    p10_4.text = "Visualisasi 3D Three.js: Workstation PM, Trend Researcher, dan studio talent terpantau secara spasial dan real-time."
    p10_4.font.name = "Arial"
    p10_4.font.size = Pt(11)
    p10_4.font.color.rgb = DEEP_TEAL
    p10_4.space_before = Pt(4)

    # 3D Office Photo Card on Left Bottom!
    add_rounded_card(s10, Inches(0.8), Inches(2.8), Inches(6.0), Inches(4.2), bg_color=WHITE, border_color=DEEP_TEAL)
    if office_img.exists():
        s10.shapes.add_picture(str(office_img), Inches(0.95), Inches(2.95), width=Inches(5.7), height=Inches(3.9))

    # Right: Dark Card with White Inner Box
    add_rounded_card(s10, Inches(7.2), Inches(1.15), Inches(5.3), Inches(5.85), bg_color=DEEP_TEAL, border_color=None)

    tb_card_title = s10.shapes.add_textbox(Inches(7.5), Inches(1.3), Inches(4.7), Inches(0.5))
    tf_ct = tb_card_title.text_frame
    pct = tf_ct.paragraphs[0]
    pct.text = "SYSTEM ACCESS & ROADMAP"
    pct.font.name = "Impact"
    pct.font.size = Pt(13)
    pct.font.color.rgb = LIME
    pct.alignment = PP_ALIGN.CENTER

    add_rounded_card(s10, Inches(7.5), Inches(1.85), Inches(4.7), Inches(4.9), bg_color=WHITE, border_color=None)
    tb_in = s10.shapes.add_textbox(Inches(7.7), Inches(2.0), Inches(4.3), Inches(4.6))
    tfin = tb_in.text_frame
    tfin.word_wrap = True

    add_bullet_point(tfin, "Server Local:", "http://localhost:5173", pt_size=9.2)
    add_bullet_point(tfin, "Security Gate:", "Protected by PIN & Token Authentication", pt_size=9.2)
    add_bullet_point(tfin, "3D Engine:", "Three.js r128 + OrbitControls 360°", pt_size=9.2)
    add_bullet_point(tfin, "Simulasi Ruang:", "Lantai 1 (Medsos & Render) & Lantai 2 (Dapur & Lounge)", pt_size=9.2)
    add_bullet_point(tfin, "Fase 1:", "Verifikasi akun Flow Nara Adelia & Rania Meutia", pt_size=9.2)
    add_bullet_point(tfin, "Fase 2:", "Uji coba video perdana karakter Nara & Rania", pt_size=9.2)
    add_bullet_point(tfin, "Fase 3:", "Sinkronisasi sound viral resmi TikTok", pt_size=9.2)
    add_bullet_point(tfin, "Fase 4:", "Produksi rutin bulanan (20 video, 10 foto)", pt_size=9.2)

    prs.save(str(PPTX_PATH))
    print(f"[OK] KLYRO-style PowerPoint saved to: {PPTX_PATH}")

def build_klyro_html():
    """Generates the interactive HTML deck with Base64 embedded images so images ALWAYS show up."""
    # Convert images to base64
    dinda_b64 = get_base64_img(ASSETS_DIR / "dinda.jpg")
    nara_b64 = get_base64_img(ASSETS_DIR / "nara.jpg")
    rania_b64 = get_base64_img(ASSETS_DIR / "rania.jpg")
    f1_b64 = get_base64_img(ASSETS_DIR / "frame-1.jpg")
    f2_b64 = get_base64_img(ASSETS_DIR / "frame-2.jpg")
    f3_b64 = get_base64_img(ASSETS_DIR / "frame-3.jpg")
    office_b64 = get_base64_img(ASSETS_DIR / "office_3d.png")

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Influencer — KLYRO Style Presentation</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;600;700;800&family=Syne:wght@700;800&display=swap');

    :root {{
      --lime: #A2E830;
      --deep-teal: #072D33;
      --mid-teal: #104750;
      --light-bg: #F5F8F5;
      --white: #FFFFFF;
      --border-gray: #CDDAD0;
      --border-dark: #0B3B42;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #041B1F;
      font-family: 'Inter', -apple-system, sans-serif;
      overflow: hidden;
      height: 100vh;
      display: flex;
      flex-direction: column;
      color: var(--deep-teal);
    }}

    /* Top Control Bar */
    .top-nav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 24px;
      background: rgba(7, 45, 51, 0.95);
      border-bottom: 1px solid var(--mid-teal);
      z-index: 1000;
    }}
    .top-brand {{
      font-family: 'Syne', sans-serif;
      font-weight: 800;
      color: var(--lime);
      font-size: 14px;
      letter-spacing: 1px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .nav-btn-group {{ display: flex; gap: 8px; align-items: center; }}
    .btn {{
      background: var(--mid-teal);
      color: white;
      border: 1px solid var(--border-dark);
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 700;
      transition: all 0.2s;
    }}
    .btn:hover {{ background: var(--lime); color: var(--deep-teal); }}
    .btn-lime {{ background: var(--lime); color: var(--deep-teal); border: none; }}
    .slide-count {{ color: #A5C0BA; font-size: 12px; font-weight: 700; margin: 0 12px; }}

    /* Main Viewport */
    .viewport {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      position: relative;
    }}

    .slide {{
      width: 100%;
      max-width: 1180px;
      height: 94%;
      max-height: 690px;
      border-radius: 20px;
      position: absolute;
      display: none;
      flex-direction: column;
      padding: 24px 36px 30px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.45);
      opacity: 0;
      transform: scale(0.98);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      overflow-y: auto;
    }}
    .slide.active {{
      display: flex;
      opacity: 1;
      transform: scale(1);
    }}

    /* Color Themes for Slides */
    .theme-light {{ background: var(--light-bg); color: var(--deep-teal); }}
    .theme-lime {{ background: var(--lime); color: var(--deep-teal); }}
    .theme-teal {{ background: var(--deep-teal); color: var(--white); }}

    /* Signature KLYRO Header Pill */
    .header-pill {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--white);
      border: 1px solid var(--border-gray);
      border-radius: 100px;
      padding: 6px 20px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.5px;
      margin-bottom: 24px;
    }}
    .theme-lime .header-pill {{
      background: var(--lime);
      border-color: var(--deep-teal);
      color: var(--deep-teal);
    }}
    .theme-teal .header-pill {{
      background: var(--deep-teal);
      border-color: var(--mid-teal);
      color: var(--white);
    }}
    .brand-dot {{
      display: inline-block;
      width: 7px;
      height: 7px;
      background: currentColor;
      border-radius: 50%;
      margin-right: 6px;
    }}

    /* Headings */
    h1.display-title {{
      font-family: 'Anton', 'Impact', sans-serif;
      text-transform: uppercase;
      line-height: 0.95;
      letter-spacing: 0.5px;
    }}
    .font-syne {{ font-family: 'Syne', sans-serif; }}

    /* Cards */
    .k-card {{
      background: var(--white);
      border-radius: 14px;
      border: 1px solid var(--border-gray);
      padding: 20px;
      display: flex;
      flex-direction: column;
    }}
    .k-card-teal {{
      background: var(--deep-teal);
      border-color: var(--border-dark);
      color: var(--white);
    }}
    .k-card-lime {{
      background: var(--lime);
      border-color: var(--deep-teal);
      color: var(--deep-teal);
    }}

    .pill-tag {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 100px;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }}

    /* Bullet lists */
    ul.k-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 7px;
      font-size: 12px;
      line-height: 1.4;
    }}
    ul.k-list li {{ position: relative; padding-left: 14px; }}
    ul.k-list li::before {{
      content: "•";
      position: absolute;
      left: 0;
      font-weight: bold;
    }}
    ul.k-list li strong {{ font-weight: 700; }}

    /* Layout Grids */
    .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; flex: 1; }}
    .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; flex: 1; }}
    .grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; flex: 1; }}

    .talent-img {{
      width: 100%;
      height: 180px;
      object-fit: cover;
      border-radius: 10px;
      margin-bottom: 12px;
      border: 1px solid var(--border-gray);
    }}

    .office-img-frame {{
      width: 100%;
      height: 260px;
      object-fit: cover;
      border-radius: 12px;
      border: 2px solid var(--deep-teal);
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }}

    /* Progress bar */
    .progress-line {{ height: 4px; background: rgba(255,255,255,0.1); width: 100%; }}
    .progress-fill {{ height: 100%; background: var(--lime); width: 10%; transition: width 0.3s; }}
  </style>
</head>
<body>

  <!-- Top Controller Bar -->
  <div class="top-nav">
    <div class="top-brand">
      <svg width="20" height="20" viewBox="0 0 100 100" fill="currentColor">
        <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
        <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
        <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
        <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
      </svg>
      AI INFLUENCER • KLYRO AGENCY EDITION
    </div>
    <div class="nav-btn-group">
      <button class="btn" onclick="prev()">❮ PREV</button>
      <span class="slide-count" id="count">01 / 10</span>
      <button class="btn btn-lime" onclick="next()">NEXT ❯</button>
      <button class="btn" onclick="fullscreen()">⛶ FULLSCREEN</button>
    </div>
  </div>
  <div class="progress-line"><div class="progress-fill" id="bar"></div></div>

  <div class="viewport">

    <!-- ==================== SLIDE 1 (/01) ==================== -->
    <div class="slide theme-light active" style="position: relative;">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/01</div>
      </div>
      <div style="display: flex; gap: 40px; flex: 1; align-items: center;">
        <div style="flex: 1.2;">
          <h1 class="display-title" style="font-size: 64px; color: var(--deep-teal); margin-bottom: 8px;">
            AI CREATIVE <br>
            <span style="color: var(--lime);">
              <svg width="48" height="48" viewBox="0 0 100 100" fill="currentColor" style="vertical-align: -4px;">
                <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
                <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
                <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
                <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
              </svg>
            </span>AGENCY
          </h1>
          <p style="font-size: 15px; color: var(--mid-teal); max-width: 480px; line-height: 1.5; margin-bottom: 24px;">
            Autonomous virtual creator pipeline that fuels continuous storytelling, high-fidelity generation, and full creative control.
          </p>
          <div style="display: flex; gap: 10px;">
            <span class="pill-tag" style="background: var(--lime); color: var(--deep-teal);">⚡ DEEPSEEK FLASH</span>
            <span class="pill-tag" style="background: var(--deep-teal); color: var(--white);">🎬 GOOGLE FLOW (OMNI 1.1)</span>
            <span class="pill-tag" style="background: var(--border-gray); color: var(--deep-teal);">🔒 TELEGRAM BOT ACC</span>
          </div>
        </div>
        <div style="flex: 0.9; height: 100%; display: flex; align-items: center; justify-content: center;">
          <div style="width: 100%; height: 380px; border-radius: 24px; overflow: hidden; border: 2px solid var(--border-gray); background: white;">
            <img src="{dinda_b64}" alt="Dinda Kemala" style="width: 100%; height: 100%; object-fit: cover;">
          </div>
        </div>
      </div>
      <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 8px; background: var(--lime); border-radius: 0 0 20px 20px;"></div>
    </div>

    <!-- ==================== SLIDE 2 (/02) ==================== -->
    <div class="slide theme-lime">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/02</div>
      </div>
      <div style="display: flex; gap: 40px; flex: 1; align-items: center;">
        <div style="flex: 0.3; text-align: center;">
          <svg width="120" height="120" viewBox="0 0 100 100" fill="var(--deep-teal)">
            <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
            <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
            <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
            <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
          </svg>
        </div>
        <div style="flex: 1.7;">
          <h1 class="display-title" style="font-size: 50px; line-height: 1.05; color: var(--deep-teal); margin-bottom: 20px;">
            AUTONOMY AND — <br>
            CONSISTENCY ARE THE <br>
            SPARK THAT FUELS <br>
            VIRTUAL TALENTS
          </h1>
          <p style="font-size: 16px; color: var(--deep-teal); max-width: 650px; line-height: 1.6; font-weight: 600;">
            Mengubah beban pembuatan konten harian menjadi ekosistem cerdas: Riset Tren otomatis → Generasi video Google Flow → Quality Assurance lokal → Persetujuan instan Telegram.
          </p>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 3 (/03) ==================== -->
    <div class="slide theme-teal" style="justify-content: center; text-align: center;">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/03</div>
      </div>
      <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <h1 class="display-title" style="font-size: 58px; line-height: 1.05; max-width: 900px; margin-bottom: 24px;">
          THE STRENGTH OF <br>
          MULTI-AGENT AI AND THE <br>
          JOY OF VIRTUAL <br>
          <span style="color: var(--lime);">
            <svg width="40" height="40" viewBox="0 0 100 100" fill="currentColor" style="vertical-align: -2px;">
              <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
              <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
              <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
              <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
            </svg>
            STORYTELLING
            <svg width="40" height="40" viewBox="0 0 100 100" fill="currentColor" style="vertical-align: -2px;">
              <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
              <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
              <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
              <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
            </svg>
          </span>
        </h1>
        <p style="font-size: 15px; color: var(--lime); font-weight: 600; letter-spacing: 0.5px;">
          Dinda Kemala • Nara Adelia • Rania Meutia • Hermes Multi-Agent Framework
        </p>
      </div>
    </div>

    <!-- ==================== SLIDE 4 (/04) ==================== -->
    <div class="slide theme-light">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/04</div>
      </div>
      <div class="grid-3">
        <!-- Dinda -->
        <div class="k-card">
          <img class="talent-img" src="{dinda_b64}" alt="Dinda">
          <h2 class="display-title" style="font-size: 20px; color: var(--deep-teal); margin-bottom: 2px;">DINDA KEMALA</h2>
          <div class="pill-tag" style="background: rgba(7,45,51,0.08); color: var(--deep-teal); margin-bottom: 10px;">LIFESTYLE & PALEMBANG VLOG ●</div>
          <ul class="k-list">
            <li><strong>Persona:</strong> Gadis hangat, santun berhijab.</li>
            <li><strong>Pilar:</strong> Kuliner khas, jalan-jalan Palembang.</li>
            <li><strong>Status:</strong> Pilot teknis 100% lulus hingga TikTok.</li>
          </ul>
        </div>
        <!-- Nara (Lime Highlight Card) -->
        <div class="k-card k-card-lime">
          <img class="talent-img" src="{nara_b64}" alt="Nara">
          <h2 class="display-title" style="font-size: 20px; color: var(--deep-teal); margin-bottom: 2px;">NARA ADELIA</h2>
          <div class="pill-tag" style="background: var(--deep-teal); color: var(--lime); margin-bottom: 10px;">BEAUTY & OFFICE LOOK MEDAN ●</div>
          <ul class="k-list">
            <li><strong>Persona:</strong> Modern, profesional, rambut cokelat.</li>
            <li><strong>Pilar:</strong> GRWM, makeup, kantor di ISK.</li>
            <li><strong>Aturan:</strong> Pekerjaan resmi tanpa mengarang.</li>
          </ul>
        </div>
        <!-- Rania -->
        <div class="k-card">
          <img class="talent-img" src="{rania_b64}" alt="Rania">
          <h2 class="display-title" style="font-size: 20px; color: var(--deep-teal); margin-bottom: 2px;">RANIA MEUTIA</h2>
          <div class="pill-tag" style="background: rgba(7,45,51,0.08); color: var(--deep-teal); margin-bottom: 10px;">WISATA & TEMPAT BAGUS ACEH ●</div>
          <ul class="k-list">
            <li><strong>Persona:</strong> Anggun, santun, ramah, berhijab syar'i.</li>
            <li><strong>Pilar:</strong> Wisata alam, pantai Sabang, spot foto estetik.</li>
            <li><strong>Aturan:</strong> Rekomendasi tempat nyata & ramah wisata.</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 5 (/05) ==================== -->
    <div class="slide theme-teal">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/05</div>
      </div>
      <div style="margin-bottom: 20px;">
        <h2 class="display-title" style="font-size: 28px; color: var(--white); display: flex; align-items: center; gap: 10px;">
          <svg width="26" height="26" viewBox="0 0 100 100" fill="var(--lime)">
            <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
            <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
            <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
            <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
          </svg>
          WE CREATE IMPACTFUL CONTENT WITH AUTONOMOUS PIPELINE
        </h2>
        <p style="font-size: 13px; color: var(--lime);">Arsitektur 4 pilar dari riset tren hingga draf publikasi otomatis.</p>
      </div>
      <div class="grid-4">
        <div class="k-card" style="color: var(--deep-teal);">
          <div style="font-size: 28px; margin-bottom: 8px;">✤</div>
          <h3 class="display-title" style="font-size: 16px; margin-bottom: 8px;">01. TREND RESEARCH</h3>
          <p style="font-size: 12px; line-height: 1.5; color: var(--mid-teal);">
            Mendeteksi audio tren TikTok & topik viral dengan validasi minimal 2 URL sumber kredibel.
          </p>
        </div>
        <div class="k-card" style="color: var(--deep-teal);">
          <div style="font-size: 28px; margin-bottom: 8px;">✤</div>
          <h3 class="display-title" style="font-size: 16px; margin-bottom: 8px;">02. FLOW GENERATION</h3>
          <p style="font-size: 12px; line-height: 1.5; color: var(--mid-teal);">
            Model Google Flow Omni 1.1 Flash 720p vertikal 9:16 durasi native 6 detik pas platform.
          </p>
        </div>
        <div class="k-card" style="color: var(--deep-teal);">
          <div style="font-size: 28px; margin-bottom: 8px;">✤</div>
          <h3 class="display-title" style="font-size: 16px; margin-bottom: 8px;">03. LOCAL FFMPEG</h3>
          <p style="font-size: 12px; line-height: 1.5; color: var(--mid-teal);">
            Normalisasi container MP4, inspeksi frame 0.25s, 2.75s, 5.5s, dan penguncian hash SHA-256.
          </p>
        </div>
        <div class="k-card" style="color: var(--deep-teal);">
          <div style="font-size: 28px; margin-bottom: 8px;">✤</div>
          <h3 class="display-title" style="font-size: 16px; margin-bottom: 8px;">04. TELEGRAM ACC</h3>
          <p style="font-size: 12px; line-height: 1.5; color: var(--mid-teal);">
            Review interaktif langsung di smartphone dengan tombol ACC instan sebelum publikasi.
          </p>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 6 (/06) ==================== -->
    <div class="slide theme-lime">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/06</div>
      </div>
      <div style="text-align: center; margin-bottom: 18px;">
        <span style="background: white; border: 2px solid var(--deep-teal); border-radius: 100px; padding: 6px 24px; font-family: 'Anton', sans-serif; font-size: 16px; letter-spacing: 1px; color: var(--deep-teal);">
          OUR PRINCIPLE
        </span>
      </div>
      <div class="grid-4">
        <div class="k-card k-card-teal">
          <div style="font-size: 24px; color: var(--lime); margin-bottom: 6px;">✤</div>
          <h3 class="display-title" style="font-size: 15px; margin-bottom: 10px;">PROJECT MANAGER</h3>
          <p style="font-size: 12px; line-height: 1.5;">
            Mengatur dapur produksi pada board Kanban, mereview draf caption & mengawasi pagu kredit Flow.
          </p>
        </div>
        <div class="k-card">
          <div style="font-size: 24px; color: var(--deep-teal); margin-bottom: 6px;">✤</div>
          <h3 class="display-title" style="font-size: 15px; margin-bottom: 10px;">GROUNDED RESEARCH</h3>
          <p style="font-size: 12px; line-height: 1.5; color: var(--mid-teal);">
            Riset tren & sound wajib menyertakan bukti 2 URL sumber kredibel; pisahkan fakta dari asumsi.
          </p>
        </div>
        <div class="k-card k-card-teal">
          <div style="font-size: 24px; color: var(--lime); margin-bottom: 6px;">✤</div>
          <h3 class="display-title" style="font-size: 15px; margin-bottom: 10px;">CONSISTENCY FIRST</h3>
          <p style="font-size: 12px; line-height: 1.5;">
            33 foto master dikunci hash SHA-256; identitas karakter tetap konsisten antar konten.
          </p>
        </div>
        <div class="k-card">
          <div style="font-size: 24px; color: var(--deep-teal); margin-bottom: 6px;">✤</div>
          <h3 class="display-title" style="font-size: 15px; margin-bottom: 10px;">HUMAN APPROVAL</h3>
          <p style="font-size: 12px; line-height: 1.5; color: var(--mid-teal);">
            Persetujuan Telegram wajib sebelum publikasi; tidak ada auto-posting publik tanpa izin.
          </p>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 7 (/07) ==================== -->
    <div class="slide theme-lime">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/07</div>
      </div>
      <div style="display: flex; gap: 30px; flex: 1; align-items: flex-end;">
        <div style="flex: 1.1; margin-bottom: 30px;">
          <h1 class="display-title" style="font-size: 46px; line-height: 1; color: var(--deep-teal); margin-bottom: 16px;">
            TRUSTED RESULTS <br>
            PROVEN BY 
            <svg width="34" height="34" viewBox="0 0 100 100" fill="currentColor" style="vertical-align: -2px;">
              <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
              <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
              <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
              <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
            </svg>
            PILOT
          </h1>
          <p style="font-size: 15px; line-height: 1.6; color: var(--deep-teal); font-weight: 600;">
            Hasil eksekusi pilot terkontrol Dinda Kemala membuktikan seluruh alur berfungsi 100% sukses dari prompt hingga draf TikTok Studio.
          </p>
        </div>

        <!-- Staggered Height Cards -->
        <div style="flex: 1.4; display: flex; gap: 14px; align-items: flex-end;">
          <div class="k-card" style="flex: 1; height: 210px; justify-content: flex-end;">
            <div class="display-title" style="font-size: 42px; line-height: 1; color: var(--deep-teal);">10</div>
            <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--mid-teal);">Kredit Flow</div>
            <div style="font-size: 18px; color: var(--lime); margin-top: 8px;">✤</div>
          </div>
          <div class="k-card k-card-teal" style="flex: 1; height: 270px; justify-content: flex-end;">
            <div class="display-title" style="font-size: 42px; line-height: 1; color: var(--lime);">6s</div>
            <div style="font-size: 11px; font-weight: 800; text-transform: uppercase;">Video 720p 180 Frame</div>
            <div style="font-size: 18px; color: var(--lime); margin-top: 8px;">✤</div>
          </div>
          <div class="k-card" style="flex: 1.2; height: 340px; justify-content: flex-end;">
            <div class="display-title" style="font-size: 44px; line-height: 1; color: var(--deep-teal);">100%</div>
            <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--mid-teal);">Telegram ACC & TikTok Draft</div>
            <div style="font-size: 24px; color: var(--lime); margin-top: 12px;">✤</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 8 (/08) ==================== -->
    <div class="slide theme-light">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/08</div>
      </div>
      <div style="margin-bottom: 14px;">
        <h2 class="display-title" style="font-size: 26px; color: var(--deep-teal); display: flex; align-items: center; gap: 8px;">
          VISUAL QUALITY CONTROL 
          <svg width="24" height="24" viewBox="0 0 100 100" fill="var(--lime)">
            <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
            <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
            <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
            <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
          </svg>
          INSPECTION
        </h2>
      </div>
      <div class="grid-3">
        <div class="k-card">
          <img class="talent-img" src="{f1_b64}" alt="Frame 1">
          <h3 class="display-title" style="font-size: 14px; margin-bottom: 4px;">FRAME 1 (DETIK 0.25)</h3>
          <ul class="k-list">
            <li><strong>Wajah:</strong> Menghadap kamera, hijab rapi.</li>
            <li><strong>Pencahayaan:</strong> Natural soft light tanpa artefak.</li>
            <li><strong>Aksesoris:</strong> Pendant/kalung terdeteksi sesuai.</li>
          </ul>
        </div>
        <div class="k-card">
          <img class="talent-img" src="{f2_b64}" alt="Frame 2">
          <h3 class="display-title" style="font-size: 14px; margin-bottom: 4px;">FRAME 2 (DETIK 2.75)</h3>
          <ul class="k-list">
            <li><strong>Ekspresi:</strong> Gerakan alami, proporsi stabil.</li>
            <li><strong>Tekstur:</strong> Kulit matte natural tanpa plastik AI.</li>
            <li><strong>Busana:</strong> Warna & lipatan baju konsisten.</li>
          </ul>
        </div>
        <div class="k-card">
          <img class="talent-img" src="{f3_b64}" alt="Frame 3">
          <h3 class="display-title" style="font-size: 14px; margin-bottom: 4px;">FRAME 3 (DETIK 5.50)</h3>
          <ul class="k-list">
            <li><strong>Transisi:</strong> Senyum konsisten hingga akhir.</li>
            <li><strong>Background:</strong> Latar stabil tanpa warping.</li>
            <li><strong>Container:</strong> Video berakhir mulus 180 frame.</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 9 (/09) ==================== -->
    <div class="slide theme-light">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/09</div>
      </div>
      <div style="margin-bottom: 24px;">
        <h1 class="display-title" style="font-size: 38px; line-height: 1.1; color: var(--deep-teal);">
          START WITH STRICT SAFETY GOALS, AND WHEN <br>
          YOU ACCOMPLISH 
          <svg width="30" height="30" viewBox="0 0 100 100" fill="var(--lime)" style="vertical-align: -2px;">
            <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
            <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
            <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
            <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
          </svg>
          THEM, <span style="color: var(--mid-teal);">SCALE WITH CONFIDENCE.</span>
        </h1>
      </div>
      <div class="grid-2">
        <div class="k-card">
          <div class="display-title" style="font-size: 36px; color: var(--deep-teal); margin-bottom: 8px;">100% ISOLATED</div>
          <ul class="k-list" style="font-size: 13px;">
            <li><strong>Akun Pribadi Terproteksi:</strong> Akun Google / Chrome Zidane · ISK dilarang disentuh oleh browser/agen.</li>
            <li><strong>use_real_profile=false:</strong> Otomasi browser dialihkan ke profil direktori terisolasi.</li>
            <li><strong>Zero Background Daemon:</strong> Tanpa bot atau background scheduler liar.</li>
          </ul>
        </div>
        <div class="k-card">
          <div class="display-title" style="font-size: 36px; color: var(--deep-teal); margin-bottom: 8px;">0 AUTO-RETRY</div>
          <ul class="k-list" style="font-size: 13px;">
            <li><strong>Proteksi Saldo Ketat:</strong> Kegagalan render tidak memicu perulangan berbayar otomatis.</li>
            <li><strong>ACC Telegram Bersidik Jari:</strong> Persetujuan mengikat hash SHA-256 media byte-per-byte.</li>
            <li><strong>Draft-Only Publishing:</strong> Publikasi awal terbatas pada status 'Only you' berlabel AI.</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ==================== SLIDE 10 (/10) — WITH REAL 3D VIRTUAL OFFICE PHOTO ==================== -->
    <div class="slide theme-lime">
      <div class="header-pill">
        <div><span class="brand-dot"></span>AI INFLUENCER</div>
        <div>PRESENTATION</div>
        <div>/10</div>
      </div>
      <div style="display: flex; gap: 24px; flex: 1; align-items: center;">
        <!-- Left: 3D Office Screenshot & Title -->
        <div style="flex: 1.15; display: flex; flex-direction: column;">
          <h1 class="display-title" style="font-size: 34px; line-height: 1.05; color: var(--deep-teal); margin-bottom: 8px;">
            VISIT OUR VIRTUAL HQ OFFICE 
            <svg width="28" height="28" viewBox="0 0 100 100" fill="white" style="vertical-align: -2px;">
              <path d="M50 50 C50 20 75 10 85 25 C95 40 75 50 50 50 Z" />
              <path d="M50 50 C80 50 90 75 75 85 C60 95 50 75 50 50 Z" />
              <path d="M50 50 C50 80 25 90 15 75 C5 60 25 50 50 50 Z" />
              <path d="M50 50 C20 50 10 25 25 15 C40 5 50 25 50 50 Z" />
            </svg>
          </h1>
          <p style="font-size: 12px; color: var(--deep-teal); line-height: 1.4; font-weight: 600; margin-bottom: 12px;">
            Kantor AI Intan: Ruang agensi 3D digital twin (Three.js) dengan workstation PM, Trend Researcher, dan studio talent.
          </p>
          <!-- Actual 3D Virtual Office Screenshot -->
          <div style="border-radius: 14px; overflow: hidden; border: 2px solid var(--deep-teal); background: #0c1222; box-shadow: 0 12px 30px rgba(0,0,0,0.25);">
            <img src="{office_b64}" alt="Kantor AI Intan 3D Virtual Office" style="width: 100%; height: 260px; object-fit: cover; display: block;">
          </div>
        </div>

        <!-- Right: Control Panel / Access Roadmap -->
        <div style="flex: 1;">
          <div class="k-card k-card-teal" style="padding: 20px; border-radius: 18px;">
            <div style="text-align: center; margin-bottom: 10px; font-family: 'Anton', sans-serif; font-size: 14px; letter-spacing: 1px; color: var(--lime);">
              SYSTEM ACCESS & ROADMAP
            </div>
            <div style="background: white; border-radius: 12px; padding: 16px; color: var(--deep-teal);">
              <ul class="k-list" style="font-size: 11.5px;">
                <li><strong>Server Local:</strong> http://localhost:5173</li>
                <li><strong>Security Gate:</strong> Protected by PIN & Token Authentication</li>
                <li><strong>3D Engine:</strong> Three.js r128 + OrbitControls 360°</li>
                <li><strong>Lantai 1:</strong> Divisi Medsos, Studio Dinda, Nara & Rania</li>
                <li><strong>Lantai 2:</strong> Ruang PM Intan, Researcher & Dapur Konten</li>
                <li><strong>Fase 1:</strong> Verifikasi akun Flow Nara Adelia & Rania Meutia</li>
                <li><strong>Fase 2:</strong> Uji coba video perdana karakter Nara & Rania</li>
                <li><strong>Fase 3:</strong> Sinkronisasi sound viral resmi TikTok</li>
                <li><strong>Fase 4:</strong> Produksi rutin bulanan (20 video, 10 foto)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <script>
    let cur = 0;
    const slides = document.querySelectorAll('.slide');
    const total = slides.length;
    const countEl = document.getElementById('count');
    const barEl = document.getElementById('bar');

    function update() {{
      slides.forEach((s, i) => s.classList.toggle('active', i === cur));
      const num = String(cur + 1).padStart(2, '0');
      const tot = String(total).padStart(2, '0');
      countEl.innerText = `${{num}} / ${{tot}}`;
      barEl.style.width = `${{((cur + 1) / total) * 100}}%`;
    }}

    function next() {{
      if (cur < total - 1) {{ cur++; update(); }}
    }}
    function prev() {{
      if (cur > 0) {{ cur--; update(); }}
    }}
    function fullscreen() {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen();
      }} else {{
        document.exitFullscreen();
      }}
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') next();
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') prev();
      if (e.key === 'Home') {{ cur = 0; update(); }}
      if (e.key === 'End') {{ cur = total - 1; update(); }}
    }});

    update();
  </script>
</body>
</html>
"""
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Self-contained KLYRO HTML presentation saved to: {HTML_PATH}")

if __name__ == "__main__":
    build_klyro_pptx()
    build_klyro_html()
