<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Guest-facing read-only project status page.
  Loaded inside the Dock Guest Portal iframe at /orga/guest/project/:name?token=dgs_xxx
  No Frappe login required — validates via Dock guest token.
-->
<script lang="ts">
export default { name: 'GuestProjectStatus' }
</script>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { TriangleAlert, CircleCheck, AlertCircle, Clock, Check } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

interface ProjectStatus {
  name: string
  project_name: string
  status: string
  progress: number
  health_status: string
  start_date: string | null
  end_date: string | null
  days_remaining: number | null
  days_overdue: number | null
}

interface TaskSummary {
  Open: number
  'In Progress': number
  Review: number
  Completed: number
  total: number
}

interface Milestone {
  milestone_name: string
  status: string
  due_date: string | null
  completion_date: string | null
  is_overdue: boolean
}

interface RecentCompletion {
  subject: string
  modified: string
}

const route = useRoute()

const loading = ref(true)
const error = ref('')
const project = ref<ProjectStatus | null>(null)
const taskSummary = ref<TaskSummary | null>(null)
const milestones = ref<Milestone[]>([])
const recentCompletions = ref<RecentCompletion[]>([])

const projectName = computed(() => route.params.name as string)
const token = computed(() => (route.query.token as string) || '')

const statusColors: Record<string, string> = {
  'Planning': 'bg-blue-100 text-blue-700',
  'Active': 'bg-green-100 text-green-700',
  'On Hold': 'bg-amber-100 text-amber-700',
  'Completed': 'bg-gray-100 text-gray-600',
  'Cancelled': 'bg-red-100 text-red-700',
}

const healthColors: Record<string, string> = {
  'Green': 'bg-green-100 text-green-700',
  'Yellow': 'bg-amber-100 text-amber-700',
  'Red': 'bg-red-100 text-red-700',
}

function formatDate(date: string | null): string {
  if (!date) return 'TBD'
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  })
}

function formatRelative(dateStr: string): string {
  const now = new Date()
  const date = new Date(dateStr)
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  return formatDate(dateStr)
}

async function loadData() {
  if (!projectName.value || !token.value) {
    error.value = 'Invalid link'
    loading.value = false
    return
  }

  try {
    const res = await fetch('/api/method/orga.orga.api.guest.get_project_status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_name: projectName.value, token: token.value }),
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      error.value = body._server_messages
        ? JSON.parse(JSON.parse(body._server_messages)[0]).message
        : 'Unable to load project'
      loading.value = false
      return
    }

    const json = await res.json()
    const data = json.message
    project.value = data.project
    taskSummary.value = data.task_summary
    milestones.value = data.milestones || []
    recentCompletions.value = data.recent_completions || []
  } catch {
    error.value = 'Unable to load project'
  }
  loading.value = false
}

