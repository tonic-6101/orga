<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardApi, useHealthApi } from '@/composables/useApi'
import { useCurrency } from '@/composables/useCurrency'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaTask, OrgaProject, DashboardStats, ActivityItem, HealthOverview } from '@/types/orga'

const router = useRouter()
const { getStats, getRecentActivity, getMyTasks, getProjectSummary, loading, error } = useDashboardApi()
const { getHealthOverview } = useHealthApi()
const { formatCurrency } = useCurrency()

// Dashboard display stat item
interface DisplayStat {
  label: string
  value: number | string
  icon: string
  color: string
  route?: string
  tooltip?: string
}

// Navigate to stat detail
function navigateToStat(stat: DisplayStat): void {
  if (stat.route) {
    router.push(stat.route)
  }
}

// Data refs
const stats = ref<DashboardStats | null>(null)
const myTasks = ref<OrgaTask[]>([])
const activities = ref<ActivityItem[]>([])
const projects = ref<OrgaProject[]>([])
const healthOverview = ref<HealthOverview | null>(null)
const isLoading = ref<boolean>(true)
const loadError = ref<string | null>(null)

// Computed stats for display
const displayStats = computed<DisplayStat[]>(() => {
  if (!stats.value) {
    return [
      { label: __('Active Projects'), value: '-', icon: 'folder-open', color: 'text-orga-500', route: '/orga/projects', tooltip: __('View all active projects') },
      { label: __('Open Tasks'), value: '-', icon: 'tasks', color: 'text-blue-500', route: '/orga/projects', tooltip: __('View all open tasks') },
      { label: __('Overdue Tasks'), value: '-', icon: 'exclamation-circle', color: 'text-red-500', route: '/orga/projects', tooltip: __('View overdue tasks') },
      { label: __('Due This Week'), value: '-', icon: 'calendar-week', color: 'text-teal-500', route: '/orga/schedule', tooltip: __('View this week\'s schedule') },
    ]
  }

  const activeCount = stats.value.projects?.by_status?.active || 0
  const openCount = stats.value.tasks?.by_status?.open || 0
  const overdueCount = stats.value.tasks?.overdue || 0
  const weekCount = stats.value.tasks?.due_this_week || 0

  return [
    {
      label: __('Active Projects'),
      value: activeCount,
      icon: 'folder-open',
      color: 'text-orga-500',
      route: '/orga/projects',
      tooltip: __("{0} project(s) currently in progress", [activeCount])
    },
    {
      label: __('Open Tasks'),
      value: openCount,
      icon: 'tasks',
      color: 'text-blue-500',
      route: '/orga/projects',
      tooltip: __("{0} task(s) awaiting completion", [openCount])
    },
    {
      label: __('Overdue Tasks'),
      value: overdueCount,
      icon: 'exclamation-circle',
      color: 'text-red-500',
      route: '/orga/projects',
      tooltip: overdueCount > 0 ? __("{0} task(s) past due date - needs attention", [overdueCount]) : __('No overdue tasks')
    },
    {
      label: __('Due This Week'),
      value: weekCount,
      icon: 'calendar-week',
      color: 'text-teal-500',
      route: '/orga/schedule',
      tooltip: __("{0} task(s) due in the next 7 days", [weekCount])
    },
  ]
})

// Badge display type
interface BadgeDisplay {
  text: string
  class: string
}

// Format due date for display
function formatDueDate(dueDate: string | null | undefined): BadgeDisplay {
  if (!dueDate) return { text: __('No due date'), class: 'bg-gray-100 text-gray-600' }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDate)
  due.setHours(0, 0, 0, 0)

  const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return { text: __('Overdue'), class: 'bg-red-100 text-red-600' }
  } else if (diffDays === 0) {
    return { text: __('Today'), class: 'bg-orange-100 text-orange-600' }
  } else if (diffDays === 1) {
    return { text: __('Tomorrow'), class: 'bg-yellow-100 text-yellow-600' }
  } else if (diffDays <= 7) {
    return { text: __('{0} days', [diffDays]), class: 'bg-blue-100 text-blue-600' }
  } else {
    return { text: due.toLocaleDateString('de-DE', { month: 'short', day: 'numeric' }), class: 'bg-gray-100 text-gray-600' }
  }
}

