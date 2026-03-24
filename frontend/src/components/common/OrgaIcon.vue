<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Dynamic icon component — maps string icon names to Lucide components.
  Use this for cases where icon names come from data (status maps, settings, etc.).
  For static icons in templates, prefer direct Lucide imports instead.

  Usage:
    <OrgaIcon name="check-circle" class="w-4 h-4" />
    <OrgaIcon :name="statusIcon" class="w-4 h-4 text-green-500" />
-->
<script lang="ts">
export default { name: 'OrgaIcon' }
</script>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import {
  // Status & state
  LockOpen, Hourglass, Eye, Check, X, Ban, Lock, Circle,
  CircleCheck, CircleDot, CircleAlert, CircleHelp, CircleArrowUp,
  AlertCircle, TriangleAlert, Info, CircleX,
  // Navigation & UI
  ChevronDown, ChevronRight, ChevronUp, ChevronLeft,
  ArrowDown, ArrowUp, ArrowLeft, ArrowRight, ArrowUpRight,
  ArrowDownWideNarrow, ArrowUpNarrowWide,
  // Actions
  Plus, Trash2, Trash, Pencil, PenLine, Copy, Download, Upload,
  Search, RotateCcw, ExternalLink, Send, Paperclip, Link, Unlink, Grip,
  // Content & files
  FileText, File, FileSpreadsheet, FileImage, FileArchive,
  FileInput, FileMinus, Clipboard, ClipboardList,
  // Layout & views
  Home, Inbox, FolderOpen, Folder, List, ListChecks,
  Columns3, Table2, LayoutGrid, SlidersHorizontal,
  // People & communication
  User, UserPlus, UserX, Users, MessageSquare, Mail, Headset,
  // Time & calendar
  Clock, Calendar, CalendarX, Timer, History,
  // Project & planning
  Flag, FlagTriangleRight, Milestone, Network, Layers,
  Target, Compass, Play, Pause, SkipForward,
  // Status indicators
  Flame, Bug, Star, FlaskConical, Wrench, Zap, Heart,
  Pin, Bookmark, Bell, Shield, Moon, Sun, Palette,
  // Finance & metrics
  DollarSign, Euro, PoundSterling, JapaneseYen, IndianRupee,
  Coins, Wallet, Calculator, TrendingUp, BarChart3, PieChart,
  // Misc
  Loader2, ToggleRight, Camera, Monitor, Pointer,
  CloudUpload, Github, ChartNoAxesColumn,
} from 'lucide-vue-next'

