<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTheme, type ThemeMode } from '@/composables/useTheme'
import { __ } from '@/composables/useTranslate'

const { mode: themeMode, isDark, setMode: setThemeMode } = useTheme()

interface UserPreferences {
  notifications_enabled: boolean
  email_notifications: boolean
  default_view: 'kanban' | 'list' | 'gantt'
  timezone: string
  language: string
}

const isLoading = ref<boolean>(true)
const isSaving = ref<boolean>(false)
const saveMessage = ref<string>('')

// Avatar upload
const avatarInputRef = ref<HTMLInputElement | null>(null)
const isUploadingAvatar = ref<boolean>(false)
const avatarUrl = ref<string | null>(null)

const preferences = ref<UserPreferences>({
  notifications_enabled: true,
  email_notifications: true,
  default_view: 'kanban',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  language: 'en'
})

type FrappeWindow = Window & { frappe?: { boot?: { user?: Record<string, string> }; csrf_token?: string } }

const user = computed(() => {
  const session = (window as FrappeWindow).frappe?.boot?.user || {}
  return {
    name: session.full_name || session.name || 'User',
    email: session.email || session.name || '',
    avatar: avatarUrl.value ?? session.user_image ?? null
  }
})

const userInitials = computed<string>(() => {
  const name = user.value.name
  if (!name || name === 'User') return 'U'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
})

function triggerAvatarUpload(): void {
  avatarInputRef.value?.click()
}

