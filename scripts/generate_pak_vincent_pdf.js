const fs = require('fs');
const { execSync } = require('child_process');

function toBase64(filePath, mimeType) {
  const data = fs.readFileSync(filePath);
  return `data:${mimeType};base64,${data.toString('base64')}`;
}

const avatarB64 = toBase64('/Users/zidane/Documents/ChatGPT/AI INFLUENCER/FOTO_KARAKTER/PakVincent/pakvincent_profile_avatar.jpg', 'image/jpeg');
const expressionsB64 = toBase64('/Users/zidane/Documents/ChatGPT/AI INFLUENCER/FOTO_KARAKTER/PakVincent/pakvincent_three_expression_sheet.jpg', 'image/jpeg');
const turnaroundB64 = toBase64('/Users/zidane/Documents/ChatGPT/AI INFLUENCER/FOTO_KARAKTER/PakVincent/pakvincent_fullbody_turnaround.jpg', 'image/jpeg');
const chelseaB64 = toBase64('/Users/zidane/Documents/ChatGPT/AI INFLUENCER/FOTO_KARAKTER/PakVincent/pakvincent_sawit_chelsea.jpg', 'image/jpeg');
const postScreenshotB64 = toBase64('/Users/zidane/.gemini/antigravity/brain/1d8aaf1c-ff3e-43b9-b260-17526da4d660/verified_post.png', 'image/png');