// Format relative time
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
  return date.toLocaleDateString('de-DE', { month: 'short', day: 'numeric' })
}

// Get activity icon based on type
function getActivityIcon(activity: ActivityItem): string {
  const icons: Record<string, string> = {
    task: '📋',
    milestone: '◆',
    project: '📁',
    comment: '💬',
    assignment: '👥'
  }
  return icons[activity.type] || '📋'
}

// Get project status display
function getProjectStatus(project: OrgaProject): BadgeDisplay {
  if (project.health_status === 'Green' || project.status === 'Active') {
    return { text: __('On Track'), class: 'bg-green-100 text-green-600' }
  } else if (project.health_status === 'Yellow' || (project.overdue_tasks && project.overdue_tasks > 0)) {
    return { text: __('At Risk'), class: 'bg-orange-100 text-orange-600' }
  } else if (project.health_status === 'Red') {
    return { text: __('Delayed'), class: 'bg-red-100 text-red-600' }
  } else if (project.status === 'Planning') {
    return { text: __('Planning'), class: 'bg-blue-100 text-blue-600' }
  }
  return { text: project.status, class: 'bg-gray-100 text-gray-600' }
}


// Load dashboard data
async function loadDashboard(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const [statsData, tasksData, activityData, projectsData, healthData] = await Promise.all([
      getStats(),
      getMyTasks(null, 5),
      getRecentActivity(5),
      getProjectSummary(),
      getHealthOverview().catch(() => null)
    ])

    stats.value = statsData
    myTasks.value = tasksData || []
    activities.value = activityData || []
    projects.value = (projectsData || []).slice(0, 5)
    healthOverview.value = healthData
  } catch (e) {
    console.error('Failed to load dashboard:', e)
    loadError.value = (e as Error).message || __('Failed to load dashboard data')
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="p-6">
    <!-- Welcome -->
    <div class="mb-6">
      <h1 class="text-h1 text-gray-800 dark:text-gray-100 m-0">{{ __('Welcome back!') }}</h1>
      <p class="text-body text-gray-600 dark:text-gray-400 mt-1">{{ __("Here's what's happening with your projects today.") }}</p>
    </div>

    <!-- Loading State - Skeleton Layout -->
    <div v-if="isLoading">
      <!-- Stats Skeletons -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Skeleton v-for="i in 4" :key="i" type="stat" />
      </div>

      <!-- Tasks & Activity Skeletons -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Skeleton type="card" :count="4" />
        <Skeleton type="card" :count="4" />
      </div>

      <!-- Health Skeletons -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Skeleton type="card" :count="3" />
        <Skeleton type="card" :count="3" />
      </div>

      <!-- Projects Skeleton -->
      <Skeleton type="card" :count="5" />
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
      <div class="flex items-center gap-3">
        <i class="fa-solid fa-exclamation-triangle text-red-500 text-xl"></i>
        <div>
          <h3 class="text-red-800 font-medium">{{ __('Error loading dashboard') }}</h3>
          <p class="text-red-600 text-sm">{{ loadError }}</p>
        </div>
      </div>
      <button
        @click="loadDashboard"
        class="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
      >
        {{ __('Try Again') }}
      </button>
    </div>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <button
          v-for="stat in displayStats"
          :key="stat.label"
          @click="navigateToStat(stat)"
          :title="stat.tooltip"
          class="stat-card bg-white dark:bg-gray-800 rounded-lg p-5 border border-gray-200 dark:border-gray-700 cursor-pointer text-left transition-all hover:shadow-md hover:border-orga-300 dark:hover:border-orga-600 focus:outline-none focus:ring-2 focus:ring-orga-500/20 group"
        >
          <i :class="['fa-solid', `fa-${stat.icon}`, 'float-right text-h2 opacity-30 group-hover:opacity-50 transition-opacity']"></i>
          <div class="text-overline text-gray-600 dark:text-gray-400 mb-2">{{ stat.label }}</div>
          <div :class="['text-display', stat.color]">{{ stat.value }}</div>
          <div class="text-xs text-gray-500 dark:text-gray-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {{ __('Click to view') }} →
          </div>
        </button>
      </div>

      <!-- Tasks & Activity -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- My Tasks -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
            <span class="text-overline text-gray-800 dark:text-gray-100">{{ __('My Tasks') }}</span>
            <router-link to="/orga/my-tasks" class="text-caption text-orga-500 hover:underline">{{ __('View All') }}</router-link>
          </div>
          <div class="p-4">
            <div v-if="myTasks.length === 0" class="text-center py-6 text-gray-600 dark:text-gray-400">
              <i class="fa-solid fa-check-circle text-3xl text-green-400 mb-2"></i>
              <p>{{ __('No tasks assigned to you') }}</p>
            </div>
            <div
              v-else
              v-for="task in myTasks"
              :key="task.name"
              class="task-row flex items-center py-2.5 border-b border-gray-100 dark:border-gray-700 last:border-0"
            >
              <div class="w-4 h-4 border-2 border-gray-300 dark:border-gray-600 rounded mr-3 cursor-pointer hover:border-orga-500"></div>
              <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-800 dark:text-gray-200 truncate">{{ task.subject }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400 truncate">{{ task.project_name || task.project }}</div>
              </div>
              <span :class="['text-xs px-2 py-1 rounded whitespace-nowrap ml-2', formatDueDate(task.due_date).class]">
                {{ formatDueDate(task.due_date).text }}
              </span>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
            <span class="text-overline text-gray-800 dark:text-gray-100">{{ __('Recent Activity') }}</span>
            <router-link to="/orga/activity" class="text-caption text-orga-500 hover:underline">{{ __('View All') }}</router-link>
          </div>
          <div class="p-4">
            <div v-if="activities.length === 0" class="text-center py-6 text-gray-600 dark:text-gray-400">
              <i class="fa-solid fa-clock text-3xl text-gray-300 dark:text-gray-600 mb-2"></i>
              <p>{{ __('No recent activity') }}</p>
            </div>
            <div
              v-else
              v-for="activity in activities"
              :key="activity.name + activity.timestamp"
              class="flex gap-3 py-2.5 border-b border-gray-100 dark:border-gray-700 last:border-0"
            >
              <div class="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-sm flex-shrink-0">
                {{ getActivityIcon(activity) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-800 dark:text-gray-200 truncate">
                  {{ activity.title }} - {{ activity.status }}
                </div>
                <div class="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {{ activity.project_name || activity.project }} · {{ formatRelativeTime(activity.timestamp) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Health Overview -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- Health Overview -->
        <div v-if="healthOverview" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
            <span class="text-overline text-gray-800 dark:text-gray-100">{{ __('Project Health') }}</span>
            <span class="text-caption text-gray-600 dark:text-gray-400">{{ __('{0} projects', [healthOverview.total]) }}</span>
          </div>
          <div class="p-4">
            <!-- Health bars with enhanced tooltips -->
            <div class="flex gap-1 h-4 mb-4 rounded overflow-hidden">
              <div
                v-if="healthOverview.summary?.green"
                class="bg-green-500 hover:bg-green-400 transition-colors cursor-help health-bar-segment"
                :style="{ flex: healthOverview.summary.green }"
                :title="`✓ ${healthOverview.summary.green} Healthy project${healthOverview.summary.green !== 1 ? 's' : ''} - On track with no issues`"
              ></div>
              <div
                v-if="healthOverview.summary?.yellow"
                class="bg-yellow-500 hover:bg-yellow-400 transition-colors cursor-help health-bar-segment"
                :style="{ flex: healthOverview.summary.yellow }"
                :title="`⚠ ${healthOverview.summary.yellow} At Risk project${healthOverview.summary.yellow !== 1 ? 's' : ''} - May need attention soon`"
              ></div>
              <div
                v-if="healthOverview.summary?.red"
                class="bg-red-500 hover:bg-red-400 transition-colors cursor-help health-bar-segment"
                :style="{ flex: healthOverview.summary.red }"
                :title="`✕ ${healthOverview.summary.red} Critical project${healthOverview.summary.red !== 1 ? 's' : ''} - Requires immediate attention`"
              ></div>
              <div
                v-if="healthOverview.summary?.unknown"
                class="bg-gray-300 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 transition-colors cursor-help health-bar-segment"
                :style="{ flex: healthOverview.summary.unknown }"
                :title="`? ${healthOverview.summary.unknown} project${healthOverview.summary.unknown !== 1 ? 's' : ''} with unknown health status`"
              ></div>
            </div>

            <!-- Legend -->
            <div class="flex flex-wrap gap-4 text-sm">
              <button
                @click="router.push('/orga/projects?health=green')"
                class="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :title="__('Click to view healthy projects')"
              >
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
                <span class="text-gray-600 dark:text-gray-400">{{ healthOverview.summary?.green || 0 }} {{ __('Healthy') }}</span>
              </button>
              <button
                @click="router.push('/orga/projects?health=yellow')"
                class="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :title="__('Click to view at-risk projects')"
              >
                <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                <span class="text-gray-600 dark:text-gray-400">{{ healthOverview.summary?.yellow || 0 }} {{ __('At Risk') }}</span>
              </button>
              <button
                @click="router.push('/orga/projects?health=red')"
                class="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :title="__('Click to view critical projects')"
              >
                <div class="w-3 h-3 rounded-full bg-red-500"></div>
                <span class="text-gray-600 dark:text-gray-400">{{ healthOverview.summary?.red || 0 }} {{ __('Critical') }}</span>
              </button>
            </div>

            <!-- At-risk projects -->
            <div v-if="healthOverview.at_risk?.length" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div class="text-overline text-gray-600 dark:text-gray-400 mb-2">{{ __('Needs Attention') }}</div>
              <div
                v-for="project in healthOverview.at_risk.slice(0, 3)"
                :key="project.name"
                class="flex items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
              >
                <div :class="['w-2 h-2 rounded-full mr-3', project.health_status === 'Red' ? 'bg-red-500' : 'bg-yellow-500']"></div>
                <router-link
                  :to="`/orga/projects/${project.name}`"
                  class="flex-1 text-sm text-gray-800 dark:text-gray-200 hover:text-orga-500 truncate"
                >
                  {{ project.project_name }}
                </router-link>
                <span class="text-xs text-gray-600 dark:text-gray-400">{{ Math.round(project.progress || 0) }}%</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Projects Overview -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-6">
        <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
          <span class="text-overline text-gray-800 dark:text-gray-100">{{ __('Projects Overview') }}</span>
          <router-link to="/orga/projects" class="text-caption text-orga-500 hover:underline">{{ __('View All') }}</router-link>
        </div>
        <div class="p-4">
          <div v-if="projects.length === 0" class="text-center py-6 text-gray-600 dark:text-gray-400">
            <i class="fa-solid fa-folder-open text-3xl text-gray-300 dark:text-gray-600 mb-2"></i>
            <p>{{ __('No active projects') }}</p>
          </div>
          <router-link
            v-else
            v-for="project in projects"
            :key="project.name"
            :to="`/orga/projects/${project.name}`"
            class="project-card flex items-center py-3 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 -mx-2 px-2 rounded transition-colors"
          >
            <span class="w-36 text-subtitle text-gray-800 dark:text-gray-200 hover:text-orga-500 truncate">
              {{ project.project_name }}
            </span>
            <div
              class="flex-1 h-5 bg-gray-100 dark:bg-gray-700 rounded mx-4 overflow-hidden cursor-help"
              :title="`${project.project_name}: ${Math.round(project.progress || 0)}% complete (${project.completed_tasks || 0}/${project.total_tasks || 0} tasks)`"
            >
              <div
                :class="[
                  'h-full rounded transition-all',
                  (project.progress || 0) >= 100 ? 'bg-green-500' :
                  (project.progress || 0) >= 75 ? 'bg-orga-500' :
                  (project.progress || 0) >= 50 ? 'bg-blue-500' :
                  (project.progress || 0) >= 25 ? 'bg-yellow-500' :
                  'bg-orange-500'
                ]"
                :style="{ width: `${project.progress || 0}%` }"
              ></div>
            </div>
            <span class="w-12 text-right text-sm font-semibold text-gray-800 dark:text-gray-200">{{ Math.round(project.progress || 0) }}%</span>
            <StatusBadge :status="getProjectStatus(project).text" type="project" size="sm" class="ml-4" />
          </router-link>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* Stat card hover effects */
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(99, 102, 241, 0.02) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

/* Health bar segments - subtle pulse on hover */
.health-bar-segment {
  position: relative;
}

.health-bar-segment:hover {
  transform: scaleY(1.1);
}

/* Project progress bar animation */
.project-card .h-5 > div {
  transition: width 0.5s ease-out;
}

/* Legend buttons */
.flex button.flex {
  cursor: pointer;
}
</style>
