/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./site.html",
    "./Gotch_site_with_russian.html",
    "./activation_server/templates/**/*.html",
    "./src/**/*.{html,js}"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#4ADE80',
          dark: '#22C55E',
          darker: '#16A34A'
        },
        danger: {
          DEFAULT: '#F87171',
          dark: '#EF4444',
        },
        info: {
          DEFAULT: '#60A5FA',
          dark: '#3B82F6',
        },
        dark: {
          DEFAULT: '#1E293B',
          light: '#334155',
          lighter: '#475569',
          dark: '#0F172A',
          darker: '#020617',
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.4s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
  darkMode: 'class'
}