const htmlContent = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Laporan Eksekutif Peluncuran Agen TikTok: Pak Vincent</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    @page {
      size: A4 portrait;
      margin: 12mm 12mm 12mm 12mm;
    }

    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      color: #1e293b;
      background-color: #ffffff;
      line-height: 1.45;
      font-size: 9.5pt;
      margin: 0;
      padding: 0;
    }

    .page {
      page-break-after: always;
      position: relative;
      height: 272mm;
      max-height: 272mm;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .page:last-child {
      page-break-after: avoid;
    }

    .content-area {
      flex: 1;
    }

    /* Header banner styling */
    .header-banner {
      background: linear-gradient(135deg, #0f3822 0%, #1b4332 55%, #2d6a4f 100%);
      color: #ffffff;
      padding: 16px 20px;
      border-radius: 10px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-left: 5px solid #d4a373;
    }

    .header-info h1 {
      margin: 0 0 3px 0;
      font-size: 16pt;
      font-weight: 800;
      letter-spacing: -0.4px;
      color: #ffffff;
    }

    .header-info p {
      margin: 0;
      font-size: 9pt;
      color: #d8f3dc;
      font-weight: 500;
    }

    .header-badge {
      text-align: right;
    }

    .badge-status {
      display: inline-block;
      background-color: #52b788;
      color: #081c15;
      font-weight: 700;
      font-size: 8pt;
      padding: 4px 10px;
      border-radius: 16px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .badge-date {
      margin-top: 4px;
      font-size: 8pt;
      color: #d8f3dc;
    }

    /* Page 2 & 3 compact header */
    .mini-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 8px;
      border-bottom: 2px solid #2d6a4f;
      margin-bottom: 12px;
    }

    .mini-header-title {
      font-size: 11pt;
      font-weight: 800;
      color: #1b4332;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .mini-header-meta {
      font-size: 8pt;
      font-family: 'JetBrains Mono', monospace;
      color: #64748b;
    }

    /* Section title styling */
    .section-title {
      font-size: 11pt;
      font-weight: 800;
      color: #1b4332;
      border-bottom: 1.5px solid #e2e8f0;
      padding-bottom: 4px;
      margin-top: 10px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .section-title::before {
      content: "";
      display: inline-block;
      width: 7px;
      height: 7px;
      background-color: #2d6a4f;
      border-radius: 2px;
    }

    /* Grids */
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 8px;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 8px;
      margin-bottom: 8px;
    }

    .grid-4 {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 8px;
      margin-bottom: 8px;
    }

    .card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px;
    }

    .card-accent {
      border-left: 3.5px solid #2d6a4f;
      background: #f4fbf7;
    }

    .card h3 {
      margin: 0 0 4px 0;
      font-size: 9.5pt;
      font-weight: 700;
      color: #1e293b;
    }

    /* Profile hero card */
    .profile-hero {
      display: flex;
      gap: 14px;
      align-items: center;
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 8px;
      padding: 10px 14px;
      margin-bottom: 10px;
    }

    .profile-avatar {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      object-fit: cover;
      border: 2.5px solid #2d6a4f;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .profile-details {
      flex: 1;
    }

    .profile-details h2 {
      margin: 0 0 2px 0;
      font-size: 13pt;
      color: #0f3822;
    }

    .profile-details .handle {
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.5pt;
      font-weight: 700;
      color: #2d6a4f;
      background: #dcfce7;
      padding: 1px 7px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 4px;
    }

    .profile-details p {
      margin: 0;
      font-size: 8.5pt;
      color: #334155;
    }

    /* Tables */
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 8.5pt;
      margin-bottom: 8px;
    }

    table.data-table th, table.data-table td {
      padding: 5px 8px;
      border: 1px solid #e2e8f0;
      text-align: left;
    }

    table.data-table th {
      background-color: #f1f5f9;
      color: #334155;
      font-weight: 700;
    }

    table.data-table tr:nth-child(even) td {
      background-color: #f8fafc;
    }

    .badge-pill {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 10px;
      font-size: 7.5pt;
      font-weight: 700;
    }

    .badge-green { background: #dcfce7; color: #166534; }
    .badge-blue { background: #dbeafe; color: #1e40af; }
    .badge-amber { background: #fef3c7; color: #92400e; }

    /* Quote Box */
    .quote-box {
      background: #f8fafc;
      border-left: 3.5px solid #d4a373;
      padding: 8px 12px;
      border-radius: 0 6px 6px 0;
      font-style: italic;
      color: #334155;
      font-size: 8.5pt;
      margin: 6px 0;
    }

    /* Images */
    .img-box {
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      overflow: hidden;
      background: #ffffff;
    }

    .img-box img {
      width: 100%;
      display: block;
      object-fit: cover;
    }

    .img-box .caption {
      padding: 4px 6px;
      font-size: 7.5pt;
      font-weight: 600;
      color: #475569;
      background: #f8fafc;
      text-align: center;
      border-top: 1px solid #e2e8f0;
    }

    /* Callout */
    .callout-success {
      background-color: #ecfdf5;
      border: 1px solid #a7f3d0;
      border-radius: 6px;
      padding: 8px 12px;
      margin: 8px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .callout-success-text h4 {
      margin: 0 0 2px 0;
      color: #065f46;
      font-size: 9pt;
      font-weight: 700;
    }

    .callout-success-text p {
      margin: 0;
      color: #047857;
      font-size: 8pt;
    }

    .footer {
      padding-top: 6px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      font-size: 7.5pt;
      color: #94a3b8;
    }
  </style>
</head>
<body>

  <!-- ==================== HALAMAN 1 ==================== -->
  <div class="page">
    <div class="content-area">
      <div class="header-banner">
        <div class="header-info">
          <h1>LAPORAN PELUNCURAN AGEN TIKTOK</h1>
          <p>Karakter Otonom AI: Pak Vincent (@pakvincent.riau) — Pekanbaru, Riau</p>
        </div>
        <div class="header-badge">
          <span class="badge-status">STATUS: RESMI TERBIT</span>
          <div class="badge-date">Rabu, 11 November 2026</div>
        </div>
      </div>

      <!-- Profil Utama -->
      <div class="profile-hero">
        <img src="${avatarB64}" class="profile-avatar" alt="Avatar Pak Vincent">
        <div class="profile-details">
          <h2>Vincentius (Pak Vincent)</h2>
          <span class="handle">@pakvincent.riau</span>
          <p><strong>Peran:</strong> Praktisi & Pekerja Perkebunan Kelapa Sawit (35 Tahun) | Pekanbaru, Riau</p>
          <p><strong>Ciri Khas:</strong> Sosok bersahaja, senyum ramah tulus, sapaan dua jari (peace sign), jersey vintage biru Samsung Chelsea, perawakan kurus liat (168 cm / 58 kg), kulit sawo matang gelap terbakar matahari.</p>
        </div>
      </div>

      <!-- Ringkasan Eksekutif -->
      <div class="section-title">1. Ringkasan Eksekutif & Key Metrics Peluncuran</div>
      <p style="margin-top: 0; margin-bottom: 6px; font-size: 8.5pt; color: #334155;">
        Pada <strong>11 November 2026</strong>, sistem dapur operasional AI Influencer secara resmi meluncurkan agen media sosial ke-4: <strong>Pak Vincent</strong> pada akun TikTok <strong><code>@pakvincent.riau</code></strong>. Seluruh rangkaian pendaftaran karakter, verifikasi master visual, riset topik sawit Riau, pembuatan video perdana di Google Flow, pasca-produksi AI Vulkan M4, otorisasi Telegram ACC, dan penerbitan live telah 100% terlaksana tanpa kendala.
      </p>

      <div class="grid-4">
        <div class="card card-accent">
          <h3>Video Perdana</h3>
          <p style="margin: 0; font-size: 10pt; font-weight: 800; color: #166534;">LIVE PUBLISHED</p>
          <p style="margin: 2px 0 0 0; font-size: 7.5pt; color: #64748b;">ID: 7706823640918019349</p>
        </div>
        <div class="card card-accent">
          <h3>Kualitas Video</h3>
          <p style="margin: 0; font-size: 10pt; font-weight: 800; color: #166534;">1080x1920 (9:16)</p>
          <p style="margin: 2px 0 0 0; font-size: 7.5pt; color: #64748b;">Varian 3 Hybrid M4</p>
        </div>
        <div class="card card-accent">
          <h3>Kebijakan Teks</h3>
          <p style="margin: 0; font-size: 10pt; font-weight: 800; color: #166534;">0% Emoji & Koma</p>
          <p style="margin: 2px 0 0 0; font-size: 7.5pt; color: #64748b;">Editorial TikTok Style</p>
        </div>
        <div class="card card-accent">
          <h3>Akun Google Flow</h3>
          <p style="margin: 0; font-size: 10pt; font-weight: 800; color: #166534;">FLOW 5 TERHUBUNG</p>
          <p style="margin: 2px 0 0 0; font-size: 7.5pt; color: #64748b;">pemuda008899@gmail.com</p>
        </div>
      </div>

      <!-- Spesifikasi Karakter -->
      <div class="section-title">2. Identitas Karakter & Persona Digital</div>
      <table class="data-table">
        <tr>
          <th style="width: 24%;">Parameter</th>
          <th style="width: 36%;">Nilai Spesifikasi</th>
          <th style="width: 40%;">Catatan Operasional & Guardrail</th>
        </tr>
        <tr>
          <td><strong>Nama Karakter</strong></td>
          <td>Vincentius / Pak Vincent (Pak Vinsen)</td>
          <td>Panggilan akrab komunitas: "Pak Vincent" atau "Pak Vinsen".</td>
        </tr>
        <tr>
          <td><strong>Usia & Fisik</strong></td>
          <td>35 Tahun | 168 cm | 58 kg</td>
          <td>Perawakan liat pekerja lapangan, kulit sawo matang gelap terbakar matahari.</td>
        </tr>
        <tr>
          <td><strong>Domisili</strong></td>
          <td>Pekanbaru, Riau</td>
          <td>Kawasan perkebunan kelapa sawit dan jalan poros tanah merah pedalaman Riau.</td>
        </tr>
        <tr>
          <td><strong>Kostum Signature</strong></td>
          <td>Jersey bola vintage biru Samsung Chelsea, celana pendek abu-abu, topi baseball cap, sandal karet kebun</td>
          <td>Kostum kerja sehari-hari khas pekerja kebun, praktis dan membumi.</td>
        </tr>
        <tr>
          <td><strong>Tone of Voice</strong></td>
          <td>Santai, bersahaja, hangat, jujur, mengayomi</td>
          <td>Tutur kata ramah khas Riau/Sumatera ("Wak", "Kawan-kawan", "Sehat-sehat ya").</td>
        </tr>
        <tr>
          <td><strong>Aturan Emoji</strong></td>
          <td><span class="badge-pill badge-green">0% Emoji (Strict)</span></td>
          <td>Wajib teks alfabet murni 100% pada caption, naskah narasi, dan komentar.</td>
        </tr>
      </table>

      <!-- Galeri Master Visual -->
      <div class="section-title">3. Master Visual Karakter Terverifikasi</div>
      <div class="grid-3">
        <div class="img-box">
          <img src="${expressionsB64}" style="height: 155px;" alt="Three Expression Sheet">
          <div class="caption">Three-Expression Master (Netral, Senyum, Serius)</div>
        </div>
        <div class="img-box">
          <img src="${turnaroundB64}" style="height: 155px;" alt="Fullbody Turnaround">
          <div class="caption">Fullbody Turnaround (Depan, Samping, Belakang)</div>
        </div>
        <div class="img-box">
          <img src="${chelseaB64}" style="height: 155px;" alt="Sawit Chelsea Pose">
          <div class="caption">Candid Signature: Jersey Chelsea di Kebun Sawit</div>
        </div>
      </div>
    </div>

    <div class="footer">
      <span>Dapur Operasional AI Influencer &copy; 2026</span>
      <span>Dokumen Resmi &mdash; Halaman 1 dari 3</span>
    </div>
  </div>

  <!-- ==================== HALAMAN 2 ==================== -->
  <div class="page">
    <div class="content-area">
      <div class="mini-header">
        <div class="mini-header-title">Riset Niche Perkebunan Riau & Guardrail Konten</div>
        <div class="mini-header-meta">DOKUMEN OPERASIONAL: PAK VINCENT (@pakvincent.riau)</div>
      </div>

      <!-- 4 Pilar Konten -->
      <div class="section-title">4. Empat Pilar Konten Perkebunan Sawit Riau</div>
      <div class="grid-2">
        <div class="card">
          <h3>1. Ladang Sawit & Motor Langsir</h3>
          <p style="margin: 0; font-size: 8pt; color: #475569;">
            Keseharian panen TBS (Tandan Buah Segar), perjuangan motor langsir modifikasi beban 400 kg melibas jalan poros tanah merah berlumpur sehabis hujan lebat, teknik dodos vs egrek, perawatan pohon dan pemupukan saat musim trek.
          </p>
        </div>
        <div class="card">
          <h3>2. Dinamika PKS & Timbangan RAM</h3>
          <p style="margin: 0; font-size: 8pt; color: #475569;">
            Dinamika sortir buah di Pabrik Kelapa Sawit (PKS) dan timbangan RAM pengepul, aturan potongan tangkai panjang, tips buah matang sempurna, update harga resmi TBS Disbun Riau tanpa spekulasi liar.
          </p>
        </div>
        <div class="card">
          <h3>3. Perbandingan Karet vs Sawit</h3>
          <p style="margin: 0; font-size: 8pt; color: #475569;">
            Nostalgia deres getah karet subuh di pedalaman Riau, dinamika alih fungsi lahan karet ke sawit, perbandingan pendapatan harian getah mangkok vs gajian bulanan panen sawit.
          </p>
        </div>
        <div class="card">
          <h3>4. Keseharian Bersahaja & Positivitas</h3>
          <p style="margin: 0; font-size: 8pt; color: #475569;">
            Suasana ngopi pagi di gubuk kebun, membuka rantang bekal makan siang bersama kawan buruh, rasa syukur atas rezeki halal, serta sapaan dua jari penyejuk hati untuk sesama pekerja lapangan.
          </p>
        </div>
      </div>

      <!-- Riset Lapangan Detail -->
      <div class="section-title">5. Riset Lapangan Regional Pekanbaru & Pedalaman Riau</div>
      <table class="data-table">
        <tr>
          <th style="width: 25%;">Topik Regional</th>
          <th style="width: 45%;">Fakta Lapangan & Wawasan Kultural</th>
          <th style="width: 30%;">Sudut Pandang Konten Pak Vincent</th>
        </tr>
        <tr>
          <td><strong>Motor Langsir Sawit</strong></td>
          <td>Motor bebek tua (biasanya modifikasi rangka bebek trail/Revo/Supra) dengan keranjang besi samping, ban cangkul, sanggup membawa 300–400 kg TBS melintasi jalan tanah merah berbukit.</td>
          <td>Edukasi modifikasi gir rantai, shockbreaker ganda, dan teknik melewati kubangan tanah merah tanpa terbalik.</td>
        </tr>
        <tr>
          <td><strong>Alat Panen (Dodos vs Egrek)</strong></td>
          <td>Dodos digunakan untuk pohon sawit muda/rendah (&lt;5 meter), sedangkan egrek sabit bertongkai panjang untuk pohon tinggi (&gt;5 meter).</td>
          <td>Teknik mengasah mata dodos agar sekali hentak tangkai buah putus rapi tanpa melukai pelepah produktif.</td>
        </tr>
        <tr>
          <td><strong>Sortir RAM & PKS</strong></td>
          <td>PKS menolak buah mentah (buah hitam) dan memotong tonase bila tangkai buah melebihi 2,5 cm (tangkai panjang).</td>
          <td>Edukasi petani swadaya agar buah tidak kena penalti timbangan dan potongan di pabrik kelapa sawit.</td>
        </tr>
        <tr>
          <td><strong>Musim Trek Sawit</strong></td>
          <td>Periode produksi buah menurun drastis karena siklus biologis dan cuaca kemarau panjang.</td>
          <td>Motivasi dan kiat manajemen pemupukan serta perawatan piringan sawit agar pohon cepat pulih.</td>
        </tr>
      </table>

      <!-- Guardrail & Kebijakan Ketat -->
      <div class="section-title">6. Guardrail Kebijakan Operasional & Larangan Keras</div>
      <div class="grid-2">
        <div class="card card-accent">
          <h3>Kebijakan Teks & Bahasa</h3>
          <ul style="margin: 0; padding-left: 16px; font-size: 8pt; color: #334155;">
            <li><strong>Aturan No-Emoji (0% Emoji):</strong> Dilarang keras menggunakan emoji atau emotikon apa pun dalam caption, naskah narasi, subtitle ASS, maupun balasan komentar.</li>
            <li><strong>Bahasa Santai Regional:</strong> Menggunakan gaya tutur ramah Sumatera/Riau yang wajar dan membumi, tanpa menggunakan bahasa gaul metropolitan yang tidak cocok dengan persona pekerja kebun.</li>
            <li><strong>Bebas Tanda Koma di Subtitle:</strong> Subtitle video menggunakan formula 2-tier editorial_tiktok tanpa tanda koma agar cepat dibaca audiens ponsel.</li>
          </ul>
        </div>
        <div class="card card-accent">
          <h3>Guardrail Akun & Finansial</h3>
          <ul style="margin: 0; padding-left: 16px; font-size: 8pt; color: #334155;">
            <li><strong>Wajib Gerbang ACC Owner:</strong> Dilarang mempublikasikan video atau postingan apa pun tanpa keputusan approval eksplisit dari Owner di Telegram.</li>
            <li><strong>Batas Durasi & Kredit Flow:</strong> Maksimal durasi 20 detik per video, resolusi input Flow wajib 360p (Omni Flash hemat kredit). Dilarang retry berbayar otomatis.</li>
            <li><strong>Perlindungan Privasi:</strong> Dilarang membagikan rekening pribadi, kontak rahasia, atau membuat janji transaksi komersial tanpa persetujuan Owner.</li>
          </ul>
        </div>
      </div>
    </div>

    <div class="footer">
      <span>Dapur Operasional AI Influencer &copy; 2026</span>
      <span>Dokumen Resmi &mdash; Halaman 2 dari 3</span>
    </div>
  </div>

  <!-- ==================== HALAMAN 3 ==================== -->
  <div class="page">
    <div class="content-area">
      <div class="mini-header">
        <div class="mini-header-title">Produksi Video Perdana, Publikasi Live & Integrasi Agen</div>
        <div class="mini-header-meta">DOKUMEN OPERASIONAL: PAK VINCENT (@pakvincent.riau)</div>
      </div>

      <!-- Laporan Teknis Video Perdana -->
      <div class="section-title">7. Laporan Teknis Produksi Video Perdana (Debut Post)</div>
      <div class="grid-2" style="align-items: start;">
        <div>
          <table class="data-table" style="margin-bottom: 6px;">
            <tr>
              <td style="width: 38%;"><strong>Platform</strong></td>
              <td>TikTok (@pakvincent.riau)</td>
            </tr>
            <tr>
              <td><strong>Status Publikasi</strong></td>
              <td><span class="badge-pill badge-green">LIVE CONFIRMED</span></td>
            </tr>
            <tr>
              <td><strong>Numeric Video ID</strong></td>
              <td><code>7706823640918019349</code></td>
            </tr>
            <tr>
              <td><strong>Durasi & Resolusi</strong></td>
              <td>8.04 Detik | 1080x1920 (9:16)</td>
            </tr>
            <tr>
              <td><strong>Ukuran File Final</strong></td>
              <td>11.53 MB (H.264 / AAC Stereo)</td>
            </tr>
            <tr>
              <td><strong>Google Flow Batch</strong></td>
              <td>Batch ID: <code>abc835c4</code> (360p Asli)</td>
            </tr>
            <tr>
              <td><strong>Engine Upscaler</strong></td>
              <td>Varian 3 Vulkan M4 Hybrid (upscayl-lite-4x + Lanczos CAS)</td>
            </tr>
            <tr>
              <td><strong>Gaya Subtitle</strong></td>
              <td>editorial_tiktok 2-tier (0% koma)</td>
            </tr>
            <tr>
              <td><strong>Owner ACC ID</strong></td>
              <td><code>5c2ea72dc7e142249622c8e80b019ec0</code></td>
            </tr>
            <tr>
              <td><strong>SQLite Record ID</strong></td>
              <td><code>1fa5374da86548a8ace51f7ced3e8720</code></td>
            </tr>
          </table>

          <div class="quote-box">
            <strong>Caption Naratif ACC (365 Karakter Alfabet Murni):</strong><br>
            "Kalau sudah masuk jalan poros kebun sawit sehabis hujan lebat di Riau, bukan soal motor mahal atau kinclong yang dicari tapi motor langsir yang sanggup bawa buah empat ratus kilo tanpa slip di jalan tanah merah. Di kebun kalian kawan-kawan motor langsir pakai modifikasi apa biar kuat nanjak? #sawitriau #motorlangsir #kebunsawit #pekanbaru #petanisawit #panensawit"
          </div>
        </div>

        <div class="img-box">
          <img src="${postScreenshotB64}" style="height: 310px; object-fit: contain; background: #000;" alt="Tangkapan Layar Live TikTok">
          <div class="caption">Verifikasi Tangkapan Layar Postingan Live di TikTok (@pakvincent.riau)</div>
        </div>
      </div>

      <!-- Integrasi Ekosistem Agen & Jadwal -->
      <div class="section-title">8. Integrasi Ekosistem Agen & Jadwal Operasional Rutin</div>
      <table class="data-table">
        <tr>
          <th>Modul Agen</th>
          <th>Identitas Sistem</th>
          <th>Model / Akun</th>
          <th>Peran & Batasan Wewenang</th>
        </tr>
        <tr>
          <td><strong>Hermes Agent Profile</strong></td>
          <td><code>ai-influencer-pak-vincent</code></td>
          <td>DeepSeek Flash</td>
          <td>Aktif di Gateway: merespons komentar audiens, membalas DM ramah, menegakkan 0% emoji.</td>
        </tr>
        <tr>
          <td><strong>Akun Google Flow</strong></td>
          <td>Akun <code>flow_5</code></td>
          <td><code>pemuda008899@gmail.com</code></td>
          <td>Proyek video terisolasi untuk generate video 360p Omni Flash hemat kredit.</td>
        </tr>
        <tr>
          <td><strong>Jadwal Operasional Harian</strong></td>
          <td>Slot Sore</td>
          <td>Produksi: 15:00 WIB<br>Publikasi: 18:00 WIB</td>
          <td>Maksimal 1 postingan per hari, durasi maks 20 detik, wajib lolos gerbang ACC Owner.</td>
        </tr>
        <tr>
          <td><strong>Database Produksi</strong></td>
          <td><code>production.sqlite</code></td>
          <td>Tabel: <code>publications</code></td>
          <td>Pencatatan hash video, hash caption, status ACC Telegram, dan ID posting platform.</td>
        </tr>
      </table>

      <div class="callout-success">
        <div style="font-size: 16pt; line-height: 1;">✓</div>
        <div class="callout-success-text">
          <h4>Status Operasional Lengkap</h4>
          <p>Pak Vincent resmi beroperasi penuh sebagai agen ke-4 dalam rangkaian media sosial AI Influencer bersama Dinda Kemala (Palembang), Intan Suar Kartika (Proyek Sipil), dan Bang Ray (Banda Aceh). Seluruh pipeline teknis, aset visual, dan repositori telah lulus 85 unit test tanpa regresi.</p>
        </div>
      </div>
    </div>

    <div class="footer">
      <span>Dapur Operasional AI Influencer &copy; 2026</span>
      <span>Dokumen Resmi &mdash; Halaman 3 dari 3</span>
    </div>
  </div>

</body>
</html>`;

fs.writeFileSync('/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scratch/pak_vincent_report_v2.html', htmlContent);
console.log('HTML report v2 generated successfully!');
