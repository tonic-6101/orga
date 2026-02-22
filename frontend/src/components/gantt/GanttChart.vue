<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * GanttChart - Main Gantt chart visualization component
 *
 * Renders tasks as horizontal bars on a timeline grid.
 * Features:
 * - Scrollable timeline with day/week columns
 * - Task bars with color coding by status
 * - Dependency arrows between tasks
 * - Click to select task and open focus panel
 * - Today marker
 */

import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import type {
  GanttTask,
  GanttItem,
  GanttMilestone,
  TaskStatus,
  TaskPriority,
  MilestoneStatus,
  DependencyType,
} from '@/types/orga';
import { isGanttTask } from '@/types/orga';
import UserAvatar from '@/components/common/UserAvatar.vue';
import { __ } from '@/composables/useTranslate';

// Grouping types
type GanttGroupMode = 'none' | 'status' | 'priority' | 'milestone' | 'assignee' | 'group'

interface GroupHeaderRow {
  kind: 'group-header'
  key: string
  label: string
  count: number
}

interface ItemRow {
  kind: 'item'
  item: GanttItem
}

type DisplayRow = GroupHeaderRow | ItemRow

const STATUS_ORDER: string[] = ['Open', 'Working', 'In Progress', 'Pending Review', 'Review', 'Overdue', 'Completed', 'Cancelled']
const PRIORITY_ORDER: string[] = ['Urgent', 'High', 'Medium', 'Low']

interface Props {
  tasks: GanttItem[]; // Now accepts both tasks and milestones
  startDate?: string;
  endDate?: string;
  selectedTaskId?: string | null;
  showDependencies?: boolean;
  cellWidth?: number;
  justReorderedId?: string | null; // Task ID to highlight after reorder
  criticalPathTasks?: string[]; // Task IDs on the critical path
}

const props = withDefaults(defineProps<Props>(), {
  showDependencies: true,
  cellWidth: 40,
  justReorderedId: null,
  criticalPathTasks: () => [],
});

// Critical path toggle state
const showCriticalPath = ref(false);

// Helper to check if a task is on the critical path
function isOnCriticalPath(taskName: string): boolean {
  return showCriticalPath.value && props.criticalPathTasks.includes(taskName);
}

const emit = defineEmits<{
  (e: 'select', item: GanttItem): void;
  (
    e: 'update-dates',
    payload: { taskId: string; startDate: string; endDate: string },
  ): void;
  (
    e: 'update-milestone-date',
    payload: { milestoneId: string; dueDate: string },
  ): void;
  (
    e: 'reorder-item',
    payload: {
      itemId: string;
      itemType: 'task' | 'milestone';
      prevItemId: string | null;
      nextItemId: string | null;
      prevItemType: 'task' | 'milestone' | null;
      nextItemType: 'task' | 'milestone' | null;
    },
  ): void;
  (
    e: 'create-dependency',
    payload: { fromTask: string; toTask: string; type: 'FS' },
  ): void;
}>();

// Dependency creation drag state
const depDragSource = ref<string | null>(null);
const depDragTarget = ref<string | null>(null);
const depDragLine = ref<{ x1: number; y1: number; x2: number; y2: number } | null>(null);