// Bounded icon map — only icons actually used in Orga are included.
// This is tree-shake friendly because the imports are explicit.
const iconMap: Record<string, Component> = {
  // Status & state
  'lock-open': LockOpen,
  'hourglass': Hourglass,
  'hourglass-half': Hourglass,
  'eye': Eye,
  'check': Check,
  'x': X,
  'xmark': X,
  'times': X,
  'ban': Ban,
  'lock': Lock,
  'circle': Circle,
  'circle-check': CircleCheck,
  'check-circle': CircleCheck,
  'circle-dot': CircleDot,
  'circle-half-stroke': CircleDot,
  'circle-alert': CircleAlert,
  'circle-question': CircleHelp,
  'circle-info': Info,
  'circle-up': CircleArrowUp,
  'circle-x': CircleX,
  'exclamation-circle': AlertCircle,
  'alert-circle': AlertCircle,
  'exclamation-triangle': TriangleAlert,
  'triangle-exclamation': TriangleAlert,
  'info-circle': Info,
  'info': Info,

  // Navigation & UI
  'chevron-down': ChevronDown,
  'chevron-right': ChevronRight,
  'chevron-up': ChevronUp,
  'chevron-left': ChevronLeft,
  'arrow-down': ArrowDown,
  'arrow-up': ArrowUp,
  'arrow-left': ArrowLeft,
  'arrow-right': ArrowRight,
  'arrow-up-right-from-square': ArrowUpRight,
  'arrow-up-right': ArrowUpRight,
  'external-link': ExternalLink,
  'arrow-down-wide-short': ArrowDownWideNarrow,
  'arrow-up-short-wide': ArrowUpNarrowWide,

  // Actions
  'plus': Plus,
  'trash': Trash2,
  'trash-can': Trash2,
  'pen': Pencil,
  'pen-to-square': PenLine,
  'pencil': Pencil,
  'copy': Copy,
  'download': Download,
  'cloud-arrow-up': CloudUpload,
  'search': Search,
  'undo': RotateCcw,
  'rotate': RotateCcw,
  'clock-rotate-left': History,
  'history': History,
  'paper-plane': Send,
  'paperclip': Paperclip,
  'link': Link,
  'link-slash': Unlink,
  'grip-vertical': Grip,
  'hand-pointer': Pointer,

  // Content & files
  'file': File,
  'file-alt': FileText,
  'file-lines': FileText,
  'file-text': FileText,
  'file-excel': FileSpreadsheet,
  'file-image': FileImage,
  'file-pdf': File,
  'file-word': FileText,
  'file-zipper': FileArchive,
  'file-import': FileInput,
  'clipboard-list': ClipboardList,

  // Layout & views
  'home': Home,
  'house': Home,
  'inbox': Inbox,
  'folder-open': FolderOpen,
  'folder': Folder,
  'list': List,
  'list-check': ListChecks,
  'columns': Columns3,
  'table-columns': Table2,
  'display': Monitor,
  'sliders': SlidersHorizontal,

  // People & communication
  'user': User,
  'user-plus': UserPlus,
  'user-slash': UserX,
  'users': Users,
  'comments': MessageSquare,
  'envelope': Mail,
  'headset': Headset,

  // Time & calendar
  'clock': Clock,
  'calendar': Calendar,
  'calendar-xmark': CalendarX,
  'stopwatch': Timer,

  // Project & planning
  'flag': Flag,
  'flag-checkered': FlagTriangleRight,
  'compass-drafting': Compass,
  'drafting-compass': Compass,
  'project-diagram': Network,
  'diagram-project': Network,
  'sitemap': Network,
  'layer-group': Layers,
  'bars-progress': ChartNoAxesColumn,
  'play': Play,
  'play-circle': Play,
  'pause': Pause,
  'forward': SkipForward,
  'right-from-bracket': ExternalLink,

  // Status indicators
  'fire': Flame,
  'bug': Bug,
  'star': Star,
  'flask': FlaskConical,
  'wrench': Wrench,
  'bolt': Zap,
  'heart': Heart,
  'thumbtack': Pin,
  'bell': Bell,
  'shield-halved': Shield,
  'moon': Moon,
  'sun': Sun,
  'palette': Palette,
  'toggle-on': ToggleRight,
  'camera': Camera,
  'sort': ArrowDownWideNarrow,
  'sort-up': ArrowUp,
  'sort-down': ArrowDown,
  'gear': SlidersHorizontal,
  'check-square': ListChecks,

  // Finance
  'dollar-sign': DollarSign,
  'euro-sign': Euro,
  'sterling-sign': PoundSterling,
  'yen-sign': JapaneseYen,
  'indian-rupee-sign': IndianRupee,
  'won-sign': Coins,
  'lira-sign': Coins,
  'brazilian-real-sign': Coins,
  'coins': Coins,
  'wallet': Wallet,
  'calculator': Calculator,
  'chart-line': TrendingUp,
  'chart-bar': BarChart3,
  'chart-pie': PieChart,

  // Misc
  'spinner': Loader2,
  'align-left': FileText,
  'minus': X,
  'exclamation': AlertCircle,
  'github': Github,
}

const props = defineProps<{
  name: string
  spin?: boolean
}>()

const resolvedIcon = computed<Component | null>(() => {
  // Strip fa-solid/fa-regular/fa-brands prefix and fa- prefix
  const clean = props.name
    .replace(/^fa-(solid|regular|brands)\s+/, '')
    .replace(/^fa-/, '')
  return iconMap[clean] ?? null
})
</script>

<template>
  <component
    v-if="resolvedIcon"
    :is="resolvedIcon"
    :class="{ 'animate-spin': spin }"
  />
</template>
