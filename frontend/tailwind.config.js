/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        pau: {
          blue: '#1E3A8A',
          btn: '#4F7396',
          btnHover: '#3D5B78',
          bg: '#F0F2F5'
        }
      }
    },
  },
  plugins: [],
}