function startDepDrag(taskName: string, event: MouseEvent): void {
  event.preventDefault();
  event.stopPropagation();
  depDragSource.value = taskName;

  const onMove = (e: MouseEvent) => {
    if (!depDragSource.value || !scrollContainerRef.value) return;

    const rect = scrollContainerRef.value.getBoundingClientRect();
    const scrollLeft = scrollContainerRef.value.scrollLeft;
    const scrollTop = scrollContainerRef.value.scrollTop;
    const x = e.clientX - rect.left + scrollLeft;
    const y = e.clientY - rect.top + scrollTop;

    // Get source bar position
    const sourceTask = sortedItems.value.find(item => item.name === depDragSource.value) as GanttTask | undefined;
    if (!sourceTask) return;
    const barPos = getBarPosition(sourceTask);
    if (!barPos) return;

    const sourceRow = displayRows.value.findIndex(r => r.kind === 'item' && r.item.name === depDragSource.value);
    const sourceY = sourceRow * ROW_HEIGHT + ROW_HEIGHT / 2;
    const sourceX = barPos.left + barPos.width;

    depDragLine.value = { x1: sourceX, y1: sourceY, x2: x, y2: y };

    // Detect hover over task bars
    depDragTarget.value = null;
    for (let i = 0; i < displayRows.value.length; i++) {
      const row = displayRows.value[i];
      if (row.kind !== 'item' || row.item.type === 'milestone') continue;
      if (row.item.name === depDragSource.value) continue;
      const task = row.item as GanttTask;
      const bp = getBarPosition(task);
      if (!bp) continue;
      const rowY = i * ROW_HEIGHT;
      if (x >= bp.left && x <= bp.left + bp.width && y >= rowY && y <= rowY + ROW_HEIGHT) {
        depDragTarget.value = task.name;
        break;
      }
    }
  };

  const onUp = () => {
    if (depDragSource.value && depDragTarget.value && depDragSource.value !== depDragTarget.value) {
      emit('create-dependency', {
        fromTask: depDragSource.value,
        toTask: depDragTarget.value,
        type: 'FS',
      });
    }
    depDragSource.value = null;
    depDragTarget.value = null;
    depDragLine.value = null;
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };

  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

// HTML5 Drag API state
interface DragData {
  taskId: string;
  taskName: string;
  startDate: string;
  dueDate: string | null;
  duration: number;
  startX: number;
  originalLeft: number; // Original bar position in pixels for snap-to-grid
  rowIndex: number;
  dragType: 'dates' | 'reorder'; // 'dates' = timeline bar drag, 'reorder' = row drag
  itemType: 'task' | 'milestone'; // What kind of item is being dragged
}

// Currently dragging task info
const draggingTask = ref<DragData | null>(null);
const dropTargetIndex = ref<number | null>(null);
const justReorderedTaskId = ref<string | null>(null);

// Grouping state
const groupMode = ref<GanttGroupMode>('none');
const collapsedGroups = ref<Set<string>>(new Set());

function toggleGroup(key: string): void {
  const next = new Set(collapsedGroups.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  collapsedGroups.value = next;
}

// Snap-to-grid: calculated day delta during drag (used by handleRowDrop for date changes)
const dragDaysDelta = ref<number>(0);
// Global drag listener cleanup (attached in handleBarDragStart, cleaned up on end)
let cleanupGlobalDragListener: (() => void) | null = null;

// Milestone drag state (uses mousedown instead of HTML5 drag for small diamond targets)
interface MilestoneDragData {
  milestoneId: string;
  milestoneName: string;
  originalDueDate: string;
  startX: number;
  originalLeft: number;
}
const draggingMilestone = ref<MilestoneDragData | null>(null);
const milestoneDragDaysDelta = ref<number>(0);

// Container refs — Area A/B/C layout
const headerScrollRef = ref<HTMLElement | null>(null); // Area A: header timeline (overflow hidden, synced by JS)
const scrollContainerRef = ref<HTMLElement | null>(null); // Area B: grid body (scrolls both directions)
const leftBodyRef = ref<HTMLElement | null>(null); // Left task name column (vertical sync)
const headerScrollbarRef = ref<HTMLElement | null>(null); // Scrollbar track in Area B footer
let isSyncingVerticalScroll = false;
let isSyncingHorizontalScroll = false;

// Custom scrollbar thumb state (reactive for inline :style binding)
const thumbWidth = ref(96); // Fixed thumb width for scrubber
const scrollbarWidth = ref(0); // Viewport width of scrollbar track (reactive for computed center)
const thumbVisible = ref(false);
const thumbHovered = ref(false);
const thumbDragging = ref(false);
const activeZone = ref('zone-center');

// Zone config: distance from drag start → velocity + direction
interface ZoneConfig {
  min: number;
  max: number;
  velocity: number;
  direction: number;
}
const ZONE_CONFIG: Record<string, ZoneConfig> = {
  'zone-2x-left': { min: -Infinity, max: -50, velocity: 2, direction: -1 },
  'zone-1x-left': { min: -50, max: -10, velocity: 1, direction: -1 },
  'zone-center': { min: -10, max: 10, velocity: 0, direction: 0 },
  'zone-1x-right': { min: 10, max: 50, velocity: 1, direction: 1 },
  'zone-2x-right': { min: 50, max: Infinity, velocity: 2, direction: 1 },
};

// Parse date string to local date (handles "YYYY-MM-DD" format correctly)
// Defined here so it can be used by dateRange computed before being hoisted
function parseLocalDate(dateStr: string): Date {
  // Split the date string to avoid timezone issues
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day); // month is 0-indexed
}

// Calculate date range from tasks or props
const dateRange = computed(() => {
  let start: Date;
  let end: Date;

  if (props.startDate && props.endDate) {
    // Parse as local dates to avoid timezone issues
    start = parseLocalDate(props.startDate);
    end = parseLocalDate(props.endDate);
  } else {
    // Calculate from tasks - parse each date as local date
    const dates = props.tasks
      .flatMap((t) => [
        t.start_date ? parseLocalDate(t.start_date) : null,
        t.due_date ? parseLocalDate(t.due_date) : null,
      ])
      .filter((d): d is Date => d !== null);

    if (dates.length === 0) {
      // Default to current month if no dates
      start = new Date();
      start.setDate(1);
      end = new Date();
      end.setMonth(end.getMonth() + 1);
      end.setDate(0);
    } else {
      start = new Date(Math.min(...dates.map((d) => d.getTime())));
      end = new Date(Math.max(...dates.map((d) => d.getTime())));
    }
  }

  // Add padding: 1 week before and 2 weeks after
  start.setDate(start.getDate() - 7);
  end.setDate(end.getDate() + 14);

  return { start, end };
});

// Generate array of days for timeline
const days = computed(() => {
  const result: Date[] = [];
  const current = new Date(dateRange.value.start);

  while (current <= dateRange.value.end) {
    result.push(new Date(current));
    current.setDate(current.getDate() + 1);
  }

  return result;
});

// Group days by month for header
const months = computed(() => {
  const result: {
    month: string;
    year: number;
    days: number;
    startIndex: number;
  }[] = [];
  let currentMonth = '';
  let startIndex = 0;

  days.value.forEach((day, index) => {
    const monthKey = `${day.getFullYear()}-${day.getMonth()}`;
    if (monthKey !== currentMonth) {
      if (currentMonth) {
        result[result.length - 1].days = index - startIndex;
      }
      currentMonth = monthKey;
      startIndex = index;
      result.push({
        month: day.toLocaleDateString('en-US', { month: 'short' }),
        year: day.getFullYear(),
        days: 0,
        startIndex: index,
      });
    }
  });

  // Set days for last month
  if (result.length > 0) {
    result[result.length - 1].days =
      days.value.length - result[result.length - 1].startIndex;
  }

  return result;
});

// Group days by week for header (ISO week numbers)
const weeks = computed(() => {
  const result: {
    weekNum: number;
    year: number;
    days: number;
    startIndex: number;
  }[] = [];
  let currentWeek = '';
  let startIndex = 0;

  days.value.forEach((day, index) => {
    const weekNum = getISOWeekNumber(day);
    const weekKey = `${day.getFullYear()}-W${weekNum}`;
    if (weekKey !== currentWeek) {
      if (currentWeek) {
        result[result.length - 1].days = index - startIndex;
      }
      currentWeek = weekKey;
      startIndex = index;
      result.push({
        weekNum,
        year: day.getFullYear(),
        days: 0,
        startIndex: index,
      });
    }
  });

  // Set days for last week
  if (result.length > 0) {
    result[result.length - 1].days =
      days.value.length - result[result.length - 1].startIndex;
  }

  return result;
});

// Get ISO week number
function getISOWeekNumber(date: Date): number {
  const d = new Date(
    Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()),
  );
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

// Check if date is start of week (Monday)
function isWeekStart(date: Date): boolean {
  return date.getDay() === 1; // Monday
}

// Get day abbreviation
function getDayAbbr(date: Date): string {
  return date.toLocaleDateString('en-US', { weekday: 'short' }).substring(0, 2);
}

// Today's index in the days array
const todayIndex = computed(() => {
  const today = new Date();
  return days.value.findIndex((d) => {
    const dayDate = new Date(d);
    return (
      dayDate.getFullYear() === today.getFullYear() &&
      dayDate.getMonth() === today.getMonth() &&
      dayDate.getDate() === today.getDate()
    );
  });
});

// Calculate task bar position and width
function getTaskBarStyle(task: GanttTask): Record<string, string> {
  if (!task.start_date) {
    return { display: 'none' };
  }

  // Parse dates as local dates to avoid timezone issues
  const startDate = parseLocalDate(task.start_date);
  const endDate = task.due_date
    ? parseLocalDate(task.due_date)
    : new Date(startDate);

  // Find start index - compare using date strings for reliability
  const startIndex = days.value.findIndex((d) => {
    const dayDate = new Date(d);
    // Compare year, month, day only
    return (
      dayDate.getFullYear() === startDate.getFullYear() &&
      dayDate.getMonth() === startDate.getMonth() &&
      dayDate.getDate() === startDate.getDate()
    );
  });

  // If exact match not found, find the first day >= start date
  let effectiveIndex = startIndex;
  if (startIndex === -1) {
    effectiveIndex = days.value.findIndex((d) => {
      const dayDate = new Date(d);
      dayDate.setHours(0, 0, 0, 0);
      const startCopy = new Date(startDate);
      startCopy.setHours(0, 0, 0, 0);
      return dayDate.getTime() >= startCopy.getTime();
    });
  }

  if (effectiveIndex === -1) {
    return { display: 'none' };
  }

  // Calculate duration in days (inclusive for visual bar width: both start and end columns)
  const durationMs = endDate.getTime() - startDate.getTime();
  const durationDays = Math.max(
    1,
    Math.ceil(durationMs / (1000 * 60 * 60 * 24)) + 1,
  );

  // Center-to-center positioning (industry standard):
  // Bar spans from center of start-day cell to center of end-day cell.
  // For single-day tasks (duration=1), bar is one cellWidth centered on the day.
  const startCenter = effectiveIndex * props.cellWidth + props.cellWidth / 2;
  const endCenter =
    (effectiveIndex + durationDays - 1) * props.cellWidth + props.cellWidth / 2;
  const barWidth = Math.max(endCenter - startCenter, props.cellWidth);
  const barLeft =
    durationDays === 1
      ? startCenter - barWidth / 2 // Single-day: center the bar on the day
      : startCenter; // Multi-day: start at center of first day

  return {
    left: `${barLeft}px`,
    width: `${barWidth}px`,
  };
}

/**
 * Position the assignee avatar just past the right edge of the task bar.
 * Adds extra offset when a dependency connector exits/enters the right side.
 */
function getAvatarStyle(task: GanttTask): Record<string, string> {
  const barStyle = getTaskBarStyle(task);
  if (barStyle.display === 'none') {
    return { display: 'none' };
  }
  const barLeft = parseFloat(barStyle.left || '0');
  const barWidth = parseFloat(barStyle.width || '0');

  // Check if any dependency line touches the right edge of this bar:
  // - As predecessor: FS or FF exit from the right
  // - As successor: FF or SF have arrow entering the right side
  const hasRightDep =
    (task.dependents_info || []).some((d) => d.type === 'FS' || d.type === 'FF') ||
    (task.dependencies_info || []).some((d) => d.type === 'FF' || d.type === 'SF');

  const gap = hasRightDep ? 16 : 4;
  return {
    left: `${barLeft + barWidth + gap}px`,
  };
}

// Status colors for task bars - matching Kanban column scheme
const statusColors: Record<TaskStatus, string> = {
  Open: 'gantt-bar-open',
  Working: 'gantt-bar-in-progress',
  'In Progress': 'gantt-bar-in-progress',
  'Pending Review': 'gantt-bar-review',
  Review: 'gantt-bar-review',
  Completed: 'gantt-bar-completed',
  Cancelled: 'bg-gray-400',
};

// Milestone status colors - violet theme
const milestoneStatusColors: Record<MilestoneStatus, string> = {
  Upcoming: 'bg-violet-500',
  'In Progress': 'bg-violet-600',
  Completed: 'bg-emerald-500',
  Missed: 'bg-rose-500',
};

// Priority indicator classes - left border color indicates priority
const priorityBorders: Record<TaskPriority, string> = {
  Urgent: 'priority-urgent',
  High: 'priority-high',
  Medium: 'priority-medium',
  Low: 'priority-low',
};

// Format day header
function formatDayHeader(date: Date): string {
  return date.getDate().toString();
}

// Check if date is weekend
function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

// Check if date is today
function isToday(date: Date): boolean {
  const today = new Date();
  return date.toDateString() === today.toDateString();
}

// Handle item click (task or milestone)
function handleItemClick(item: GanttItem) {
  emit('select', item);
}

// Get milestone marker position
function getMilestonePosition(
  milestone: GanttMilestone,
): Record<string, string> {
  if (!milestone.due_date) {
    return { display: 'none' };
  }

  // Parse date as local date to avoid timezone issues
  const dueDate = parseLocalDate(milestone.due_date);

  // Find day index - compare using date components for reliability
  const dayIndex = days.value.findIndex((d) => {
    const dayDate = new Date(d);
    return (
      dayDate.getFullYear() === dueDate.getFullYear() &&
      dayDate.getMonth() === dueDate.getMonth() &&
      dayDate.getDate() === dueDate.getDate()
    );
  });

  if (dayIndex === -1) {
    return { display: 'none' };
  }

  return {
    left: `${dayIndex * props.cellWidth + props.cellWidth / 2 - 8}px`, // Center the 16px diamond
  };
}

// Get milestone diamond center X coordinate (for connection line endpoints)
function getMilestoneCenterX(milestone: GanttMilestone): number | null {
  if (!milestone.due_date) return null;
  const dueDate = parseLocalDate(milestone.due_date);
  const dayIndex = days.value.findIndex((d) => {
    const dayDate = new Date(d);
    return (
      dayDate.getFullYear() === dueDate.getFullYear() &&
      dayDate.getMonth() === dueDate.getMonth() &&
      dayDate.getDate() === dueDate.getDate()
    );
  });
  if (dayIndex === -1) return null;
  return dayIndex * props.cellWidth + props.cellWidth / 2;
}

// Calculate task duration in days (exclusive: end_date - start_date)
function getTaskDuration(task: GanttTask): number {
  if (!task.start_date) return 0;
  const startDate = parseLocalDate(task.start_date);
  const endDate = task.due_date ? parseLocalDate(task.due_date) : startDate;
  const durationMs = endDate.getTime() - startDate.getTime();
  return Math.max(1, Math.ceil(durationMs / (1000 * 60 * 60 * 24)));
}

// Format date as YYYY-MM-DD for API
function formatDateForApi(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// ============================================
// HTML5 Drag and Drop Handlers
// ============================================

/**
 * Handle drag start for timeline bar - changes dates horizontally
 * Uses snap-to-grid method: calculates day delta from pixel movement
 */
function handleBarDragStart(
  event: DragEvent,
  task: GanttTask,
  rowIndex: number,
): void {
  if (!event.dataTransfer || !task.start_date) return;

  const target = event.currentTarget as HTMLElement;

  // Get the original left position of the bar for snap-to-grid calculation
  const barStyle = getTaskBarStyle(task);
  const originalLeft = parseInt(barStyle.left || '0', 10);

  // Store drag data for date changes
  const dragData: DragData = {
    taskId: task.name,
    taskName: task.subject,
    startDate: task.start_date,
    dueDate: task.due_date || null,
    duration: getTaskDuration(task),
    startX: event.clientX, // Click point in viewport coords (delta = 0 at start)
    originalLeft, // Store original position for snap-to-grid
    rowIndex,
    dragType: 'dates',
    itemType: 'task',
  };

  // Set data transfer
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('application/json', JSON.stringify(dragData));

  // Create custom drag image for better visual feedback
  const dragImage = target.cloneNode(true) as HTMLElement;
  dragImage.style.position = 'absolute';
  dragImage.style.top = '-1000px';
  dragImage.style.opacity = '0.8';
  dragImage.style.transform = 'scale(1.02)';
  dragImage.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
  document.body.appendChild(dragImage);
  event.dataTransfer.setDragImage(dragImage, event.offsetX, event.offsetY);

  // Clean up drag image after a frame
  requestAnimationFrame(() => {
    document.body.removeChild(dragImage);
  });

  // Update state
  draggingTask.value = dragData;

  // Global dragover listener: fires continuously during drag regardless of cursor position.
  // The bar's @dragover.stop prevents the row-level handler from firing when the cursor
  // is over the bar itself. This global listener ensures preview updates always work.
  const onGlobalDragOver = (e: DragEvent) => {
    if (!draggingTask.value || draggingTask.value.dragType !== 'dates') return;
    e.preventDefault();
    const pixelsDeltaX = e.clientX - draggingTask.value.startX;
    dragDaysDelta.value = Math.round(pixelsDeltaX / props.cellWidth);
  };
  // Use capture phase (3rd arg = true) so this fires BEFORE the bar's
  // @dragover.stop can call stopPropagation() and block bubbling to document.
  document.addEventListener('dragover', onGlobalDragOver, true);
  cleanupGlobalDragListener = () => {
    document.removeEventListener('dragover', onGlobalDragOver, true);
    cleanupGlobalDragListener = null;
  };

  // Add visual feedback class
  requestAnimationFrame(() => {
    target.classList.add('dragging');
  });
}

/**
 * Handle drag start for row reordering - from the left panel
 * Works for both tasks and milestones (unified drag system)
 */
function handleRowDragStart(
  event: DragEvent,
  item: GanttItem,
  rowIndex: number,
): void {
  if (groupMode.value !== 'none') return;
  if (!event.dataTransfer) return;

  const target = event.currentTarget as HTMLElement;
  const itemType = isGanttTask(item)
    ? ('task' as const)
    : ('milestone' as const);

  // Store drag data for reordering
  const dragData: DragData = {
    taskId: item.name,
    taskName: item.subject,
    startDate: item.start_date || '',
    dueDate: item.due_date || null,
    duration: isGanttTask(item) ? getTaskDuration(item) : 0,
    startX: event.clientX,
    originalLeft: 0, // Not used for reordering
    rowIndex,
    dragType: 'reorder',
    itemType,
  };

  // Set data transfer
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('application/json', JSON.stringify(dragData));

  // Update state
  draggingTask.value = dragData;

  // Add visual feedback
  requestAnimationFrame(() => {
    target.classList.add('dragging-row');
  });
}

/**
 * Handle drag over a timeline row - combines date preview + reorder targeting
 * so both left and right panels coordinate visual feedback.
 */
function handleTimelineDragOver(event: DragEvent, rowIndex: number): void {
  event.preventDefault();
  if (!event.dataTransfer) return;

  event.dataTransfer.dropEffect = 'move';

  if (draggingTask.value) {
    // Track horizontal movement for day-delta calculation
    const pixelsDeltaX = event.clientX - draggingTask.value.startX;
    dragDaysDelta.value = Math.round(pixelsDeltaX / props.cellWidth);

    if (
      draggingTask.value.dragType === 'reorder' &&
      draggingTask.value.rowIndex !== rowIndex
    ) {
      // Highlight drop target row
      dropTargetIndex.value = rowIndex;
    }
  }
}

/**
 * Handle drag over a specific row - for reordering
 */
function handleRowDragOver(event: DragEvent, rowIndex: number): void {
  event.preventDefault();
  if (!event.dataTransfer) return;

  event.dataTransfer.dropEffect = 'move';

  // Highlight drop target row if different from source
  if (draggingTask.value && draggingTask.value.rowIndex !== rowIndex) {
    dropTargetIndex.value = rowIndex;
  }
}

/**
 * Handle drag leave - remove drop target highlight
 */
function handleDragLeave(event: DragEvent): void {
  // Only clear if leaving the row (not entering a child element)
  const relatedTarget = event.relatedTarget as HTMLElement | null;
  const currentTarget = event.currentTarget as HTMLElement | null;
  if (!relatedTarget || !currentTarget?.contains(relatedTarget)) {
    dropTargetIndex.value = null;
  }
}

/**
 * Handle drop on row - handles both date changes and reordering
 * Uses snap-to-grid method for date changes
 * Unified: any item type can be dropped on any row
 */
function handleRowDrop(event: DragEvent, targetRowIndex: number): void {
  event.preventDefault();
  event.stopPropagation();
  if (!event.dataTransfer || !draggingTask.value) return;

  const data = draggingTask.value;

  // Handle based on drag type
  if (data.dragType === 'dates' && data.startDate) {
    // SNAP-TO-GRID METHOD: Calculate day delta from pixel movement
    const pixelsDelta = event.clientX - data.startX;
    const daysDelta = Math.round(pixelsDelta / props.cellWidth);

    // Only emit if there's an actual change
    if (daysDelta !== 0) {
      // Calculate new dates by adding daysDelta to original dates
      const originalStart = parseLocalDate(data.startDate);
      const newStartDate = new Date(originalStart);
      newStartDate.setDate(newStartDate.getDate() + daysDelta);

      // Calculate new end date maintaining original duration
      const newEndDate = new Date(newStartDate);
      newEndDate.setDate(newEndDate.getDate() + data.duration);

      // Emit the date update
      emit('update-dates', {
        taskId: data.taskId,
        startDate: formatDateForApi(newStartDate),
        endDate: formatDateForApi(newEndDate),
      });
    }
  } else if (data.dragType === 'reorder') {
    // Unified reorder: compute the new neighbours at the drop position
    const fromIndex = data.rowIndex;
    const toIndex = targetRowIndex;
    if (fromIndex !== toIndex) {
      // Build the new order by splicing locally
      const items = [...sortedItems.value];
      const [movedItem] = items.splice(fromIndex, 1);
      items.splice(toIndex, 0, movedItem);

      // Find the neighbours of the moved item at its new position
      const newPos = items.indexOf(movedItem);
      const prevItem = newPos > 0 ? items[newPos - 1] : null;
      const nextItem = newPos < items.length - 1 ? items[newPos + 1] : null;

      emit('reorder-item', {
        itemId: data.taskId,
        itemType: data.itemType,
        prevItemId: prevItem ? prevItem.name : null,
        nextItemId: nextItem ? nextItem.name : null,
        prevItemType: prevItem
          ? isGanttTask(prevItem)
            ? 'task'
            : 'milestone'
          : null,
        nextItemType: nextItem
          ? isGanttTask(nextItem)
            ? 'task'
            : 'milestone'
          : null,
      });
    }
  }

  // Reset drag state
  resetDragState();
}

/**
 * Handle drag end - cleanup
 */
function handleDragEnd(event: DragEvent): void {
  const target = event.currentTarget as HTMLElement;
  target?.classList?.remove('dragging');
  target?.classList?.remove('dragging-row');
  resetDragState();
}

/**
 * Reset all drag state
 */
function resetDragState(): void {
  if (cleanupGlobalDragListener) {
    cleanupGlobalDragListener();
  }
  draggingTask.value = null;
  dropTargetIndex.value = null;
  dragDaysDelta.value = 0;
}

// ============================================
// Milestone Drag Handlers (mousedown-based)
// ============================================

/**
 * Handle mousedown on milestone diamond to start dragging
 * Uses mousedown/mousemove/mouseup instead of HTML5 drag API
 * because the diamond target is small and needs precise control
 */
function handleMilestoneDragStart(
  event: MouseEvent,
  milestone: GanttMilestone,
): void {
  event.preventDefault();
  event.stopPropagation();

  if (!milestone.due_date) return;

  const pos = getMilestonePosition(milestone);
  const originalLeft = parseInt(pos.left || '0', 10);

  draggingMilestone.value = {
    milestoneId: milestone.name,
    milestoneName: milestone.subject,
    originalDueDate: milestone.due_date,
    startX: event.clientX,
    originalLeft,
  };
  milestoneDragDaysDelta.value = 0;

  // Attach global listeners for move and up
  document.addEventListener('mousemove', handleMilestoneDragMove);
  document.addEventListener('mouseup', handleMilestoneDragEnd);
}

/**
 * Handle mousemove during milestone drag - snap to grid
 */
function handleMilestoneDragMove(event: MouseEvent): void {
  if (!draggingMilestone.value) return;

  const pixelsDelta = event.clientX - draggingMilestone.value.startX;
  milestoneDragDaysDelta.value = Math.round(pixelsDelta / props.cellWidth);
}

/**
 * Handle mouseup to complete milestone drag
 */
function handleMilestoneDragEnd(): void {
  document.removeEventListener('mousemove', handleMilestoneDragMove);
  document.removeEventListener('mouseup', handleMilestoneDragEnd);

  if (!draggingMilestone.value) return;

  const daysDelta = milestoneDragDaysDelta.value;

  if (daysDelta !== 0) {
    const originalDate = parseLocalDate(
      draggingMilestone.value.originalDueDate,
    );
    const newDate = new Date(originalDate);
    newDate.setDate(newDate.getDate() + daysDelta);

    emit('update-milestone-date', {
      milestoneId: draggingMilestone.value.milestoneId,
      dueDate: formatDateForApi(newDate),
    });
  }

  draggingMilestone.value = null;
  milestoneDragDaysDelta.value = 0;
}

/**
 * Get the preview position for a milestone being dragged
 */
function getMilestoneDragPreviewPosition(
  milestone: GanttMilestone,
): Record<string, string> | null {
  if (
    !draggingMilestone.value ||
    draggingMilestone.value.milestoneId !== milestone.name
  ) {
    return null;
  }
  if (milestoneDragDaysDelta.value === 0) return null;

  const newLeft =
    draggingMilestone.value.originalLeft +
    milestoneDragDaysDelta.value * props.cellWidth;
  return {
    left: `${newLeft}px`,
  };
}

/**
 * Check if a milestone is currently being dragged
 */
function isMilestoneBeingDragged(milestone: GanttMilestone): boolean {
  return draggingMilestone.value?.milestoneId === milestone.name;
}

/**
 * Check if a task is currently being dragged
 */
function isTaskBeingDragged(task: GanttTask): boolean {
  return draggingTask.value?.taskId === task.name;
}

/**
 * Check if a task was just reordered (for highlight animation)
 * Uses prop from parent (set after data reload) OR local state
 */
function isJustReordered(task: GanttTask): boolean {
  return (
    props.justReorderedId === task.name ||
    justReorderedTaskId.value === task.name
  );
}

/**
 * Check if a row is a valid drop target (different from source)
 */
function isValidDropTarget(rowIndex: number): boolean {
  return (
    dropTargetIndex.value === rowIndex &&
    draggingTask.value?.dragType === 'reorder' &&
    draggingTask.value?.rowIndex !== rowIndex
  );
}

// Sync vertical scroll between left task names and right grid
function syncVerticalScroll(event: Event): void {
  if (isSyncingVerticalScroll) return;
  isSyncingVerticalScroll = true;

  const source = event.target as HTMLElement;
  const scrollTop = source.scrollTop;

  if (source === scrollContainerRef.value && leftBodyRef.value) {
    leftBodyRef.value.scrollTop = scrollTop;
  } else if (source === leftBodyRef.value && scrollContainerRef.value) {
    scrollContainerRef.value.scrollTop = scrollTop;
  }

  requestAnimationFrame(() => {
    isSyncingVerticalScroll = false;
  });
}

// Sync horizontal scroll from Area B body → Area A header
function syncHorizontalScroll(): void {
  if (isSyncingHorizontalScroll) return;
  isSyncingHorizontalScroll = true;

  const body = scrollContainerRef.value;
  const header = headerScrollRef.value;
  if (body && header) {
    header.scrollLeft = body.scrollLeft;
  }

  requestAnimationFrame(() => {
    isSyncingHorizontalScroll = false;
  });
}

// ============================================
// Custom scrollbar thumb between header and grid
// ============================================

// Detect dark mode for thumb color
const isDarkMode = ref(false);
function checkDarkMode(): void {
  isDarkMode.value = document.documentElement.classList.contains('dark');
}

// Scroll progress (0–100%) for position indicator
const scrollProgress = ref(0);

// Thumb center position — fully reactive (depends on two refs)
const thumbLeftPosition = computed(() => {
  if (scrollbarWidth.value <= 0) return 0;
  return (scrollbarWidth.value - thumbWidth.value) / 2;
});

// Computed inline style for the scrubber thumb — always centered in viewport
const thumbStyle = computed(() => {
  let bgColor: string;
  if (isDarkMode.value) {
    bgColor = thumbDragging.value
      ? '#4b5563'
      : thumbHovered.value
        ? '#4b5563'
        : '#374151';
  } else {
    bgColor = thumbDragging.value
      ? '#6b7280'
      : thumbHovered.value
        ? '#9ca3af'
        : '#d1d5db';
  }
  return {
    position: 'absolute' as const,
    top: '0',
    height: '100%',
    width: `${thumbWidth.value}px`,
    left: `${thumbLeftPosition.value}px`,
    backgroundColor: bgColor,
    borderRadius: '4px',
    border: '1px solid',
    borderColor: isDarkMode.value ? '#6b7280' : '#d1d5db',
    cursor: thumbDragging.value ? 'grabbing' : 'grab',
    transition: thumbDragging.value
      ? 'transform 0.1s ease'
      : 'background-color 0.2s, transform 0.1s ease',
    transform: thumbDragging.value ? 'translateY(-2px)' : 'translateY(0)',
    display: 'block',
    zIndex: '11',
    overflow: 'hidden',
  };
});

// Measure scrollbar viewport width and determine visibility
function updateScrollbarThumb(): void {
  const container = scrollContainerRef.value;
  if (!container) return;

  const visibleWidth = container.clientWidth;
  const totalContentWidth = container.scrollWidth;
  const scrollableDistance = totalContentWidth - visibleWidth;

  scrollbarWidth.value = visibleWidth;
  thumbVisible.value = scrollableDistance > 0;
}

// Get zone name from pixel distance from drag start
function getZoneForDistance(distance: number): string {
  for (const [zone, config] of Object.entries(ZONE_CONFIG)) {
    if (distance >= config.min && distance < config.max) {
      return zone;
    }
  }
  return 'zone-center';
}

// Scrubber drag: zone-based velocity scrolling with continuous animation
let dragAnimationFrame: number | null = null;

function handleThumbMouseDown(e: MouseEvent): void {
  e.preventDefault();
  e.stopPropagation();

  const container = scrollContainerRef.value;
  if (!container) return;

  thumbDragging.value = true;
  activeZone.value = 'zone-center';

  const startX = e.clientX;
  let currentDistance = 0;

  // Continuous scroll loop — runs while dragging
  const scrollLoop = (): void => {
    if (!thumbDragging.value) return;

    const zone = getZoneForDistance(currentDistance);
    activeZone.value = zone;
    const config = ZONE_CONFIG[zone];

    if (config.velocity > 0) {
      const maxScroll = container.scrollWidth - container.clientWidth;
      const scrollAmount = config.velocity * 8 * config.direction;
      container.scrollLeft = Math.max(
        0,
        Math.min(maxScroll, container.scrollLeft + scrollAmount),
      );
      updateScrollProgress();
    }

    dragAnimationFrame = requestAnimationFrame(scrollLoop);
  };

  const onMouseMove = (moveEvent: MouseEvent): void => {
    currentDistance = moveEvent.clientX - startX;
  };

  const onMouseUp = (): void => {
    thumbDragging.value = false;
    activeZone.value = 'zone-center';
    if (dragAnimationFrame !== null) {
      cancelAnimationFrame(dragAnimationFrame);
      dragAnimationFrame = null;
    }
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  };

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);

  // Start the scroll loop
  dragAnimationFrame = requestAnimationFrame(scrollLoop);
}

// Click on the track: jump to that position (video player style)
function handleTrackClick(e: MouseEvent): void {
  const container = scrollContainerRef.value;
  const track = headerScrollbarRef.value;
  if (!container || !track) return;

  const trackRect = track.getBoundingClientRect();
  const clickX = e.clientX - trackRect.left;
  const scrollPercentage = clickX / track.clientWidth;
  const maxScroll = container.scrollWidth - container.clientWidth;

  container.scrollLeft = Math.max(
    0,
    Math.min(maxScroll, scrollPercentage * maxScroll),
  );
  updateScrollProgress();
}

// Update scroll progress percentage and sync header
function updateScrollProgress(): void {
  const container = scrollContainerRef.value;
  if (!container) return;
  const maxScroll = container.scrollWidth - container.clientWidth;
  scrollProgress.value =
    maxScroll > 0 ? (container.scrollLeft / maxScroll) * 100 : 0;
  // Keep header in sync when scrolling programmatically (scrubber drag, track click)
  if (headerScrollRef.value) {
    headerScrollRef.value.scrollLeft = container.scrollLeft;
  }
}

// Combined scroll handler for Area B body container
function onContainerScroll(event: Event): void {
  syncVerticalScroll(event);
  syncHorizontalScroll();
  updateScrollProgress();
}

// Resize observer to update thumb when container size changes
let resizeObserver: ResizeObserver | null = null;
let darkModeObserver: MutationObserver | null = null;

onMounted(() => {
  checkDarkMode();

  // Scroll to today at 1/4 from left edge (past context left, future right)
  if (todayIndex.value >= 0 && scrollContainerRef.value) {
    const todayPosition = todayIndex.value * props.cellWidth;
    const quarterViewport = scrollContainerRef.value.clientWidth / 4;
    const maxScroll =
      scrollContainerRef.value.scrollWidth -
      scrollContainerRef.value.clientWidth;
    const scrollPosition = Math.max(
      0,
      Math.min(maxScroll, todayPosition - quarterViewport),
    );
    scrollContainerRef.value.scrollLeft = scrollPosition;
    // Sync header to match initial scroll position
    if (headerScrollRef.value) {
      headerScrollRef.value.scrollLeft = scrollPosition;
    }
  }

  // Initial thumb + progress calculation
  requestAnimationFrame(() => {
    updateScrollbarThumb();
    updateScrollProgress();
  });

  // Watch for container and scrollbar track resize
  resizeObserver = new ResizeObserver(() => {
    updateScrollbarThumb();
  });
  if (scrollContainerRef.value) {
    resizeObserver.observe(scrollContainerRef.value);
  }
  if (headerScrollbarRef.value) {
    resizeObserver.observe(headerScrollbarRef.value);
  }

  // Watch for dark mode changes
  darkModeObserver = new MutationObserver(checkDarkMode);
  darkModeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  });
});

