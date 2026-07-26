"""
AIForge V2 – Tailwind CSS Configuration Generator
=================================================
Generates tailwind.config.js and index.css stylesheet rules.
"""


class TailwindStyleGenerator:

    def generate_tailwind_config(self) -> str:
        return """/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        }
      }
    },
  },
  plugins: [],
};
"""

    def generate_index_css(self) -> str:
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-slate-950 text-slate-100 antialiased font-sans;
  }
}
"""


global_style_generator = TailwindStyleGenerator()
