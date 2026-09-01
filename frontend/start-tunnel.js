import localtunnel from 'localtunnel';

(async () => {
  try {
    const tunnel = await localtunnel({ port: 5173 });
    console.log('=== LUMINA PUBLIC TUNNEL READY ===');
    console.log('PUBLIC_URL=' + tunnel.url);
    console.log('===================================');

    tunnel.on('close', () => {
      console.log('Tunnel closed');
    });
  } catch (err) {
    console.error('Tunnel error:', err);
  }
})();
