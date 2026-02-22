// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import type { App } from 'vue'
import { __ } from '@/composables/useTranslate'

export const TranslatePlugin = {
  install(app: App) {
    // Make __() available in all Vue templates as this.__()
    app.config.globalProperties.__ = __

    // Also expose on window for console debugging
    window.__ = __
  }
}
