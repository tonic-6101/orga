// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * useCascadeCalculation - Calculate cascade effect of date changes on dependent tasks
 *
 * This composable provides utilities for calculating how date changes on one task
 * will affect all dependent tasks in a dependency chain.
 */

import type { GanttTask, CascadeChange, DependencyType } from '@/types/orga'

/**
 * Add days to a date string
 */
function addDays(dateStr: string, days: number): string {
  const date = new Date(dateStr)
  date.setDate(date.getDate() + days)
  return date.toISOString().split('T')[0]
}

/**
 * Calculate the number of days between two dates
 */
function daysBetween(startDate: string, endDate: string): number {
  const start = new Date(startDate)
  const end = new Date(endDate)
  const diffTime = end.getTime() - start.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

/**
 * Get effective date shift based on dependency type
 *
 * @param sourceTask - The task being changed
 * @param targetTask - The dependent task
 * @param depType - Dependency type (FS, SS, FF, SF)
 * @param baseShift - Base shift in days
 * @param lag - Lag/lead days from dependency
 * @returns Effective shift to apply to target task
 */
function getEffectiveShift(
  depType: DependencyType,
  baseShift: number,
  lag: number
): number {
  // For all dependency types, the shift propagates with the lag
  // FS (Finish-to-Start): Successor starts after predecessor finishes
  // SS (Start-to-Start): Both tasks start together
  // FF (Finish-to-Finish): Both tasks finish together
  // SF (Start-to-Finish): Predecessor starts before successor finishes
  return baseShift + lag
}

export function useCascadeCalculation() {
  /**
   * Calculate the cascade effect of changing a task's dates.
   *
   * This function traverses the dependency chain and calculates how
   * each dependent task's dates will shift as a result of the change.
   *
   * @param changedTask - The task being modified
   * @param allTasks - All tasks in the project
   * @param dateShift - Number of days the task is shifting (positive = later, negative = earlier)
   * @param changedField - Which date field changed ('start_date' or 'end_date')
   * @returns Array of affected tasks with their new dates
   */
  function calculateCascade(
    changedTask: GanttTask,
    allTasks: GanttTask[],
    dateShift: number,
    changedField: 'start_date' | 'end_date' = 'end_date'
  ): CascadeChange[] {
    const changes: CascadeChange[] = []
    const visited = new Set<string>()

    /**
     * Recursively find all dependent tasks and calculate their date shifts
     */
    function findDependents(taskId: string, taskName: string, shift: number) {
      // Find all tasks that depend on this task
      const dependents = allTasks.filter(t =>
        t.dependencies_info?.some(d => d.task_id === taskId)
      )

      for (const dependent of dependents) {
        if (visited.has(dependent.name)) continue
        visited.add(dependent.name)

        // Find the specific dependency configuration
        const dependency = dependent.dependencies_info?.find(d => d.task_id === taskId)
        if (!dependency) continue

        // Calculate effective shift based on dependency type and lag
        const effectiveShift = getEffectiveShift(
          dependency.type,
          shift,
          dependency.lag || 0
        )

        // Only create change if there's an actual shift
        if (effectiveShift !== 0 && dependent.start_date) {
          changes.push({
            task_id: dependent.name,
            task_name: dependent.subject,
            field: 'start_date',
            old_value: dependent.start_date,
            new_value: addDays(dependent.start_date, effectiveShift),
            days_shift: effectiveShift
          })

          // If the task has an end date, also calculate its shift
          if (dependent.due_date) {
            changes.push({
              task_id: dependent.name,
              task_name: dependent.subject,
              field: 'end_date',
              old_value: dependent.due_date,
              new_value: addDays(dependent.due_date, effectiveShift),
              days_shift: effectiveShift
            })
          }
        }

        // Recursively find dependents of this dependent
        findDependents(dependent.name, dependent.subject, effectiveShift)
      }
    }

    // Start cascade calculation from the changed task
    findDependents(changedTask.name, changedTask.subject, dateShift)

    // Remove duplicate entries (keep only start_date changes for display)
    const uniqueChanges = changes.filter(c => c.field === 'start_date')

    return uniqueChanges
  }

  /**
   * Calculate the total impact of cascade changes
   *
   * @param changes - Array of cascade changes
   * @returns Summary statistics
   */
  function calculateCascadeImpact(changes: CascadeChange[]): {
    totalAffected: number
    maxShift: number
    minShift: number
    avgShift: number
    delayedTasks: number
    advancedTasks: number
  } {
    if (changes.length === 0) {
      return {
        totalAffected: 0,
        maxShift: 0,
        minShift: 0,
        avgShift: 0,
        delayedTasks: 0,
        advancedTasks: 0
      }
    }

    const shifts = changes.map(c => c.days_shift)
    const totalAffected = changes.length
    const maxShift = Math.max(...shifts)
    const minShift = Math.min(...shifts)
    const avgShift = shifts.reduce((a, b) => a + b, 0) / shifts.length
    const delayedTasks = changes.filter(c => c.days_shift > 0).length
    const advancedTasks = changes.filter(c => c.days_shift < 0).length

    return {
      totalAffected,
      maxShift,
      minShift,
      avgShift: Math.round(avgShift * 10) / 10,
      delayedTasks,
      advancedTasks
    }
  }

  /**
   * Check if a cascade would create any conflicts
   *
   * @param changes - Array of cascade changes
   * @param allTasks - All tasks in the project
   * @param projectEndDate - Optional project end date constraint
   * @returns Array of conflict warnings
   */
  function checkCascadeConflicts(
    changes: CascadeChange[],
    allTasks: GanttTask[],
    projectEndDate?: string
  ): string[] {
    const warnings: string[] = []

    for (const change of changes) {
      const task = allTasks.find(t => t.name === change.task_id)
      if (!task) continue

      // Check if new date exceeds project end date
      if (projectEndDate && change.new_value > projectEndDate) {
        warnings.push(`"${change.task_name}" would extend beyond project end date`)
      }

      // Check if task would start in the past
      const today = new Date().toISOString().split('T')[0]
      if (change.field === 'start_date' && change.new_value < today && change.old_value >= today) {
        warnings.push(`"${change.task_name}" would be scheduled in the past`)
      }
    }

    return warnings
  }

  /**
   * Generate a cascade preview for display
   *
   * @param changes - Array of cascade changes
   * @returns Formatted preview data
   */
  function formatCascadePreview(changes: CascadeChange[]): {
    summary: string
    delayed: CascadeChange[]
    advanced: CascadeChange[]
  } {
    const delayed = changes.filter(c => c.days_shift > 0)
    const advanced = changes.filter(c => c.days_shift < 0)

    let summary = ''
    if (delayed.length > 0 && advanced.length > 0) {
      summary = `${delayed.length} task${delayed.length !== 1 ? 's' : ''} delayed, ${advanced.length} task${advanced.length !== 1 ? 's' : ''} advanced`
    } else if (delayed.length > 0) {
      summary = `${delayed.length} task${delayed.length !== 1 ? 's' : ''} will be delayed`
    } else if (advanced.length > 0) {
      summary = `${advanced.length} task${advanced.length !== 1 ? 's' : ''} will move earlier`
    } else {
      summary = 'No tasks affected'
    }

    return { summary, delayed, advanced }
  }

  return {
    calculateCascade,
    calculateCascadeImpact,
    checkCascadeConflicts,
    formatCascadePreview,
    addDays,
    daysBetween
  }
}