// Update thumb when timeline data changes
watch([days, () => props.cellWidth], () => {
  requestAnimationFrame(updateScrollbarThumb);
});

// Reset collapsed groups when grouping mode changes
watch(groupMode, () => {
  collapsedGroups.value = new Set();
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  darkModeObserver?.disconnect();
  if (dragAnimationFrame !== null) {
    cancelAnimationFrame(dragAnimationFrame);
  }
  // Clean up any lingering drag listeners
  if (cleanupGlobalDragListener) {
    cleanupGlobalDragListener();
  }
  document.removeEventListener('mousemove', handleMilestoneDragMove);
  document.removeEventListener('mouseup', handleMilestoneDragEnd);
});

// Unified item list sorted by float sort_order (backend is source of truth).
// Items with sort_order > 0 are sorted numerically.
// Items with sort_order === 0 (pre-migration) preserve parent array order and appear after sorted items.
const sortedItems = computed(() => {
  const items = [...props.tasks];

  // Sort by sort_order (float). Items with 0 keep their relative parent order.
  const tagged = items.map((item, index) => ({
    item,
    sortOrder: ('sort_order' in item ? item.sort_order : 0) || 0,
    originalIndex: index,
  }));

  tagged.sort((a, b) => {
    // Both have sort_order: numeric comparison
    if (a.sortOrder > 0 && b.sortOrder > 0) {
      return a.sortOrder - b.sortOrder;
    }
    // Sorted items before unsorted
    if (a.sortOrder > 0 && b.sortOrder === 0) return -1;
    if (a.sortOrder === 0 && b.sortOrder > 0) return 1;
    // Both unsorted: preserve parent order
    return a.originalIndex - b.originalIndex;
  });

  return tagged.map((t) => t.item);
});

