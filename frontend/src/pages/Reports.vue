<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef, markRaw } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { useReportsApi, useProjectApi } from '../composables/useApi'
import { useCurrency } from '../composables/useCurrency'
import { useTheme } from '../composables/useTheme'
import { __ } from '@/composables/useTranslate'
import type {
  OrgaProject,
  ProjectSummaryReport,
  ContactUtilizationReport,
  ContactUtilization,
  TaskCompletionReport,
  BudgetTrackingReport,
  MilestoneReport,
  OrgaMilestone,
  OrgaTask
} from '@/types/orga'

const reportsApi = useReportsApi()
const projectApi = useProjectApi()
const { formatCurrency, currencyIcon } = useCurrency()
const { isDark } = useTheme()

// ============================================
// Tab Definitions
// ============================================

interface TabDef {
  key: string
  label: string
  icon: string
}

const tabs = computed<TabDef[]>(() => [
  { key: 'project-summary', label: __('Projects'), icon: 'fa-solid fa-folder-open' },
  { key: 'resource-utilization', label: __('Utilization'), icon: 'fa-solid fa-users' },
  { key: 'task-completion', label: __('Tasks'), icon: 'fa-solid fa-check-circle' },
  { key: 'budget', label: __('Budget'), icon: currencyIcon.value },
  { key: 'milestones', label: __('Milestones'), icon: 'fa-solid fa-flag' }
])

const activeTab = ref('project-summary')

// ============================================
// Filter State
// ============================================

const filterProject = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const filterDaysAhead = ref(30)

// Dropdown options
const projects = ref<OrgaProject[]>([])

// ============================================
// Report Data (cached per tab)
// ============================================

const projectReport = ref<ProjectSummaryReport | null>(null)
const utilizationReport = ref<ContactUtilizationReport | null>(null)
const taskReport = ref<TaskCompletionReport | null>(null)
const budgetReport = ref<BudgetTrackingReport | null>(null)
const milestoneReport = ref<MilestoneReport | null>(null)

const loadingTab = ref(false)
const errorMessage = ref('')
const loadedTabs = ref<Set<string>>(new Set())

// ============================================
// Theme-Aware Chart Colors
// ============================================

const chartForeColor = computed(() => isDark.value ? '#9CA3AF' : '#4B5563')
const chartGridColor = computed(() => isDark.value ? '#374151' : '#E5E7EB')

function baseChartOptions(extra: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    chart: {
      background: 'transparent',
      foreColor: chartForeColor.value,
      toolbar: { show: false },
      ...((extra.chart as Record<string, unknown>) || {})
    },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    grid: {
      borderColor: chartGridColor.value,
      ...((extra.grid as Record<string, unknown>) || {})
    },
    legend: {
      labels: { colors: chartForeColor.value },
      ...((extra.legend as Record<string, unknown>) || {})
    },
    ...extra,
    // Re-spread chart/grid/legend so they're merged, not overwritten
  }
}

// ============================================
// Status Colors
// ============================================

const statusColors: Record<string, string> = {
  // Project status
  'Planning': '#6366F1',
  'In Progress': '#3B82F6',
  'Completed': '#10B981',
  'On Hold': '#F59E0B',
  'Cancelled': '#EF4444',
  // Health
  'green': '#10B981',
  'yellow': '#F59E0B',
  'red': '#EF4444',
  'Green': '#10B981',
  'Yellow': '#F59E0B',
  'Red': '#EF4444',
  // Utilization status
  'overallocated': '#EF4444',
  'busy': '#F59E0B',
  'available': '#10B981',
  // Budget status
  'over': '#EF4444',
  'on_track': '#10B981',
  'under': '#3B82F6',
  // Milestone status
  'upcoming': '#3B82F6',
  'completed': '#10B981',
  'missed': '#EF4444',
  'Pending': '#F59E0B',
  'Missed': '#EF4444',
  // Task priority
  'Low': '#6366F1',
  'Medium': '#3B82F6',
  'High': '#F59E0B',
  'Urgent': '#EF4444',
}

function getColor(key: string): string {
  return statusColors[key] || '#6B7280'
}

// ============================================
// Chart Options — Projects Tab
// ============================================

