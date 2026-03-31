/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx}',
    './src/components/**/*.{js,ts,jsx,tsx}',
    './src/dashboards/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Manrope"', 'sans-serif'],
        body: ['"Manrope"', 'sans-serif']
      },
      colors: {
        bg: '#f7f3eb',
        panel: '#fffdf9',
        ink: '#0f172a',
        accent: '#0891b2',
        accentSoft: '#cffafe',
        sand: '#efe7d8',
        gold: '#f5bc61'
      },
      boxShadow: {
        panel: '0 24px 64px rgba(15, 23, 42, 0.1)'
      }
    }
  },
  plugins: []
};
