// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

// ESM entry point for Orga's settings component.
// Dock's DockSettingsAppHost lazy-loads this bundle and renders OrgaSettings
// inside the Dock SPA at /dock/settings/app/orga.
//
// This file is built as a separate Vite library entry: orga-settings.esm.js

export { default as OrgaSettings } from './pages/Settings.vue'
