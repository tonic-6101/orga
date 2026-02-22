// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { createApp, type App as VueApp } from 'vue'
import {
  FrappeUI,
  setConfig,
  frappeRequest,
  Button,
  Input,
  Badge,
  Spinner,
} from 'frappe-ui'

import router from './router'
import App from './App.vue'
import { TranslatePlugin } from './plugins/translate'
import { getLang } from './composables/useTranslate'
import './index.css'

const app: VueApp = createApp(App)

// Configure FrappeUI to use Frappe's request handler
setConfig('resourceFetcher', frappeRequest)

// Install plugins
app.use(router)
app.use(FrappeUI, { socketio: false })
app.use(TranslatePlugin)

// Set HTML lang attribute to match user language
document.documentElement.lang = getLang()

// Register global components from FrappeUI
app.component('Button', Button)
app.component('Input', Input)
app.component('Badge', Badge)
app.component('Spinner', Spinner)

// Global error handler to prevent silent SPA crashes
app.config.errorHandler = (err, _instance, info) => {
  console.error(`[Orga] Unhandled error (${info}):`, err)
}

app.mount('#app')