// Display rows: wraps sortedItems with optional group headers
const displayRows = computed<DisplayRow[]>(() => {
  const items = sortedItems.value;

  if (groupMode.value === 'none') {
    return items.map((item): ItemRow => ({ kind: 'item', item }));
  }

  const groups = new Map<string, GanttItem[]>();
  const mode = groupMode.value;

  for (const item of items) {
    let key: string;

    if (!isGanttTask(item)) {
      if (mode === 'status') {
        key = (item as GanttMilestone).status || 'Upcoming';
      } else {
        key = '__milestones__';
      }
    } else {
      const task = item as GanttTask;
      switch (mode) {
        case 'status':
          key = task.status || 'Open';
          break;
        case 'priority':
          key = task.priority || 'Medium';
          break;
        case 'milestone':
          key = task.milestone || '__no_milestone__';
          break;
        case 'assignee':
          key = task.assigned_to_name || '__unassigned__';
          break;
        case 'group':
          key = task.task_group || '__ungrouped__';
          break;
        default:
          key = '__default__';
      }
    }

    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(item);
  }

  const sortedKeys = [...groups.keys()].sort((a, b) => {
    const specialKeys = ['__milestones__', '__no_milestone__', '__unassigned__', '__ungrouped__', '__default__'];
    const aSpecial = specialKeys.includes(a);
    const bSpecial = specialKeys.includes(b);
    if (aSpecial && !bSpecial) return 1;
    if (!aSpecial && bSpecial) return -1;

    if (mode === 'status') {
      const ai = STATUS_ORDER.indexOf(a);
      const bi = STATUS_ORDER.indexOf(b);
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    }
    if (mode === 'priority') {
      const ai = PRIORITY_ORDER.indexOf(a);
      const bi = PRIORITY_ORDER.indexOf(b);
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    }

    return a.localeCompare(b);
  });

  const rows: DisplayRow[] = [];
  for (const key of sortedKeys) {
    const groupItems = groups.get(key)!;

    let label = key;
    if (key === '__milestones__') label = __('Milestones');
    if (key === '__no_milestone__') label = __('No Milestone');
    if (key === '__unassigned__') label = __('Unassigned');
    if (key === '__ungrouped__') label = __('Ungrouped');
    if (key === '__default__') label = __('Other');

    rows.push({
      kind: 'group-header',
      key,
      label,
      count: groupItems.length,
    });

    if (!collapsedGroups.value.has(key)) {
      for (const item of groupItems) {
        rows.push({ kind: 'item', item });
      }
    }
  }

  return rows;
});

// Filtered views for dependency edges (only tasks have dependencies)
const sortedTasks = computed(() => {
  return sortedItems.value.filter((item) => isGanttTask(item)) as GanttTask[];
});

// Total calendar width = days × cellWidth — explicit width for header + body sync
const totalCalendarWidth = computed<number>(() => {
  return days.value.length * props.cellWidth;
});

// ============================================
// Dependency Arrows (SVG overlay)
// ============================================

const ROW_HEIGHT = 40; // h-10 = 40px per row

// Dependency edge for SVG rendering
interface DependencyEdge {
  fromTask: string;
  toTask: string;
  fromRow: number;
  toRow: number;
  fromX: number; // Right edge of source bar (or left for SS)
  fromY: number; // Center of source row
  toX: number; // Left edge of target bar (or right for FF)
  toY: number; // Center of target row
  type: DependencyType;
  path: string; // SVG path d attribute
  arrowPoints: string; // SVG polygon points for arrowhead
  color: string;
}

// Color for dependency lines — uniform black for clean professional look
const dependencyColors: Record<DependencyType, string> = {
  FS: '#1a1a1a',
  SS: '#1a1a1a',
  FF: '#1a1a1a',
  SF: '#1a1a1a',
};

// Get bar position for a task (reuses same logic as getTaskBarStyle)
function getBarPosition(
  task: GanttTask,
): { left: number; width: number } | null {
  if (!task.start_date) return null;

  const startDate = parseLocalDate(task.start_date);
  const endDate = task.due_date
    ? parseLocalDate(task.due_date)
    : new Date(startDate);

  const startIndex = days.value.findIndex((d) => {
    const dayDate = new Date(d);
    return (
      dayDate.getFullYear() === startDate.getFullYear() &&
      dayDate.getMonth() === startDate.getMonth() &&
      dayDate.getDate() === startDate.getDate()
    );
  });

  let effectiveIndex = startIndex;
  if (startIndex === -1) {
    effectiveIndex = days.value.findIndex((d) => {
      const dayDate = new Date(d);
      dayDate.setHours(0, 0, 0, 0);
      const startCopy = new Date(startDate);
      startCopy.setHours(0, 0, 0, 0);
      return dayDate.getTime() >= startCopy.getTime();
    });
  }

  if (effectiveIndex === -1) return null;

  const durationMs = endDate.getTime() - startDate.getTime();
  const durationDays = Math.max(
    1,
    Math.ceil(durationMs / (1000 * 60 * 60 * 24)) + 1,
  );

  // Center-to-center positioning (matches getTaskBarStyle)
  const startCenter = effectiveIndex * props.cellWidth + props.cellWidth / 2;
  const endCenter =
    (effectiveIndex + durationDays - 1) * props.cellWidth + props.cellWidth / 2;
  const barWidth = Math.max(endCenter - startCenter, props.cellWidth);
  const barLeft = durationDays === 1 ? startCenter - barWidth / 2 : startCenter;

  return {
    left: barLeft,
    width: barWidth,
  };
}

// Generate SVG path with orthogonal routing and rounded corners.
// Uses quarter-circle arc segments at each bend.
//
// SVG arc: A rx ry rotation large-arc sweep endX endY
//   sweep=1 → clockwise from current to end
//   sweep=0 → counter-clockwise from current to end
//
// Corner sweep-flag truth table (verified geometrically):
//
//   Turn shape   | Start → End                          | Sweep
//   ╮ right→down | (x-r, y) → (x, y+r)                 | 1 (CW)
//   ╰ down→right | (x, y-r) → (x+r, y)                 | 0 (CCW)
//   ╭ left→down  | (x+r, y) → (x, y+r)                 | 0 (CCW)
//   ╯ down→left  | (x, y-r) → (x-r, y)                 | 1 (CW)
//   ╯ right→up   | (x-r, y) → (x, y-r)                 | 0 (CCW)
//   ╭ up→right   | (x, y+r) → (x+r, y)                 | 1 (CW)
//   ╮ left→up    | (x+r, y) → (x, y-r)                 | 1 (CW)
//   ╰ up→left    | (x, y+r) → (x-r, y)                 | 0 (CCW)
//
// Exit/entry direction for dependency path routing
type PathDirection = 'right' | 'left';

