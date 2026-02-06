/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core grays (dark theme)
        'gray-950': '#0a0b0f',
        'gray-900': '#0f1117',
        'gray-800': '#1a1d27',
        'gray-700': '#252936',
        'gray-600': '#374151',
        'gray-500': '#4B5563',
        'gray-400': '#9CA3AF',
        'gray-300': '#D1D5DB',
        'gray-200': '#E5E7EB',
        'gray-100': '#F3F4F6',
        'gray-50': '#F9FAFB',
        // Brand colors (indigo/purple gradient from Stitch)
        'brand-blue': '#3B82F6',
        'brand-purple': '#8B5CF6',
        'brand-indigo': '#6366F1',
        // Accent colors
        'accent-emerald': '#10B981',
        'accent-teal': '#14B8A6',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-premium': 'linear-gradient(135deg, var(--tw-gradient-from) 0%, var(--tw-gradient-to) 100%)',
      },
      boxShadow: {
        'glow-indigo': '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-emerald': '0 0 20px rgba(16, 185, 129, 0.2)',
      },
    },
  },
  plugins: [],
}