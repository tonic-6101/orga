<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  UserAvatar.vue - Reusable user avatar component with image/initials fallback

  Usage:
    <UserAvatar
      :name="user.full_name"
      :image="user.user_image"
      size="md"
    />
-->
<template>
  <div
    :class="[
      'rounded-full overflow-hidden shrink-0',
      sizeClasses[size]
    ]"
  >
    <!-- User Image -->
    <img
      v-if="imageSrc && !imageError"
      :src="imageSrc"
      :alt="name || 'User'"
      class="w-full h-full object-cover"
      @error="handleImageError"
    />

    <!-- Initials Fallback -->
    <div
      v-else
      :class="[
        'w-full h-full flex items-center justify-center font-semibold',
        colorClass,
        textSizeClasses[size]
      ]"
    >
      {{ initials }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
type AvatarColor = 'teal' | 'orga' | 'blue' | 'purple' | 'pink' | 'amber' | 'gray'

interface Props {
  /** User's full name (used for initials and alt text) */
  name?: string | null
  /** User's avatar image URL */
  image?: string | null
  /** Avatar size: xs=24px, sm=28px, md=32px, lg=40px, xl=48px */
  size?: AvatarSize
  /** Background color for initials fallback */
  color?: AvatarColor
}

const props = withDefaults(defineProps<Props>(), {
  name: null,
  image: null,
  size: 'md',
  color: 'teal'
})

const imageError = ref(false)

/**
 * Size classes for avatar container
 */
const sizeClasses: Record<AvatarSize, string> = {
  xs: 'w-6 h-6',
  sm: 'w-7 h-7',
  md: 'w-8 h-8',
  lg: 'w-10 h-10',
  xl: 'w-12 h-12'
}

/**
 * Text size classes for initials based on avatar size
 */
const textSizeClasses: Record<AvatarSize, string> = {
  xs: 'text-[10px]',
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
  xl: 'text-lg'
}

/**
 * Background/text color classes for initials fallback
 */
const colorClasses: Record<AvatarColor, string> = {
  teal: 'bg-teal-500 text-white',
  orga: 'bg-orga-500 text-white',
  blue: 'bg-blue-500 text-white',
  purple: 'bg-purple-500 text-white',
  pink: 'bg-pink-500 text-white',
  amber: 'bg-amber-500 text-white',
  gray: 'bg-gray-400 text-white dark:bg-gray-600'
}

/**
 * Get color class based on prop or derive from name
 */
const colorClass = computed(() => {
  if (props.color) {
    return colorClasses[props.color]
  }
  // Default to teal
  return colorClasses.teal
})

/**
 * Compute initials from name
 */
const initials = computed(() => {
  if (!props.name) return '?'

  const name = props.name.trim()
  const parts = name.split(/\s+/).filter(Boolean)

  if (parts.length >= 2) {
    // First letter of first and last name
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  } else if (parts.length === 1 && parts[0].length >= 2) {
    // First two letters of single name
    return parts[0].substring(0, 2).toUpperCase()
  } else if (parts.length === 1) {
    return parts[0][0].toUpperCase()
  }

  return '?'
})

/**
 * Resolve image source URL
 * Frappe stores images with paths like "/files/user_image.png"
 */
const imageSrc = computed(() => {
  if (!props.image) return null

  // If it's already a full URL, use it directly
  if (props.image.startsWith('http://') || props.image.startsWith('https://')) {
    return props.image
  }

  // If it starts with /, it's a relative path from Frappe
  if (props.image.startsWith('/')) {
    return props.image
  }

  // Otherwise, assume it's a file path
  return `/files/${props.image}`
})

/**
 * Handle image load error - fallback to initials
 */
function handleImageError() {
  imageError.value = true
}
</script>
