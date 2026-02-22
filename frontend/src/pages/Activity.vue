<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Activity.vue - Activity feed page with Manager panel integration

  Features:
  - Activity feed with type and project filtering
  - Pin indicator on activities (sorted to top)
  - Archive filtering with toggle
  - Panel events for pin/archive/delete
-->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { useDashboardApi, useProjectApi, useActivityApi } from '@/composables/useApi'
import { useActivityUnread } from '@/composables/useActivityUnread'
import { useActivityKeyboard } from '@/composables/useActivityKeyboard'
import ActivityPanel from '@/components/ActivityPanel.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import ActivityCard from '@/components/activity/ActivityCard.vue'
import ActivityDateGroup from '@/components/activity/ActivityDateGroup.vue'
import AggregatedActivityCard from '@/components/activity/AggregatedActivityCard.vue'
import KeyboardShortcutsModal from '@/components/activity/KeyboardShortcutsModal.vue'
import NewActivityBanner from '@/components/activity/NewActivityBanner.vue'
import { useActivityGrouping } from '@/composables/useActivityGrouping'
import type { AggregatedActivity } from '@/composables/useActivityGrouping'
import { __ } from '@/composables/useTranslate'
import type { OrgaProject, ActivityItem } from '@/types/orga'

const { getRecentActivity, getActivitySince } = useDashboardApi()
const { getProjects } = useProjectApi()
const { getPinnedActivities, getArchivedActivities, getActivityLastViewed, markActivityViewed } = useActivityApi()
const { resetCount } = useActivityUnread()

// State
const activities = ref<ActivityItem[]>([])
const projects = ref<OrgaProject[]>([])
const activeFilter = ref<string>('all')
const selectedProject = ref<string>('')
const selectedUser = ref<string>('')
const isLoading = ref<boolean>(true)
const loadError = ref<string | null>(null)
const selectedActivity = ref<ActivityItem | null>(null)
const showArchived = ref<boolean>(false)

// Read/unread state
const lastViewed = ref<string | null>(null)
const readIds = ref<Set<string>>(new Set())

// Panel visibility state
const showManager = ref<boolean>(false)
const showDetails = ref<boolean>(false)

// User preferences (pinned/archived activity identifiers)
const pinnedIds = ref<Set<string>>(new Set())
const archivedIds = ref<Set<string>>(new Set())

const filters: { key: string; label: string }[] = [
  { key: 'all', label: __('All') },
  { key: 'tasks', label: __('Tasks') },
  { key: 'milestones', label: __('Milestones') },
  { key: 'projects', label: __('Projects') },
  { key: 'events', label: __('Events') },
  { key: 'external', label: __('External') },
]

// User typeahead state
const userSearch = ref<string>('')
const showUserSuggestions = ref<boolean>(false)

const filteredUserSuggestions = computed(() => {
  if (!userSearch.value.trim()) return activityUsers.value
  const q = userSearch.value.toLowerCase()
  return activityUsers.value.filter(u =>
    u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
  )
})

function selectUser(user: { email: string; name: string }) {
  selectedUser.value = user.email
  userSearch.value = user.name
  showUserSuggestions.value = false
}

function clearUser() {
  selectedUser.value = ''
  userSearch.value = ''
  showUserSuggestions.value = false
}

function handleUserBlur() {
  // Delay to allow click on suggestion to register
  setTimeout(() => { showUserSuggestions.value = false }, 150)
}

/**
 * Unique users from loaded activities for the user filter dropdown
 */
