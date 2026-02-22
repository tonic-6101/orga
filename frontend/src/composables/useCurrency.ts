// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Global currency composable (singleton pattern).
 *
 * Uses module-level refs so all components share the same currency setting.
 * Loads the configured default_currency from Orga Settings and provides
 * a shared formatCurrency() function using Intl.NumberFormat.
 */

import { ref, computed } from 'vue'
import { useSettingsApi } from './useApi'

// ============================================
// Module-level singleton state
// ============================================

const currency = ref('USD')
let initialized = false

/**
 * Composable providing shared currency formatting.
 *
 * Auto-initializes on first use by loading from Orga Settings.
 * All components that call useCurrency() share the same currency ref.
 */
export function useCurrency() {
  const { getSettings } = useSettingsApi()

  async function loadCurrency(): Promise<void> {
    try {
      const settings = await getSettings()
      currency.value = settings.default_currency || 'USD'
      initialized = true
    } catch (e) {
      console.error('Failed to load currency setting:', e)
      // Keep fallback 'USD'
    }
  }

  function formatCurrency(value: number | null | undefined): string {
    if (!value && value !== 0) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency.value,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(0)
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.value,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  // Auto-initialize on first use
  if (!initialized) {
    initialized = true // Prevent duplicate fetches
    loadCurrency()
  }

  /** Currency symbol (e.g. €, $, £) derived from the active currency code. */
  const currencySymbol = computed(() => {
    const symbols: Record<string, string> = {
      EUR: '€', USD: '$', GBP: '£', CHF: 'CHF', JPY: '¥', INR: '₹',
      KRW: '₩', BRL: 'R$', CNY: '¥', TRY: '₺', PLN: 'zł', CZK: 'Kč',
      HUF: 'Ft', ZAR: 'R', SEK: 'kr', NOK: 'kr', DKK: 'kr',
    }
    return symbols[currency.value] || currency.value
  })

  /** FontAwesome icon class for the active currency (for tab icons, badges, etc.). */
  const currencyIcon = computed(() => {
    const icons: Record<string, string> = {
      USD: 'fa-solid fa-dollar-sign',
      EUR: 'fa-solid fa-euro-sign',
      GBP: 'fa-solid fa-sterling-sign',
      JPY: 'fa-solid fa-yen-sign',
      CNY: 'fa-solid fa-yen-sign',
      INR: 'fa-solid fa-indian-rupee-sign',
      KRW: 'fa-solid fa-won-sign',
      TRY: 'fa-solid fa-lira-sign',
      BRL: 'fa-solid fa-brazilian-real-sign',
    }
    return icons[currency.value] || 'fa-solid fa-coins'
  })

  return { currency, formatCurrency, loadCurrency, currencySymbol, currencyIcon }
}
