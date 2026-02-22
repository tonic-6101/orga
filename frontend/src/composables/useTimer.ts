// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Global timer composable (singleton pattern).
 *
 * Uses module-level refs so all components share the same timer state.
 * Start/stop from TaskTimeTab, EventTimeTab, or FloatingTimer —
 * all see the same running timer.
 */

import { ref, computed } from 'vue'
import type { OrgaTimeLog, TrackingContext, TimerState } from '@/types/orga'
import { useTimeLogApi } from './useApi'

// ============================================
// Module-level singleton state
// ============================================

const timerState = ref<TimerState>({
  isRunning: false,
  activeTimeLog: null,
  elapsedSeconds: 0,
  context: null,
  contextLabel: ''
})

let tickInterval: ReturnType<typeof setInterval> | null = null
let initialized = false

// ============================================
// Internal helpers
// ============================================

function startTick(): void {
  stopTick()
  tickInterval = setInterval(() => {
    if (timerState.value.isRunning && timerState.value.activeTimeLog?.timer_started_at) {
      const started = new Date(timerState.value.activeTimeLog.timer_started_at).getTime()
      const now = Date.now()
      timerState.value.elapsedSeconds = Math.max(0, Math.floor((now - started) / 1000))
    }
  }, 1000)
}

function stopTick(): void {
  if (tickInterval !== null) {
    clearInterval(tickInterval)
    tickInterval = null
  }
}

function getContextLabel(log: OrgaTimeLog | null): string {
  if (!log) return ''
  switch (log.tracking_context) {
    case 'task':
      return log.task_subject || log.task || 'Task'
    case 'event':
      return log.event_subject || log.event || 'Event'
    case 'project':
      return log.project_name || log.project || 'Project'
    case 'standalone':
      return log.description || 'Standalone'
    default:
      return ''
  }
}

function updateStateFromLog(log: OrgaTimeLog | null): void {
  if (log && log.is_running) {
    timerState.value = {
      isRunning: true,
      activeTimeLog: log,
      elapsedSeconds: 0,
      context: log.tracking_context,
      contextLabel: getContextLabel(log)
    }
    // Calculate initial elapsed
    if (log.timer_started_at) {
      const started = new Date(log.timer_started_at).getTime()
      timerState.value.elapsedSeconds = Math.max(0, Math.floor((Date.now() - started) / 1000))
    }
    startTick()
  } else {
    timerState.value = {
      isRunning: false,
      activeTimeLog: null,
      elapsedSeconds: 0,
      context: null,
      contextLabel: ''
    }
    stopTick()
  }
}

// ============================================
// Public composable
// ============================================

interface StartTimerOptions {
  trackingContext: TrackingContext
  task?: string
  event?: string
  project?: string
  description?: string
}

export function useTimer() {
  const api = useTimeLogApi()

  /**
   * Load active timer from server (call on app mount).
   */
  async function loadActiveTimer(): Promise<void> {
    try {
      const timer = await api.getActiveTimer()
      updateStateFromLog(timer as OrgaTimeLog | null)
      initialized = true
    } catch {
      // No active timer or API error — stay idle
      updateStateFromLog(null)
      initialized = true
    }
  }

  /**
   * Start a new timer. Auto-stops any existing running timer.
   */
  async function startTimer(options: StartTimerOptions): Promise<OrgaTimeLog> {
    const result = await api.startTimer(
      options.trackingContext,
      options.task,
      options.event,
      options.project,
      options.description
    )
    updateStateFromLog(result as OrgaTimeLog)
    return result as OrgaTimeLog
  }

  /**
   * Stop the running timer and save the time log.
   */
  async function stopTimer(name?: string): Promise<OrgaTimeLog> {
    const result = await api.stopTimer(name)
    updateStateFromLog(null)
    return result as OrgaTimeLog
  }

  /**
   * Discard the running timer without saving.
   */
  async function discardTimer(name?: string): Promise<void> {
    await api.discardTimer(name)
    updateStateFromLog(null)
  }

  /**
   * Formatted elapsed time as HH:MM:SS
   */
  const formattedTime = computed<string>(() => {
    const total = timerState.value.elapsedSeconds
    const h = Math.floor(total / 3600)
    const m = Math.floor((total % 3600) / 60)
    const s = total % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  })

  /**
   * Whether the timer is tracking a specific task
   */
  function isTrackingTask(taskName: string): boolean {
    return timerState.value.isRunning
      && timerState.value.context === 'task'
      && timerState.value.activeTimeLog?.task === taskName
  }

  /**
   * Whether the timer is tracking a specific event
   */
  function isTrackingEvent(eventName: string): boolean {
    return timerState.value.isRunning
      && timerState.value.context === 'event'
      && timerState.value.activeTimeLog?.event === eventName
  }

  // Auto-initialize on first use if not yet done
  if (!initialized) {
    loadActiveTimer()
  }

  return {
    timerState,
    formattedTime,
    loadActiveTimer,
    startTimer,
    stopTimer,
    discardTimer,
    isTrackingTask,
    isTrackingEvent,
    loading: api.loading
  }
}