const activityUsers = computed(() => {
  const userMap = new Map<string, { name: string; image?: string }>()
  for (const a of activities.value) {
    const email = a.user
    const name = a.user_name || a.user_fullname || email
    if (email && !userMap.has(email)) {
      userMap.set(email, { name, image: a.user_image })
    }
  }
  return Array.from(userMap.entries())
    .map(([email, info]) => ({ email, name: info.name, image: info.image }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

/**
 * Generate a unique key for an activity
 */
function getActivityKey(activity: ActivityItem): string {
  const doctype = activity.reference_doctype || activity.doctype
  const docname = activity.reference_name || activity.name
  return `${doctype}_${docname}`
}

/**
 * Filter activities based on active filter, project, and archive status
 */
const filteredActivities = computed<ActivityItem[]>(() => {
  let result = activities.value

  // Filter by type
  if (activeFilter.value !== 'all') {
    const typeFilter = activeFilter.value.toLowerCase().replace(/s$/, '') // Remove trailing 's'
    result = result.filter((a: ActivityItem) => a.type === typeFilter)
  }

  // Filter by project
  if (selectedProject.value) {
    result = result.filter((a: ActivityItem) => a.project === selectedProject.value)
  }

  // Filter by user
  if (selectedUser.value) {
    result = result.filter((a: ActivityItem) => a.user === selectedUser.value)
  }

  // Filter archived unless showArchived is enabled
  if (!showArchived.value) {
    result = result.filter((a: ActivityItem) => !archivedIds.value.has(getActivityKey(a)))
  }

  // Sort pinned activities to top
  result = [...result].sort((a, b) => {
    const aIsPinned = pinnedIds.value.has(getActivityKey(a))
    const bIsPinned = pinnedIds.value.has(getActivityKey(b))
    if (aIsPinned && !bIsPinned) return -1
    if (!aIsPinned && bIsPinned) return 1
    return 0
  })

  return result
})

// Group filtered activities by date and aggregate consecutive same-user items
const { grouped: groupedActivities } = useActivityGrouping(filteredActivities)

/**
 * Get a unique key for grouped/aggregated items
 */
function getItemKey(item: ActivityItem | AggregatedActivity): string {
  if ('isAggregated' in item && item.isAggregated) {
    return `agg_${item.user}_${item.type}_${item.action}_${item.timestamp}`
  }
  return (item as ActivityItem).name + (item as ActivityItem).timestamp
}

/**
 * Check if an item is aggregated
 */
function isAggregated(item: ActivityItem | AggregatedActivity): item is AggregatedActivity {
  return 'isAggregated' in item && item.isAggregated === true
}

/**
 * Check if an activity is unread (modified after lastViewed and not individually read)
 */
function isUnread(activity: ActivityItem): boolean {
  if (!lastViewed.value) return false
  if (readIds.value.has(activity.name + activity.timestamp)) return false
  return activity.timestamp > lastViewed.value
}

/**
 * Mark a single activity as read (frontend-only, until page leave persists all)
 */
function markAsRead(activity: ActivityItem): void {
  readIds.value.add(activity.name + activity.timestamp)
}

/**
 * Whether any activities are unread (for showing "Mark read" button)
 */
const hasUnreadActivities = computed(() => {
  if (!lastViewed.value) return false
  return filteredActivities.value.some(a => isUnread(a))
})

/**
 * Mark all activity as read
 */
async function markAllAsRead(): Promise<void> {
  try {
    const result = await markActivityViewed()
    lastViewed.value = result.last_viewed
    await resetCount()
  } catch {
    // Silently ignore
  }
}

/**
 * Load activity data and user preferences
 */
async function loadActivity(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const [activityData, projectData, pinned, archived, lastViewedData] = await Promise.all([
      getRecentActivity(50),
      getProjects({ limit: 100 }),
      getPinnedActivities().catch(() => []),
      getArchivedActivities().catch(() => []),
      getActivityLastViewed().catch(() => ({ last_viewed: null }))
    ])

    lastViewed.value = lastViewedData.last_viewed

    activities.value = activityData || []
    projects.value = projectData || []

    // Build sets for quick lookup
    pinnedIds.value = new Set(
      pinned.map(p => `${p.doctype}_${p.name}`)
    )
    archivedIds.value = new Set(
      archived.map(a => `${a.doctype}_${a.name}`)
    )
  } catch (e) {
    console.error('Failed to load activity:', e)
    loadError.value = (e as Error).message || __('Failed to load activity')
  } finally {
    isLoading.value = false
  }
}

function setFilter(filterKey: string): void {
  activeFilter.value = filterKey
}

// Format relative time (kept for Details panel)
function formatRelativeTime(timestamp: string | null | undefined): string {
  if (!timestamp) return ''
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __('{0} min ago', [diffMins])
  if (diffHours < 24) return __('{0} hours ago', [diffHours])
  if (diffDays === 1) return __('Yesterday')
  if (diffDays < 7) return __('{0} days ago', [diffDays])
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/**
 * Check if an activity is pinned
 */
function isActivityPinned(activity: ActivityItem): boolean {
  return pinnedIds.value.has(getActivityKey(activity))
}

/**
 * Check if an activity is archived
 */
function isActivityArchived(activity: ActivityItem): boolean {
  return archivedIds.value.has(getActivityKey(activity))
}

// Select activity for panel
function selectActivity(activity: ActivityItem): void {
  selectedActivity.value = activity
  markAsRead(activity)
  // Auto-show manager when activity is selected
  if (!showManager.value) {
    showManager.value = true
  }
}

// Close panel
function closePanel(): void {
  selectedActivity.value = null
}

// Toggle Manager panel
function toggleManager(): void {
  showManager.value = !showManager.value
}

// Toggle Details panel
function toggleDetails(): void {
  showDetails.value = !showDetails.value
}

// ============================================
// Panel Event Handlers
// ============================================

/**
 * Handle pin toggle from panel
 */
function handleActivityPin(isPinned: boolean): void {
  if (selectedActivity.value) {
    const key = getActivityKey(selectedActivity.value)
    if (isPinned) {
      pinnedIds.value.add(key)
    } else {
      pinnedIds.value.delete(key)
    }
    // Force reactivity update
    pinnedIds.value = new Set(pinnedIds.value)
  }
}

/**
 * Handle archive toggle from panel
 */
function handleActivityArchive(isArchived: boolean): void {
  if (selectedActivity.value) {
    const key = getActivityKey(selectedActivity.value)
    if (isArchived) {
      archivedIds.value.add(key)
      // Close panel when archiving if not showing archived
      if (!showArchived.value) {
        selectedActivity.value = null
      }
    } else {
      archivedIds.value.delete(key)
    }
    // Force reactivity update
    archivedIds.value = new Set(archivedIds.value)
  }
}

/**
 * Handle delete from panel
 */
function handleActivityDelete(): void {
  if (selectedActivity.value) {
    const key = getActivityKey(selectedActivity.value)
    // Remove from local state
    pinnedIds.value.delete(key)
    archivedIds.value.delete(key)
    // Optionally remove from activities list
    activities.value = activities.value.filter(
      a => getActivityKey(a) !== key
    )
    selectedActivity.value = null
  }
}

/**
 * Handle update event - reload user preferences
 */
async function handleActivityUpdate(): Promise<void> {
  try {
    const [pinned, archived] = await Promise.all([
      getPinnedActivities().catch(() => []),
      getArchivedActivities().catch(() => [])
    ])

    pinnedIds.value = new Set(
      pinned.map(p => `${p.doctype}_${p.name}`)
    )
    archivedIds.value = new Set(
      archived.map(a => `${a.doctype}_${a.name}`)
    )
  } catch (e) {
    console.error('Failed to refresh activity preferences:', e)
  }
}

onMounted(loadActivity)

// ============================================
// Live Polling (Phase 5)
// ============================================

const POLL_INTERVAL_MS = 15_000
const pendingNewActivities = ref<ActivityItem[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

/**
 * The timestamp of the most recently loaded activity.
 * Used as the baseline for delta polling.
 */
const latestTimestamp = computed<string | null>(() => {
  if (activities.value.length === 0) return null
  // activities are sorted desc by timestamp from backend
  return String(activities.value[0].timestamp)
})

/**
 * Poll for new activities since the latest loaded timestamp.
 * Only runs when the browser tab is visible.
 */
async function pollForNew(): Promise<void> {
  if (document.visibilityState !== 'visible') return
  if (!latestTimestamp.value) return

  try {
    const result = await getActivitySince(latestTimestamp.value, 20)
    if (result.count > 0) {
      // Filter out any items already in the current list (de-duplicate)
      const existingKeys = new Set(
        activities.value.map(a => `${a.reference_doctype || a.doctype}_${a.reference_name || a.name}`)
      )
      const genuinelyNew = result.items.filter(item => {
        const key = `${item.reference_doctype || item.doctype}_${item.reference_name || item.name}`
        return !existingKeys.has(key)
      })
      if (genuinelyNew.length > 0) {
        pendingNewActivities.value = genuinelyNew
      }
    }
  } catch {
    // Silently ignore polling errors
  }
}

/**
 * Load pending new activities into the main list (called when user clicks banner)
 */
function loadNewActivities(): void {
  if (pendingNewActivities.value.length === 0) return

  // Merge new items, de-duplicating by reference key
  const existingKeys = new Set(
    activities.value.map(a => `${a.reference_doctype || a.doctype}_${a.reference_name || a.name}`)
  )
  const toAdd = pendingNewActivities.value.filter(item => {
    const key = `${item.reference_doctype || item.doctype}_${item.reference_name || item.name}`
    return !existingKeys.has(key)
  })

  // Prepend new items and re-sort
  activities.value = [...toAdd, ...activities.value]
  activities.value.sort((a, b) => {
    const ta = new Date(a.timestamp).getTime()
    const tb = new Date(b.timestamp).getTime()
    return tb - ta
  })

  pendingNewActivities.value = []

  // Scroll to top so user sees the new items
  nextTick(() => {
    if (activityListRef.value) {
      activityListRef.value.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
}

function startPolling(): void {
  if (pollTimer) return
  pollTimer = setInterval(pollForNew, POLL_INTERVAL_MS)
}

function stopPolling(): void {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// Start/stop polling based on page visibility
function handleVisibilityChange(): void {
  if (document.visibilityState === 'visible') {
    // Poll immediately when tab becomes visible, then resume interval
    pollForNew()
    startPolling()
  } else {
    stopPolling()
  }
}

onMounted(() => {
  startPolling()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  stopPolling()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})

// ============================================
// Keyboard Navigation (Phase 4)
// ============================================

const showShortcutsHelp = ref(false)

/**
 * Flat list of navigable ActivityItems from grouped activities.
 * Aggregated groups contribute their first item for selection.
 */
const navigableItems = computed<ActivityItem[]>(() => {
  const items: ActivityItem[] = []
  for (const group of groupedActivities.value) {
    for (const item of group.items) {
      if ('isAggregated' in item && item.isAggregated) {
        // Use the first item of the aggregated group
        if (item.items.length > 0) {
          items.push(item.items[0])
        }
      } else {
        items.push(item as ActivityItem)
      }
    }
  }
  return items
})

const activityListRef = ref<HTMLElement | null>(null)

function scrollSelectedIntoView() {
  nextTick(() => {
    if (!activityListRef.value || !selectedActivity.value) return
    // Find the card with the selected background class
    const cards = activityListRef.value.querySelectorAll('.bg-orga-50')
    if (cards.length > 0) {
      cards[0].scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

function selectByIndex(index: number) {
  const items = navigableItems.value
  if (items.length === 0) return
  const clamped = Math.max(0, Math.min(index, items.length - 1))
  selectActivity(items[clamped])
  scrollSelectedIntoView()
}

function getCurrentIndex(): number {
  if (!selectedActivity.value) return -1
  return navigableItems.value.findIndex(a => a.name === selectedActivity.value!.name)
}

useActivityKeyboard({
  onNext() {
    const idx = getCurrentIndex()
    selectByIndex(idx + 1)
  },
  onPrevious() {
    const idx = getCurrentIndex()
    if (idx <= 0) {
      selectByIndex(0)
    } else {
      selectByIndex(idx - 1)
    }
  },
  onOpen() {
    if (selectedActivity.value) {
      showManager.value = true
    }
  },
  onClose() {
    if (showShortcutsHelp.value) {
      showShortcutsHelp.value = false
    } else if (showManager.value || showDetails.value) {
      showManager.value = false
      showDetails.value = false
    } else {
      selectedActivity.value = null
    }
  },
  onTogglePin() {
    if (!selectedActivity.value) return
    const isPinned = isActivityPinned(selectedActivity.value)
    handleActivityPin(!isPinned)
  },
  onToggleArchive() {
    if (!selectedActivity.value) return
    const isArchived = isActivityArchived(selectedActivity.value)
    handleActivityArchive(!isArchived)
  },
  onReply() {
    if (!selectedActivity.value) return
    showManager.value = true
    // Focus will be handled by the panel opening
  },
  onMarkRead() {
    if (hasUnreadActivities.value) {
      markAllAsRead()
    }
  },
  onShowHelp() {
    showShortcutsHelp.value = !showShortcutsHelp.value
  }
})

// Mark as read and stop polling when navigating away from Activity page
onBeforeRouteLeave(async () => {
  stopPolling()
  try {
    await markActivityViewed()
    await resetCount()
  } catch {
    // Silently ignore
  }
})
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors">
    <!-- Top Header -->
    <div class="flex-shrink-0 p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div>
            <h1 class="text-xl font-bold text-gray-800 dark:text-gray-100 m-0">{{ __('Activity') }}</h1>
            <p class="text-sm text-gray-600 dark:text-gray-400 m-0">{{ __('{0} activities', [filteredActivities.length]) }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <!-- Mark All as Read -->
          <button
            v-if="hasUnreadActivities"
            @click="markAllAsRead"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 border bg-white dark:bg-gray-700 text-orga-600 dark:text-orga-400 border-gray-200 dark:border-gray-600 hover:bg-orga-50 dark:hover:bg-gray-600"
            :title="__('Mark all as read')"
          >
            <i class="fa-solid fa-check-double"></i>
            <span class="hidden sm:inline">{{ __('Mark read') }}</span>
          </button>

          <!-- Keyboard Shortcuts Help -->
          <button
            @click="showShortcutsHelp = true"
            class="px-2 py-1.5 rounded-lg text-sm transition-all border bg-white dark:bg-gray-700 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 hover:text-gray-600 dark:hover:text-gray-300"
            :title="__('Keyboard shortcuts (?)')"
          >
            <i class="fa-regular fa-keyboard"></i>
          </button>

          <!-- Refresh Button -->
          <button
            @click="loadActivity"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 border bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
            :title="__('Refresh')"
          >
            <i class="fa-solid fa-rotate-right"></i>
          </button>

          <!-- Panel Toggles -->
          <div class="flex gap-1 ml-4">
            <button
              @click="toggleDetails"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 border',
                showDetails ? 'bg-orga-500 text-white border-orga-500' : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
              ]"
            >
              <i class="fa-solid fa-circle-info"></i> {{ __('Details') }}
            </button>
            <button
              @click="toggleManager"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 border',
                showManager ? 'bg-orga-500 text-white border-orga-500' : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
              ]"
            >
              <i class="fa-solid fa-sliders"></i> {{ __('Manager') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Main Activity List -->
      <div class="flex-1 flex flex-col overflow-hidden bg-white dark:bg-gray-900">
        <!-- Filters Bar -->
        <div class="flex flex-col gap-2 px-5 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <!-- Row 1: Type filter pills -->
          <div class="flex items-center gap-2 flex-wrap">
            <button
              v-for="filter in filters"
              :key="filter.key"
              :class="[
                'px-3 py-1.5 rounded-full text-xs border transition-all cursor-pointer',
                activeFilter === filter.key
                  ? 'bg-orga-500 text-white border-orga-500'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:border-orga-500 hover:text-orga-500'
              ]"
              @click="setFilter(filter.key)"
            >
              {{ filter.label }}
            </button>
          </div>

          <!-- Row 2: Dropdowns and toggles -->
          <div class="flex items-center gap-3 flex-wrap">
            <!-- User typeahead -->
            <div class="relative">
              <div class="flex items-center">
                <input
                  v-model="userSearch"
                  @focus="showUserSuggestions = true"
                  @blur="handleUserBlur"
                  @input="showUserSuggestions = true"
                  type="text"
                  :placeholder="__('All Users')"
                  class="w-36 px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 placeholder-gray-400 dark:placeholder-gray-500 focus:border-orga-500 focus:outline-none focus:ring-1 focus:ring-orga-500/20"
                />
                <button
                  v-if="selectedUser"
                  @click="clearUser"
                  class="absolute right-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  :title="__('Clear')"
                >
                  <i class="fa-solid fa-xmark text-[10px]"></i>
                </button>
              </div>
              <!-- Suggestions dropdown -->
              <div
                v-if="showUserSuggestions && filteredUserSuggestions.length > 0"
                class="absolute top-full left-0 mt-1 w-56 max-h-48 overflow-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20"
              >
                <button
                  v-if="selectedUser"
                  @click="clearUser"
                  class="w-full px-3 py-2 text-left text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700"
                >
                  {{ __('All Users') }}
                </button>
                <button
                  v-for="u in filteredUserSuggestions"
                  :key="u.email"
                  @click="selectUser(u)"
                  class="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <UserAvatar :name="u.name" :image="u.image" size="xs" color="orga" />
                  <div class="min-w-0 flex-1">
                    <div class="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{{ u.name }}</div>
                    <div class="text-[10px] text-gray-400 dark:text-gray-500 truncate">{{ u.email }}</div>
                  </div>
                </button>
              </div>
            </div>

            <select
              v-model="selectedProject"
              class="px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800"
            >
              <option value="">{{ __('All Projects') }}</option>
              <option v-for="project in projects" :key="project.name" :value="project.name">
                {{ project.project_name }}
              </option>
            </select>

            <label class="ml-auto flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 cursor-pointer select-none">
              <input
                type="checkbox"
                v-model="showArchived"
                class="rounded border-gray-300 dark:border-gray-600 text-orga-500 focus:ring-orga-500 w-3.5 h-3.5 bg-white dark:bg-gray-800"
              />
              <span>{{ __('Show Archived') }}</span>
            </label>
          </div>
        </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-600 dark:text-gray-400">{{ __('Loading activity...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="flex-1 flex items-center justify-center p-6">
      <div class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center">
        <i class="fa-solid fa-exclamation-triangle text-red-500 text-3xl mb-3"></i>
        <h3 class="text-red-800 dark:text-red-400 font-medium mb-2">{{ __('Error loading activity') }}</h3>
        <p class="text-red-600 dark:text-red-400 text-sm mb-4">{{ loadError }}</p>
        <button @click="loadActivity" class="px-4 py-2 bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/70 transition-colors">
          {{ __('Try Again') }}
        </button>
      </div>
    </div>

    <!-- Activity Stream -->
    <template v-else>
      <!-- Empty State -->
      <div v-if="filteredActivities.length === 0" class="flex-1 flex items-center justify-center p-6">
        <div class="text-center">
          <i class="fa-solid fa-clock-rotate-left text-5xl text-gray-300 dark:text-gray-600 mb-4"></i>
          <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">{{ __('No activity yet') }}</h3>
          <p class="text-gray-600 dark:text-gray-400">{{ __('Activity will appear here as you work on tasks and projects.') }}</p>
        </div>
      </div>

      <!-- Activity List (Grouped by Date) -->
      <div v-else ref="activityListRef" class="flex-1 overflow-y-auto px-5">
        <!-- New Activity Banner -->
        <NewActivityBanner :count="pendingNewActivities.length" @load="loadNewActivities" />

        <template v-for="group in groupedActivities" :key="group.date">
          <!-- Date Group Header -->
          <ActivityDateGroup :label="group.label" />

          <!-- Group Items -->
          <template v-for="item in group.items" :key="getItemKey(item)">
            <!-- Aggregated Card (3+ consecutive same user+type+action) -->
            <AggregatedActivityCard
              v-if="isAggregated(item)"
              :activity="item"
              :is-unread="item.items.some(i => isUnread(i))"
              @select="selectActivity"
              @update="handleActivityUpdate"
              @read="item.items.forEach(i => markAsRead(i))"
            />

            <!-- Regular Activity Card -->
            <ActivityCard
              v-else
              :activity="(item as ActivityItem)"
              :is-selected="selectedActivity?.name === (item as ActivityItem).name"
              :is-pinned="isActivityPinned(item as ActivityItem)"
              :is-archived="isActivityArchived(item as ActivityItem)"
              :is-unread="isUnread(item as ActivityItem)"
              @select="selectActivity"
              @update="handleActivityUpdate"
            />
          </template>
        </template>
      </div>
        </template>
      </div>

      <!-- Right Sidebar: Manager Panel -->
      <aside v-if="showManager" class="w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0 overflow-hidden transition-colors">
        <ActivityPanel
          v-if="selectedActivity"
          :activity="selectedActivity"
          @close="closePanel"
          @update="handleActivityUpdate"
          @pin="handleActivityPin"
          @archive="handleActivityArchive"
          @delete="handleActivityDelete"
        />

        <!-- Empty State - No activity selected -->
        <div v-else class="flex-1 flex flex-col">
          <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
              <i class="fa-solid fa-sliders text-orga-500"></i> {{ __('Manager') }}
            </h3>
            <button @click="showManager = false" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          <div class="flex-1 flex items-center justify-center p-6 text-center">
            <div>
              <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-orga-50 dark:bg-orga-900/30 flex items-center justify-center">
                <i class="fa-solid fa-hand-pointer text-2xl text-orga-500"></i>
              </div>
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('No activity selected') }}</p>
              <p class="text-xs text-gray-600 dark:text-gray-400">{{ __('Click on an activity from the list to view and manage its details.') }}</p>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Bottom Bar: Details -->
    <div v-if="showDetails" class="flex-shrink-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 transition-colors">
      <div class="flex divide-x divide-gray-200 dark:divide-gray-700">
        <!-- Activity Stats -->
        <div class="flex-1 p-4">
          <h4 class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-3 flex items-center gap-2">
            <i class="fa-solid fa-chart-pie"></i> {{ __('Activity Stats') }}
          </h4>
          <div class="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span class="text-gray-600 dark:text-gray-400">{{ __('Total:') }}</span>
              <span class="ml-2 font-medium text-gray-800 dark:text-gray-200">{{ activities.length }}</span>
            </div>
            <div>
              <span class="text-gray-600 dark:text-gray-400">{{ __('Tasks:') }}</span>
              <span class="ml-2 font-medium text-gray-800 dark:text-gray-200">{{ activities.filter(a => a.type === 'task').length }}</span>
            </div>
            <div>
              <span class="text-gray-600 dark:text-gray-400">{{ __('Milestones:') }}</span>
              <span class="ml-2 font-medium text-gray-800 dark:text-gray-200">{{ activities.filter(a => a.type === 'milestone').length }}</span>
            </div>
            <div>
              <span class="text-gray-600 dark:text-gray-400">{{ __('Events:') }}</span>
              <span class="ml-2 font-medium text-gray-800 dark:text-gray-200">{{ activities.filter(a => a.type === 'event').length }}</span>
            </div>
          </div>
        </div>

        <!-- Quick Info -->
        <div class="w-80 p-4">
          <h4 class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-3 flex items-center gap-2">
            <i class="fa-solid fa-circle-info"></i> {{ __('Selection') }}
          </h4>
          <div v-if="selectedActivity" class="text-sm">
            <p class="text-gray-800 dark:text-gray-200 font-medium">{{ selectedActivity.title }}</p>
            <p class="text-gray-600 dark:text-gray-400 text-xs mt-1">{{ selectedActivity.type }} · {{ formatRelativeTime(selectedActivity.timestamp) }}</p>
          </div>
          <p v-else class="text-sm text-gray-400 dark:text-gray-500">{{ __('No activity selected') }}</p>
        </div>
      </div>
    </div>

    <!-- Keyboard Shortcuts Help Modal -->
    <KeyboardShortcutsModal :open="showShortcutsHelp" @close="showShortcutsHelp = false" />
  </div>
</template>
