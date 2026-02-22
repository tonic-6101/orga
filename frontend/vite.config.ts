import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'

// Type for frappe-ui vite plugin
type FrappeUIVitePlugin = (options?: {
  frappeProxy?: boolean
  lucideIcons?: boolean
  jinjaBootData?: boolean
}) => Plugin

// Try to load frappe-ui vite plugin
let frappeui: FrappeUIVitePlugin | undefined
try {
  const module = await import('frappe-ui/vite')
  frappeui = module.default as FrappeUIVitePlugin
} catch {
  console.warn('frappe-ui vite plugin not found, continuing without it')
}

// Type for bundle chunk
interface BundleChunk {
  type: 'asset' | 'chunk'
  fileName: string
  isEntry?: boolean
}

// Type for manifest
interface FrappeManifest {
  js?: string
  css?: string
}

// Plugin to generate assets manifest for Frappe
function frappeManifestPlugin(): Plugin {
  return {
    name: 'frappe-manifest',
    writeBundle(options, bundle: Record<string, BundleChunk>): void {
      const manifest: FrappeManifest = {}
      const cssFiles: string[] = []

      for (const [fileName, chunk] of Object.entries(bundle)) {
        if (chunk.type === 'asset' || chunk.type === 'chunk') {
          if (fileName.endsWith('.js') && chunk.isEntry) {
            manifest.js = fileName
          }
          if (fileName.endsWith('.css')) {
            cssFiles.push(fileName)
          }
        }
      }
      // Use the main CSS file (largest one, which contains Tailwind)
      manifest.css = cssFiles.find(f => f.includes('main-')) || cssFiles[0]

      // Write manifest
      const manifestPath = path.resolve(options.dir || '', 'manifest.json')
      fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2))

      // Generate orga.html for Frappe www
      // Note: manifest.js/css already include 'assets/' prefix from rollup output
      const jsFile = manifest.js?.replace('assets/', '') || ''
      const cssFile = manifest.css?.replace('assets/', '') || ''
      const htmlContent = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Orga</title>
    <meta name="description" content="Orga - Project Management System" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
    <link rel="icon" type="image/svg+xml" href="/assets/orga/images/orga-icon.svg" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
    <script type="module" crossorigin src="/assets/orga/frontend/assets/${jsFile}"></script>
    <link rel="stylesheet" crossorigin href="/assets/orga/frontend/assets/${cssFile}">
  </head>
  <body>
    <script>
      // Prevent flash of wrong theme before Vue loads
      (function() {
        var stored = localStorage.getItem('orga-theme');
        var isDark = stored === 'dark' ||
          (!stored || stored === 'auto') && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDark) document.documentElement.classList.add('dark');
      })();
    </script>
    <div id="app" class="h-screen"></div>
    <div id="modals"></div>
    <div id="popovers"></div>
    <script>
      window.csrf_token = "{{ csrf_token }}"
    </script>
    {% for key in boot %}
    <script>
      window["{{ key }}"] = {{ boot[key] | tojson }};
    </script>
    {% endfor %}
  </body>
</html>`

      const htmlPath = path.resolve(__dirname, '../orga/www/orga.html')
      fs.writeFileSync(htmlPath, htmlContent)
      console.log('Generated orga.html with assets:', manifest)
    }
  }
}

export default defineConfig({
  base: '/assets/orga/frontend/',
  plugins: [
    vue(),
    frappeui && frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true
    }),
    frappeManifestPlugin()
  ].filter(Boolean) as Plugin[],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  build: {
    outDir: '../orga/public/frontend',
    emptyOutDir: true,
    target: 'es2015',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '^/(api|assets|files)': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  optimizeDeps: {
    include: ['frappe-ui', 'feather-icons', 'vue', 'vue-router']
  }
})