onMounted(loadData)
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <div class="w-8 h-8 border-2 border-gray-300 border-t-green-500 rounded-full animate-spin" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center min-h-[60vh] px-4">
      <div class="text-center max-w-sm">
        <div class="w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
          <TriangleAlert class="w-5 h-5 text-red-500" aria-hidden="true" />
        </div>
        <p class="text-gray-600 text-sm">{{ error }}</p>
      </div>
    </div>

    <!-- Content -->
    <div v-else-if="project" class="max-w-3xl mx-auto px-4 py-6 sm:px-6 sm:py-8">

      <!-- Project Header -->
      <div class="mb-6">
        <div class="flex items-start gap-3 mb-3">
          <h1 class="text-xl sm:text-2xl font-semibold text-gray-900 flex-1">
            {{ project.project_name }}
          </h1>
          <span :class="['px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap', statusColors[project.status] || 'bg-gray-100 text-gray-600']">
            {{ project.status }}
          </span>
        </div>

        <!-- Health + Dates -->
        <div class="flex flex-wrap items-center gap-3 text-sm text-gray-500">
          <span v-if="project.health_status" :class="['px-2 py-0.5 rounded-full text-xs font-medium', healthColors[project.health_status] || 'bg-gray-100 text-gray-500']">
            {{ project.health_status }}
          </span>
          <span v-if="project.start_date">
            {{ formatDate(project.start_date) }}
            <template v-if="project.end_date"> &ndash; {{ formatDate(project.end_date) }}</template>
          </span>
          <span v-if="project.days_overdue && project.days_overdue > 0" class="text-red-600 font-medium">
            {{ project.days_overdue }} days overdue
          </span>
          <span v-else-if="project.days_remaining !== null && project.days_remaining >= 0" class="text-gray-500">
            {{ project.days_remaining }} days remaining
          </span>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-gray-700">Progress</span>
          <span class="text-sm font-semibold text-gray-900">{{ project.progress }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5">
          <div
            class="h-2.5 rounded-full transition-all"
            :class="project.progress >= 100 ? 'bg-green-500' : 'bg-green-400'"
            :style="{ width: Math.min(project.progress, 100) + '%' }"
          />
        </div>
      </div>

      <!-- Task Summary -->
      <div v-if="taskSummary" class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
          <div class="text-lg font-semibold text-gray-900">{{ taskSummary.Open }}</div>
          <div class="text-xs text-gray-500">Open</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
          <div class="text-lg font-semibold text-blue-600">{{ taskSummary['In Progress'] }}</div>
          <div class="text-xs text-gray-500">In Progress</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
          <div class="text-lg font-semibold text-amber-600">{{ taskSummary.Review }}</div>
          <div class="text-xs text-gray-500">Review</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
          <div class="text-lg font-semibold text-green-600">{{ taskSummary.Completed }}</div>
          <div class="text-xs text-gray-500">Completed</div>
        </div>
      </div>

      <!-- Milestones -->
      <div v-if="milestones.length > 0" class="bg-white rounded-lg border border-gray-200 mb-4">
        <div class="px-4 py-3 border-b border-gray-100">
          <h2 class="text-sm font-semibold text-gray-700">Milestones</h2>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="m in milestones" :key="m.milestone_name" class="px-4 py-3 flex items-center gap-3">
            <div class="flex-shrink-0">
              <CircleCheck v-if="m.status === 'Completed'" class="w-4 h-4 text-green-500" aria-hidden="true" />
              <AlertCircle v-else-if="m.is_overdue" class="w-4 h-4 text-red-500" aria-hidden="true" />
              <Clock v-else class="w-4 h-4 text-blue-500" aria-hidden="true" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-800 truncate">{{ m.milestone_name }}</div>
              <div class="text-xs text-gray-500">
                <template v-if="m.status === 'Completed'">
                  Completed {{ formatDate(m.completion_date) }}
                </template>
                <template v-else>
                  Due {{ formatDate(m.due_date) }}
                </template>
              </div>
            </div>
            <span
              :class="[
                'px-2 py-0.5 rounded-full text-xs font-medium',
                m.status === 'Completed' ? 'bg-green-100 text-green-700' :
                m.is_overdue ? 'bg-red-100 text-red-700' :
                'bg-blue-100 text-blue-700'
              ]"
            >
              {{ m.status === 'Completed' ? 'Done' : m.is_overdue ? 'Overdue' : 'Upcoming' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Recent Completions -->
      <div v-if="recentCompletions.length > 0" class="bg-white rounded-lg border border-gray-200">
        <div class="px-4 py-3 border-b border-gray-100">
          <h2 class="text-sm font-semibold text-gray-700">Recent Activity</h2>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="item in recentCompletions" :key="item.subject" class="px-4 py-2.5 flex items-center gap-3">
            <Check class="w-3 h-3 text-green-500 flex-shrink-0" aria-hidden="true" />
            <span class="text-sm text-gray-700 flex-1 truncate">{{ item.subject }}</span>
            <span class="text-xs text-gray-400 flex-shrink-0">{{ formatRelative(item.modified) }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
