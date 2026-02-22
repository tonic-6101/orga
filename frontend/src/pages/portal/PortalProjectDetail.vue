<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePortalApi } from '@/composables/usePortalApi'
import { useCurrency } from '@/composables/useCurrency'
import { __ } from '@/composables/useTranslate'
import type {
  PortalProjectDetail,
  PortalMilestone,
  PortalTaskSummary,
  PortalActivityItem,
  ProjectStatus
} from '@/types/portal'
import { PROJECT_STATUS_COLORS, HEALTH_STATUS_COLORS, MILESTONE_STATUS_COLORS } from '@/types/portal'

const route = useRoute()
const { getPortalProject, loading, error } = usePortalApi()
const { formatCurrency } = useCurrency()

const project = ref<PortalProjectDetail | null>(null)
const milestones = ref<PortalMilestone[]>([])
const taskSummary = ref<PortalTaskSummary | null>(null)
const recentActivity = ref<PortalActivityItem[]>([])

/**
 * Load project data on mount
 */
onMounted(async () => {
  const projectId = route.params.id as string
  if (!projectId) return

  try {
    const data = await getPortalProject(projectId)
    project.value = data.project
    milestones.value = data.milestones
    taskSummary.value = data.task_summary
    recentActivity.value = data.recent_activity
  } catch (e) {
    console.error('Failed to load project:', e)
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
  if (!date) return __('TBD')
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Format relative time
 */
function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __('{0}m ago', [diffMins])
  if (diffHours < 24) return __('{0}h ago', [diffHours])
  if (diffDays < 7) return __('{0}d ago', [diffDays])
  return formatDate(timestamp)
}


/**
 * Task status cards
 */
const taskStatusCards = computed(() => {
  if (!taskSummary.value) return []
  return [
    { label: __('Open'), value: taskSummary.value.Open, color: 'text-gray-600' },
    { label: __('In Progress'), value: taskSummary.value.Working, color: 'text-yellow-600' },
    { label: __('In Review'), value: taskSummary.value['Pending Review'], color: 'text-blue-600' },
    { label: __('Completed'), value: taskSummary.value.Completed, color: 'text-green-600' }
  ]
})

/**
 * Budget bar color based on utilization
 */
const budgetBarColor = computed(() => {
  if (!project.value?.budget_utilization) return 'bg-green-500'
  const util = project.value.budget_utilization
  if (util > 90) return 'bg-red-500'
  if (util > 75) return 'bg-yellow-500'
  return 'bg-green-500'
})
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-500">{{ __('Loading project...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <i class="fa-solid fa-exclamation-triangle text-red-500 text-xl"></i>
        <div>
          <h3 class="text-red-800 font-medium">{{ __('Error loading project') }}</h3>
          <p class="text-red-600 text-sm">{{ error }}</p>
        </div>
      </div>
      <router-link
        to="/orga/portal"
        class="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 no-underline"
      >
        <i class="fa-solid fa-arrow-left"></i>
        {{ __('Back to Projects') }}
      </router-link>
    </div>

    <!-- Project Content -->
    <div v-else-if="project">
      <!-- Project Header Card -->
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
        <div class="p-6">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <!-- Badges -->
              <div class="flex items-center gap-2 mb-3">
                <span :class="['px-3 py-1 text-sm font-medium rounded-full', getStatusClass(project.status)]">
                  {{ project.status }}
                </span>
                <span
                  v-if="project.health_status"
                  :class="['px-3 py-1 text-sm font-medium rounded-full', getHealthClass(project.health_status)]"
                >
                  <i class="fa-solid fa-heart mr-1"></i>
                  {{ project.health_status }}
                </span>
              </div>

              <!-- Project Name -->
              <h1 class="text-2xl font-bold text-gray-800 mb-2">{{ project.project_name }}</h1>
              <p v-if="project.description" class="text-gray-500">{{ project.description }}</p>
            </div>

            <!-- Progress Display -->
            <div class="text-right">
              <div class="text-4xl font-bold text-orga-500">{{ Math.round(project.progress || 0) }}%</div>
              <div class="text-sm text-gray-500">{{ __('Complete') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column (2/3) -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Progress Overview -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-4 border-b border-gray-100">
              <h2 class="font-semibold text-gray-800 flex items-center gap-2">
                <i class="fa-solid fa-chart-line text-orga-500"></i>
                {{ __('Progress Overview') }}
              </h2>
            </div>
            <div class="p-4">
              <!-- Main Progress Bar -->
              <div class="mb-6">
                <div class="flex justify-between mb-2">
                  <span class="text-sm text-gray-500">{{ __('Overall Progress') }}</span>
                  <span class="text-sm font-semibold text-gray-700">{{ Math.round(project.progress || 0) }}%</span>
                </div>
                <div class="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-orga-500 rounded-full transition-all"
                    :style="{ width: `${project.progress || 0}%` }"
                  ></div>
                </div>
              </div>

              <!-- Task Stats Grid -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div
                  v-for="stat in taskStatusCards"
                  :key="stat.label"
                  class="border border-gray-200 rounded-lg p-3 text-center"
                >
                  <div :class="['text-2xl font-bold', stat.color]">{{ stat.value }}</div>
                  <div class="text-xs text-gray-500">{{ stat.label }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Milestones -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-4 border-b border-gray-100">
              <h2 class="font-semibold text-gray-800 flex items-center gap-2">
                <i class="fa-solid fa-flag text-yellow-500"></i>
                {{ __('Milestones') }}
              </h2>
            </div>
            <div class="p-4">
              <div v-if="milestones.length" class="space-y-4">
                <div
                  v-for="milestone in milestones"
                  :key="milestone.name"
                  class="flex gap-3"
                >
                  <!-- Status Icon -->
                  <div class="flex-shrink-0 pt-0.5">
                    <div
                      v-if="milestone.status === 'Completed'"
                      class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center"
                    >
                      <i class="fa-solid fa-check text-green-600"></i>
                    </div>
                    <div
                      v-else-if="milestone.is_overdue"
                      class="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center"
                    >
                      <i class="fa-solid fa-exclamation text-red-600"></i>
                    </div>
                    <div v-else class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <i class="fa-solid fa-clock text-blue-600"></i>
                    </div>
                  </div>

                  <!-- Content -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-start justify-between gap-2">
                      <div>
                        <h4
                          :class="[
                            'font-medium',
                            milestone.status === 'Completed' ? 'text-gray-400 line-through' : 'text-gray-800'
                          ]"
                        >
                          {{ milestone.milestone_name }}
                        </h4>
                        <p v-if="milestone.description" class="text-sm text-gray-500 line-clamp-2">
                          {{ milestone.description }}
                        </p>
                      </div>
                      <span
                        :class="[
                          'px-2 py-0.5 text-xs font-medium rounded whitespace-nowrap',
                          MILESTONE_STATUS_COLORS[milestone.status] || 'bg-gray-100 text-gray-600'
                        ]"
                      >
                        {{ milestone.status }}
                      </span>
                    </div>
                    <div class="text-xs text-gray-400 mt-1">
                      <template v-if="milestone.status === 'Completed' && milestone.completion_date">
                        <i class="fa-solid fa-check-circle text-green-500 mr-1"></i>
                        {{ __('Completed') }} {{ formatDate(milestone.completion_date) }}
                      </template>
                      <template v-else-if="milestone.is_overdue">
                        <i class="fa-solid fa-exclamation-triangle text-red-500 mr-1"></i>
                        {{ __('Overdue - was due {0}', [formatDate(milestone.due_date)]) }}
                      </template>
                      <template v-else>
                        <i class="fa-regular fa-calendar mr-1"></i>
                        {{ __('Due {0}', [formatDate(milestone.due_date)]) }}
                      </template>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else class="text-center py-8 text-gray-500">
                <i class="fa-solid fa-flag fa-2x text-gray-300 mb-2"></i>
                <p>{{ __('No milestones defined for this project.') }}</p>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div v-if="recentActivity.length" class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-4 border-b border-gray-100">
              <h2 class="font-semibold text-gray-800 flex items-center gap-2">
                <i class="fa-solid fa-history text-gray-500"></i>
                {{ __('Recent Activity') }}
              </h2>
            </div>
            <div class="divide-y divide-gray-100">
              <div
                v-for="(activity, idx) in recentActivity"
                :key="`${activity.type}-${idx}`"
                class="p-4 flex items-center gap-3"
              >
                <span
                  :class="[
                    'w-8 h-8 rounded-full flex items-center justify-center text-white',
                    activity.type === 'milestone' ? 'bg-yellow-500' : 'bg-green-500'
                  ]"
                >
                  <i :class="['fa-solid text-sm', activity.type === 'milestone' ? 'fa-flag' : 'fa-check']"></i>
                </span>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-800 truncate">{{ activity.title }}</div>
                  <div class="text-xs text-gray-500">
                    {{ activity.type === 'milestone' ? __('Milestone') : __('Task') }}
                    {{ activity.action }} - {{ formatRelativeTime(activity.timestamp) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column (1/3) -->
        <div class="space-y-6">
          <!-- Project Details -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-4 border-b border-gray-100">
              <h2 class="font-semibold text-gray-800 flex items-center gap-2">
                <i class="fa-solid fa-info-circle text-blue-500"></i>
                {{ __('Project Details') }}
              </h2>
            </div>
            <div class="p-4">
              <dl class="space-y-3">
                <div v-if="project.start_date" class="flex justify-between py-2 border-b border-gray-100">
                  <dt class="text-gray-500">{{ __('Start Date') }}</dt>
                  <dd class="font-medium text-gray-800">{{ formatDate(project.start_date) }}</dd>
                </div>
                <div v-if="project.end_date" class="flex justify-between py-2 border-b border-gray-100">
                  <dt class="text-gray-500">{{ __('Target End') }}</dt>
                  <dd class="font-medium text-gray-800">{{ formatDate(project.end_date) }}</dd>
                </div>
                <div v-if="project.days_remaining && project.days_remaining > 0" class="flex justify-between py-2 border-b border-gray-100">
                  <dt class="text-gray-500">{{ __('Days Remaining') }}</dt>
                  <dd class="font-medium text-green-600">{{ __('{0} days', [project.days_remaining]) }}</dd>
                </div>
                <div v-else-if="project.days_overdue && project.days_overdue > 0" class="flex justify-between py-2 border-b border-gray-100">
                  <dt class="text-gray-500">{{ __('Days Overdue') }}</dt>
                  <dd class="font-medium text-red-600">{{ __('{0} days', [project.days_overdue]) }}</dd>
                </div>
                <div v-if="project.manager_name" class="flex justify-between py-2 border-b border-gray-100">
                  <dt class="text-gray-500">{{ __('Project Manager') }}</dt>
                  <dd class="font-medium text-gray-800">{{ project.manager_name }}</dd>
                </div>
                <div class="flex justify-between py-2">
                  <dt class="text-gray-500">{{ __('Total Tasks') }}</dt>
                  <dd class="font-medium text-gray-800">{{ taskSummary?.total || 0 }}</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Budget (if available) -->
          <div v-if="project.budget" class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-4 border-b border-gray-100">
              <h2 class="font-semibold text-gray-800 flex items-center gap-2">
                <i class="fa-solid fa-coins text-yellow-500"></i>
                {{ __('Budget') }}
              </h2>
            </div>
            <div class="p-4">
              <div class="mb-3">
                <div class="flex justify-between mb-1">
                  <span class="text-sm text-gray-500">{{ __('Spent') }}</span>
                  <span class="text-sm font-semibold text-gray-700">
                    {{ formatCurrency(project.spent) }} / {{ formatCurrency(project.budget) }}
                  </span>
                </div>
                <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    :class="['h-full rounded-full transition-all', budgetBarColor]"
                    :style="{ width: `${Math.min(project.budget_utilization, 100)}%` }"
                  ></div>
                </div>
              </div>
              <p class="text-sm text-gray-500">
                {{ __('{0}% of budget used', [project.budget_utilization]) }}
              </p>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="p-4 border-b border-gray-100">
              <h2 class="font-semibold text-gray-800 flex items-center gap-2">
                <i class="fa-solid fa-bolt text-orga-500"></i>
                {{ __('Quick Actions') }}
              </h2>
            </div>
            <div class="p-4 space-y-2">
              <router-link
                to="/orga/portal"
                class="flex items-center gap-2 w-full px-4 py-2 text-gray-700 border border-gray-200 rounded hover:bg-gray-50 no-underline"
              >
                <i class="fa-solid fa-arrow-left text-gray-500"></i>
                {{ __('Back to Projects') }}
              </router-link>
              <router-link
                :to="`/orga/portal/support?project=${project.name}`"
                class="flex items-center gap-2 w-full px-4 py-2 text-gray-700 border border-gray-200 rounded hover:bg-gray-50 no-underline"
              >
                <i class="fa-solid fa-envelope text-gray-500"></i>
                {{ __('Contact Support') }}
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
