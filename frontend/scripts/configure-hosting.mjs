// Run only after verifying the actual ResumeIQ Render URL and account costs.
// This sets public routing configuration; it never reads or writes a secret.
import { writeFileSync } from 'node:fs';

const upstream = new URL(process.argv[2] ?? 'invalid:');
if (upstream.protocol !== 'https:' || !upstream.hostname.endsWith('.onrender.com') ||
    upstream.username || upstream.password || upstream.pathname !== '/' || upstream.search || upstream.hash || upstream.port) {
  throw new Error('Pass the verified HTTPS origin of the ResumeIQ Render service.');
}
const config = {
  $schema: 'https://openapi.vercel.sh/vercel.json', framework: 'vite',
  buildCommand: 'npm run build', outputDirectory: 'dist',
  rewrites: [
    { source: '/api/:path*', destination: `${upstream.origin}/api/:path*` },
    { source: '/((?!api/).*)', destination: '/index.html' },
  ],
  headers: [
    { source: '/api/:path*', headers: [{ key: 'Cache-Control', value: 'no-store' }] },
    { source: '/(.*)', headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" },
    ] },
  ],
};
writeFileSync(new URL('../vercel.json', import.meta.url), JSON.stringify(config, null, 2) + '\n');
console.log('Configured the verified backend origin. Review and commit vercel.json before deployment.');
