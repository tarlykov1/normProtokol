import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        success: '#15803d',
        warning: '#b45309',
        danger: '#b91c1c',
        muted: '#6b7280'
      }
    }
  },
  plugins: []
} satisfies Config
