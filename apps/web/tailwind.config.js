/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#0f65f2", hover: "#1a5ad7" },
      },
      borderRadius: { DEFAULT: "8px" },
    },
  },
  plugins: [],
};
