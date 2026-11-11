export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  let body = req.body;
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body);
    } catch (e) {
      body = {};
    }
  }

  const pin = String(body?.pin || '').trim();
  const validPins = ['7463982122', 'intan', 'admin', '88329104'];

  if (pin && validPins.includes(pin)) {
    const token = 'token_intan_ai_hq_88329104';
    res.setHeader('Set-Cookie', `access_token=${token}; Path=/; SameSite=Lax; Max-Age=2592000`);
    return res.status(200).json({
      authenticated: true,
      token,
      role: 'Owner / Executive',
      message: 'Akses Diterima. Selamat datang di Kantor AI Intan.'
    });
  }

  return res.status(401).json({
    authenticated: false,
    error: 'PIN atau kata sandi belum sesuai.'
  });
}
