// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, type Ref } from 'vue'

interface UseSidebarReturn {
  collapsed: Ref<boolean>
  mobileOpen: Ref<boolean>
  toggle: () => void
  closeMobile: () => void
  isMobile: () => boolean
}

const STORAGE_KEY = 'orga-sidebar-collapsed'
const collapsed = ref<boolean>(localStorage.getItem(STORAGE_KEY) === 'true')
const mobileOpen = ref<boolean>(false)

export function useSidebar(): UseSidebarReturn {
  const toggle = (): void => {
    if (window.innerWidth <= 576) {
      mobileOpen.value = !mobileOpen.value
    } else {
      collapsed.value = !collapsed.value
      localStorage.setItem(STORAGE_KEY, String(collapsed.value))
    }
  }

  const closeMobile = (): void => {
    mobileOpen.value = false
  }

  const isMobile = (): boolean => window.innerWidth <= 576

  return {
    collapsed,
    mobileOpen,
    toggle,
    closeMobile,
    isMobile
  }
}