function generateDependencyPath(
  fromX: number,
  fromY: number,
  toX: number,
  toY: number,
  exitDir: PathDirection = 'right',
  entryDir: PathDirection = 'right',
): string {
  const r = 5; // Corner radius
  const stub = 10; // Horizontal stub before first turn

  // Same row — straight line (adjust direction for left-exit/entry)
  if (fromY === toY) {
    if (exitDir === 'left' && entryDir === 'right') {
      // SS backward: go left, down, across, up, right into target
      const loopY = fromY + ROW_HEIGHT * 0.6;
      const minX = Math.min(fromX, toX) - stub;
      return `M ${fromX} ${fromY} L ${minX} ${fromY} L ${minX} ${loopY} L ${toX - stub} ${loopY} L ${toX - stub} ${toY} L ${toX} ${toY}`;
    }
    return `M ${fromX} ${fromY} L ${toX} ${toY}`;
  }

  const goingDown = toY > fromY;

  // ── Both exit right, enter right: standard FS-style routing ──
  if (exitDir === 'right' && entryDir === 'right') {
    const gap = toX - fromX;

    if (gap > stub + r * 2) {
      // Z-shape: right → vertical → right
      const midX = fromX + gap / 2;
      const vDist = Math.abs(toY - fromY);
      const cr = Math.min(r, vDist / 2, gap / 4);

      if (goingDown) {
        return [
          `M ${fromX} ${fromY}`,
          `L ${midX - cr} ${fromY}`,
          `A ${cr} ${cr} 0 0 1 ${midX} ${fromY + cr}`,
          `L ${midX} ${toY - cr}`,
          `A ${cr} ${cr} 0 0 0 ${midX + cr} ${toY}`,
          `L ${toX} ${toY}`,
        ].join(' ');
      } else {
        return [
          `M ${fromX} ${fromY}`,
          `L ${midX - cr} ${fromY}`,
          `A ${cr} ${cr} 0 0 0 ${midX} ${fromY - cr}`,
          `L ${midX} ${toY + cr}`,
          `A ${cr} ${cr} 0 0 1 ${midX + cr} ${toY}`,
          `L ${toX} ${toY}`,
        ].join(' ');
      }
    }

    // S-shape for tight/backward cases
    const stubEnd = fromX + stub;
    const entryStart = toX - stub;
    const midY = fromY + (toY - fromY) / 2;
    const vHalf = Math.abs(toY - fromY) / 2;
    const cr = Math.min(r, vHalf / 2, stub / 2);

    if (Math.abs(toY - fromY) < cr * 4) {
      const mx = Math.max(stubEnd, fromX + 12);
      return `M ${fromX} ${fromY} L ${mx} ${fromY} L ${mx} ${toY} L ${toX} ${toY}`;
    }

    if (goingDown) {
      return [
        `M ${fromX} ${fromY}`,
        `L ${stubEnd - cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 1 ${stubEnd} ${fromY + cr}`,
        `L ${stubEnd} ${midY - cr}`,
        `A ${cr} ${cr} 0 0 1 ${stubEnd - cr} ${midY}`,
        `L ${entryStart + cr} ${midY}`,
        `A ${cr} ${cr} 0 0 0 ${entryStart} ${midY + cr}`,
        `L ${entryStart} ${toY - cr}`,
        `A ${cr} ${cr} 0 0 0 ${entryStart + cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    } else {
      return [
        `M ${fromX} ${fromY}`,
        `L ${stubEnd - cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 0 ${stubEnd} ${fromY - cr}`,
        `L ${stubEnd} ${midY + cr}`,
        `A ${cr} ${cr} 0 0 0 ${stubEnd - cr} ${midY}`,
        `L ${entryStart + cr} ${midY}`,
        `A ${cr} ${cr} 0 0 1 ${entryStart} ${midY - cr}`,
        `L ${entryStart} ${toY + cr}`,
        `A ${cr} ${cr} 0 0 1 ${entryStart + cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    }
  }

  // ── Exit left, enter right: SS-style routing ──
  // Line goes left from start, then routes to target's start
  //
  //   ◀──╮  predecessor start
  //      │
  //      ╰──▶  successor start
  //
  if (exitDir === 'left' && entryDir === 'right') {
    const minX = Math.min(fromX, toX) - stub;
    const vDist = Math.abs(toY - fromY);
    const cr = Math.min(r, vDist / 2, stub / 2);

    if (vDist < cr * 4) {
      return `M ${fromX} ${fromY} L ${minX} ${fromY} L ${minX} ${toY} L ${toX} ${toY}`;
    }

    if (goingDown) {
      // Corner 1: ╭ left→down at (minX, fromY): sweep=0
      // Corner 2: ╰ down→right at (minX, toY):  sweep=0
      return [
        `M ${fromX} ${fromY}`,
        `L ${minX + cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 0 ${minX} ${fromY + cr}`,
        `L ${minX} ${toY - cr}`,
        `A ${cr} ${cr} 0 0 0 ${minX + cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    } else {
      // Corner 1: ╮ left→up at (minX, fromY): sweep=1
      // Corner 2: ╭ up→right at (minX, toY):  sweep=1
      return [
        `M ${fromX} ${fromY}`,
        `L ${minX + cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 1 ${minX} ${fromY - cr}`,
        `L ${minX} ${toY + cr}`,
        `A ${cr} ${cr} 0 0 1 ${minX + cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    }
  }

  // ── Exit right, enter left: FF-style routing ──
  // Line goes right from end, then routes to target's end (arriving from right)
  //
  //   predecessor end ──╮
  //                     │
  //   successor end  ◀──╯
  //
  if (exitDir === 'right' && entryDir === 'left') {
    const maxX = Math.max(fromX, toX) + stub;
    const vDist = Math.abs(toY - fromY);
    const cr = Math.min(r, vDist / 2, stub / 2);

    if (vDist < cr * 4) {
      return `M ${fromX} ${fromY} L ${maxX} ${fromY} L ${maxX} ${toY} L ${toX} ${toY}`;
    }

    if (goingDown) {
      // Corner 1: ╮ right→down at (maxX, fromY): sweep=1
      // Corner 2: ╯ down→left at (maxX, toY):    sweep=1
      return [
        `M ${fromX} ${fromY}`,
        `L ${maxX - cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 1 ${maxX} ${fromY + cr}`,
        `L ${maxX} ${toY - cr}`,
        `A ${cr} ${cr} 0 0 1 ${maxX - cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    } else {
      // Corner 1: ╯ right→up at (maxX, fromY):  sweep=0
      // Corner 2: ╰ up→left at (maxX, toY):     sweep=0
      return [
        `M ${fromX} ${fromY}`,
        `L ${maxX - cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 0 ${maxX} ${fromY - cr}`,
        `L ${maxX} ${toY + cr}`,
        `A ${cr} ${cr} 0 0 0 ${maxX - cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    }
  }

  // ── Exit left, enter left: SF-style routing ──
  // Line goes left from start, routes down/up, then arrives from right at target's end
  //
  //   ◀──╮  predecessor start
  //      │
  //      │     ╭──╮
  //      ╰─────╯  │
  //        successor end ◀──╯
  //
  if (exitDir === 'left' && entryDir === 'left') {
    const minX = Math.min(fromX, toX) - stub;
    const maxX = toX + stub;
    const vDist = Math.abs(toY - fromY);
    const midY = fromY + (toY - fromY) / 2;
    const cr = Math.min(r, vDist / 4, stub / 2);

    if (vDist < cr * 4) {
      return `M ${fromX} ${fromY} L ${minX} ${fromY} L ${minX} ${toY} L ${toX} ${toY}`;
    }

    if (goingDown) {
      return [
        `M ${fromX} ${fromY}`,
        `L ${minX + cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 0 ${minX} ${fromY + cr}`,
        `L ${minX} ${midY - cr}`,
        `A ${cr} ${cr} 0 0 0 ${minX + cr} ${midY}`,
        `L ${maxX - cr} ${midY}`,
        `A ${cr} ${cr} 0 0 1 ${maxX} ${midY + cr}`,
        `L ${maxX} ${toY - cr}`,
        `A ${cr} ${cr} 0 0 1 ${maxX - cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    } else {
      return [
        `M ${fromX} ${fromY}`,
        `L ${minX + cr} ${fromY}`,
        `A ${cr} ${cr} 0 0 1 ${minX} ${fromY - cr}`,
        `L ${minX} ${midY + cr}`,
        `A ${cr} ${cr} 0 0 1 ${minX + cr} ${midY}`,
        `L ${maxX - cr} ${midY}`,
        `A ${cr} ${cr} 0 0 0 ${maxX} ${midY - cr}`,
        `L ${maxX} ${toY + cr}`,
        `A ${cr} ${cr} 0 0 0 ${maxX - cr} ${toY}`,
        `L ${toX} ${toY}`,
      ].join(' ');
    }
  }

  // Fallback: straight line
  return `M ${fromX} ${fromY} L ${toX} ${toY}`;
}

// Compute all dependency edges for rendering
// Uses displayRows for row index → Y coordinate mapping (accounts for group headers)
const dependencyEdges = computed<DependencyEdge[]>(() => {
  if (!props.showDependencies) return [];

  const edges: DependencyEdge[] = [];
  const tasks = sortedTasks.value;

  // Build a name→visual-row-index map from displayRows
  const itemRowMap = new Map<string, number>();
  displayRows.value.forEach((row, idx) => {
    if (row.kind === 'item') {
      itemRowMap.set(row.item.name, idx);
    }
  });

  for (const task of tasks) {
    const deps = task.dependencies_info || [];
    const toRow = itemRowMap.get(task.name);
    if (toRow === undefined) continue;

    for (const dep of deps) {
      const fromRow = itemRowMap.get(dep.task_id);
      if (fromRow === undefined) continue; // Predecessor not in current view

      const fromTask = tasks.find((t) => t.name === dep.task_id);
      if (!fromTask) continue;

      const fromPos = getBarPosition(fromTask);
      const toPos = getBarPosition(task);

      if (!fromPos || !toPos) continue; // Task has no dates

      const type = dep.type || 'FS';

      // Determine connection points and directions based on dependency type
      let fromX: number;
      let toX: number;
      let exitDir: PathDirection;
      let entryDir: PathDirection;

      switch (type) {
        case 'FS': // Finish → Start: exit right, enter right
          fromX = fromPos.left + fromPos.width;
          toX = toPos.left;
          exitDir = 'right';
          entryDir = 'right';
          break;
        case 'SS': // Start → Start: exit left, enter right
          fromX = fromPos.left;
          toX = toPos.left;
          exitDir = 'left';
          entryDir = 'right';
          break;
        case 'FF': // Finish → Finish: exit right, enter left
          fromX = fromPos.left + fromPos.width;
          toX = toPos.left + toPos.width;
          exitDir = 'right';
          entryDir = 'left';
          break;
        case 'SF': // Start → Finish: exit left, enter left
          fromX = fromPos.left;
          toX = toPos.left + toPos.width;
          exitDir = 'left';
          entryDir = 'left';
          break;
        default:
          fromX = fromPos.left + fromPos.width;
          toX = toPos.left;
          exitDir = 'right';
          entryDir = 'right';
      }

      const fromY = fromRow * ROW_HEIGHT + ROW_HEIGHT / 2;
      const toY = toRow * ROW_HEIGHT + ROW_HEIGHT / 2;

      const path = generateDependencyPath(fromX, fromY, toX, toY, exitDir, entryDir);

      // Arrowhead direction depends on entry side
      const arrowSize = 5;
      let arrowPoints: string;
      if (entryDir === 'right') {
        // Arrow pointing right ▶ (entering target's start/left side)
        arrowPoints = `${toX},${toY} ${toX - arrowSize},${toY - arrowSize} ${toX - arrowSize},${toY + arrowSize}`;
      } else {
        // Arrow pointing left ◀ (entering target's end/right side)
        arrowPoints = `${toX},${toY} ${toX + arrowSize},${toY - arrowSize} ${toX + arrowSize},${toY + arrowSize}`;
      }

      edges.push({
        fromTask: fromTask.name,
        toTask: task.name,
        fromRow,
        toRow,
        fromX,
        fromY,
        toX,
        toY,
        type,
        path,
        arrowPoints,
        color: dependencyColors[type] || dependencyColors.FS,
      });
    }
  }

  return edges;
});

// Milestone connection edges.
//
// Same smooth routing as dependency lines (via generateDependencyPath) but:
// - Horizontally offset: exit point is 6px to the right of the bar edge,
//   so the milestone line's vertical segment runs parallel to (but separated
//   from) any dependency line on the same task — no overlapping paths
// - Violet color (matching the milestone diamond) instead of black
// - Arrow stops 10px before the diamond center to avoid overlap
//
interface MilestoneEdge {
  taskName: string;
  milestoneName: string;
  dotX: number;   // Origin dot position (bar edge)
  fromX: number;  // Path start (bar edge + offset)
  fromY: number;
  toX: number;
  toY: number;
  path: string;
  arrowPoints: string;
}

// Horizontal offset so milestone lines don't overlap dependency lines
const MS_LINE_X_OFFSET = 6;

const milestoneEdges = computed<MilestoneEdge[]>(() => {
  const edges: MilestoneEdge[] = [];
  const tasks = sortedTasks.value;

  // Build a name→visual-row-index map from displayRows
  const itemRowMap = new Map<string, number>();
  displayRows.value.forEach((row, idx) => {
    if (row.kind === 'item') {
      itemRowMap.set(row.item.name, idx);
    }
  });

  // Milestone lookup
  const milestoneMap = new Map<string, GanttMilestone>();
  for (const item of sortedItems.value) {
    if (!isGanttTask(item)) {
      milestoneMap.set(item.name, item as GanttMilestone);
    }
  }

  // Diamond is w-4 h-4 (16px) rotated 45° → visual tip ~10px from center
  const diamondOffset = 10;
  const arrowSize = 5;

  for (const task of tasks) {
    if (!task.milestone) continue;

    const milestone = milestoneMap.get(task.milestone);
    if (!milestone) continue;

    const taskRow = itemRowMap.get(task.name);
    const milestoneRow = itemRowMap.get(milestone.name);
    if (taskRow === undefined || milestoneRow === undefined) continue;

    const taskPos = getBarPosition(task);
    if (!taskPos) continue;

    const milestoneCx = getMilestoneCenterX(milestone);
    if (milestoneCx === null) continue;

    // Exit from right edge of task bar + horizontal offset
    const fromX = taskPos.left + taskPos.width + MS_LINE_X_OFFSET;
    const fromY = taskRow * ROW_HEIGHT + ROW_HEIGHT / 2;

    // Entry: left of diamond
    const toX = milestoneCx - diamondOffset;
    const toY = milestoneRow * ROW_HEIGHT + ROW_HEIGHT / 2;

    const path = generateDependencyPath(fromX, fromY, toX, toY);
    const arrowPoints = `${toX},${toY} ${toX - arrowSize},${toY - arrowSize} ${toX - arrowSize},${toY + arrowSize}`;

    edges.push({
      taskName: task.name,
      milestoneName: milestone.name,
      dotX: taskPos.left + taskPos.width,
      fromX,
      fromY,
      toX,
      toY,
      path,
      arrowPoints,
    });
  }

  return edges;
});

// Total height for SVG overlay — uses displayRows count (includes group headers)
const dependencySvgHeight = computed<number>(() => {
  return displayRows.value.length * ROW_HEIGHT;
});
</script>

<template>
  <div
    class="gantt-chart flex flex-col h-full bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
    <!-- Empty state -->
    <div
      v-if="tasks.length === 0"
      class="flex-1 flex items-center justify-center p-8 text-gray-500 dark:text-gray-400">
      <div class="text-center">
        <i
          class="fa-solid fa-diagram-project text-4xl text-gray-300 dark:text-gray-600 mb-3"></i>
        <p class="text-sm">{{ __('No tasks with dates to display') }}</p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
          {{ __('Add start and due dates to tasks to see them on the Gantt chart') }}
        </p>
      </div>
    </div>

    <!-- Chart - Area A / B / C Layout -->
    <template v-else>
      <!-- AREA A: Fixed Header (Top) — never scrolls vertically -->
      <div class="gantt-area-a flex-shrink-0">
        <div class="flex">
          <!-- Left column header -->
          <div class="gantt-left-header">
            <div
              class="gantt-header-height bg-gray-50 dark:bg-gray-800 flex items-center px-3 gap-2">
              <span
                class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase"
                >{{ __('Tasks') }}</span
              >
              <select v-model="groupMode"
                class="text-[10px] bg-transparent border border-gray-300 dark:border-gray-600 rounded px-1.5 py-0.5 text-gray-500 dark:text-gray-400 cursor-pointer focus:outline-none focus:ring-1 focus:ring-orga-500">
                <option value="none">{{ __('No Grouping') }}</option>
                <option value="group">{{ __('By Group') }}</option>
                <option value="status">{{ __('By Status') }}</option>
                <option value="priority">{{ __('By Priority') }}</option>
                <option value="milestone">{{ __('By Milestone') }}</option>
                <option value="assignee">{{ __('By Assignee') }}</option>
              </select>
              <label
                v-if="criticalPathTasks.length > 0"
                class="flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400 cursor-pointer select-none"
                :title="`${criticalPathTasks.length} task(s) on critical path`">
                <input
                  type="checkbox"
                  v-model="showCriticalPath"
                  class="w-3 h-3 rounded border-gray-300 dark:border-gray-600 text-red-600 focus:ring-red-500" />
                <span>{{ __('Critical Path') }}</span>
              </label>
            </div>
          </div>

          <!-- Right: calendar headers (overflow hidden, scrollLeft synced by JS) -->
          <div ref="headerScrollRef" class="gantt-header-scroll">
            <div :style="{ width: `${totalCalendarWidth}px` }">
              <div class="bg-gray-50 dark:bg-gray-800">
                <!-- Month headers -->
                <div
                  class="h-6 flex border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <div
                    v-for="month in months"
                    :key="`${month.month}-${month.year}-${month.startIndex}`"
                    :style="{ width: `${month.days * cellWidth}px` }"
                    class="month-header border-r border-gray-300 dark:border-gray-700 px-2 flex items-center bg-white dark:bg-gray-800 flex-shrink-0">
                    <span
                      class="text-xs font-semibold text-gray-700 dark:text-gray-300"
                      >{{ month.month }} {{ month.year }}</span
                    >
                  </div>
                </div>
                <!-- Week headers -->
                <div
                  class="h-5 flex border-b border-gray-200 dark:border-gray-700 bg-gray-100/50 dark:bg-gray-700/50">
                  <div
                    v-for="week in weeks"
                    :key="`W${week.weekNum}-${week.year}-${week.startIndex}`"
                    :style="{ width: `${week.days * cellWidth}px` }"
                    class="week-header border-r border-gray-200 dark:border-gray-700 px-1 flex items-center justify-center flex-shrink-0">
                    <span
                      class="text-[10px] font-medium text-gray-500 dark:text-gray-400"
                      >W{{ week.weekNum }}</span
                    >
                  </div>
                </div>
                <!-- Day headers with date and abbreviation -->
                <div class="h-9 flex">
                  <div
                    v-for="(day, index) in days"
                    :key="index"
                    :style="{ width: `${cellWidth}px` }"
                    :class="[
                      'day-header flex flex-col items-center justify-center text-xs leading-tight flex-shrink-0',
                      isWeekend(day)
                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500'
                        : 'text-gray-600 dark:text-gray-400',
                      isToday(day) ? 'today-header' : '',
                      isWeekStart(day)
                        ? 'border-l-2 border-l-gray-300 dark:border-l-gray-600'
                        : 'border-l border-l-gray-100 dark:border-l-gray-700',
                    ]">
                    <span class="day-number text-[11px]">{{
                      formatDayHeader(day)
                    }}</span>
                    <span class="day-abbr text-[9px] opacity-70">{{
                      getDayAbbr(day)
                    }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AREA B: Scrollable Content + Scrollbar (Middle) -->
      <div class="gantt-area-b flex-1 flex flex-col min-h-0">
        <!-- Scrollable grid body -->
        <div class="flex flex-1 min-h-0">
          <!-- Left task name column -->
          <div class="gantt-left-body-wrapper">
            <div
              ref="leftBodyRef"
              class="gantt-left-body"
              @scroll="syncVerticalScroll">
              <template
                v-for="(row, rowIndex) in displayRows"
                :key="`name-${row.kind === 'item' ? row.item.name : row.key}`">
                <!-- Group header row -->
                <div
                  v-if="row.kind === 'group-header'"
                  class="h-10 px-3 flex items-center gap-2 border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 cursor-pointer select-none"
                  @click="toggleGroup(row.key)">
                  <i
                    :class="collapsedGroups.has(row.key) ? 'fa-solid fa-chevron-right' : 'fa-solid fa-chevron-down'"
                    class="text-[10px] text-gray-400 dark:text-gray-500 w-3"></i>
                  <span class="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">{{ row.label }}</span>
                  <span class="text-[10px] text-gray-400 dark:text-gray-500">({{ row.count }})</span>
                </div>
                <!-- Task row -->
                <div
                  v-else-if="isGanttTask(row.item)"
                  :draggable="groupMode === 'none'"
                  @dragstart="handleRowDragStart($event, row.item, rowIndex)"
                  @dragend="handleDragEnd"
                  @dragover.prevent="handleRowDragOver($event, rowIndex)"
                  @dragleave="handleDragLeave"
                  @drop="handleRowDrop($event, rowIndex)"
                  @click="handleItemClick(row.item)"
                  :class="[
                    'gantt-task-row h-10 px-3 flex items-center gap-2 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 cursor-pointer select-none overflow-hidden',
                    selectedTaskId === row.item.name
                      ? 'bg-orga-50 dark:bg-orga-900/20'
                      : 'hover:bg-gray-50/50 dark:hover:bg-gray-800/50',
                    isValidDropTarget(rowIndex) ? 'drag-over' : '',
                    isTaskBeingDragged(row.item as GanttTask) &&
                    draggingTask?.dragType === 'reorder'
                      ? 'dragging'
                      : '',
                    isJustReordered(row.item as GanttTask) ? 'just-reordered' : '',
                  ]">
                  <i
                    v-if="groupMode === 'none'"
                    class="fa-solid fa-grip-vertical text-[10px] text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 cursor-grab shrink-0"></i>
                  <span
                    :class="[
                      'w-2 h-2 rounded-full shrink-0',
                      statusColors[(row.item as GanttTask).status],
                    ]"></span>
                  <span
                    class="text-sm text-gray-800 dark:text-gray-200 truncate min-w-0 flex-1"
                    :title="row.item.subject"
                    >{{ row.item.subject }}</span
                  >
                </div>

                <!-- Milestone row (uses same unified drag system as tasks) -->
                <div
                  v-else
                  :draggable="groupMode === 'none'"
                  @dragstart="handleRowDragStart($event, row.item, rowIndex)"
                  @dragend="handleDragEnd"
                  @dragover.prevent="handleRowDragOver($event, rowIndex)"
                  @dragleave="handleDragLeave"
                  @drop="handleRowDrop($event, rowIndex)"
                  @click="handleItemClick(row.item)"
                  :class="[
                    'gantt-task-row h-10 px-3 flex items-center gap-2 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 cursor-pointer select-none transition-all duration-150',
                    selectedTaskId === row.item.name
                      ? 'bg-indigo-100 dark:bg-indigo-900/30'
                      : 'hover:bg-indigo-50 dark:hover:bg-indigo-900/20',
                    isValidDropTarget(rowIndex) ? 'drag-over' : '',
                    draggingTask?.taskId === row.item.name &&
                    draggingTask?.dragType === 'reorder'
                      ? 'dragging'
                      : '',
                  ]">
                  <i
                    v-if="groupMode === 'none'"
                    data-drag-handle
                    class="fa-solid fa-grip-vertical text-[10px] text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 cursor-grab"></i>
                  <span
                    class="w-2 h-2 rotate-45 shrink-0"
                    :class="
                      milestoneStatusColors[(row.item as GanttMilestone).status]
                    "></span>
                  <i
                    class="fa-solid fa-flag text-[10px] text-indigo-400 dark:text-indigo-300"></i>
                  <span
                    class="text-sm text-gray-800 dark:text-gray-200 truncate flex-1"
                    >{{ row.item.subject }}</span
                  >
                </div>
              </template>
            </div>
          </div>

          <!-- Right: scrollable grid (scrolls both X and Y) -->
          <div
            ref="scrollContainerRef"
            class="gantt-body-scroll"
            @scroll="onContainerScroll">
            <div class="relative" :style="{ width: `${totalCalendarWidth}px` }">
              <!-- Unified timeline rows (tasks and milestones interleaved) -->
              <template
                v-for="(row, rowIndex) in displayRows"
                :key="`timeline-${row.kind === 'item' ? row.item.name : row.key}`">
                <!-- Group header timeline row (empty row with grid background) -->
                <div
                  v-if="row.kind === 'group-header'"
                  class="h-10 relative border-b border-gray-200 dark:border-gray-600 bg-gray-50/80 dark:bg-gray-800/60"
                  @click="toggleGroup(row.key)">
                  <div class="absolute inset-0 flex pointer-events-none">
                    <div
                      v-for="(day, index) in days"
                      :key="index"
                      :style="{ width: `${cellWidth}px` }"
                      :class="[
                        'h-full grid-cell flex-shrink-0',
                        isWeekend(day)
                          ? 'bg-gray-100/60 dark:bg-gray-800/40'
                          : '',
                        isWeekStart(day)
                          ? 'border-l-2 border-l-gray-300 dark:border-l-gray-600'
                          : 'border-l border-l-gray-100 dark:border-l-gray-800',
                      ]"></div>
                  </div>
                  <div
                    v-if="todayIndex >= 0"
                    class="today-marker absolute top-0 bottom-0 w-0.5 bg-sky-500 dark:bg-sky-400 z-10 pointer-events-none"
                    :style="{
                      left: `${todayIndex * cellWidth + cellWidth / 2}px`,
                    }"></div>
                </div>
                <!-- Task timeline row -->
                <div
                  v-else-if="isGanttTask(row.item)"
                  @dragover.prevent="handleTimelineDragOver($event, rowIndex)"
                  @dragleave="handleDragLeave"
                  @drop="handleRowDrop($event, rowIndex)"
                  :class="[
                    'gantt-timeline-row h-10 relative',
                    'border-b border-gray-100 dark:border-gray-700',
                    selectedTaskId === row.item.name
                      ? 'bg-orga-50 dark:bg-orga-900/20'
                      : 'hover:bg-gray-50/50 dark:hover:bg-gray-800/50',
                    isValidDropTarget(rowIndex) ? 'drag-over' : '',
                    draggingTask?.taskId === row.item.name &&
                    draggingTask?.dragType === 'reorder'
                      ? 'dragging'
                      : '',
                    isJustReordered(row.item as GanttTask) ? 'just-reordered' : '',
                  ]">
                  <!-- Grid background with visual hierarchy -->
                  <div class="absolute inset-0 flex pointer-events-none">
                    <div
                      v-for="(day, index) in days"
                      :key="index"
                      :style="{ width: `${cellWidth}px` }"
                      :class="[
                        'h-full grid-cell flex-shrink-0',
                        isWeekend(day)
                          ? 'bg-gray-100/60 dark:bg-gray-800/40'
                          : '',
                        isToday(day) ? 'bg-sky-50/50 dark:bg-sky-900/20' : '',
                        isWeekStart(day)
                          ? 'border-l-2 border-l-gray-300 dark:border-l-gray-600'
                          : 'border-l border-l-gray-100 dark:border-l-gray-800',
                      ]"></div>
                  </div>

                  <!-- Today marker line -->
                  <div
                    v-if="todayIndex >= 0"
                    class="today-marker absolute top-0 bottom-0 w-0.5 bg-sky-500 dark:bg-sky-400 z-10 pointer-events-none"
                    :style="{
                      left: `${todayIndex * cellWidth + cellWidth / 2}px`,
                    }"></div>

                  <!-- Task bar (draggable for date changes) -->
                  <div
                    v-if="(row.item as GanttTask).start_date"
                    :draggable="(row.item as GanttTask).task_scheduling_type !== 'Hammock'"
                    @click.stop="handleItemClick(row.item)"
                    @dragstart.stop="
                      (row.item as GanttTask).task_scheduling_type !== 'Hammock' &&
                      handleBarDragStart($event, row.item as GanttTask, rowIndex)
                    "
                    @dragend="handleDragEnd"
                    @dragover.stop
                    @drop.stop="handleRowDrop($event, rowIndex)"
                    :style="getTaskBarStyle(row.item as GanttTask)"
                    :class="[
                      'gantt-bar absolute top-1.5 h-7 z-20',
                      'flex items-center px-2 overflow-hidden gap-1',
                      'select-none',
                      (row.item as GanttTask).task_scheduling_type === 'Hammock'
                        ? 'gantt-bar-hammock'
                        : (row.item as GanttTask).task_scheduling_type === 'Buffer'
                          ? 'gantt-bar-buffer'
                          : statusColors[(row.item as GanttTask).status],
                      (row.item as GanttTask).task_scheduling_type !== 'Hammock' && (row.item as GanttTask).task_scheduling_type !== 'Buffer'
                        ? priorityBorders[(row.item as GanttTask).priority]
                        : '',
                      (row.item as GanttTask).task_scheduling_type !== 'Hammock' ? 'cursor-grab' : 'cursor-default',
                      selectedTaskId === row.item.name
                        ? 'ring-2 ring-orga-500 ring-offset-1'
                        : '',
                      isTaskBeingDragged(row.item as GanttTask) &&
                      draggingTask?.dragType === 'dates'
                        ? 'opacity-50 shadow-lg'
                        : '',
                      isOnCriticalPath(row.item.name) && 'gantt-bar-critical',
                      showCriticalPath && criticalPathTasks.length > 0 && !isOnCriticalPath(row.item.name) && 'opacity-40',
                    ]"
                    :title="(row.item as GanttTask).task_scheduling_type === 'Hammock'
                      ? `${row.item.subject} (Hammock — auto-calculated)\n${(row.item as GanttTask).start_date} - ${(row.item as GanttTask).due_date || (row.item as GanttTask).start_date}\nDuration: ${getTaskDuration(row.item as GanttTask)} day(s)`
                      : (row.item as GanttTask).task_scheduling_type === 'Buffer'
                        ? `${row.item.subject} (Buffer)\n${(row.item as GanttTask).start_date} - ${(row.item as GanttTask).due_date || (row.item as GanttTask).start_date}\nBuffer: ${(row.item as GanttTask).buffer_size || 0} days, ${Math.round((row.item as GanttTask).buffer_consumed || 0)}% consumed`
                        : `${row.item.subject}\n${(row.item as GanttTask).start_date} - ${(row.item as GanttTask).due_date || (row.item as GanttTask).start_date}\nDuration: ${getTaskDuration(row.item as GanttTask)} day(s)${(row.item as GanttTask).depends_on_group ? `\nGroup dependency: ${(row.item as GanttTask).depends_on_group}${(row.item as GanttTask).is_blocked ? ' (BLOCKED)' : ' (unblocked)'}` : ''}\n\nDrag bar left/right to change dates\nDrag row handle to reorder`">
                    <!-- Hammock icon -->
                    <i
                      v-if="(row.item as GanttTask).task_scheduling_type === 'Hammock'"
                      class="fa-solid fa-arrows-left-right text-[9px] text-indigo-500 dark:text-indigo-400 shrink-0"
                    ></i>
                    <!-- Buffer icon -->
                    <i
                      v-else-if="(row.item as GanttTask).task_scheduling_type === 'Buffer'"
                      class="fa-solid fa-shield-halved text-[9px] text-amber-700 dark:text-amber-400 shrink-0"
                    ></i>
                    <!-- Blocked by group icon -->
                    <i
                      v-else-if="(row.item as GanttTask).depends_on_group && (row.item as GanttTask).is_blocked"
                      class="fa-solid fa-lock text-[9px] text-amber-600 dark:text-amber-400 shrink-0"
                      :title="`Blocked by group: ${(row.item as GanttTask).depends_on_group}`"
                    ></i>
                    <span
                      class="gantt-bar-text text-xs truncate font-medium flex-1">
                      {{ row.item.subject }}
                    </span>
                    <span
                      v-if="getTaskDuration(row.item as GanttTask) > 1"
                      class="gantt-bar-duration text-[10px] px-1 rounded shrink-0">
                      {{ getTaskDuration(row.item as GanttTask) }}d
                    </span>
                    <!-- Progress bar (regular tasks) -->
                    <div
                      v-if="(row.item as GanttTask).task_scheduling_type !== 'Buffer' && ((row.item as GanttTask).progress ?? 0) > 0"
                      class="gantt-bar-progress absolute bottom-0 left-0 h-1 rounded-b"
                      :style="{
                        width: `${(row.item as GanttTask).progress ?? 0}%`,
                      }"></div>
                    <!-- Buffer consumption indicator -->
                    <div
                      v-if="(row.item as GanttTask).task_scheduling_type === 'Buffer' && ((row.item as GanttTask).buffer_consumed ?? 0) > 0"
                      class="gantt-buffer-consumption"
                      :class="[
                        ((row.item as GanttTask).buffer_consumed ?? 0) <= 33 ? 'buffer-healthy'
                          : ((row.item as GanttTask).buffer_consumed ?? 0) <= 66 ? 'buffer-caution'
                          : 'buffer-critical'
                      ]"
                      :style="{
                        width: `${Math.min(100, (row.item as GanttTask).buffer_consumed ?? 0)}%`,
                      }"></div>
                    <!-- Dependency creation handle (right edge, visible on hover) -->
                    <div
                      v-if="(row.item as GanttTask).task_scheduling_type !== 'Hammock'"
                      class="dep-create-handle"
                      :class="depDragTarget === row.item.name ? 'dep-target-active' : ''"
                      @mousedown.stop="startDepDrag(row.item.name, $event)"
                      :title="__('Drag to create dependency')">
                      <div class="dep-handle-dot"></div>
                    </div>
                  </div>
                  <!-- Assignee avatar (positioned after bar's right edge) -->
                  <UserAvatar
                    v-if="(row.item as GanttTask).start_date && (row.item as GanttTask).assigned_to_name"
                    :name="(row.item as GanttTask).assigned_to_name"
                    :image="(row.item as GanttTask).assigned_to_image"
                    size="xs"
                    color="orga"
                    class="!w-5 !h-5 !text-[9px] absolute top-1/2 -translate-y-1/2 z-30"
                    :style="getAvatarStyle(row.item as GanttTask)"
                    :title="(row.item as GanttTask).assigned_to_name"
                  />

                  <!-- No dates indicator -->
                  <div
                    v-if="!(row.item as GanttTask).start_date"
                    class="absolute left-2 top-1.5 h-7 flex items-center text-xs text-gray-400 dark:text-gray-500">
                    <i class="fa-solid fa-calendar-xmark mr-1"></i>
                    {{ __('No dates set') }}
                  </div>
                </div>

                <!-- Milestone timeline row (accepts drops for unified reorder) -->
                <div
                  v-else
                  @click="handleItemClick(row.item)"
                  @dragover.prevent="handleTimelineDragOver($event, rowIndex)"
                  @dragleave="handleDragLeave"
                  @drop="handleRowDrop($event, rowIndex)"
                  :class="[
                    'gantt-timeline-row h-10 relative border-b border-gray-100 dark:border-gray-700 bg-indigo-50/30 dark:bg-indigo-950/20 cursor-pointer transition-colors',
                    selectedTaskId === row.item.name
                      ? 'bg-indigo-100 dark:bg-indigo-900/30'
                      : 'hover:bg-indigo-50 dark:hover:bg-indigo-900/20',
                    isValidDropTarget(rowIndex) ? 'drag-over' : '',
                    draggingTask?.taskId === row.item.name &&
                    draggingTask?.dragType === 'reorder'
                      ? 'dragging'
                      : '',
                  ]">
                  <!-- Grid background for milestone rows -->
                  <div class="absolute inset-0 flex pointer-events-none">
                    <div
                      v-for="(day, index) in days"
                      :key="index"
                      :style="{ width: `${cellWidth}px` }"
                      :class="[
                        'h-full grid-cell flex-shrink-0',
                        isWeekend(day)
                          ? 'bg-gray-100/60 dark:bg-gray-800/40'
                          : '',
                        isToday(day) ? 'bg-sky-50/50 dark:bg-sky-900/20' : '',
                        isWeekStart(day)
                          ? 'border-l-2 border-l-gray-300 dark:border-l-gray-600'
                          : 'border-l border-l-gray-100 dark:border-l-gray-800',
                      ]"></div>
                  </div>

                  <!-- Today marker line -->
                  <div
                    v-if="todayIndex >= 0"
                    class="today-marker absolute top-0 bottom-0 w-0.5 bg-sky-500 dark:bg-sky-400 z-10 pointer-events-none"
                    :style="{
                      left: `${todayIndex * cellWidth + cellWidth / 2}px`,
                    }"></div>

                  <!-- Diamond marker (draggable via mousedown) -->
                  <div
                    v-if="(row.item as GanttMilestone).due_date"
                    :style="
                      getMilestoneDragPreviewPosition(row.item as GanttMilestone) ||
                      getMilestonePosition(row.item as GanttMilestone)
                    "
                    @mousedown="
                      handleMilestoneDragStart($event, row.item as GanttMilestone)
                    "
                    :class="[
                      'absolute top-1/2 -translate-y-1/2 w-4 h-4 rotate-45 cursor-grab z-20',
                      isMilestoneBeingDragged(row.item as GanttMilestone)
                        ? 'opacity-70 scale-110 cursor-grabbing'
                        : 'transition-all',
                      milestoneStatusColors[(row.item as GanttMilestone).status],
                      selectedTaskId === row.item.name
                        ? 'ring-2 ring-orga-500 ring-offset-2 dark:ring-offset-gray-900'
                        : 'hover:scale-110',
                    ]"
                    :title="`${row.item.subject}\nDue: ${(row.item as GanttMilestone).due_date}\nStatus: ${(row.item as GanttMilestone).status}\n\nDrag to change date`"></div>

                  <!-- Ghost preview diamond during drag -->
                  <div
                    v-if="
                      isMilestoneBeingDragged(row.item as GanttMilestone) &&
                      milestoneDragDaysDelta !== 0
                    "
                    :style="getMilestonePosition(row.item as GanttMilestone)"
                    :class="[
                      'absolute top-1/2 -translate-y-1/2 w-4 h-4 rotate-45 z-15 pointer-events-none opacity-30 border-2 border-dashed',
                      milestoneStatusColors[(row.item as GanttMilestone).status],
                    ]"></div>

                  <!-- Milestone label (follows dragged position) -->
                  <div
                    v-if="(row.item as GanttMilestone).due_date"
                    :style="{
                      left: `${parseInt((getMilestoneDragPreviewPosition(row.item as GanttMilestone) || getMilestonePosition(row.item as GanttMilestone)).left || '0') + 22}px`,
                    }"
                    class="absolute top-1/2 -translate-y-1/2 text-xs text-indigo-600 dark:text-indigo-300 font-medium whitespace-nowrap pointer-events-none">
                    {{ row.item.subject }}
                    <span
                      v-if="
                        isMilestoneBeingDragged(row.item as GanttMilestone) &&
                        milestoneDragDaysDelta !== 0
                      "
                      class="text-[10px] ml-1 text-indigo-400">
                      ({{ milestoneDragDaysDelta > 0 ? '+' : ''
                      }}{{ milestoneDragDaysDelta }}d)
                    </span>
                  </div>
                </div>
              </template>

              <!-- Dependency creation drag line (temporary) -->
              <svg
                v-if="depDragLine"
                class="dependency-arrows"
                :width="totalCalendarWidth"
                :height="dependencySvgHeight"
                style="z-index: 30; pointer-events: none;">
                <line
                  :x1="depDragLine.x1"
                  :y1="depDragLine.y1"
                  :x2="depDragLine.x2"
                  :y2="depDragLine.y2"
                  :stroke="depDragTarget ? '#16a34a' : '#6b7280'"
                  stroke-width="2"
                  stroke-dasharray="6,4"
                  stroke-linecap="round" />
                <circle
                  :cx="depDragLine.x1"
                  :cy="depDragLine.y1"
                  r="4"
                  :fill="depDragTarget ? '#16a34a' : '#6b7280'" />
                <circle
                  v-if="depDragTarget"
                  :cx="depDragLine.x2"
                  :cy="depDragLine.y2"
                  r="5"
                  fill="#16a34a"
                  opacity="0.6" />
              </svg>

              <!-- Dependency arrows SVG overlay -->
              <svg
                v-if="showDependencies && dependencyEdges.length > 0"
                class="dependency-arrows"
                :width="totalCalendarWidth"
                :height="dependencySvgHeight">
                <g
                  v-for="edge in dependencyEdges"
                  :key="`${edge.fromTask}-${edge.toTask}`"
                  :opacity="showCriticalPath && criticalPathTasks.length > 0
                    ? (isOnCriticalPath(edge.fromTask) && isOnCriticalPath(edge.toTask) ? 1 : 0.15)
                    : undefined">
                  <!-- Origin dot at connection start -->
                  <circle
                    :cx="edge.fromX"
                    :cy="edge.fromY"
                    :r="showCriticalPath && isOnCriticalPath(edge.fromTask) && isOnCriticalPath(edge.toTask) ? 4 : 3"
                    :fill="showCriticalPath && isOnCriticalPath(edge.fromTask) && isOnCriticalPath(edge.toTask) ? '#dc2626' : edge.color"
                    opacity="0.6" />
                  <!-- Connection line with rounded corners -->
                  <path
                    :d="edge.path"
                    :stroke="showCriticalPath && isOnCriticalPath(edge.fromTask) && isOnCriticalPath(edge.toTask) ? '#dc2626' : edge.color"
                    :stroke-width="showCriticalPath && isOnCriticalPath(edge.fromTask) && isOnCriticalPath(edge.toTask) ? 2.5 : 1.5"
                    fill="none"
                    stroke-linecap="round"
                    opacity="0.5" />
                  <!-- Arrowhead -->
                  <polygon
                    :points="edge.arrowPoints"
                    :fill="showCriticalPath && isOnCriticalPath(edge.fromTask) && isOnCriticalPath(edge.toTask) ? '#dc2626' : edge.color"
                    opacity="0.6" />
                </g>
              </svg>

              <!-- Milestone connection lines SVG overlay -->
              <svg
                v-if="milestoneEdges.length > 0"
                class="milestone-connections"
                :width="totalCalendarWidth"
                :height="dependencySvgHeight">
                <g
                  v-for="edge in milestoneEdges"
                  :key="`ms-${edge.taskName}-${edge.milestoneName}`">
                  <!-- Origin dot stuck to task bar edge -->
                  <circle
                    :cx="edge.dotX"
                    :cy="edge.fromY"
                    r="3"
                    fill="#7c3aed"
                    opacity="0.6" />
                  <!-- Smooth path to milestone -->
                  <path
                    :d="edge.path"
                    stroke="#7c3aed"
                    :stroke-width="1.5"
                    fill="none"
                    stroke-linecap="round"
                    opacity="0.5" />
                  <!-- Arrowhead at milestone entry -->
                  <polygon
                    :points="edge.arrowPoints"
                    fill="#7c3aed"
                    opacity="0.6" />
                </g>
              </svg>
            </div>
          </div>
        </div>

        <!-- Scrubber scrollbar — inside Area B footer, always visible -->
        <div
          v-show="thumbVisible"
          ref="headerScrollbarRef"
          class="gantt-header-scrollbar flex-shrink-0"
          @mousedown="handleTrackClick">
          <!-- Progress fill showing scroll position -->
          <div
            class="scrollbar-progress"
            :style="{ width: scrollProgress + '%' }"></div>
          <!-- Velocity scrubber thumb -->
          <div
            :style="thumbStyle"
            @mousedown.stop="handleThumbMouseDown"
            @mouseenter="thumbHovered = true"
            @mouseleave="thumbHovered = false">
            <!-- Velocity zone sheet (visible during drag) -->
            <div v-if="thumbDragging" class="thumb-velocity-sheet">
              <div
                class="velocity-zone zone-2x-left"
                :class="{ active: activeZone === 'zone-2x-left' }">
                <span class="velocity-label">&laquo;</span>
              </div>
              <div
                class="velocity-zone zone-1x-left"
                :class="{ active: activeZone === 'zone-1x-left' }">
                <span class="velocity-label">&lsaquo;</span>
              </div>
              <div
                class="velocity-zone zone-center"
                :class="{ active: activeZone === 'zone-center' }">
                <span class="velocity-label">&middot;</span>
              </div>
              <div
                class="velocity-zone zone-1x-right"
                :class="{ active: activeZone === 'zone-1x-right' }">
                <span class="velocity-label">&rsaquo;</span>
              </div>
              <div
                class="velocity-zone zone-2x-right"
                :class="{ active: activeZone === 'zone-2x-right' }">
                <span class="velocity-label">&raquo;</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AREA C: Fixed Legend Footer (Bottom) — never scrolls -->
      <div
        class="flex-shrink-0 h-8 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
        <span class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded bg-gray-400"></span> {{ __('Open') }}
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded bg-blue-500"></span> {{ __('Working') }}
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded bg-purple-500"></span> {{ __('Review') }}
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-3 h-3 rounded bg-green-500"></span> {{ __('Completed') }}
        </span>
        <span
          class="border-l border-gray-300 dark:border-gray-600 pl-3 flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rotate-45 bg-indigo-500"></span> {{ __('Milestone') }}
        </span>
        <span class="ml-auto flex items-center gap-1.5">
          <span class="w-0.5 h-4 bg-sky-500 dark:bg-sky-400 shadow-sm"></span>
          {{ __('Today') }}
        </span>
        <span class="flex items-center gap-1.5">
          <span
            class="w-3 h-3 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-sm"></span>
          {{ __('Weekend') }}
        </span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.gantt-chart {
  min-height: 400px;
}

/* ========== AREA A / B / C LAYOUT ========== */
/*
 * ┌──────────────────────────────────────┐
 * │  AREA A: Fixed Header (flex-shrink-0)│  ← never scrolls
 * ├──────────────────────────────────────┤
 * │  AREA B: Scrollable Content          │
 * │    ├─ grid body (flex-1, scrolls)    │
 * │    └─ scrubber (flex-shrink-0)       │
 * ├──────────────────────────────────────┤
 * │  AREA C: Fixed Legend (flex-shrink-0)│  ← never scrolls
 * └──────────────────────────────────────┘
 */

/* AREA A: Fixed header — never scrolls vertically */
.gantt-area-a {
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .gantt-area-a {
  border-bottom-color: #374151;
}

/* Left column header in Area A */
.gantt-left-header {
  width: 16rem;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
}

:global(.dark) .gantt-left-header {
  border-right-color: #374151;
}

/* Right header — overflow hidden, scrollLeft synced by JS from body scroll */
.gantt-header-scroll {
  flex: 1;
  overflow: hidden;
}

/* AREA B: Scrollable content + scrollbar footer */
.gantt-area-b {
  overflow: hidden;
}

/* Left body wrapper in Area B */
.gantt-left-body-wrapper {
  width: 16rem;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
  overflow: hidden;
}

:global(.dark) .gantt-left-body-wrapper {
  border-right-color: #374151;
}

/* Left body scrolls vertically in sync with grid */
.gantt-left-body {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
}

/* Hide scrollbar on left body — grid scrollbar handles vertical scroll */
.gantt-left-body::-webkit-scrollbar {
  width: 0;
  display: none;
}

/* Right body — scrolls both X and Y, native horizontal scrollbar hidden */
.gantt-body-scroll {
  flex: 1;
  overflow-x: scroll;
  overflow-y: auto;
}

/* Hide native horizontal scrollbar — custom scrubber handles it */
.gantt-body-scroll::-webkit-scrollbar:horizontal {
  height: 0;
  display: none;
}

/* Vertical scrollbar styling */
.gantt-body-scroll::-webkit-scrollbar {
  width: 8px;
}

.gantt-body-scroll::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.gantt-body-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

:global(.dark) .gantt-body-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

:global(.dark) .gantt-body-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Scrollbar track — Area B footer, always visible when content is scrollable */
.gantt-header-scrollbar {
  position: relative;
  overflow: visible;
  height: 24px;
  background: #f3f4f6;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
  cursor: pointer;
  display: flex !important;
  align-items: center;
}

:global(.dark) .gantt-header-scrollbar {
  background: rgb(31, 41, 55);
  border-top-color: rgb(55, 65, 81);
}

/* Progress fill — shows current scroll position */
.scrollbar-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(
    90deg,
    rgba(59, 130, 246, 0.2),
    rgba(96, 165, 250, 0.3)
  );
  transition: width 0.1s ease-out;
  pointer-events: none;
}

:global(.dark) .scrollbar-progress {
  background: linear-gradient(
    90deg,
    rgba(59, 130, 246, 0.1),
    rgba(96, 165, 250, 0.15)
  );
}

/* Velocity sheet inside thumb — 5 zones */
.thumb-velocity-sheet {
  display: flex;
  width: 100%;
  height: 100%;
}

.velocity-zone {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #9ca3af;
  background: transparent;
  transition: background-color 0.1s ease;
  user-select: none;
}

.velocity-zone:not(:last-child) {
  border-right: 1px solid rgba(107, 114, 128, 0.2);
}

.velocity-zone.active {
  color: #fff;
}

.zone-2x-left.active {
  background: rgba(239, 68, 68, 0.5);
}

.zone-1x-left.active {
  background: rgba(251, 146, 60, 0.4);
}

.zone-center.active {
  background: rgba(59, 130, 246, 0.3);
}

.zone-1x-right.active {
  background: rgba(34, 197, 94, 0.4);
}

.zone-2x-right.active {
  background: rgba(34, 197, 94, 0.5);
}

.velocity-label {
  font-size: 11px;
  line-height: 1;
}

/* Header height: Month (24px) + Week (20px) + Day (36px) = 80px */
.gantt-header-height {
  height: 80px;
}

/* Month header styling - uses Tailwind bg-white/dark:bg-gray-800 from template */

/* Week header styling - inherits bg from parent container (bg-gray-100/50 / dark:bg-gray-700/50) */

/* Day header styling */
.day-header {
  transition: background-color 0.15s ease;
}

.day-header.today-header {
  background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 100%);
  border-left: 2px solid #0284c7 !important;
  border-right: 1px solid #7dd3fc;
  color: #0369a1;
  font-weight: 600;
}

:global(.dark) .day-header.today-header {
  background: linear-gradient(
    180deg,
    rgba(14, 116, 144, 0.3) 0%,
    rgba(8, 145, 178, 0.2) 100%
  );
  border-left: 2px solid #0ea5e9 !important;
  border-right: 1px solid rgba(56, 189, 248, 0.3);
  color: #7dd3fc;
}

/* Grid cell styling for visual hierarchy */
.grid-cell {
  transition: background-color 0.1s ease;
}

/* Today marker styling - calm blue reference */
.today-marker {
  box-shadow: 0 0 8px rgba(14, 165, 233, 0.4);
}

:global(.dark) .today-marker {
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

/* ========== DEPENDENCY ARROWS ========== */

.dependency-arrows {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 5;
  overflow: visible;
}

/* ========== MILESTONE CONNECTION LINES ========== */

.milestone-connections {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 4;
  overflow: visible;
}

/* ========== GANTT BAR COLORS - Pastel & Minimalistic ========== */
/* Background color = STATUS, Left border = PRIORITY */

/* Base bar styling */
.gantt-bar-open,
.gantt-bar-in-progress,
.gantt-bar-review,
.gantt-bar-completed {
  border-radius: 4px;
  border-left: 4px solid #d97706; /* Default border, will be overridden by priority */
  transition: all 0.2s ease-out;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

:global(.dark) .gantt-bar-open,
:global(.dark) .gantt-bar-in-progress,
:global(.dark) .gantt-bar-review,
:global(.dark) .gantt-bar-completed {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  border-left-color: #f59e0b;
}

/* Open - Soft Blue background */
.gantt-bar-open {
  background: #d1e7f7;
}

.gantt-bar-open:hover {
  background: #bcdcf0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

:global(.dark) .gantt-bar-open {
  background: rgba(59, 130, 246, 0.3);
}

:global(.dark) .gantt-bar-open:hover {
  background: rgba(59, 130, 246, 0.4);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

/* In Progress - Soft Amber background */
.gantt-bar-in-progress {
  background: #fde8c8;
}

.gantt-bar-in-progress:hover {
  background: #fcd8a0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

:global(.dark) .gantt-bar-in-progress {
  background: rgba(245, 158, 11, 0.3);
}

:global(.dark) .gantt-bar-in-progress:hover {
  background: rgba(245, 158, 11, 0.4);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
}

/* Review - Soft Purple background */
.gantt-bar-review {
  background: #e9d5ff;
}

.gantt-bar-review:hover {
  background: #ddbbe8;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

:global(.dark) .gantt-bar-review {
  background: rgba(168, 85, 247, 0.3);
}

:global(.dark) .gantt-bar-review:hover {
  background: rgba(168, 85, 247, 0.4);
  box-shadow: 0 4px 12px rgba(168, 85, 247, 0.25);
}

/* Completed - Soft Teal/Green background */
.gantt-bar-completed {
  background: #ccfbf1;
  opacity: 0.85;
}

.gantt-bar-completed:hover {
  background: #a0f0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
  opacity: 1;
}

:global(.dark) .gantt-bar-completed {
  background: rgba(16, 185, 129, 0.3);
  opacity: 0.85;
}

:global(.dark) .gantt-bar-completed:hover {
  background: rgba(16, 185, 129, 0.4);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
  opacity: 1;
}

/* ========== GANTT BAR TEXT & ELEMENTS ========== */

/* Bar text - dark gray for readability on pastel backgrounds */
.gantt-bar-text {
  color: #1f2937;
  text-shadow: none;
}

:global(.dark) .gantt-bar-text {
  color: #f3f4f6;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Duration badge - subtle styling */
.gantt-bar-duration {
  color: #6b7280;
  background: rgba(0, 0, 0, 0.08);
}

:global(.dark) .gantt-bar-duration {
  color: #d1d5db;
  background: rgba(255, 255, 255, 0.15);
}

/* Progress indicator - subtle */
.gantt-bar-progress {
  background: rgba(0, 0, 0, 0.15);
}

:global(.dark) .gantt-bar-progress {
  background: rgba(255, 255, 255, 0.2);
}

/* ========== PRIORITY INDICATORS (Left Border) ========== */

/* Low Priority - Dark brown border */
.priority-low {
  border-left-color: #92400e !important;
}

/* Medium Priority - Orange border (default) */
.priority-medium {
  border-left-color: #d97706 !important;
}

/* High Priority - Dark orange border */
.priority-high {
  border-left-color: #ea580c !important;
}

/* Urgent Priority - Red border, slightly thicker */
.priority-urgent {
  border-left-color: #dc2626 !important;
  border-left-width: 5px !important;
}

.priority-urgent:hover {
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2) !important;
}

/* Dark mode priority - brighter borders for visibility */
:global(.dark) .priority-low {
  border-left-color: #d97706 !important;
}

:global(.dark) .priority-medium {
  border-left-color: #f59e0b !important;
}

:global(.dark) .priority-high {
  border-left-color: #f97316 !important;
}

:global(.dark) .priority-urgent {
  border-left-color: #ef4444 !important;
}

:global(.dark) .priority-urgent:hover {
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
}

/* ========== HAMMOCK TASK STYLING ========== */

.gantt-bar-hammock {
  background: repeating-linear-gradient(
    45deg,
    #e0e7ff,
    #e0e7ff 4px,
    #c7d2fe 4px,
    #c7d2fe 8px
  ) !important;
  border-left-style: dashed !important;
  cursor: default !important;
}

:global(.dark) .gantt-bar-hammock {
  background: repeating-linear-gradient(
    45deg,
    rgba(99, 102, 241, 0.25),
    rgba(99, 102, 241, 0.25) 4px,
    rgba(99, 102, 241, 0.4) 4px,
    rgba(99, 102, 241, 0.4) 8px
  ) !important;
}

/* ========== BUFFER TASK STYLING ========== */

.gantt-bar-buffer {
  background: repeating-linear-gradient(
    -45deg,
    #fef3c7,
    #fef3c7 4px,
    #fde68a 4px,
    #fde68a 8px
  ) !important;
  border-left-color: #92400e !important;
  border-left-style: dotted !important;
}

:global(.dark) .gantt-bar-buffer {
  background: repeating-linear-gradient(
    -45deg,
    rgba(251, 191, 36, 0.2),
    rgba(251, 191, 36, 0.2) 4px,
    rgba(251, 191, 36, 0.35) 4px,
    rgba(251, 191, 36, 0.35) 8px
  ) !important;
  border-left-color: #f59e0b !important;
}

/* Buffer consumption indicator inside bar */
.gantt-buffer-consumption {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  border-radius: 0 0 4px 4px;
  transition: width 0.3s ease;
}

.buffer-healthy { background: #16a34a; }
.buffer-caution { background: #ca8a04; }
.buffer-critical { background: #dc2626; }

/* ========== DEPENDENCY CREATION HANDLE ========== */

.dep-create-handle {
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  cursor: crosshair;
  opacity: 0;
  transition: opacity 0.15s ease;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gantt-bar:hover .dep-create-handle {
  opacity: 1;
}

.dep-handle-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
  border: 1.5px solid white;
  transition: all 0.15s ease;
}

.dep-create-handle:hover .dep-handle-dot {
  background: #16a34a;
  transform: scale(1.3);
}

.dep-target-active {
  opacity: 1 !important;
}

.dep-target-active .dep-handle-dot {
  background: #16a34a;
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.3);
}

:global(.dark) .dep-handle-dot {
  border-color: #374151;
}

/* ========== CRITICAL PATH HIGHLIGHTING ========== */

.gantt-bar-critical {
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.4), 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  z-index: 25 !important;
}

.gantt-bar-critical:hover {
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.6), 0 4px 12px rgba(220, 38, 38, 0.2) !important;
}

:global(.dark) .gantt-bar-critical {
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.5), 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}

:global(.dark) .gantt-bar-critical:hover {
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.7), 0 4px 12px rgba(239, 68, 68, 0.3) !important;
}

/* ========== TASK ROW STYLING ========== */

.gantt-task-row {
  min-width: fit-content;
  transition: all 0.15s ease;
}

/* Dragging cursor styles */
.cursor-grab {
  cursor: grab;
}

.cursor-grab:active {
  cursor: grabbing;
}

/* ========== DRAG VISUAL STATES ========== */
/* Applied to both .gantt-task-row (left panel) and .gantt-timeline-row (right panel)
   so drag feedback spans the full visual row width. */

/* Row being dragged */
.gantt-task-row.dragging,
.gantt-timeline-row.dragging {
  opacity: 0.5 !important;
  background: rgba(79, 70, 229, 0.08) !important;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}

.gantt-task-row.dragging {
  border: 2px dashed #818cf8 !important;
  border-radius: 6px;
  transform: scale(0.98);
}

:global(.dark) .gantt-task-row.dragging,
:global(.dark) .gantt-timeline-row.dragging {
  background: rgba(99, 102, 241, 0.15) !important;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}

:global(.dark) .gantt-task-row.dragging {
  border-color: #818cf8 !important;
}

/* Drop zone indicator - where the row will be placed */
.gantt-task-row.drag-over,
.gantt-timeline-row.drag-over {
  background: rgba(79, 70, 229, 0.1) !important;
  position: relative;
}

.gantt-task-row.drag-over {
  border: 2px dashed #4f46e5 !important;
  border-radius: 6px;
}

.gantt-timeline-row.drag-over {
  box-shadow: inset 0 2px 6px rgba(79, 70, 229, 0.15);
}

:global(.dark) .gantt-task-row.drag-over,
:global(.dark) .gantt-timeline-row.drag-over {
  background: rgba(99, 102, 241, 0.2) !important;
}

:global(.dark) .gantt-task-row.drag-over {
  border-color: #818cf8 !important;
}

:global(.dark) .gantt-timeline-row.drag-over {
  box-shadow: inset 0 2px 6px rgba(99, 102, 241, 0.25);
}

.gantt-task-row.drag-over::before,
.gantt-timeline-row.drag-over::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #4f46e5;
  border-radius: 4px 0 0 4px;
  z-index: 25;
}

/* Just-reordered highlight animation */
.gantt-task-row.just-reordered,
.gantt-timeline-row.just-reordered {
  animation: reorderHighlight 1.5s ease-out;
}

@keyframes reorderHighlight {
  0% {
    background: rgba(234, 179, 8, 0.4);
    transform: scale(1.01);
    box-shadow: 0 0 12px rgba(234, 179, 8, 0.3);
  }
  50% {
    background: rgba(234, 179, 8, 0.2);
  }
  100% {
    background: transparent;
    transform: scale(1);
    box-shadow: none;
  }
}

/* ========== GRIP HANDLE STYLING ========== */

/* Grip handle base styling */
.gantt-task-row .fa-grip-vertical {
  transition: all 0.15s ease;
  opacity: 0.4;
}

/* Grip handle hover effect */
.gantt-task-row:hover .fa-grip-vertical {
  color: #4f46e5;
  opacity: 1;
  transform: scale(1.1);
}

:global(.dark) .gantt-task-row:hover .fa-grip-vertical {
  color: #818cf8;
}

/* Grip handle active state */
.gantt-task-row:active .fa-grip-vertical,
.gantt-task-row.dragging .fa-grip-vertical {
  color: #4338ca;
  opacity: 1;
}

:global(.dark) .gantt-task-row:active .fa-grip-vertical,
:global(.dark) .gantt-task-row.dragging .fa-grip-vertical {
  color: #a5b4fc;
}

/* ========== DRAGGABLE ELEMENT STYLING ========== */

/* Improve draggable appearance */
[draggable='true'] {
  touch-action: none;
}

/* Row draggable - grab cursor on grip handle */
.gantt-task-row[draggable='true'] {
  cursor: default;
}

.gantt-task-row[draggable='true'] .fa-grip-vertical {
  cursor: grab;
}

.gantt-task-row[draggable='true']:active .fa-grip-vertical {
  cursor: grabbing;
}

/* ========== TASK BAR DRAG STYLING ========== */

/* Task bar has its own grab cursor */
.gantt-task-row [draggable='true']:not(.gantt-task-row) {
  cursor: grab;
  transition: all 0.15s ease;
}

.gantt-task-row [draggable='true']:not(.gantt-task-row):active {
  cursor: grabbing;
}

/* Task bar being dragged (for date changes) */
.gantt-task-row [draggable='true']:not(.gantt-task-row).dragging {
  opacity: 0.5 !important;
  cursor: grabbing !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
  transform: scale(1.02);
}

:global(.dark)
  .gantt-task-row
  [draggable='true']:not(.gantt-task-row).dragging {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
}

</style>

<style>
/* Global styles for drag operation */
.gantt-drag-active {
  user-select: none;
}
</style>
