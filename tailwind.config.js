// tailwind.config.js - Create this file manually
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'media',
  content: [
    './**/*.html', // Scans all your Django templates for utility classes
    '!./static/**/*.html',
    // Add other paths like './static/js/*.js' if needed
  ],
  theme: {
    extend: {
      // You can still add your custom theme values here
    },
  },
  // If you use plugins, they MUST be listed here
  plugins: [
    // require('@tailwindcss/forms'),
  ],
};