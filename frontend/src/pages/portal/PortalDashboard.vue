<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePortalApi } from '@/composables/usePortalApi'
import { useAuth } from '@/composables/useAuth'
import { __ } from '@/composables/useTranslate'
import type {
  PortalClient,
  PortalProject,
  PortalStats,
  ProjectStatus
} from '@/types/portal'
import { PROJECT_STATUS_COLORS, HEALTH_STATUS_COLORS } from '@/types/portal'
import { Loader2, TriangleAlert, FolderOpen, Heart, CircleCheck, Calendar, Flag, Headset } from 'lucide-vue-next'
import OrgaIcon from '@/components/common/OrgaIcon.vue'

const { getPortalDashboard, loading, error } = usePortalApi()
const { user } = useAuth()

const client = ref<PortalClient | null>(null)
const projects = ref<PortalProject[]>([])
const stats = ref<PortalStats | null>(null)

/**
 * Load dashboard data on mount
 */
onMounted(async () => {
  try {
    const data = await getPortalDashboard()
    client.value = data.client
    projects.value = data.projects
    stats.value = data.stats
  } catch (e) {
    console.error('Failed to load portal dashboard:', e)
  }
})

/**
 * Get status badge class
 */
function getStatusClass(status: ProjectStatus): string {
  return PROJECT_STATUS_COLORS[status] || 'bg-gray-100 text-gray-600'
}

/**
 * Get health badge class
 */
function getHealthClass(health: string | undefined): string {
  if (!health) return 'bg-gray-100 text-gray-500'
  return HEALTH_STATUS_COLORS[health as keyof typeof HEALTH_STATUS_COLORS] || 'bg-gray-100 text-gray-500'
}

/**
 * Format date for display
 */
function formatDate(date: string | undefined): string {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Stats cards configuration
 */
const statsCards = computed(() => {
  if (!stats.value) return []
  return [
    {
      label: __('Total Projects'),
      value: stats.value.total_projects,
      icon: 'folder',
      color: 'text-accent-500'
    },
    {
      label: __('Active'),
      value: stats.value.active_projects,
      icon: 'play',
      color: 'text-blue-500'
    },
    {
      label: __('Completed'),
      value: stats.value.completed_projects,
      icon: 'circle-check',
      color: 'text-green-500'
    },
    {
      label: __('Overall Progress'),
      value: `${stats.value.overall_progress}%`,
      icon: 'trending-up',
      color: 'text-purple-500'
    }
  ]
})
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <Loader2 class="w-8 h-8 text-accent-500 mb-3 animate-spin" aria-hidden="true" />
        <p class="text-gray-500">{{ __('Loading your portal...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <TriangleAlert class="w-5 h-5 text-red-500" aria-hidden="true" />
        <div>
          <h3 class="text-red-800 font-medium">{{ __('Error loading dashboard') }}</h3>
          <p class="text-red-600 text-sm">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else>
      <!-- Welcome Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800 mb-1">
          {{ __('Welcome, {0}', [client?.client_name || user?.full_name || __('Client')]) }}
        </h1>
        <p v-if="client?.company" class="text-gray-500">{{ client.company }}</p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div
          v-for="stat in statsCards"
          :key="stat.label"
          class="bg-white rounded-lg p-5 border border-gray-200 shadow-sm"
        >
          <OrgaIcon :name="stat.icon" :class="['w-6 h-6 float-right opacity-30', stat.color]" />
          <div class="text-xs text-gray-500 uppercase mb-2">{{ stat.label }}</div>
          <div :class="['text-3xl font-bold', stat.color]">{{ stat.value }}</div>
        </div>
      </div>

      <!-- Projects Section -->
      <div class="mb-4">
        <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <FolderOpen class="w-5 h-5 text-accent-500" aria-hidden="true" />
          {{ __('Your Projects') }}
        </h2>
      </div>

      <!-- Projects Grid -->
      <div v-if="projects.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <router-link
          v-for="project in projects"
          :key="project.name"
          :to="`/orga/portal/project/${project.name}`"
          class="block bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow no-underline"
        >
          <!-- Card Header -->
          <div class="p-4 pb-2">
            <div class="flex items-start justify-between mb-2">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusClass(project.status)]">
                {{ project.status }}
              </span>
              <span
                v-if="project.health_status"
                :class="['px-2 py-1 text-xs font-medium rounded-full', getHealthClass(project.health_status)]"
              >
                <Heart class="w-3 h-3 inline mr-1" aria-hidden="true" />
                {{ project.health_status }}
              </span>
            </div>

            <!-- Project Name -->
            <h3 class="text-base font-semibold text-gray-800 mb-1 line-clamp-1">
              {{ project.project_name }}
            </h3>

            <!-- Description -->
            <p v-if="project.description" class="text-sm text-gray-500 line-clamp-2 mb-3">
              {{ project.description }}
            </p>
          </div>

          <!-- Card Body -->
          <div class="px-4 pb-4">
            <!-- Progress Bar -->
            <div class="mb-3">
              <div class="flex justify-between items-center mb-1">
                <span class="text-xs text-gray-500">{{ __('Progress') }}</span>
                <span class="text-sm font-semibold text-gray-700">{{ Math.round(project.progress || 0) }}%</span>
              </div>
              <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-accent-500 rounded-full transition-all"
                  :style="{ width: `${project.progress || 0}%` }"
                ></div>
              </div>
            </div>

            <!-- Task Stats -->
            <div class="flex items-center justify-between text-sm text-gray-500 mb-2">
              <span>
                <CircleCheck class="w-3.5 h-3.5 text-green-500 inline mr-1" aria-hidden="true" />
                {{ __("{0}/{1} tasks", [project.completed_tasks, project.task_count]) }}
              </span>
              <span v-if="project.end_date">
                <Calendar class="w-3.5 h-3.5 inline mr-1" aria-hidden="true" />
                {{ formatDate(project.end_date) }}
              </span>
            </div>

            <!-- Upcoming Milestone -->
            <div
              v-if="project.upcoming_milestone"
              class="bg-blue-50 border border-blue-100 rounded p-2 text-sm"
            >
              <Flag class="w-3.5 h-3.5 text-blue-500 inline mr-1" aria-hidden="true" />
              <span class="font-medium text-blue-700">{{ __('Next:') }}</span>
              <span class="text-blue-600 ml-1">{{ project.upcoming_milestone.milestone_name }}</span>
              <span v-if="project.upcoming_milestone.due_date" class="text-blue-400 text-xs ml-1">
                ({{ formatDate(project.upcoming_milestone.due_date) }})
              </span>
            </div>
          </div>
        </router-link>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <FolderOpen class="w-12 h-12 text-gray-300 mb-4 mx-auto" aria-hidden="true" />
        <h3 class="text-lg font-medium text-gray-800 mb-2">{{ __('No Projects Yet') }}</h3>
        <p class="text-gray-500 mb-4">
          {{ __("Your projects will appear here once they're assigned to you.") }}<br>
          {{ __('Contact your project manager for more information.') }}
        </p>
        <router-link
          to="/orga/portal/support"
          class="inline-flex items-center gap-2 px-4 py-2 bg-accent-500 text-white rounded hover:bg-accent-600 no-underline"
        >
          <Headset class="w-4 h-4 inline" aria-hidden="true" />
          {{ __('Contact Support') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
