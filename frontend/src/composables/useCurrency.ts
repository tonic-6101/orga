// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Global currency composable (singleton pattern).
 *
 * Reads currency from Dock Settings (ecosystem-wide org default)
 * and provides shared formatCurrency() / currencySymbol / currencyIcon
 * for all Orga components.
 */

import { ref, computed } from 'vue'

// ============================================
// Module-level singleton state
// ============================================

const currency = ref('EUR')
let initialized = false

function readDockCurrency(): string {
  try {
    return (window as any).frappe?.boot?.dock?.settings?.currency || 'EUR'
  } catch {
    return 'EUR'
  }
}

/**
 * Composable providing shared currency formatting.
 *
 * Reads currency from Dock Settings (via frappe.boot.dock.settings.currency).
 * All components that call useCurrency() share the same currency ref.
 */
export function useCurrency() {
  function loadCurrency(): void {
    currency.value = readDockCurrency()
    initialized = true
  }

  function formatCurrency(value: number | null | undefined): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.value,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value ?? 0)
  }

  // Auto-initialize on first use
  if (!initialized) {
    initialized = true
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

  /** Lucide icon name for the active currency (for tab icons, badges, etc.). */
  const currencyIcon = computed(() => {
    const icons: Record<string, string> = {
      USD: 'dollar-sign',
      EUR: 'euro',
      GBP: 'pound-sterling',
      JPY: 'japanese-yen',
      CNY: 'japanese-yen',
      INR: 'indian-rupee',
      KRW: 'coins',
      TRY: 'coins',
      BRL: 'coins',
    }
    return icons[currency.value] || 'coins'
  })

  return { currency, formatCurrency, loadCurrency, currencySymbol, currencyIcon }
}
