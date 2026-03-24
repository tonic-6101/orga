import dockPreset from '../../dock/frontend/src/styles/dock-tailwind-preset.js'

/** @type {import('tailwindcss').Config} */
export default {
  presets: [dockPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
    // Dock navbar components loaded at runtime via ESM — scan source so
    // Tailwind generates the utility classes they use (search bar, bell, etc.)
    '../../dock/frontend/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          350: '#9CA3AF',
          750: '#374151',
          850: '#1F2937',
        },
        // Domain-specific colors (not part of shared design system)
        'task-status': {
          open: '#3B82F6',
          'in-progress': '#F59E0B',
          review: '#8B5CF6',
          completed: '#10B981',
          cancelled: '#6B7280',
        },
        'milestone-status': {
          upcoming: '#3B82F6',
          'in-progress': '#F59E0B',
          completed: '#10B981',
          missed: '#EF4444',
        },
        priority: {
          critical: '#c0392b',
          high: '#e67e22',
          medium: '#3498db',
          low: '#95a5a6',
        },
        activity: {
          task: '#3498db',
          comment: '#7f8c8d',
          assignment: '#9b59b6',
          milestone: '#f1c40f',
          event: '#2980b9',
          project: '#1abc9c',
        },
        gantt: {
          default: '#17a2b8',
          highlight: '#B4138D',
          milestone: '#f1c40f',
          'at-risk': '#e67e22',
          completed: '#95a5a6',
        },
      },
    },
  },
  plugins: [],
}
