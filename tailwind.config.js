module.exports = {
    content: ["./app/templates/**/*.{html,js}"],
    theme: {
        extend: {
            colors: {
                'soft-blue': '#3B82F6',
                'soft-purple': '#8B5CF6',
                'soft-green': '#10B981',
                'danger-red': '#EF4444',
                'light-gray': '#F9FAFB',
            },
            fontFamily: {
                sans: ['Inter', 'Roboto', 'sans-serif'],
            },
        },
    },
    plugins: [],
}