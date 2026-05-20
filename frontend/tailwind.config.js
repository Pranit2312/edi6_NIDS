/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f8f9fa',
          100: '#f0f2f5',
          200: '#e1e4e8',
          300: '#d0d6db',
          400: '#a8b3be',
          500: '#78828f',
          600: '#586069',
          700: '#3e4451',
          800: '#2d333b',
          900: '#1c2128',
        },
        neon: {
          blue: '#00d9ff',
          purple: '#b536d9',
          pink: '#ff006e',
          green: '#00ff88',
        },
      },
      boxShadow: {
        glow: '0 0 20px rgba(0, 217, 255, 0.3)',
        'glow-purple': '0 0 20px rgba(181, 54, 217, 0.3)',
        'glow-pink': '0 0 20px rgba(255, 0, 110, 0.3)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        float: 'float 6s ease-in-out infinite',
        glow: 'glow 2s ease-in-out infinite',
        scan: 'scan 3s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 217, 255, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 217, 255, 0.6)' },
        },
        scan: {
          '0%': { top: '0%' },
          '100%': { top: '100%' },
        },
      },
    },
  },
  plugins: [],
}
