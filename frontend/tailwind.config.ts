import type { Config } from 'tailwindcss';

// Paleta: verdes (agricultura), cinzas (tecnologia) e cores de status para alertas.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#effaf3',
          100: '#d8f3e1',
          200: '#b4e5c6',
          300: '#82d1a4',
          400: '#4eb57d',
          500: '#2b9a61',
          600: '#1d7c4d',
          700: '#186340',
          800: '#164f35',
          900: '#13412d',
        },
        status: {
          cold: '#2563eb',
          ok: '#16a34a',
          warning: '#ea580c',
          critical: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config;
