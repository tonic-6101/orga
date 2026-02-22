// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { computed, type Ref } from 'vue'
import type { ActivityItem } from '@/types/orga'

export interface AggregatedActivity {
  isAggregated: true
  user: string
  user_name: string
  user_image?: string
  type: string
  action: string
  count: number
  items: ActivityItem[]
  timestamp: string
  projects: string[]
}

export interface ActivityGroup {
  label: string
  date: string
  items: (ActivityItem | AggregatedActivity)[]
}

function getDateLabel(date: Date): string {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const diffDays = Math.floor((today.getTime() - target.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return 'This Week'
  if (diffDays < 14) return 'Last Week'
  return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
}

function getDateKey(date: Date): string {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const diffDays = Math.floor((today.getTime() - target.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return 'this-week'
  if (diffDays < 14) return 'last-week'
  return target.toISOString().slice(0, 10)
}

function aggregateItems(items: ActivityItem[]): (ActivityItem | AggregatedActivity)[] {
  const result: (ActivityItem | AggregatedActivity)[] = []
  let i = 0

  while (i < items.length) {
    const current = items[i]
    const key = `${current.user}_${current.type}_${current.action || 'updated'}`

    // Collect consecutive items with same user+type+action
    const group: ActivityItem[] = [current]
    let j = i + 1
    while (j < items.length) {
      const next = items[j]
      const nextKey = `${next.user}_${next.type}_${next.action || 'updated'}`
      if (nextKey === key) {
        group.push(next)
        j++
      } else {
        break
      }
    }

    if (group.length >= 3) {
      const projectNames = [...new Set(
        group.map(a => a.project_name || a.project).filter(Boolean) as string[]
      )]
      result.push({
        isAggregated: true,
        user: current.user,
        user_name: current.user_name || current.user_fullname || current.user,
        user_image: current.user_image,
        type: current.type || 'activity',
        action: current.action || 'updated',
        count: group.length,
        items: group,
        timestamp: group[0].timestamp,
        projects: projectNames
      })
    } else {
      result.push(...group)
    }

    i = j
  }

  return result
}

export function useActivityGrouping(activities: Ref<ActivityItem[]>) {
  const grouped = computed<ActivityGroup[]>(() => {
    if (!activities.value.length) return []

    const groups = new Map<string, { label: string; date: string; items: ActivityItem[] }>()

    for (const activity of activities.value) {
      const date = new Date(activity.timestamp)
      const key = getDateKey(date)
      const label = getDateLabel(date)

      if (!groups.has(key)) {
        groups.set(key, { label, date: key, items: [] })
      }
      groups.get(key)!.items.push(activity)
    }

    return Array.from(groups.values()).map(group => ({
      label: group.label,
      date: group.date,
      items: aggregateItems(group.items)
    }))
  })

  return { grouped }
}