async function handleAvatarUpload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // Validate file type
  if (!file.type.startsWith('image/')) {
    saveMessage.value = __('Please select an image file')
    setTimeout(() => { saveMessage.value = '' }, 3000)
    input.value = ''
    return
  }

  // Validate file size (5MB max)
  if (file.size > 5 * 1024 * 1024) {
    saveMessage.value = __('Image must be smaller than 5 MB')
    setTimeout(() => { saveMessage.value = '' }, 3000)
    input.value = ''
    return
  }

  const session = (window as FrappeWindow).frappe?.boot?.user || {}
  const userName = session.name || session.email
  if (!userName) return

  isUploadingAvatar.value = true
  saveMessage.value = ''

  try {
    // Upload the file
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doctype', 'User')
    formData.append('docname', userName)
    formData.append('is_private', '0')

    const fileUrl: string = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const resp = JSON.parse(xhr.responseText)
          resolve(resp.message?.file_url || '')
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`))
        }
      }
      xhr.onerror = () => reject(new Error('Upload failed'))
      xhr.open('POST', '/api/method/upload_file')
      xhr.setRequestHeader('X-Frappe-CSRF-Token', (window as FrappeWindow).frappe?.csrf_token || '')
      xhr.send(formData)
    })

    if (!fileUrl) throw new Error('No file URL returned')

    // Set user_image on the User document
    await fetch('/api/method/frappe.client.set_value', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as FrappeWindow).frappe?.csrf_token || ''
      },
      body: JSON.stringify({
        doctype: 'User',
        name: userName,
        fieldname: 'user_image',
        value: fileUrl
      })
    })

    // Update local state and boot data so all components reflect the change
    avatarUrl.value = fileUrl
    const bootUser = (window as FrappeWindow).frappe?.boot?.user
    if (bootUser) {
      bootUser.user_image = fileUrl
    }

    saveMessage.value = __('Avatar updated successfully')
    setTimeout(() => { saveMessage.value = '' }, 3000)
  } catch (e) {
    console.error('Failed to upload avatar:', e)
    saveMessage.value = __('Failed to upload avatar')
    setTimeout(() => { saveMessage.value = '' }, 3000)
  } finally {
    isUploadingAvatar.value = false
    input.value = ''
  }
}

async function loadPreferences(): Promise<void> {
  isLoading.value = true
  try {
    // In a full implementation, this would load from the backend
    // For now, use defaults
    await new Promise(resolve => setTimeout(resolve, 300))
  } catch (e) {
    console.error('Failed to load preferences:', e)
  } finally {
    isLoading.value = false
  }
}

async function savePreferences(): Promise<void> {
  isSaving.value = true
  saveMessage.value = ''
  try {
    // In a full implementation, this would save to the backend
    await new Promise(resolve => setTimeout(resolve, 500))
    saveMessage.value = __('Preferences saved successfully')
    setTimeout(() => { saveMessage.value = '' }, 3000)
  } catch (e) {
    console.error('Failed to save preferences:', e)
    saveMessage.value = __('Failed to save preferences')
  } finally {
    isSaving.value = false
  }
}

onMounted(loadPreferences)
</script>

<template>
  <div class="h-full flex flex-col bg-white dark:bg-gray-950">
    <!-- Header -->
    <div class="flex justify-between items-center px-5 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
      <span class="text-sm font-semibold text-gray-800 dark:text-gray-100">
        <i class="fa-solid fa-sliders text-orga-500 mr-2"></i>
        {{ __('Preferences') }}
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-500 dark:text-gray-400">{{ __('Loading preferences...') }}</p>
      </div>
    </div>

    <!-- Content -->
    <div v-else class="flex-1 overflow-auto p-6">
      <div class="max-w-2xl mx-auto space-y-8">
        <!-- Profile Section -->
        <section>
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <i class="fa-solid fa-user text-orga-500"></i>
            {{ __('Profile') }}
          </h2>
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div class="flex items-center gap-4">
              <!-- Clickable Avatar -->
              <button
                @click="triggerAvatarUpload"
                :disabled="isUploadingAvatar"
                class="relative w-16 h-16 rounded-full overflow-hidden shrink-0 group cursor-pointer focus:outline-none focus:ring-2 focus:ring-orga-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:cursor-wait"
              >
                <img
                  v-if="user.avatar"
                  :src="user.avatar"
                  :alt="user.name"
                  class="w-full h-full object-cover"
                />
                <div
                  v-else
                  class="w-full h-full bg-orga-500 text-white flex items-center justify-center font-semibold text-xl"
                >
                  {{ userInitials }}
                </div>
                <!-- Upload overlay -->
                <div
                  v-if="isUploadingAvatar"
                  class="absolute inset-0 bg-black/60 flex items-center justify-center"
                >
                  <i class="fa-solid fa-spinner fa-spin text-white text-lg"></i>
                </div>
                <div
                  v-else
                  class="absolute inset-0 bg-black/50 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <i class="fa-solid fa-camera text-white text-sm"></i>
                  <span class="text-white text-[9px] mt-0.5 font-medium">{{ __('Change') }}</span>
                </div>
              </button>
              <input
                ref="avatarInputRef"
                type="file"
                accept="image/*"
                class="hidden"
                @change="handleAvatarUpload"
              />
              <div>
                <p class="font-medium text-gray-800 dark:text-gray-100">{{ user.name }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ user.email }}</p>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {{ __('Click the avatar to upload a new photo') }}
                </p>
              </div>
            </div>
          </div>
        </section>

        <!-- Notifications Section -->
        <section>
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <i class="fa-solid fa-bell text-orga-500"></i>
            {{ __('Notifications') }}
          </h2>
          <div class="space-y-4">
            <label class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <div>
                <p class="font-medium text-gray-800 dark:text-gray-100">{{ __('In-app notifications') }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('Receive notifications within the application') }}</p>
              </div>
              <input
                v-model="preferences.notifications_enabled"
                type="checkbox"
                class="w-5 h-5 text-orga-500 rounded border-gray-300 dark:border-gray-600 focus:ring-orga-500"
              />
            </label>

            <label class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <div>
                <p class="font-medium text-gray-800 dark:text-gray-100">{{ __('Email notifications') }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('Receive notifications via email') }}</p>
              </div>
              <input
                v-model="preferences.email_notifications"
                type="checkbox"
                class="w-5 h-5 text-orga-500 rounded border-gray-300 dark:border-gray-600 focus:ring-orga-500"
              />
            </label>
          </div>
        </section>

        <!-- Appearance Section -->
        <section>
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <i class="fa-solid fa-palette text-orga-500"></i>
            {{ __('Appearance') }}
          </h2>
          <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <span class="font-medium text-gray-800 dark:text-gray-100 block mb-3">{{ __('Theme') }}</span>
            <div class="grid grid-cols-3 gap-3">
              <button
                @click="setThemeMode('light')"
                :class="[
                  'flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all',
                  themeMode === 'light'
                    ? 'border-orga-500 bg-orga-50 dark:bg-orga-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
              >
                <i class="fa-solid fa-sun text-lg text-amber-500"></i>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Light') }}</span>
              </button>
              <button
                @click="setThemeMode('dark')"
                :class="[
                  'flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all',
                  themeMode === 'dark'
                    ? 'border-orga-500 bg-orga-50 dark:bg-orga-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
              >
                <i class="fa-solid fa-moon text-lg text-indigo-400"></i>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Dark') }}</span>
              </button>
              <button
                @click="setThemeMode('auto')"
                :class="[
                  'flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all',
                  themeMode === 'auto'
                    ? 'border-orga-500 bg-orga-50 dark:bg-orga-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
              >
                <i class="fa-solid fa-circle-half-stroke text-lg text-gray-500 dark:text-gray-400"></i>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Auto') }}</span>
              </button>
            </div>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-3">
              <template v-if="themeMode === 'auto'">
                {{ __('Follows your system preference. Currently:') }} <strong class="text-gray-600 dark:text-gray-300">{{ isDark ? __('Dark') : __('Light') }}</strong>
              </template>
              <template v-else>
                {{ __('Theme is set to {0} mode', [themeMode]) }}
              </template>
            </p>
          </div>
        </section>

        <!-- Display Section -->
        <section>
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <i class="fa-solid fa-display text-orga-500"></i>
            {{ __('Display') }}
          </h2>
          <div class="space-y-4">
            <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <label class="block">
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ __('Default task view') }}</span>
                <select
                  v-model="preferences.default_view"
                  class="mt-2 block w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:ring-1 focus:ring-orga-500"
                >
                  <option value="kanban">{{ __('Kanban Board') }}</option>
                  <option value="list">{{ __('List View') }}</option>
                  <option value="gantt">{{ __('Gantt Chart') }}</option>
                </select>
              </label>
            </div>

            <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <label class="block">
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ __('Timezone') }}</span>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">{{ preferences.timezone }}</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">
                  {{ __('Timezone is detected from your browser') }}
                </p>
              </label>
            </div>
          </div>
        </section>

        <!-- Save Button -->
        <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <p v-if="saveMessage" :class="[
            'text-sm',
            saveMessage.includes('success') ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          ]">
            {{ saveMessage }}
          </p>
          <div v-else></div>
          <button
            @click="savePreferences"
            :disabled="isSaving"
            class="px-4 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <i :class="['fa-solid', isSaving ? 'fa-spinner fa-spin' : 'fa-check']"></i>
            {{ isSaving ? __('Saving...') : __('Save Preferences') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
