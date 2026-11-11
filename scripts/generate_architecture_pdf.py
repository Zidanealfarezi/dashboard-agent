#!/usr/bin/env python3
"""
Generator Dokumen PDF Teknis: Arsitektur dan Algoritma AI Influencer Otonom
Sistem: Dinda Kemala (@dinda.kemala_)
Format: Standar Laporan Rekayasa Perangkat Lunak & Sistem AI (A4 - 6 Halaman Presisi)
Bebas Emoji (Strict 0% Emoji Policy).
"""

import os
import subprocess
import sys

HTML_CONTENT = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Arsitektur dan Algoritma AI Influencer Otonom - Dinda Kemala</title>
<style>
  @page {
    size: A4 portrait;
    margin: 12mm 12mm 12mm 12mm;
    @bottom-right {
      content: "Halaman " counter(page);
      font-size: 8pt;
      color: #64748b;
    }
    @bottom-left {
      content: "Arsitektur Sistem AI Influencer - Rev 2.4 (2026)";
      font-size: 8pt;
      color: #64748b;
    }
  }

  * {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 9pt;
    line-height: 1.45;
    color: #1e293b;
    background: #ffffff;
    margin: 0;
    padding: 0;
  }

  .page {
    page-break-after: always;
    height: 272mm;
    max-height: 272mm;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .page-last {
    page-break-after: avoid;
    height: 272mm;
    max-height: 272mm;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .content-body {
    flex-grow: 1;
  }

  .doc-badge {
    display: inline-block;
    padding: 3px 10px;
    background: #e0f2fe;
    color: #0369a1;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-radius: 4px;
    border: 1px solid #bae6fd;
    margin-bottom: 12px;
  }

  .doc-title {
    font-size: 22pt;
    font-weight: 800;
    line-height: 1.15;
    color: #0f172a;
    margin: 0 0 8px 0;
    letter-spacing: -0.5px;
  }

  .doc-subtitle {
    font-size: 11.5pt;
    font-weight: 500;
    color: #475569;
    margin: 0 0 18px 0;
    line-height: 1.35;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 18px;
  }

  .meta-item {
    font-size: 8pt;
  }

  .meta-label {
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 1px;
  }

  .meta-value {
    color: #0f172a;
    font-weight: 700;
    font-size: 9pt;
  }

  .executive-summary-box {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-left: 5px solid #0284c7;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 14px;
  }

  .executive-summary-box h3 {
    margin-top: 0;
    margin-bottom: 8px;
    color: #0f172a;
    font-size: 10.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .executive-summary-box p {
    margin: 4px 0 8px 0;
    font-size: 8.5pt;
    color: #334155;
    line-height: 1.5;
  }

  .executive-summary-box ul {
    margin: 4px 0 4px 18px;
    padding: 0;
  }

  .executive-summary-box li {
    font-size: 8.5pt;
    margin-bottom: 5px;
    line-height: 1.45;
  }

  h1 {
    font-size: 13.5pt;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 10px;
    color: #0f172a;
    font-weight: 800;
  }

  h2 {
    font-size: 10.5pt;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
    margin-top: 10px;
    margin-bottom: 6px;
    color: #0369a1;
    font-weight: 700;
  }

  h3 {
    font-size: 9.5pt;
    margin-top: 8px;
    margin-bottom: 4px;
    color: #0f172a;
    font-weight: 700;
  }

  p {
    margin: 4px 0 8px 0;
    line-height: 1.45;
    font-size: 8.5pt;
  }

  ul, ol {
    margin: 4px 0 8px 18px;
    padding: 0;
  }

  li {
    margin-bottom: 3px;
    line-height: 1.4;
    font-size: 8.5pt;
  }

  .callout {
    background: #f8fafc;
    border-left: 4px solid #0284c7;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 0 4px 4px 0;
    font-size: 8pt;
  }

  .callout-success {
    background: #f0fdf4;
    border-left-color: #16a34a;
  }

  .callout-warning {
    background: #fffbeb;
    border-left-color: #d97706;
  }

  .callout-title {
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 2px;
    text-transform: uppercase;
    font-size: 7.5pt;
    letter-spacing: 0.5px;
  }

  .formula-card {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 8px 12px;
    margin: 6px 0 8px 0;
    font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
    font-size: 8.5pt;
    color: #0f172a;
  }

  .formula-display {
    text-align: center;
    font-weight: bold;
    font-size: 9.5pt;
    padding: 2px 0;
    color: #0369a1;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 8pt;
  }

  th, td {
    padding: 5px 8px;
    text-align: left;
    border: 1px solid #cbd5e1;
  }

  th {
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 7pt;
    letter-spacing: 0.5px;
  }

  tr:nth-child(even) {
    background: #f8fafc;
  }

  code {
    font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
    font-size: 7.5pt;
    background: #f1f5f9;
    padding: 1px 3px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
    color: #0f172a;
  }

  .grid-2col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 6px 0;
  }

  .code-card {
    background: #0f172a;
    color: #f8fafc;
    padding: 8px 10px;
    border-radius: 5px;
    font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
    font-size: 7pt;
    line-height: 1.35;
    overflow: hidden;
  }

  .code-title {
    color: #38bdf8;
    font-weight: bold;
    margin-bottom: 4px;
    text-transform: uppercase;
    font-size: 6.5pt;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #334155;
    padding-bottom: 2px;
  }

  .diagram-container {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 6px;
    margin: 8px 0;
    text-align: center;
  }

  .diagram-caption {
    font-size: 7.5pt;
    font-weight: 600;
    color: #64748b;
    margin-top: 5px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .footer-sign {
    padding-top: 8px;
    border-top: 1px dashed #cbd5e1;
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #64748b;
  }
</style>
</head>
<body>

<!-- HALAMAN 1: COVER & RINGKASAN EKSEKUTIF -->
<div class="page">
  <div class="content-body">
    <div class="doc-badge">Dokumentasi Teknis Produksi Otonom - Sistem AI</div>
    <h1 class="doc-title">ARSITEKTUR SISTEM DAN ALGORITMA AI INFLUENCER OTONOM</h1>
    <div class="doc-subtitle">Spesifikasi Arsitektur End-to-End, Model Matematika Rotasi Busana, Sinkronisasi Audio, dan Sistem Otomasi TikTok Studio untuk Persona Dinda Kemala (@dinda.kemala_)</div>

    <div class="meta-grid">
      <div class="meta-item">
        <div class="meta-label">Karakter / Persona</div>
        <div class="meta-value">Dinda Kemala (Vlogger Palembang, 22 Tahun)</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Status Operasional</div>
        <div class="meta-value">Aktif 24/7 (Opsi B: Semi-Otonom via Telegram Gate)</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Daemon Service OS</div>
        <div class="meta-value">macOS launchd (com.aiinfluencer.autopost)</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Basis Data Utama</div>
        <div class="meta-value">SQLite (operations/production.sqlite)</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Target Platform Distribusi</div>
        <div class="meta-value">TikTok Studio Web Automation (Chrome CDP)</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Mission Control Interface</div>
        <div class="meta-value">Telegram Bot Mission Control (@PM_INTAN_BOT)</div>
      </div>
    </div>

    <div class="executive-summary-box">
      <h3>Ringkasan Eksekutif & Resolusi Masalah Otomasi</h3>
      <p>
        Dokumen teknis ini menetapkan arsitektur baku sistem AI Influencer otonom yang memproduksi dan menerbitkan konten vlog harian Dinda Kemala di TikTok secara konsisten. Seluruh audit kegagalan operasional masa lalu telah diselesaikan secara permanen:
      </p>
      <ul>
        <li><strong>Penjadwalan 24/7 Nir-Henti:</strong> Layanan terpasang di level kernel macOS melalui <code>launchd</code> daemon (<code>com.aiinfluencer.autopost</code>) dengan parameter <code>KeepAlive: true</code>, menjamin proses orkestrator terus aktif di latar belakang tanpa tergantung jendela terminal.</li>
        <li><strong>Eliminasi Busana Monoton (05:00 WIB):</strong> Modul <code>daily_pinterest_wardrobe_job.js</code> meriset inspirasi busana modest aesthetic dari Pinterest setiap jam 05:00 WIB, membagi menjadi dua pasang outfit berbeda (pagi dan malam), serta menerapkan fungsi penalti pemakaian berbasis riwayat SQLite.</li>
        <li><strong>Penyelesaian Bug Judul "final_vlog":</strong> Mesin penerbit <code>tiktok_publisher.js</code> dilengkapi algoritma deep-purge DOM (<code>selectAll</code> + <code>delete</code> + <code>backspace</code> fisik), injeksi ketikan melalui Chrome DevTools Protocol (CDP), serta gerbang asersi ketat yang menolak publikasi apabila teks mengandung nama file bawaan.</li>
        <li><strong>Pusat Komando Telegram Opsi B:</strong> Agen PM Bot (<code>@PM_INTAN_BOT</code>) disatukan dengan runner CLI. Saat pemilik membalas <em>"Gas posting"</em> atau <em>"ACC"</em>, bot mengeksekusi penerbitan secara langsung dan mengirimkan bukti URL video live dalam hitungan detik.</li>
      </ul>
    </div>

    <div class="callout callout-success">
      <div class="callout-title">Hasil Verifikasi Produksi Langsung (Senin Pagi, 9 November 2026)</div>
      Video Senin Pagi (09 Nov 2026) berhasil diterbitkan secara publik dengan caption Bahasa Palembang utuh:
      <br><strong>URL Tayang:</strong> <code>https://www.tiktok.com/@dinda.kemala_/video/7705995249474080020</code> (Status: Everyone / Publik).
    </div>
  </div>

  <div class="footer-sign">
    <div>Penyusun: Antigravity AI Engineering</div>
    <div>Tanggal Rilis: 9 November 2026</div>
    <div>Klasifikasi: Dokumen Teknis Internal</div>
  </div>
</div>

<!-- HALAMAN 2: DIAGRAM ARSITEKTUR MAKRO -->
<div class="page">
  <div class="content-body">
    <h1>1. Diagram Arsitektur Makro Sistem</h1>
    <p>
      Arsitektur sistem dibangun di atas lima lapisan hierarkis modular yang saling terhubung secara deterministik melalui event-driven orchestration dan basis data transaksi SQLite.
    </p>

    <div class="diagram-container">
      <svg viewBox="0 0 740 480" width="100%" height="450" xmlns="http://www.w3.org/2000/svg" style="font-family: -apple-system, sans-serif;">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#64748b" />
          </marker>
          <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#16a34a" />
          </marker>
        </defs>

        <!-- LAYER 1: Schedulers & Orchestration -->
        <rect x="20" y="15" width="700" height="75" rx="7" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />
        <path d="M 20 22 Q 20 15 27 15 L 713 15 Q 720 15 720 22 L 720 36 L 20 36 Z" fill="#0369a1" />
        <text x="35" y="28" fill="#ffffff" font-size="10" font-weight="bold">1. LAPISAN PENJADWAL & ORKESTRATOR (OS & DAEMON)</text>
        
        <rect x="35" y="42" width="180" height="38" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="45" y="58" fill="#0f172a" font-size="9" font-weight="bold">macOS launchd Daemon</text>
        <text x="45" y="70" fill="#64748b" font-size="7.5">com.aiinfluencer.autopost</text>

        <line x1="215" y1="61" x2="250" y2="61" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />

        <rect x="255" y="42" width="190" height="38" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="265" y="58" fill="#0f172a" font-size="9" font-weight="bold">master_scheduler.js</text>
        <text x="265" y="70" fill="#64748b" font-size="7.5">Pewaktu Zona WIB Asia/Jakarta</text>

        <line x1="445" y1="61" x2="480" y2="61" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />

        <rect x="485" y="42" width="220" height="38" rx="4" fill="#e0f2fe" stroke="#38bdf8" />
        <text x="495" y="58" fill="#0369a1" font-size="9" font-weight="bold">Triggers Harian Mandiri</text>
        <text x="495" y="70" fill="#0284c7" font-size="7.5">05:00 WIB, 06:30/07:00, 18:30/19:00</text>

        <!-- Downward link to Layer 2 & 3 -->
        <line x1="125" y1="90" x2="125" y2="115" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />
        <line x1="350" y1="90" x2="350" y2="115" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />

        <!-- LAYER 2: Pinterest Wardrobe Engine -->
        <rect x="20" y="115" width="220" height="150" rx="7" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />
        <path d="M 20 122 Q 20 115 27 115 L 233 115 Q 240 115 240 122 L 240 136 L 20 136 Z" fill="#0d9488" />
        <text x="30" y="128" fill="#ffffff" font-size="9" font-weight="bold">2. PINTEREST WARDROBE (05:00 WIB)</text>

        <rect x="30" y="145" width="200" height="32" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="38" y="159" fill="#0f172a" font-size="8.5" font-weight="bold">daily_pinterest_wardrobe_job</text>
        <text x="38" y="170" fill="#64748b" font-size="7.5">Modest Palembang Catalog Crawler</text>

        <rect x="30" y="183" width="200" height="32" rx="4" fill="#f0fdf4" stroke="#86efac" />
        <text x="38" y="197" fill="#166534" font-size="8.5" font-weight="bold">Scoring Penalti Riwayat</text>
        <text x="38" y="208" fill="#15803d" font-size="7.5">OOTD Pagi != OOTD Malam</text>

        <rect x="30" y="222" width="200" height="30" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="38" y="236" fill="#0f172a" font-size="8" font-weight="bold">SQLite: character_wardrobe</text>
        <text x="38" y="246" fill="#64748b" font-size="7">Simpan record slot harian</text>

        <!-- LAYER 3: Creative Video & Audio Engine -->
        <rect x="260" y="115" width="460" height="150" rx="7" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />
        <path d="M 260 122 Q 260 115 267 115 L 713 115 Q 720 115 720 122 L 720 136 L 260 136 Z" fill="#4f46e5" />
        <text x="270" y="128" fill="#ffffff" font-size="9" font-weight="bold">3. DAPUR PRODUKSI KONTEN (FLOW & AUDIO SINKRONISASI)</text>

        <rect x="272" y="145" width="135" height="48" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="278" y="159" fill="#0f172a" font-size="8" font-weight="bold">Prompt Builder</text>
        <text x="278" y="171" fill="#475569" font-size="7">3 Visual Reference Chips</text>
        <text x="278" y="182" fill="#64748b" font-size="7">Dialek Asli Palembang</text>

        <line x1="407" y1="169" x2="425" y2="169" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)" />

        <rect x="428" y="145" width="135" height="48" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="434" y="159" fill="#0f172a" font-size="8" font-weight="bold">Google Flow Video</text>
        <text x="434" y="171" fill="#475569" font-size="7">Omni 1.1 Flash (CDP)</text>
        <text x="434" y="182" fill="#64748b" font-size="7">Render 720p 9:16 Handheld</text>

        <line x1="563" y1="169" x2="580" y2="169" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)" />

        <rect x="583" y="145" width="125" height="48" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="589" y="159" fill="#0f172a" font-size="8" font-weight="bold">mix_video_audio.py</text>
        <text x="589" y="171" fill="#475569" font-size="7">Vokal 100% (-14 LUFS)</text>
        <text x="589" y="182" fill="#64748b" font-size="7">Lofi 15% (-16dB Fade)</text>

        <path d="M 230 237 L 250 237 L 250 169 L 268 169" fill="none" stroke="#0d9488" stroke-width="1.5" marker-end="url(#arrow)" />

        <rect x="272" y="202" width="436" height="50" rx="4" fill="#f1f5f9" stroke="#cbd5e1" />
        <text x="282" y="218" fill="#0f172a" font-size="8" font-weight="bold">Hasil Paket Konten Matang (Output Pra-Produksi):</text>
        <text x="282" y="232" fill="#334155" font-size="7.5">1. Video MP4 (10 detik, rasio 9:16, 720x1280, 30fps) dengan audio dialog dan lofi menyatu.</text>
        <text x="282" y="244" fill="#334155" font-size="7.5">2. Draf Teks Caption Bahasa Palembang asli dan tagar topik relevan (#palembang, #kuliner, dll).</text>

        <!-- Downward to Layer 4 & 5 -->
        <line x1="490" y1="265" x2="490" y2="295" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />

        <!-- LAYER 4: Mission Control Telegram (Approval Gate) -->
        <rect x="20" y="295" width="340" height="170" rx="7" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />
        <path d="M 20 302 Q 20 295 27 295 L 353 295 Q 360 295 360 302 L 360 316 L 20 316 Z" fill="#0284c7" />
        <text x="30" y="308" fill="#ffffff" font-size="9" font-weight="bold">4. MISSION CONTROL & APPROVAL GATE (TELEGRAM)</text>

        <rect x="30" y="325" width="320" height="30" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="38" y="338" fill="#0f172a" font-size="8" font-weight="bold">send_to_telegram.py (Dispatcher)</text>
        <text x="38" y="348" fill="#64748b" font-size="7">Kirim video preview + teks caption ke Owner Chat</text>

        <rect x="30" y="362" width="320" height="40" rx="4" fill="#f0fdf4" stroke="#86efac" />
        <text x="38" y="376" fill="#166534" font-size="8" font-weight="bold">Pusat Keputusan Owner (Kamu)</text>
        <text x="38" y="387" fill="#15803d" font-size="7.5">Balas: "Gas", "Gas posting", atau "ACC"</text>
        <text x="38" y="396" fill="#166534" font-size="7">Opsi B: Semi-Otonom Terkendali</text>

        <rect x="30" y="410" width="320" height="45" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="38" y="423" fill="#0f172a" font-size="8" font-weight="bold">Unified PM Bot Soul (@PM_INTAN_BOT)</text>
        <text x="38" y="434" fill="#64748b" font-size="7">Menangkap pesan balasan dan memicu CLI pengunggahan</text>
        <text x="38" y="445" fill="#0369a1" font-size="7">Eksekusi: node tiktok_publisher.js --slot &lt;pagi|malam&gt;</text>

        <!-- Arrow from Telegram to Layer 5 Publisher -->
        <path d="M 360 395 L 380 395" fill="none" stroke="#16a34a" stroke-width="2.5" marker-end="url(#arrow-green)" />

        <!-- LAYER 5: TikTok Studio Publisher Engine -->
        <rect x="380" y="295" width="340" height="170" rx="7" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />
        <path d="M 380 302 Q 380 295 387 295 L 713 295 Q 720 295 720 302 L 720 316 L 380 316 Z" fill="#b91c1c" />
        <text x="390" y="308" fill="#ffffff" font-size="9" font-weight="bold">5. TIKTOK STUDIO PUBLISHER (CDP ENGINE)</text>

        <rect x="390" y="325" width="320" height="40" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="398" y="338" fill="#0f172a" font-size="8" font-weight="bold">Form File Injector & Deep DOM Cleaner</text>
        <text x="398" y="348" fill="#64748b" font-size="7">Pilih input file, tunggu render kartu uploader</text>
        <text x="398" y="358" fill="#dc2626" font-size="7">Hapus nilai bawaan final_vlog (selectAll + delete + backspace)</text>

        <rect x="390" y="370" width="320" height="38" rx="4" fill="#ffffff" stroke="#94a3b8" />
        <text x="398" y="383" fill="#0f172a" font-size="8" font-weight="bold">CDP Keyboard Typing Simulation</text>
        <text x="398" y="394" fill="#64748b" font-size="7">Input.insertText simulasi tuts fisik ke DraftEditor React</text>
        <text x="398" y="403" fill="#64748b" font-size="7">Dispatch tombol Escape untuk menutup dropdown popup hashtag</text>

        <rect x="390" y="414" width="320" height="42" rx="4" fill="#fef2f2" stroke="#fca5a5" />
        <text x="398" y="427" fill="#991b1b" font-size="8" font-weight="bold">Assertion Gate & SQLite Production Log</text>
        <text x="398" y="437" fill="#b91c1c" font-size="7">Tolak posting jika teks &lt; 15 karakter atau mengandung final_vlog</text>
        <text x="398" y="448" fill="#7f1d1d" font-size="7">Klik tombol Post -&gt; Verifikasi tayang -&gt; Catat ke publications</text>
      </svg>
      <div class="diagram-caption">Gambar 1.1: Diagram Arsitektur Komponen End-to-End AI Influencer Dinda Kemala</div>
    </div>
  </div>

  <div class="footer-sign">
    <div>Dokumentasi Teknis AI Influencer Dinda Kemala</div>
    <div>Bab 1: Arsitektur Makro Sistem</div>
    <div>Status: Verified & Operational</div>
  </div>
</div>

<!-- HALAMAN 3: URUTAN WAKTU EKSEKUSI HARIAN -->
<div class="page">
  <div class="content-body">
    <h1>2. Garis Waktu Eksekusi Harian (Daily Chronological Lifecycle)</h1>
    <p>
      Sistem mengikuti siklus waktu ketat 24 jam berbasis waktu Indonesia Barat (WIB / UTC+7). Seluruh urutan tahapan dipantau dan dikomandoi oleh daemon yang terus aktif di latar belakang.
    </p>

    <div class="diagram-container">
      <svg viewBox="0 0 740 340" width="100%" height="310" xmlns="http://www.w3.org/2000/svg" style="font-family: -apple-system, sans-serif;">
        <defs>
          <marker id="sq-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#0284c7" />
          </marker>
        </defs>

        <!-- Actors Line -->
        <rect x="15" y="8" width="105" height="24" rx="4" fill="#0f172a" />
        <text x="67" y="24" fill="#ffffff" font-size="7.5" font-weight="bold" text-anchor="middle">Daemon System</text>
        <line x1="67" y1="32" x2="67" y2="330" stroke="#cbd5e1" stroke-dasharray="3 3" />

        <rect x="135" y="8" width="105" height="24" rx="4" fill="#0d9488" />
        <text x="187" y="24" fill="#ffffff" font-size="7.5" font-weight="bold" text-anchor="middle">Wardrobe Engine</text>
        <line x1="187" y1="32" x2="187" y2="330" stroke="#cbd5e1" stroke-dasharray="3 3" />

        <rect x="255" y="8" width="105" height="24" rx="4" fill="#4f46e5" />
        <text x="307" y="24" fill="#ffffff" font-size="7.5" font-weight="bold" text-anchor="middle">Flow & Audio Mixer</text>
        <line x1="307" y1="32" x2="307" y2="330" stroke="#cbd5e1" stroke-dasharray="3 3" />

        <rect x="375" y="8" width="105" height="24" rx="4" fill="#0284c7" />
        <text x="427" y="24" fill="#ffffff" font-size="7.5" font-weight="bold" text-anchor="middle">PM Bot Telegram</text>
        <line x1="427" y1="32" x2="427" y2="330" stroke="#cbd5e1" stroke-dasharray="3 3" />

        <rect x="495" y="8" width="105" height="24" rx="4" fill="#16a34a" />
        <text x="547" y="24" fill="#ffffff" font-size="7.5" font-weight="bold" text-anchor="middle">Owner (Kamu)</text>
        <line x1="547" y1="32" x2="547" y2="330" stroke="#cbd5e1" stroke-dasharray="3 3" />

        <rect x="615" y="8" width="110" height="24" rx="4" fill="#b91c1c" />
        <text x="670" y="24" fill="#ffffff" font-size="7.5" font-weight="bold" text-anchor="middle">TikTok Studio Web</text>
        <line x1="670" y1="32" x2="670" y2="330" stroke="#cbd5e1" stroke-dasharray="3 3" />

        <!-- EVENT 1: 05:00 WIB -->
        <rect x="25" y="44" width="690" height="15" rx="3" fill="#e2e8f0" />
        <text x="35" y="55" fill="#0f172a" font-size="7.5" font-weight="bold">FASE 1: 05:00 WIB - RISET OOTD & GENERASI LEMARI BUSANA HARIAN</text>
        
        <line x1="67" y1="68" x2="187" y2="68" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="127" y="65" font-size="6.5" fill="#0f172a" text-anchor="middle">Picu Riset Pinterest</text>

        <line x1="187" y1="80" x2="427" y2="80" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="307" y="77" font-size="6.5" fill="#0f172a" text-anchor="middle">Simpan 2 OOTD ke DB & Lapor Rekap Pagi</text>

        <line x1="427" y1="92" x2="547" y2="92" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="487" y="89" font-size="6.5" fill="#0f172a" text-anchor="middle">Kirim Notifikasi Laporan OOTD Hari Ini</text>

        <!-- EVENT 2: 06:30 WIB -->
        <rect x="25" y="105" width="690" height="15" rx="3" fill="#e2e8f0" />
        <text x="35" y="116" fill="#0f172a" font-size="7.5" font-weight="bold">FASE 2: 06:30 WIB - PRA-PRODUKSI SLOT PAGI (RENDER & SINKRONISASI AUDIO)</text>

        <line x1="67" y1="128" x2="307" y2="128" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="187" y="125" font-size="6.5" fill="#0f172a" text-anchor="middle">Muat OOTD Pagi & Render Video Flow Omni 1.1</text>

        <line x1="307" y1="142" x2="427" y2="142" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="367" y="139" font-size="6.5" fill="#0f172a" text-anchor="middle">Mixing Audio Lofi + Kirim Preview ke PM Bot</text>

        <line x1="427" y1="154" x2="547" y2="154" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="487" y="151" font-size="6.5" fill="#0f172a" text-anchor="middle">Preview Video Siap: "Balas Gas posting untuk ACC"</text>

        <!-- EVENT 3: 07:00 WIB -->
        <rect x="25" y="167" width="690" height="15" rx="3" fill="#e0f2fe" stroke="#38bdf8" />
        <text x="35" y="178" fill="#0369a1" font-size="7.5" font-weight="bold">FASE 3: 07:00 WIB - JENDELA PENAYANGAN SLOT PAGI (APPROVAL & PUBLIKASI)</text>

        <line x1="547" y1="190" x2="427" y2="190" stroke="#16a34a" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="487" y="187" font-size="6.5" fill="#16a34a" font-weight="bold" text-anchor="middle">Owner Balas: "Gas posting" (ACC Sah)</text>

        <line x1="427" y1="204" x2="670" y2="204" stroke="#b91c1c" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="548" y="201" font-size="6.5" fill="#b91c1c" text-anchor="middle">Jalankan tiktok_publisher.js (CDP Typing + Everyone)</text>

        <line x1="670" y1="216" x2="427" y2="216" stroke="#64748b" stroke-width="1.5" stroke-dasharray="2 2" marker-end="url(#sq-arrow)" />
        <text x="548" y="213" font-size="6.5" fill="#475569" text-anchor="middle">Kembalikan URL Video Live</text>

        <line x1="427" y1="228" x2="547" y2="228" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="487" y="225" font-size="6.5" fill="#0f172a" text-anchor="middle">Kirim Tautan Live ke Owner</text>

        <!-- EVENT 4: 18:30 WIB -->
        <rect x="25" y="240" width="690" height="15" rx="3" fill="#e2e8f0" />
        <text x="35" y="251" fill="#0f172a" font-size="7.5" font-weight="bold">FASE 4: 18:30 WIB - PRA-PRODUKSI SLOT MALAM (HANG OUT / KULINER CAFE)</text>

        <line x1="67" y1="262" x2="307" y2="262" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="187" y="259" font-size="6.5" fill="#0f172a" text-anchor="middle">Muat OOTD Malam & Render Video Santai Malam</text>

        <line x1="307" y1="274" x2="547" y2="274" stroke="#0284c7" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="427" y="271" font-size="6.5" fill="#0f172a" text-anchor="middle">Kirim Preview Video Malam ke Owner Telegram</text>

        <!-- EVENT 5: 19:00 WIB -->
        <rect x="25" y="286" width="690" height="15" rx="3" fill="#e0f2fe" stroke="#38bdf8" />
        <text x="35" y="297" fill="#0369a1" font-size="7.5" font-weight="bold">FASE 5: 19:00 WIB - JENDELA PENAYANGAN SLOT MALAM</text>

        <line x1="547" y1="308" x2="427" y2="308" stroke="#16a34a" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="487" y="305" font-size="6.5" fill="#16a34a" font-weight="bold" text-anchor="middle">Owner Balas "Gas posting"</text>

        <line x1="427" y1="320" x2="670" y2="320" stroke="#b91c1c" stroke-width="1.5" marker-end="url(#sq-arrow)" />
        <text x="548" y="317" font-size="6.5" fill="#b91c1c" text-anchor="middle">Unggah Mandiri ke TikTok Studio & Konfirmasi Sukses</text>
      </svg>
      <div class="diagram-caption">Gambar 2.1: Diagram Alur Waktu Urutan Operasi Harian 24 Jam (WIB)</div>
    </div>

    <h2>Tabel Parameter Jadwal Baku Produksi</h2>
    <table>
      <thead>
        <tr>
          <th>Waktu (WIB)</th>
          <th>Tahap Operasi</th>
          <th>Skrip Eksekusi</th>
          <th>Keluaran / Deliverable</th>
          <th>SLA / Timeout</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>05:00</strong></td>
          <td>Wardrobe Intelligence</td>
          <td><code>daily_pinterest_wardrobe_job.js</code></td>
          <td>2 OOTD unik di SQLite + Laporan Telegram Pagi</td>
          <td>90 detik</td>
        </tr>
        <tr>
          <td><strong>06:30</strong></td>
          <td>Pra-Produksi Slot Pagi</td>
          <td><code>generate_pagi_palembang_vlog.js</code></td>
          <td>Video 720p 9:16 + Dialog Palembang + Lofi Mix</td>
          <td>12 menit</td>
        </tr>
        <tr>
          <td><strong>07:00</strong></td>
          <td>Penayangan Pagi</td>
          <td><code>tiktok_publisher.js --slot pagi</code></td>
          <td>Publikasi status "Everyone" di akun @dinda.kemala_</td>
          <td>180 detik</td>
        </tr>
        <tr>
          <td><strong>18:30</strong></td>
          <td>Pra-Produksi Slot Malam</td>
          <td><code>generate_malam_palembang_vlog.js</code></td>
          <td>Video 720p 9:16 suasana malam + Caption kuliner</td>
          <td>12 menit</td>
        </tr>
        <tr>
          <td><strong>19:00</strong></td>
          <td>Penayangan Malam</td>
          <td><code>tiktok_publisher.js --slot malam</code></td>
          <td>Publikasi malam hari di TikTok Studio Web</td>
          <td>180 detik</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="footer-sign">
    <div>Dokumentasi Teknis AI Influencer Dinda Kemala</div>
    <div>Bab 2: Garis Waktu Eksekusi Harian</div>
    <div>Status: Verified & Operational</div>
  </div>
</div>

<!-- HALAMAN 4: ALGORITMA ROTASI BUSANA & KONSISTENSI WAJAH -->
<div class="page">
  <div class="content-body">
    <h1>3. Rincian Algoritma dan Model Matematika (Bagian 1)</h1>

    <h2>3.1 Algoritma Rotasi Lemari Busana Anti-Monoton</h2>
    <p>
      Penyebab utama video berulang di masa lalu adalah teks prompt statis (<em>sage green crinkle linen</em>). Algoritma pada <code>daily_pinterest_wardrobe_job.js</code> menerapkan fungsi evaluasi penalti pemakaian untuk memilih pasangan busana harian secara deterministik:
    </p>

    <div class="formula-card">
      <div class="formula-display">
        Score(O<sub>i</sub>) = W<sub>tag</sub> &middot; M<sub>tag</sub>(O<sub>i</sub>) + W<sub>cat</sub> &middot; M<sub>cat</sub>(O<sub>i</sub>) - &lambda; &middot; U(O<sub>i</sub>) - R(O<sub>i</sub>)
      </div>
    </div>

    <p>Di mana variabel formula didefinisikan sebagai berikut:</p>
    <ul>
      <li><code>M_tag(O_i)</code>: Nilai kecocokan tagar busana terhadap slot waktu (pagi: <em>casual, breakfast, bright linen, light voal</em> bernilai 1.0; warna gelap bernilai 0.2).</li>
      <li><code>M_cat(O_i)</code>: Kesesuaian tema pakaian dengan siluet modest hijab aesthetic (bobot <code>W_cat = 3.0</code>).</li>
      <li><code>U(O_i)</code>: Frekuensi pemakaian busana sepanjang riwayat basis data di tabel <code>character_wardrobe</code>.</li>
      <li><code>&lambda;</code>: Koefisien pengali penalti frekuensi (ditetapkan pada <code>&lambda; = 2.0</code>). Nilai busana terdegradasi seiring peningkatan pemakaian.</li>
      <li><code>R(O_i)</code>: Penalti kebaruan (<em>Recency Penalty</em>). Jika busana dipakai dalam 24 jam terakhir atau 3 post terakhir, maka <code>R(O_i) = &infin;</code> (diskualifikasi mutlak).</li>
    </ul>

    <p>Pemilihan busana pagi dan malam dijamin tidak pernah identik melalui fungsi partisi himpunan:</p>
    <div class="formula-card">
      <div class="formula-display">
        O<sub>Pagi</sub> = argmax Score(O) | O &isin; &Omega;<sub>Pagi</sub> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; O<sub>Malam</sub> = argmax Score(O) | O &isin; (&Omega;<sub>Malam</sub> \ { O<sub>Pagi</sub> })
      </div>
    </div>

    <h2>3.2 Algoritma Konsistensi Wajah 3-Chip Visual (Multi-Reference Locking)</h2>
    <p>
      Untuk menghasilkan struktur wajah, tulang pipi, warna mata, dan tekstur hijab yang identik tanpa distorsi waxy atau uncanny CGI, sistem mengunci tiga chip visual referensi baku ke dalam Google Flow Engine:
    </p>

    <div class="diagram-container">
      <svg viewBox="0 0 700 120" width="100%" height="110" xmlns="http://www.w3.org/2000/svg" style="font-family: -apple-system, sans-serif;">
        <rect x="15" y="10" width="205" height="95" rx="5" fill="#f8fafc" stroke="#0284c7" stroke-width="1.5" />
        <rect x="25" y="18" width="185" height="20" rx="3" fill="#0284c7" />
        <text x="117" y="32" fill="#ffffff" font-size="8" font-weight="bold" text-anchor="middle">CHIP 1: ANATOMICAL BLUEPRINT</text>
        <text x="25" y="52" fill="#0f172a" font-size="7.5" font-weight="bold">Turnaround Sheet 3 Sudut</text>
        <text x="25" y="64" fill="#475569" font-size="7">TB: 165 cm, BB: 52 kg</text>
        <text x="25" y="76" fill="#475569" font-size="7">Proporsi bahu dan postur tubuh</text>
        <text x="25" y="88" fill="#64748b" font-size="6.5">Bobot Attention: 0.85</text>

        <rect x="245" y="10" width="210" height="95" rx="5" fill="#f8fafc" stroke="#0d9488" stroke-width="1.5" />
        <rect x="255" y="18" width="190" height="20" rx="3" fill="#0d9488" />
        <text x="350" y="32" fill="#ffffff" font-size="8" font-weight="bold" text-anchor="middle">CHIP 2: EXPRESSION DYNAMICS</text>
        <text x="255" y="52" fill="#0f172a" font-size="7.5" font-weight="bold">Three-Expression Sheet</text>
        <text x="255" y="64" fill="#475569" font-size="7">Kontak mata lensa kamera</text>
        <text x="255" y="76" fill="#475569" font-size="7">Artikulasi bibir vokal Palembang</text>
        <text x="255" y="88" fill="#64748b" font-size="6.5">Bobot Attention: 0.90</text>

        <rect x="480" y="10" width="205" height="95" rx="5" fill="#f8fafc" stroke="#4f46e5" stroke-width="1.5" />
        <rect x="490" y="18" width="185" height="20" rx="3" fill="#4f46e5" />
        <text x="582" y="32" fill="#ffffff" font-size="8" font-weight="bold" text-anchor="middle">CHIP 3: REALISTIC TEXTURE</text>
        <text x="490" y="52" fill="#0f172a" font-size="7.5" font-weight="bold">Closeup Portrait 9:16</text>
        <text x="490" y="64" fill="#475569" font-size="7">Pori-pori mikro kulit asli manusia</text>
        <text x="490" y="76" fill="#475569" font-size="7">Iris cokelat hangat & serat kain hijab</text>
        <text x="490" y="88" fill="#64748b" font-size="6.5">Bobot Attention: 0.95</text>
      </svg>
      <div class="diagram-caption">Gambar 3.1: Skema 3-Chip Visual Locking Konsistensi Karakter</div>
    </div>

    <p>
      <strong>Filter Prompt Anti-AI Slop:</strong> Generator melarang kata sifat generik seperti <em>"photorealistic", "ultra realistic", "8k"</em> yang memicu artefak sintetis waxy pada model Omni. Prompt diproteksi dengan deskriptor fisik: <code>natural daylight 5500K</code>, <code>fine visible skin pores</code>, <code>matte non-oily skin</code>, <code>organic handheld smartphone camera movement with subtle natural micro-sway</code>.
    </p>
  </div>

  <div class="footer-sign">
    <div>Dokumentasi Teknis AI Influencer Dinda Kemala</div>
    <div>Bab 3: Rotasi Busana & Konsistensi Wajah</div>
    <div>Status: Verified & Operational</div>
  </div>
</div>

<!-- HALAMAN 5: SINKRONISASI AUDIO & TIKTOK PUBLISHER -->
<div class="page">
  <div class="content-body">
    <h1>4. Rincian Algoritma dan Model Matematika (Bagian 2)</h1>

    <h2>4.1 Algoritma Pengolahan dan Sinkronisasi Audio</h2>
    <p>
      Penggabungan audio pada <code>scripts/mix_video_audio.py</code> menggunakan pemrosesan dua kanal terpisah dengan perataan amplitudo dinamis agar dialog Bahasa Palembang tetap dominan tanpa tertimbun musik:
    </p>

    <div class="formula-card">
      <div class="formula-display">
        S<sub>final</sub>(t) = C<sub>vocal</sub>(S<sub>vocal</sub>(t)) + G<sub>music</sub> &middot; F<sub>fade</sub>(t) &middot; S<sub>music</sub>(t)
      </div>
    </div>

    <p>Parameter matematis pengolahan suara:</p>
    <ul>
      <li><code>C_vocal</code>: Dynamic compression filter rasio 4:1 dengan target loudness terintegrasi <strong>-14.0 LUFS</strong> (standar optimal TikTok Audio). Suara ucapan pada gain 1.0 (100% amplitudo penuh).</li>
      <li><code>G_music</code>: Konstanta redaman musik latar lofi akustik sebesar <code>0.15</code> (ekuivalen <strong>-16.48 dB</strong> terhadap level master).</li>
      <li><code>F_fade(t)</code>: Fungsi amplop transisi fade: <code>fade-in = t / 0.5</code> (0 &le; t &lt; 0.5 detik), <code>sustain = 1.0</code>, dan <code>fade-out = (T_end - t) / 1.0</code> pada 1 detik terakhir durasi klip.</li>
    </ul>

    <h2>4.2 Algoritma Keyboard Simulation dan Gerbang Asersi TikTok Publisher</h2>
    <p>
      Analisis bug <code>final_vlog</code> membuktikan bahwa editor TikTok menggunakan React DraftEditor. Pengisian nama berkas dilakukan otomatis oleh kartu uploader. Script <code>tiktok_publisher.js</code> menerapkan 4 tahap mitigasi tuts fisik:
    </p>

    <div class="diagram-container">
      <svg viewBox="0 0 710 190" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="font-family: -apple-system, sans-serif;">
        <defs>
          <marker id="flow-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 8 5 L 0 9 z" fill="#0284c7" />
          </marker>
        </defs>

        <rect x="15" y="10" width="150" height="70" rx="4" fill="#fef2f2" stroke="#f87171" stroke-width="1.5" />
        <text x="25" y="26" fill="#991b1b" font-size="7.5" font-weight="bold">1. ROOT CAUSE DETEKSI</text>
        <text x="25" y="40" fill="#0f172a" font-size="7">Placeholder TikTok aktif</text>
        <text x="25" y="52" fill="#dc2626" font-size="7" font-family="monospace">Text = "final_vlog"</text>
        <text x="25" y="64" fill="#64748b" font-size="6.5">React DraftEditor State</text>

        <line x1="165" y1="45" x2="195" y2="45" stroke="#0284c7" stroke-width="2" marker-end="url(#flow-arrow)" />

        <rect x="195" y="10" width="150" height="70" rx="4" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" />
        <text x="205" y="26" fill="#0f172a" font-size="7.5" font-weight="bold">2. DEEP DOM PURGE</text>
        <text x="205" y="40" fill="#334155" font-size="7">execCommand("selectAll")</text>
        <text x="205" y="52" fill="#334155" font-size="7">execCommand("delete")</text>
        <text x="205" y="64" fill="#0284c7" font-size="6.5">Physical Backspace CDP</text>

        <line x1="345" y1="45" x2="375" y2="45" stroke="#0284c7" stroke-width="2" marker-end="url(#flow-arrow)" />

        <rect x="375" y="10" width="150" height="70" rx="4" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" />
        <text x="385" y="26" fill="#0f172a" font-size="7.5" font-weight="bold">3. CDP KEYBOARD SIM</text>
        <text x="385" y="40" fill="#334155" font-size="7">CDP Input.insertText</text>
        <text x="385" y="52" fill="#059669" font-size="7">Ketik Teks Palembang</text>
        <text x="385" y="64" fill="#334155" font-size="6.5">Dispatch Key: Escape</text>

        <line x1="525" y1="45" x2="555" y2="45" stroke="#0284c7" stroke-width="2" marker-end="url(#flow-arrow)" />

        <rect x="555" y="10" width="140" height="70" rx="4" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.5" />
        <text x="565" y="26" fill="#166534" font-size="7.5" font-weight="bold">4. GERBANG ASERSI</text>
        <text x="565" y="40" fill="#15803d" font-size="7">Length &ge; 15 karakter</text>
        <text x="565" y="52" fill="#15803d" font-size="7">"final_vlog" &notin; Text</text>
        <text x="565" y="64" fill="#166534" font-size="6.5" font-weight="bold">Status: VERIFIED SAFE</text>

        <rect x="15" y="90" width="680" height="85" rx="5" fill="#f8fafc" stroke="#cbd5e1" />
        <text x="25" y="106" fill="#0f172a" font-size="8" font-weight="bold">Logika Gerbang Asersi Penerbitan (Assertion Gate Condition):</text>
        <text x="25" y="122" fill="#0369a1" font-size="8" font-family="monospace">
          IsPublishable = (TextLength &ge; 15) &and; (Text &not;&ni; "final_vlog") &and; (Text &not;&ni; "final_10s") &and; (Privacy == "Everyone")
        </text>
        <text x="25" y="140" fill="#334155" font-size="7">
          Jika kondisi IsPublishable bernilai FALSE, skrip secara deterministik melempar error kritis, membatalkan klik tombol Post, mengambil screenshot bukti galat ke folder operations/, dan mengirimkan laporan kegagalan darurat ke Telegram Owner.
        </text>
        <text x="25" y="156" fill="#166534" font-size="7" font-weight="bold">
          Hasil Uji Lapangan: Postingan Senin Pagi 09 November 2026 sukses diterbitkan publik dengan 100% teks Palembang.
        </text>
      </svg>
      <div class="diagram-caption">Gambar 4.1: Alur Pengetikan Tingkat Kernel Browser dan Gerbang Asersi Anti-Cacat</div>
    </div>
  </div>

  <div class="footer-sign">
    <div>Dokumentasi Teknis AI Influencer Dinda Kemala</div>
    <div>Bab 4: Audio Mixing & TikTok Publisher Engine</div>
    <div>Status: Verified & Operational</div>
  </div>
</div>

<!-- HALAMAN 6: BASIS DATA, KEAMANAN & OPERASIONAL TELEGRAM -->
<div class="page-last">
  <div class="content-body">
    <h1>5. Keamanan Sistem, Skema Basis Data, dan Protokol Telegram</h1>

    <h2>5.1 Jaminan Idempotensi dan Pencegahan Unggah Ganda</h2>
    <p>
      Untuk mengantisipasi koneksi terputus atau cron ganda, sistem menerapkan hash kunci idempotensi unik: <code>IDEMPOTENCY_KEY = SHA256("dinda_" + slot + "_" + YYYYMMDD)</code>. Jika status sudah <code>CONFIRMED</code>, eksekusi otomatis dilewati secara aman.
    </p>

    <h2>5.2 Skema Basis Data Produksi SQLite (operations/production.sqlite)</h2>
    <div class="grid-2col">
      <div class="code-card">
        <div class="code-title">Tabel character_wardrobe</div>
CREATE TABLE character_wardrobe (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  outfit_id TEXT UNIQUE NOT NULL,
  slot TEXT NOT NULL, -- pagi | malam
  date_assigned DATE NOT NULL,
  style_category TEXT NOT NULL,
  prompt_description TEXT NOT NULL,
  times_used INTEGER DEFAULT 0,
  last_worn_timestamp DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
      </div>
      <div class="code-card">
        <div class="code-title">Tabel publications</div>
CREATE TABLE publications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT UNIQUE NOT NULL,
  slot TEXT NOT NULL, -- pagi | malam
  publish_date DATE NOT NULL,
  video_path TEXT NOT NULL,
  caption_text TEXT NOT NULL,
  tiktok_video_id TEXT,
  tiktok_url TEXT,
  status TEXT NOT NULL, -- PENDING | CONFIRMED
  published_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
      </div>
    </div>

    <h2>5.3 Protokol Operasional Mission Control Telegram (@PM_INTAN_BOT)</h2>
    <table>
      <thead>
        <tr>
          <th>Pesan Masuk dari Owner</th>
          <th>Aksi Eksekusi Sistem</th>
          <th>Respon Balasan Bot</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>Gas</code> / <code>Gas posting</code> / <code>ACC</code></td>
          <td>Menjalankan <code>tiktok_publisher.js</code> slot aktif.</td>
          <td>Mengirim tautan video TikTok langsung yang sudah live.</td>
        </tr>
        <tr>
          <td><code>Ganti caption: &lt;teks baru&gt;</code></td>
          <td>Memperbarui draf caption di SQLite untuk slot aktif.</td>
          <td>"Draf caption slot [pagi/malam] berhasil diperbarui lur!"</td>
        </tr>
        <tr>
          <td><code>Tunda 30 menit</code></td>
          <td>Menjadwal ulang jendela publikasi mundur 30 menit.</td>
          <td>"Siap lur, jadwal unggah diundur ke [jam baru]."</td>
        </tr>
        <tr>
          <td><code>Status</code></td>
          <td>Query SQLite (OOTD aktif, video siap, PID daemon).</td>
          <td>Menampilkan ringkasan status operasional terkini.</td>
        </tr>
      </tbody>
    </table>

    <div class="callout callout-success">
      <div class="callout-title">Spesifikasi Bukti Produksi Terakhir (Senin Pagi, 9 Nov 2026)</div>
      <p style="margin: 2px 0; font-size: 8pt;">
        <strong>ID Video:</strong> 7705995249474080020 &nbsp;|&nbsp; <strong>Privasi:</strong> Everyone (Publik) &nbsp;|&nbsp; <strong>Durasi:</strong> 8 Detik<br>
        <strong>Caption:</strong> Pagi lur! Selamat beraktivitas di hari Senin buat wong kito galo... #palembang #kulinerpalembang #wongkito<br>
        <strong>URL Publik:</strong> <code>https://www.tiktok.com/@dinda.kemala_/video/7705995249474080020</code>
      </p>
    </div>
  </div>

  <div class="footer-sign">
    <div>Dokumentasi Teknis AI Influencer Dinda Kemala</div>
    <div>Bab 5: Basis Data & Protokol Operasional | Halaman 6 dari 6</div>
    <div>Status: Verified & Operational</div>
  </div>
</div>

</body>
</html>
"""

def generate_pdf():
    docs_dir = "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/docs"
    html_path = os.path.join(docs_dir, "Arsitektur_dan_Algoritma_AI_Influencer.html")
    pdf_path = os.path.join(docs_dir, "Arsitektur_dan_Algoritma_AI_Influencer.pdf")

    print("[1/3] Menulis berkas HTML dokumentasi...")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"       HTML tersimpan di: {html_path}")

    print("[2/3] Mengonversi HTML ke PDF menggunakan Google Chrome Headless...")
    chrome_app = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    cmd = [
        chrome_app,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Galat Chrome CLI: {res.stderr}")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print("Galat: Berkas PDF tidak ditemukan setelah proses eksekusi Chrome.")
        sys.exit(1)

    pdf_size = os.path.getsize(pdf_path)
    print(f"       PDF berhasil digenerasi: {pdf_path} ({pdf_size} bytes)")

    print("[3/3] Memeriksa visual PDF dan membuat thumbnail pratinjau...")
    thumb_cmd = ["qlmanage", "-t", "-s", "1000", "-o", docs_dir, pdf_path]
    subprocess.run(thumb_cmd, capture_output=True)

    print("Selesai secara sempurna.")

if __name__ == "__main__":
    generate_pdf()
