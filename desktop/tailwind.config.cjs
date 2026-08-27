/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
        extend: {
            fontFamily: {
                sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
                mono: ["SFMono-Regular", "Cascadia Code", "ui-monospace", "monospace"],
            },
            boxShadow: {
                panel: "0 24px 80px rgba(2, 8, 23, 0.28)",
            },
        },
    },
    plugins: [],
};
