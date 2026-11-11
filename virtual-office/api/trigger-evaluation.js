export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // On cloud deployment, weekly evaluation runs via Hermes scheduler on local edge server.
  return res.status(200).json({
    ok: true,
    message: 'Evaluasi mingguan tercatat aktif via Hermes scheduler (Minggu 20:00 WIB).'
  });
}
