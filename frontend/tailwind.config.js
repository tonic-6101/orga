/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Typography Scale
      fontSize: {
        'display': ['2rem', { lineHeight: '1.2', fontWeight: '700', letterSpacing: '-0.02em' }],      // 32px
        'h1': ['1.75rem', { lineHeight: '1.2', fontWeight: '700', letterSpacing: '-0.01em' }],       // 28px
        'h2': ['1.5rem', { lineHeight: '1.25', fontWeight: '600' }],                                  // 24px
        'h3': ['1.25rem', { lineHeight: '1.3', fontWeight: '600' }],                                  // 20px
        'h4': ['1rem', { lineHeight: '1.4', fontWeight: '600' }],                                     // 16px
        'subtitle': ['0.875rem', { lineHeight: '1.4', fontWeight: '500' }],                           // 14px
        'body': ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],                               // 14px
        'caption': ['0.75rem', { lineHeight: '1.5', fontWeight: '400' }],                             // 12px
        'overline': ['0.6875rem', { lineHeight: '1.5', fontWeight: '600', letterSpacing: '0.05em' }], // 11px
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'Consolas', 'monospace'],
      },
      colors: {
        gray: {
          350: '#9CA3AF',  // Dark mode secondary text
          750: '#374151',  // Dark mode card backgrounds
          850: '#1F2937',  // Dark mode deeper backgrounds
        },
        orga: {
          50: '#e6f4ec',   // Primary Light
          100: '#ccead9',
          200: '#99d5b3',
          300: '#66c08d',
          400: '#33ab67',
          500: '#018137',  // Primary
          600: '#015a27',  // Primary Dark
          700: '#014d21',
          800: '#01401b',
          900: '#003315',
          950: '#00260f',
        },
        // Secondary accent (pink/magenta)
        accent: {
          50: '#f9e6f4',   // Secondary Light
          100: '#f3cce9',
          200: '#e799d3',
          300: '#db66bd',
          400: '#cf33a7',
          500: '#B4138D',  // Secondary
          600: '#8a0f6c',  // Secondary Dark
          700: '#730c5a',
          800: '#5c0948',
          900: '#450736',
          950: '#2e0424',
        },
        // Project Status colors
        status: {
          active: '#018137',
          'at-risk': '#f39c12',
          delayed: '#e74c3c',
          'on-hold': '#95a5a6',
          completed: '#018137',
        },
        // Task Status colors (semantic - WCAG compliant)
        'task-status': {
          open: '#3B82F6',           // Blue
          'in-progress': '#F59E0B',  // Amber
          review: '#8B5CF6',         // Purple
          completed: '#10B981',      // Green
          cancelled: '#6B7280',      // Gray
        },
        // Milestone Status colors
        'milestone-status': {
          upcoming: '#3B82F6',
          'in-progress': '#F59E0B',
          completed: '#10B981',
          missed: '#EF4444',
        },
        // Priority colors
        priority: {
          critical: '#c0392b',
          high: '#e67e22',
          medium: '#3498db',
          low: '#95a5a6',
        },
        // Activity type colors
        activity: {
          task: '#3498db',
          comment: '#7f8c8d',
          assignment: '#9b59b6',
          milestone: '#f1c40f',
          event: '#2980b9',
          project: '#1abc9c',
        },
        // Gantt colors
        gantt: {
          default: '#17a2b8',
          highlight: '#B4138D',
          milestone: '#f1c40f',
          'at-risk': '#e67e22',
          completed: '#95a5a6',
        }
      },
    },
  },
  plugins: [],
}
