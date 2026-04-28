// ── REPLACE the existing SANDBOX_ID block and btn-connect listener with this ──

// Your Railway token server URL — update this after deploying token_server.py
const TOKEN_SERVER_URL = 'https://YOUR-RAILWAY-APP.railway.app/token';

document.getElementById('btn-connect').addEventListener('click', async () => {
  if (room) { room.disconnect(); return; }
  const btn = document.getElementById('btn-connect');
  btn.textContent = 'Connecting…'; btn.disabled = true;
  try {
    const res = await fetch(TOKEN_SERVER_URL, { method: 'POST' });
    if (!res.ok) throw new Error('Could not get token from server');
    const data = await res.json();
    const err = await connect(data.serverUrl, data.token);
    if (err) {
      status('ERROR', '');
      btn.textContent = 'Connect'; btn.disabled = false;
    } else {
      btn.textContent = 'Disconnect';
      btn.classList.add('disc');
      btn.disabled = false;
    }
  } catch(e) {
    console.error('Token fetch error:', e);
    status('ERROR', '');
    btn.textContent = 'Connect'; btn.disabled = false;
  }
});
