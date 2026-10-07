/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { ink: 'var(--background)', panel: 'var(--panel)', line: 'var(--border)', accent: 'var(--accent)', mint: 'var(--success)' }, fontFamily: { sans: ['DM Sans', 'sans-serif'], mono: ['DM Mono', 'monospace'] } } },
  plugins: []
}
