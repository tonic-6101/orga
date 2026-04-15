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
    <link rel="stylesheet" href="/assets/dock/css/dock-tokens.css">
    <link rel="stylesheet" href="/assets/dock/css/dock-navbar.css">
    <script type="module" crossorigin src="/assets/orga/frontend/assets/${jsFile}"></script>
    <link rel="stylesheet" crossorigin href="/assets/orga/frontend/assets/${cssFile}">
  </head>
  <body>
    <script>
      // Prevent flash of wrong theme before Vue loads
      (function() {
        var stored = localStorage.getItem('dock-theme');
        var isDark = stored === 'dark' ||
          (!stored || stored === 'auto') && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDark) document.documentElement.classList.add('dark');
        var cm = localStorage.getItem('color-mode');
        if (cm === 'neutral') document.documentElement.setAttribute('data-color-mode', 'neutral');
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

// Vite plugin: resolve any /assets/dock/* import as external.
// Dock's ESM bundle is served by Frappe at runtime when Dock is installed.
// Without this, Rollup errors on the unresolvable URL at build time.
const dockExternalPlugin: Plugin = {
  name: 'dock-external',
  enforce: 'pre',
  resolveId(id: string) {
    if (id.startsWith('/assets/dock/')) {
      return { id, external: true }
    }
  },
}

// Vite plugin: share Vue + Vue Router runtimes with Dock.
// Dock ships Vue's ESM browser build at /assets/dock/js/vendor/vue.esm.js
// and Vue Router at /assets/dock/js/vendor/vue-router.esm.js.
// By externalizing both, Orga uses the SAME instances as Dock's components
// (DockLayout, DockSidebarShell), preventing dual-instance injection failures.
const vueSharedPlugin: Plugin = {
  name: 'vue-shared',
  enforce: 'pre',
  resolveId(id: string) {
    if (id === 'vue' || id === '@vue/runtime-dom' || id === '@vue/runtime-core' || id === '@vue/reactivity') {
      return { id: '/assets/dock/js/vendor/vue.esm.js', external: true }
    }
    if (id === 'vue-router') {
      return { id: '/assets/dock/js/vendor/vue-router.esm.js', external: true }
    }
  },
}

// ── Settings ESM build ──────────────────────────────────────────────
// Builds orga-settings.esm.js — a standalone ESM bundle that exports
// OrgaSettings component for Dock's unified settings hub.
// This runs as a secondary build after the main SPA build.
function settingsEsmPlugin(): Plugin {
  return {
    name: 'orga-settings-esm',
    async closeBundle() {
      const { build } = await import('vite')
      await build({
        configFile: false,
        base: '/assets/orga/js/',
        plugins: [
          vueSharedPlugin,
          vue(),
          ...(frappeui ? [frappeui({ frappeProxy: false, lucideIcons: true, jinjaBootData: false, buildConfig: false })] : []),
        ],
        resolve: {
          alias: {
            '@': path.resolve(__dirname, 'src'),
          },
        },
        build: {
          outDir: path.resolve(__dirname, '../orga/public/js'),
          emptyOutDir: false,
          lib: {
            entry: path.resolve(__dirname, 'src/dock-settings.ts'),
            formats: ['es'],
            fileName: () => 'orga-settings.esm.js',
          },
          rollupOptions: {
            external: [
              'vue',
              'vue-router',
              '@vue/runtime-dom',
              '@vue/runtime-core',
              '@vue/reactivity',
              /^\/assets\/dock\//,
            ],
            output: {
              paths: {
                vue: '/assets/dock/js/vendor/vue.esm.js',
                'vue-router': '/assets/dock/js/vendor/vue-router.esm.js',
              },
            },
          },
        },
      })
      console.log('Built orga-settings.esm.js')
    },
  }
}

// Read version from package.json for build-time injection
const pkg = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'package.json'), 'utf-8'))

export default defineConfig({
  base: '/assets/orga/frontend/',
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  plugins: [
    vueSharedPlugin,
    dockExternalPlugin,
    vue(),
    frappeui && frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: false,
    }),
    frappeManifestPlugin(),
    settingsEsmPlugin(),
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
