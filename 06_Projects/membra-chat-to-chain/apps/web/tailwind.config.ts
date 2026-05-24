import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#050505',
          50: '#0B0D10',
          100: '#111318',
          200: '#1A1D24',
          300: '#242830',
        },
        primary: {
          orange: '#FF8A1F',
          gold: '#D6A64F',
          bronze: '#9A6A35',
        },
        text: {
          primary: '#F7F2E8',
          muted: '#9B9489',
          dim: '#6B6459',
        },
        success: '#49D17D',
        danger: '#D84A32',
        warning: '#E8A840',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-orange': '0 0 20px rgba(255, 138, 31, 0.15)',
        'glow-gold': '0 0 20px rgba(214, 166, 79, 0.15)',
        'glow-red': '0 0 20px rgba(216, 74, 50, 0.15)',
      },
    },
  },
  plugins: [],
};

export default config;