const projectStatusChartOptions = computed(() => {
  const data = projectReport.value?.summary.by_status || {}
  const labels = Object.keys(data)
  const colors = labels.map(l => getColor(l))
  return {
    chart: { type: 'donut', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    labels,
    colors,
    legend: { position: 'bottom' as const, labels: { colors: chartForeColor.value } },
    plotOptions: { pie: { donut: { size: '55%' } } },
    dataLabels: { enabled: true },
    title: { text: 'By Status', style: { color: chartForeColor.value } }
  }
})

const projectStatusChartSeries = computed(() => {
  const data = projectReport.value?.summary.by_status || {}
  return Object.values(data)
})

const projectHealthChartOptions = computed(() => {
  const data = projectReport.value?.summary.by_health || {}
  const labels = Object.keys(data).map(k => k.charAt(0).toUpperCase() + k.slice(1))
  const colors = Object.keys(data).map(k => getColor(k))
  return {
    chart: { type: 'donut', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    labels,
    colors,
    legend: { position: 'bottom' as const, labels: { colors: chartForeColor.value } },
    plotOptions: { pie: { donut: { size: '55%' } } },
    dataLabels: { enabled: true },
    title: { text: 'By Health', style: { color: chartForeColor.value } }
  }
})

const projectHealthChartSeries = computed(() => {
  const data = projectReport.value?.summary.by_health || {}
  return Object.values(data)
})

// ============================================
// Chart Options — Utilization Tab
// ============================================

const utilizationBarOptions = computed(() => {
  const resources = (utilizationReport.value?.resources || []).slice(0, 10)
  return {
    chart: { type: 'bar', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    plotOptions: { bar: { horizontal: true, barHeight: '60%' } },
    grid: { borderColor: chartGridColor.value },
    xaxis: { categories: resources.map(r => r.resource_name), max: 100, labels: { formatter: (v: number) => `${v}%` } },
    colors: ['#3B82F6'],
    dataLabels: { enabled: true, formatter: (v: number) => `${v.toFixed(0)}%` },
    title: { text: 'Top Resources by Utilization', style: { color: chartForeColor.value } }
  }
})

const utilizationBarSeries = computed(() => {
  const resources = (utilizationReport.value?.resources || []).slice(0, 10)
  return [{ name: 'Utilization', data: resources.map(r => Math.round(r.utilization_percent)) }]
})

const utilizationDonutOptions = computed(() => {
  const summary = utilizationReport.value?.summary
  if (!summary) return {}
  const labels = ['Overallocated', 'Busy', 'Available']
  const colors = [getColor('overallocated'), getColor('busy'), getColor('available')]
  return {
    chart: { type: 'donut', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    labels,
    colors,
    legend: { position: 'bottom' as const, labels: { colors: chartForeColor.value } },
    plotOptions: { pie: { donut: { size: '55%' } } },
    title: { text: 'Status Distribution', style: { color: chartForeColor.value } }
  }
})

const utilizationDonutSeries = computed(() => {
  const s = utilizationReport.value?.summary
  if (!s) return []
  return [s.overallocated, s.busy, s.available]
})

// ============================================
// Chart Options — Tasks Tab
// ============================================

const taskPriorityBarOptions = computed(() => {
  const data = taskReport.value?.by_priority || {}
  return {
    chart: { type: 'bar', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    grid: { borderColor: chartGridColor.value },
    xaxis: { categories: Object.keys(data) },
    colors: Object.keys(data).map(k => getColor(k)),
    plotOptions: { bar: { distributed: true, columnWidth: '50%' } },
    legend: { show: false },
    dataLabels: { enabled: true },
    title: { text: 'Completed by Priority', style: { color: chartForeColor.value } }
  }
})

const taskPriorityBarSeries = computed(() => {
  const data = taskReport.value?.by_priority || {}
  return [{ name: 'Completed', data: Object.values(data) }]
})

const taskProjectBarOptions = computed(() => {
  const data = taskReport.value?.by_project || {}
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10)
  return {
    chart: { type: 'bar', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    plotOptions: { bar: { horizontal: true, barHeight: '60%' } },
    grid: { borderColor: chartGridColor.value },
    xaxis: { categories: entries.map(([k]) => k) },
    colors: ['#6366F1'],
    dataLabels: { enabled: true },
    title: { text: 'Completed by Project (Top 10)', style: { color: chartForeColor.value } }
  }
})

const taskProjectBarSeries = computed(() => {
  const data = taskReport.value?.by_project || {}
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 10)
  return [{ name: 'Completed', data: entries.map(([, v]) => v) }]
})

// ============================================
// Chart Options — Budget Tab
// ============================================

const budgetBarOptions = computed(() => {
  const projs = budgetReport.value?.projects || []
  const top = projs.slice(0, 10)
  return {
    chart: { type: 'bar', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    plotOptions: { bar: { horizontal: true, barHeight: '60%' } },
    grid: { borderColor: chartGridColor.value },
    xaxis: { categories: top.map(p => p.project_name) },
    colors: ['#3B82F6', '#EF4444'],
    dataLabels: { enabled: false },
    title: { text: 'Budget vs Spent', style: { color: chartForeColor.value } },
    legend: { position: 'top' as const, labels: { colors: chartForeColor.value } }
  }
})

const budgetBarSeries = computed(() => {
  const projs = budgetReport.value?.projects || []
  const top = projs.slice(0, 10)
  return [
    { name: 'Budget', data: top.map(p => p.budget || 0) },
    { name: 'Spent', data: top.map(p => p.spent || 0) }
  ]
})

const budgetDonutOptions = computed(() => {
  const s = budgetReport.value?.summary
  if (!s) return {}
  const labels = ['Over Budget', 'On Track', 'Under Budget']
  const colors = [getColor('over'), getColor('on_track'), getColor('under')]
  return {
    chart: { type: 'donut', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    labels,
    colors,
    legend: { position: 'bottom' as const, labels: { colors: chartForeColor.value } },
    plotOptions: { pie: { donut: { size: '55%' } } },
    title: { text: 'Budget Status', style: { color: chartForeColor.value } }
  }
})

const budgetDonutSeries = computed(() => {
  const s = budgetReport.value?.summary
  if (!s) return []
  return [s.projects_over_budget, s.projects_on_track, s.projects_under_budget]
})

// ============================================
// Chart Options — Milestones Tab
// ============================================

const milestoneDonutOptions = computed(() => {
  const s = milestoneReport.value?.summary
  if (!s) return {}
  const labels = ['Completed', 'Upcoming', 'Missed']
  const colors = [getColor('completed'), getColor('upcoming'), getColor('missed')]
  return {
    chart: { type: 'donut', background: 'transparent', foreColor: chartForeColor.value, toolbar: { show: false } },
    theme: { mode: isDark.value ? 'dark' as const : 'light' as const },
    labels,
    colors,
    legend: { position: 'bottom' as const, labels: { colors: chartForeColor.value } },
    plotOptions: { pie: { donut: { size: '55%' } } },
    title: { text: 'Milestone Status', style: { color: chartForeColor.value } }
  }
})

const milestoneDonutSeries = computed(() => {
  const s = milestoneReport.value?.summary
  if (!s) return []
  return [s.completed, s.upcoming, s.missed]
})

// ============================================
// Generated At Timestamp
// ============================================

const generatedAt = computed(() => {
  switch (activeTab.value) {
    case 'project-summary': return projectReport.value?.generated_at
    case 'resource-utilization': return utilizationReport.value?.generated_at
    case 'task-completion': return taskReport.value?.generated_at
    case 'budget': return budgetReport.value?.generated_at
    case 'milestones': return milestoneReport.value?.generated_at
    default: return undefined
  }
})

// ============================================
// Data Loading
// ============================================

async function loadDropdowns(): Promise<void> {
  try {
    const projectResult = await projectApi.getProjects({ limit: 200 })
    projects.value = projectResult?.projects || []
  } catch (e) {
    console.error('Failed to load filter options:', e)
  }
}

async function loadActiveTab(force = false): Promise<void> {
  const tab = activeTab.value
  if (!force && loadedTabs.value.has(tab)) return

  loadingTab.value = true
  errorMessage.value = ''

  try {
    switch (tab) {
      case 'project-summary': {
        const filters: { date_from?: string; date_to?: string } = {}
        if (filterDateFrom.value) filters.date_from = filterDateFrom.value
        if (filterDateTo.value) filters.date_to = filterDateTo.value
        projectReport.value = await reportsApi.getProjectSummaryReport(filters)
        break
      }
      case 'resource-utilization': {
        const filters: { date_from?: string; date_to?: string } = {}
        if (filterDateFrom.value) filters.date_from = filterDateFrom.value
        if (filterDateTo.value) filters.date_to = filterDateTo.value
        utilizationReport.value = await reportsApi.getContactUtilizationReport(filters)
        break
      }
      case 'task-completion': {
        const filters: { project?: string; date_from?: string; date_to?: string } = {}
        if (filterProject.value) filters.project = filterProject.value
        if (filterDateFrom.value) filters.date_from = filterDateFrom.value
        if (filterDateTo.value) filters.date_to = filterDateTo.value
        taskReport.value = await reportsApi.getTaskCompletionReport(filters)
        break
      }
      case 'budget': {
        budgetReport.value = await reportsApi.getBudgetTrackingReport(null)
        break
      }
      case 'milestones': {
        const filters: { days_ahead?: number } = {}
        filters.days_ahead = filterDaysAhead.value
        milestoneReport.value = await reportsApi.getMilestoneReport(filters)
        break
      }
    }
    loadedTabs.value.add(tab)
  } catch (e: unknown) {
    console.error(`Failed to load ${tab} report:`, e)
    errorMessage.value = e instanceof Error ? e.message : __('Failed to load report data')
  } finally {
    loadingTab.value = false
  }
}

function invalidateAndReload(): void {
  loadedTabs.value.clear()
  loadActiveTab(true)
}

// ============================================
// Computed: Active tab has data?
// ============================================

const hasData = computed(() => {
  switch (activeTab.value) {
    case 'project-summary': return projectReport.value && (projectReport.value.projects?.length || 0) > 0
    case 'resource-utilization': return utilizationReport.value && (utilizationReport.value.resources?.length || 0) > 0
    case 'task-completion': return taskReport.value && (taskReport.value.tasks?.length || 0) > 0
    case 'budget': return budgetReport.value && (budgetReport.value.projects?.length || 0) > 0
    case 'milestones': return milestoneReport.value && (milestoneReport.value.milestones?.length || 0) > 0
    default: return false
  }
})

// ============================================
// Helpers
// ============================================

function formatPercent(v: number | undefined): string {
  if (v === undefined || v === null) return '0%'
  return `${Math.round(v)}%`
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr + 'T00:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

function daysLabel(dateStr: string): string {
  const d = daysUntil(dateStr)
  if (d === 0) return __('Today')
  if (d > 0) return __('in {0}d', [d])
  return __('{0}d ago', [Math.abs(d)])
}

function statusBadgeClass(status: string): string {
  switch (status.toLowerCase()) {
    case 'completed': case 'green': case 'available': case 'on_track': case 'under':
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    case 'in progress': case 'working': case 'busy': case 'yellow':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
    case 'planning': case 'upcoming': case 'open':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    case 'on hold': case 'overallocated': case 'over': case 'red': case 'missed':
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
    case 'cancelled':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
  }
}

function budgetStatusLabel(status: string): string {
  switch (status) {
    case 'over': return __('Over Budget')
    case 'on_track': return __('On Track')
    case 'under': return __('Under Budget')
    default: return status
  }
}

// ============================================
// Which filters are visible per tab
// ============================================

const showProjectFilter = computed(() => activeTab.value === 'task-completion')
const showDateFilters = computed(() =>
  ['project-summary', 'resource-utilization', 'task-completion'].includes(activeTab.value)
)
const showDaysAhead = computed(() => activeTab.value === 'milestones')

// ============================================
// Sorting
// ============================================

const sortColumn = ref('')
const sortAsc = ref(true)

function toggleSort(col: string): void {
  if (sortColumn.value === col) {
    sortAsc.value = !sortAsc.value
  } else {
    sortColumn.value = col
    sortAsc.value = true
  }
}

function sortIcon(col: string): string {
  if (sortColumn.value !== col) return 'fa-sort'
  return sortAsc.value ? 'fa-sort-up' : 'fa-sort-down'
}

function sortedArray<T>(arr: T[], key: string): T[] {
  if (!sortColumn.value) return arr
  const copy = [...arr]
  copy.sort((a, b) => {
    const aVal = (a as Record<string, unknown>)[key]
    const bVal = (b as Record<string, unknown>)[key]
    if (aVal == null && bVal == null) return 0
    if (aVal == null) return 1
    if (bVal == null) return -1
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortAsc.value ? aVal - bVal : bVal - aVal
    }
    const aStr = String(aVal).toLowerCase()
    const bStr = String(bVal).toLowerCase()
    return sortAsc.value ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr)
  })
  return copy
}

// Sorted table data per tab
const sortedProjects = computed(() => {
  if (!projectReport.value?.projects) return []
  return sortedArray(projectReport.value.projects, sortColumn.value)
})

const sortedResources = computed(() => {
  if (!utilizationReport.value?.resources) return []
  return sortedArray(utilizationReport.value.resources, sortColumn.value)
})

const sortedTasks = computed(() => {
  if (!taskReport.value?.tasks) return []
  return sortedArray(taskReport.value.tasks, sortColumn.value)
})

const sortedBudgetProjects = computed(() => {
  if (!budgetReport.value?.projects) return []
  return sortedArray(budgetReport.value.projects, sortColumn.value)
})

const sortedMilestones = computed(() => {
  if (!milestoneReport.value?.milestones) return []
  return sortedArray(milestoneReport.value.milestones, sortColumn.value)
})

// ============================================
// Watchers
// ============================================

watch(activeTab, () => {
  sortColumn.value = ''
  sortAsc.value = true
  loadActiveTab()
})

watch([filterProject, filterDateFrom, filterDateTo, filterDaysAhead], () => {
  invalidateAndReload()
})

// ============================================
// Lifecycle
// ============================================

onMounted(() => {
  loadDropdowns()
  loadActiveTab()
})
</script>

<template>
  <div class="p-6 bg-white dark:bg-gray-950 min-h-full">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Reports') }}</h1>
        <span
          v-if="generatedAt"
          class="text-xs text-gray-400 dark:text-gray-500"
        >
          {{ __('Generated {0}', [formatDate(generatedAt.split('T')[0])]) }}
        </span>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-2">
        <select
          v-if="showProjectFilter"
          v-model="filterProject"
          class="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
        >
          <option value="">{{ __('All Projects') }}</option>
          <option v-for="p in projects" :key="p.name" :value="p.name">{{ p.project_name }}</option>
        </select>

        <input
          v-if="showDateFilters"
          v-model="filterDateFrom"
          type="date"
          class="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
          :placeholder="__('From')"
        />
        <input
          v-if="showDateFilters"
          v-model="filterDateTo"
          type="date"
          class="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
          :placeholder="__('To')"
        />

        <select
          v-if="showDaysAhead"
          v-model.number="filterDaysAhead"
          class="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
        >
          <option :value="7">{{ __('Next 7 days') }}</option>
          <option :value="14">{{ __('Next 14 days') }}</option>
          <option :value="30">{{ __('Next 30 days') }}</option>
          <option :value="60">{{ __('Next 60 days') }}</option>
          <option :value="90">{{ __('Next 90 days') }}</option>
        </select>
      </div>
    </div>

    <!-- Tab Bar -->
    <div class="flex gap-1 mb-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
          activeTab === tab.key
            ? 'border-orga-500 text-orga-600 dark:text-orga-400'
            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500'
        ]"
      >
        <i :class="[tab.icon, 'text-xs']"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loadingTab" class="py-16 text-center">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 text-2xl"></i>
      <p class="text-sm text-gray-400 mt-3 m-0">{{ __('Loading report data...') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="py-16 text-center">
      <i class="fa-solid fa-triangle-exclamation text-red-400 text-2xl"></i>
      <p class="text-sm text-red-500 dark:text-red-400 mt-3 m-0">{{ errorMessage }}</p>
      <button
        @click="loadActiveTab(true)"
        class="mt-3 px-4 py-1.5 bg-orga-500 text-white text-sm rounded hover:bg-orga-600 transition-colors"
      >
        {{ __('Retry') }}
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasData" class="py-16 text-center">
      <i class="fa-regular fa-chart-bar text-3xl text-gray-300 dark:text-gray-600 mb-3"></i>
      <p class="text-gray-500 dark:text-gray-400 m-0">{{ __('No data available for the selected filters') }}</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1 m-0">{{ __('Try adjusting your filter criteria') }}</p>
    </div>

    <!-- ==================== PROJECTS TAB ==================== -->
    <template v-else-if="activeTab === 'project-summary' && projectReport">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total Projects') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ projectReport.summary.total_projects }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Avg Progress') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatPercent(projectReport.summary.avg_progress) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total Budget') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatCurrency(projectReport.summary.total_budget) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total Spent') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatCurrency(projectReport.summary.total_spent) }}</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6" v-if="projectStatusChartSeries.length > 0 || projectHealthChartSeries.length > 0">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="projectStatusChartSeries.length > 0">
          <VueApexCharts type="donut" height="280" :options="projectStatusChartOptions" :series="projectStatusChartSeries" />
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="projectHealthChartSeries.length > 0">
          <VueApexCharts type="donut" height="280" :options="projectHealthChartOptions" :series="projectHealthChartSeries" />
        </div>
      </div>

      <!-- Data Table -->
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('project_name')">
                  {{ __('Name') }} <i :class="['fa-solid text-xs ml-1', sortIcon('project_name')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('status')">
                  {{ __('Status') }} <i :class="['fa-solid text-xs ml-1', sortIcon('status')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('health_status')">
                  {{ __('Health') }} <i :class="['fa-solid text-xs ml-1', sortIcon('health_status')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('progress')">
                  {{ __('Progress') }} <i :class="['fa-solid text-xs ml-1', sortIcon('progress')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('budget')">
                  {{ __('Budget') }} <i :class="['fa-solid text-xs ml-1', sortIcon('budget')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('spent')">
                  {{ __('Spent') }} <i :class="['fa-solid text-xs ml-1', sortIcon('spent')]"></i>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="proj in sortedProjects"
                :key="proj.name"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <td class="px-4 py-3 text-gray-800 dark:text-gray-200">{{ proj.project_name }}</td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusBadgeClass(proj.status)]">{{ proj.status }}</span>
                </td>
                <td class="px-4 py-3">
                  <span v-if="proj.health_status" :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusBadgeClass(proj.health_status)]">
                    {{ proj.health_status }}
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                  <div class="flex items-center justify-end gap-2">
                    <div class="w-16 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                      <div class="h-full bg-orga-500 rounded-full" :style="{ width: `${Math.min(proj.progress || 0, 100)}%` }"></div>
                    </div>
                    <span class="text-xs">{{ formatPercent(proj.progress) }}</span>
                  </div>
                </td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">{{ formatCurrency(proj.budget) }}</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">{{ formatCurrency(proj.spent) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ==================== UTILIZATION TAB ==================== -->
    <template v-else-if="activeTab === 'resource-utilization' && utilizationReport">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total Contacts') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ utilizationReport.summary.total_contacts }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Overallocated') }}</p>
          <p class="text-2xl font-bold text-red-600 dark:text-red-400 m-0 mt-1">{{ utilizationReport.summary.overallocated }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Busy') }}</p>
          <p class="text-2xl font-bold text-yellow-600 dark:text-yellow-400 m-0 mt-1">{{ utilizationReport.summary.busy }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Available') }}</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 m-0 mt-1">{{ utilizationReport.summary.available }}</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="utilizationBarSeries[0]?.data?.length">
          <VueApexCharts type="bar" height="280" :options="utilizationBarOptions" :series="utilizationBarSeries" />
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="utilizationDonutSeries.length > 0">
          <VueApexCharts type="donut" height="280" :options="utilizationDonutOptions" :series="utilizationDonutSeries" />
        </div>
      </div>

      <!-- Data Table -->
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('resource_name')">
                  {{ __('Name') }} <i :class="['fa-solid text-xs ml-1', sortIcon('resource_name')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('department')">
                  {{ __('Department') }} <i :class="['fa-solid text-xs ml-1', sortIcon('department')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('weekly_capacity')">
                  {{ __('Capacity') }} <i :class="['fa-solid text-xs ml-1', sortIcon('weekly_capacity')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('allocated_hours')">
                  {{ __('Allocated') }} <i :class="['fa-solid text-xs ml-1', sortIcon('allocated_hours')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('utilization_percent')">
                  {{ __('Utilization') }} <i :class="['fa-solid text-xs ml-1', sortIcon('utilization_percent')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('status')">
                  {{ __('Status') }} <i :class="['fa-solid text-xs ml-1', sortIcon('status')]"></i>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="res in sortedResources"
                :key="res.resource"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <td class="px-4 py-3 text-gray-800 dark:text-gray-200">{{ res.resource_name }}</td>
                <td class="px-4 py-3 text-gray-500 dark:text-gray-400 hidden md:table-cell">{{ res.department || '-' }}</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ res.weekly_capacity }}h</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ res.allocated_hours.toFixed(1) }}h</td>
                <td class="px-4 py-3 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <div class="w-16 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full"
                        :class="res.status === 'overallocated' ? 'bg-red-500' : res.status === 'busy' ? 'bg-yellow-500' : 'bg-green-500'"
                        :style="{ width: `${Math.min(res.utilization_percent, 100)}%` }"
                      ></div>
                    </div>
                    <span class="text-xs text-gray-700 dark:text-gray-300">{{ formatPercent(res.utilization_percent) }}</span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium capitalize', statusBadgeClass(res.status)]">{{ res.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ==================== TASKS TAB ==================== -->
    <template v-else-if="activeTab === 'task-completion' && taskReport">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Completed') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ taskReport.summary.total_completed }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('On-Time Rate') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatPercent(taskReport.summary.on_time_rate) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Est. Hours') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ taskReport.summary.total_estimated_hours.toFixed(1) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Efficiency') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatPercent(taskReport.summary.efficiency) }}</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="taskPriorityBarSeries[0]?.data?.length">
          <VueApexCharts type="bar" height="280" :options="taskPriorityBarOptions" :series="taskPriorityBarSeries" />
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="taskProjectBarSeries[0]?.data?.length">
          <VueApexCharts type="bar" height="280" :options="taskProjectBarOptions" :series="taskProjectBarSeries" />
        </div>
      </div>

      <!-- Data Table -->
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('subject')">
                  {{ __('Task') }} <i :class="['fa-solid text-xs ml-1', sortIcon('subject')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('project')">
                  {{ __('Project') }} <i :class="['fa-solid text-xs ml-1', sortIcon('project')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('priority')">
                  {{ __('Priority') }} <i :class="['fa-solid text-xs ml-1', sortIcon('priority')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('estimated_hours')">
                  {{ __('Est. Hours') }} <i :class="['fa-solid text-xs ml-1', sortIcon('estimated_hours')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('actual_hours')">
                  {{ __('Actual Hours') }} <i :class="['fa-solid text-xs ml-1', sortIcon('actual_hours')]"></i>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in sortedTasks"
                :key="task.name"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <td class="px-4 py-3 text-gray-800 dark:text-gray-200">{{ task.subject }}</td>
                <td class="px-4 py-3 text-gray-500 dark:text-gray-400 hidden md:table-cell">{{ task.project || '-' }}</td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusBadgeClass(task.priority)]">{{ task.priority }}</span>
                </td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">{{ task.estimated_hours?.toFixed(1) || '-' }}</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">{{ task.actual_hours?.toFixed(1) || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ==================== BUDGET TAB ==================== -->
    <template v-else-if="activeTab === 'budget' && budgetReport">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total Budget') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatCurrency(budgetReport.summary.total_budget) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total Spent') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatCurrency(budgetReport.summary.total_spent) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Remaining') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatCurrency(budgetReport.summary.total_remaining) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Overall Utilization') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ formatPercent(budgetReport.summary.overall_utilization) }}</p>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="budgetBarSeries[0]?.data?.length">
          <VueApexCharts type="bar" height="280" :options="budgetBarOptions" :series="budgetBarSeries" />
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" v-if="budgetDonutSeries.length > 0">
          <VueApexCharts type="donut" height="280" :options="budgetDonutOptions" :series="budgetDonutSeries" />
        </div>
      </div>

      <!-- Data Table -->
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('project_name')">
                  {{ __('Project') }} <i :class="['fa-solid text-xs ml-1', sortIcon('project_name')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('status')">
                  {{ __('Status') }} <i :class="['fa-solid text-xs ml-1', sortIcon('status')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('budget')">
                  {{ __('Budget') }} <i :class="['fa-solid text-xs ml-1', sortIcon('budget')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('spent')">
                  {{ __('Spent') }} <i :class="['fa-solid text-xs ml-1', sortIcon('spent')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('remaining')">
                  {{ __('Remaining') }} <i :class="['fa-solid text-xs ml-1', sortIcon('remaining')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('utilization_percent')">
                  {{ __('Utilization') }} <i :class="['fa-solid text-xs ml-1', sortIcon('utilization_percent')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('budget_status')">
                  {{ __('Budget Status') }} <i :class="['fa-solid text-xs ml-1', sortIcon('budget_status')]"></i>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="proj in sortedBudgetProjects"
                :key="proj.name"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <td class="px-4 py-3 text-gray-800 dark:text-gray-200">{{ proj.project_name }}</td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusBadgeClass(proj.status)]">{{ proj.status }}</span>
                </td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ formatCurrency(proj.budget) }}</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ formatCurrency(proj.spent) }}</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">{{ formatCurrency(proj.remaining) }}</td>
                <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300 hidden md:table-cell">{{ formatPercent(proj.utilization_percent) }}</td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusBadgeClass(proj.budget_status)]">
                    {{ budgetStatusLabel(proj.budget_status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ==================== MILESTONES TAB ==================== -->
    <template v-else-if="activeTab === 'milestones' && milestoneReport">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Total') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 m-0 mt-1">{{ milestoneReport.summary.total }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Completed') }}</p>
          <p class="text-2xl font-bold text-green-600 dark:text-green-400 m-0 mt-1">{{ milestoneReport.summary.completed }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Upcoming') }}</p>
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 m-0 mt-1">{{ milestoneReport.summary.upcoming }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 uppercase tracking-wider">{{ __('Missed') }}</p>
          <p class="text-2xl font-bold text-red-600 dark:text-red-400 m-0 mt-1">{{ milestoneReport.summary.missed }}</p>
        </div>
      </div>

      <!-- Chart -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6" v-if="milestoneDonutSeries.length > 0">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <VueApexCharts type="donut" height="280" :options="milestoneDonutOptions" :series="milestoneDonutSeries" />
        </div>
      </div>

      <!-- Data Table -->
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('milestone_name')">
                  {{ __('Name') }} <i :class="['fa-solid text-xs ml-1', sortIcon('milestone_name')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 hidden md:table-cell" @click="toggleSort('project')">
                  {{ __('Project') }} <i :class="['fa-solid text-xs ml-1', sortIcon('project')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('status')">
                  {{ __('Status') }} <i :class="['fa-solid text-xs ml-1', sortIcon('status')]"></i>
                </th>
                <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100" @click="toggleSort('due_date')">
                  {{ __('Due Date') }} <i :class="['fa-solid text-xs ml-1', sortIcon('due_date')]"></i>
                </th>
                <th class="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">
                  {{ __('Timeline') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ms in sortedMilestones"
                :key="ms.name"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <td class="px-4 py-3 text-gray-800 dark:text-gray-200">{{ ms.milestone_name }}</td>
                <td class="px-4 py-3 text-gray-500 dark:text-gray-400 hidden md:table-cell">{{ ms.project || '-' }}</td>
                <td class="px-4 py-3">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusBadgeClass(ms.status)]">{{ ms.status }}</span>
                </td>
                <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ formatDate(ms.due_date) }}</td>
                <td class="px-4 py-3 text-right">
                  <span
                    :class="[
                      'text-xs font-medium',
                      daysUntil(ms.due_date) < 0 && ms.status !== 'Completed' ? 'text-red-500' :
                      daysUntil(ms.due_date) <= 7 && ms.status !== 'Completed' ? 'text-yellow-500' :
                      'text-gray-500 dark:text-gray-400'
                    ]"
                  >
                    {{ ms.status === 'Completed' ? (ms.completed_date ? formatDate(ms.completed_date) : __('Done')) : daysLabel(ms.due_date) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
