/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./.vitepress/**/*.{vue,js,ts,jsx,tsx}", "./**/*.md"],
  theme: {
    extend: {
      colors: {
        brand: {
          light: "#646cff",
          DEFAULT: "#646cff",
          dark: "#535bf2",
        },
        monoco: {
          bg: "#0f172a", // Slate 900
          text: "#f8fafc", // Slate 50
        },
      },
    },
  },
  plugins: [],
};
