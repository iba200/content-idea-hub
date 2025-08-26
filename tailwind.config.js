module.exports = {
  content: ["./app/templates/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        'wireframe-black': '#000000',
        'wireframe-white': '#FFFFFF',
        'wireframe-gray': '#E5E7EB'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif']
      },
      boxShadow: {
        'wireframe': '0 0 0 1px #000000' // Bordures noires fines
      }
    }
  },
  plugins: []
}