/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#06101E',
          800: '#0A1628',
          700: '#0E1D35',
          600: '#1A2942',
          500: '#243B53',
        },
        accent: {
          DEFAULT: '#38BDF8',
          dark: '#0EA5E9',
          light: '#7DD3FC',
        },
        positive: {
          DEFAULT: '#34D399',
          dark: '#10B981',
          light: '#6EE7B7',
        },
        negative: {
          DEFAULT: '#F87171',
          dark: '#EF4444',
          light: '#FCA5A5',
        },
        warning: {
          DEFAULT: '#FBBF24',
          dark: '#F59E0B',
          light: '#FCD34D',
        },
      },
      fontFamily: {
        mono: ['IBM Plex Mono', 'Menlo', 'Monaco', 'monospace'],
        sans: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
