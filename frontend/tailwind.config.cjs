/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eefaf6',
          100: '#d8f3e9',
          200: '#b3e8d6',
          300: '#83d8bb',
          400: '#4bc59d',
          500: '#10a37f',
          600: '#0f8b6d',
          700: '#11745d',
          800: '#155d4d',
          900: '#154d42',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
