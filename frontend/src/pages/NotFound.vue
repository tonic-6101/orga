<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { __ } from '@/composables/useTranslate'

const router = useRouter()

function goHome() {
  router.push('/orga')
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/orga')
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-full bg-gray-50 dark:bg-gray-900 p-6">
    <div class="text-center max-w-lg">

      <!-- Illustration -->
      <div class="mb-8 select-none">
        <div class="relative inline-block">
          <!-- Desk with scattered papers -->
          <svg viewBox="0 0 280 200" class="w-64 h-auto mx-auto" xmlns="http://www.w3.org/2000/svg">
            <!-- Background circle -->
            <circle cx="140" cy="100" r="90" class="fill-gray-100 dark:fill-gray-800" />

            <!-- Desk surface -->
            <rect x="50" y="120" width="180" height="8" rx="3" class="fill-orga-400 dark:fill-orga-600" />
            <!-- Desk legs -->
            <rect x="65" y="128" width="6" height="40" rx="2" class="fill-orga-300 dark:fill-orga-700" />
            <rect x="209" y="128" width="6" height="40" rx="2" class="fill-orga-300 dark:fill-orga-700" />

            <!-- Coffee mug -->
            <rect x="175" y="104" width="18" height="16" rx="3" class="fill-amber-200 dark:fill-amber-700" />
            <path d="M193 108 Q200 108 200 114 Q200 120 193 120" stroke-width="2.5" fill="none" class="stroke-amber-300 dark:stroke-amber-600" />
            <!-- Steam -->
            <path d="M181 100 Q183 94 181 88" stroke-width="1.5" fill="none" stroke-linecap="round" class="stroke-gray-300 dark:stroke-gray-600 animate-float" />
            <path d="M187 102 Q189 95 187 89" stroke-width="1.5" fill="none" stroke-linecap="round" class="stroke-gray-300 dark:stroke-gray-600 animate-float-delayed" />

            <!-- Paper 1 (tilted on desk) -->
            <g transform="rotate(-8 110 105)">
              <rect x="90" y="88" width="40" height="32" rx="2" class="fill-white dark:fill-gray-700" />
              <line x1="96" y1="96" x2="124" y2="96" stroke-width="2" class="stroke-gray-200 dark:stroke-gray-600" />
              <line x1="96" y1="102" x2="118" y2="102" stroke-width="2" class="stroke-gray-200 dark:stroke-gray-600" />
              <line x1="96" y1="108" x2="121" y2="108" stroke-width="2" class="stroke-gray-200 dark:stroke-gray-600" />
            </g>

            <!-- Paper 2 (falling/floating) -->
            <g transform="rotate(15 85 70)" class="animate-sway">
              <rect x="65" y="55" width="36" height="28" rx="2" class="fill-white dark:fill-gray-700" opacity="0.9" />
              <line x1="71" y1="63" x2="95" y2="63" stroke-width="2" class="stroke-gray-200 dark:stroke-gray-600" />
              <line x1="71" y1="69" x2="89" y2="69" stroke-width="2" class="stroke-gray-200 dark:stroke-gray-600" />
              <text x="76" y="78" font-size="7" font-weight="bold" class="fill-red-400">?</text>
            </g>

            <!-- Paper 3 (on floor) -->
            <g transform="rotate(25 210 155)">
              <rect x="195" y="145" width="30" height="22" rx="2" class="fill-white dark:fill-gray-700" opacity="0.7" />
              <line x1="200" y1="151" x2="220" y2="151" stroke-width="1.5" class="stroke-gray-200 dark:stroke-gray-600" />
              <line x1="200" y1="156" x2="215" y2="156" stroke-width="1.5" class="stroke-gray-200 dark:stroke-gray-600" />
            </g>

            <!-- Magnifying glass (searching) -->
            <g transform="rotate(-20 155 72)">
              <circle cx="155" cy="65" r="16" stroke-width="3" fill="none" class="stroke-orga-500" />
              <circle cx="155" cy="65" r="13" class="fill-orga-100/50 dark:fill-orga-900/30" />
              <line x1="167" y1="77" x2="178" y2="88" stroke-width="4" stroke-linecap="round" class="stroke-orga-400 dark:stroke-orga-600" />
              <!-- Question mark in lens -->
              <text x="150" y="71" font-size="16" font-weight="bold" class="fill-orga-500 dark:fill-orga-400">?</text>
            </g>

            <!-- Small plant on desk -->
            <rect x="67" y="108" width="12" height="12" rx="2" class="fill-amber-100 dark:fill-amber-800" />
            <path d="M73 108 Q70 98 65 95" stroke-width="2" fill="none" stroke-linecap="round" class="stroke-green-400 dark:stroke-green-600" />
            <path d="M73 108 Q76 96 80 94" stroke-width="2" fill="none" stroke-linecap="round" class="stroke-green-500 dark:stroke-green-500" />
            <path d="M73 108 Q73 97 73 92" stroke-width="2" fill="none" stroke-linecap="round" class="stroke-green-400 dark:stroke-green-600" />
          </svg>
        </div>
      </div>

      <!-- 404 text -->
      <h1 class="text-6xl font-bold text-orga-500 mb-3">404</h1>

      <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-3">
        {{ __('This page wandered off') }}
      </h2>

      <p class="text-gray-500 dark:text-gray-400 mb-8 leading-relaxed">
        {{ __("It's not you, it's the link. The page you're looking for might have been moved, renamed, or is taking a well-deserved coffee break. Your projects and data are perfectly safe.") }}
      </p>

      <!-- Actions -->
      <div class="flex items-center justify-center gap-3">
        <button
          @click="goBack"
          class="px-5 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm flex items-center gap-2"
        >
          <i class="fa-solid fa-arrow-left"></i>
          {{ __('Go Back') }}
        </button>
        <button
          @click="goHome"
          class="px-5 py-2.5 bg-orga-500 text-white rounded-lg hover:bg-orga-600 transition-colors text-sm flex items-center gap-2"
        >
          <i class="fa-solid fa-house"></i>
          {{ __('Dashboard') }}
        </button>
      </div>

      <!-- Path hint -->
      <p class="mt-8 text-xs text-gray-400 dark:text-gray-600">
        {{ __('Tried:') }} <code class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-gray-500 dark:text-gray-500">{{ $route.fullPath }}</code>
      </p>
    </div>
  </div>
</template>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}
@keyframes float-delayed {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
@keyframes sway {
  0%, 100% { transform: rotate(15deg) translateY(0); }
  50% { transform: rotate(12deg) translateY(-2px); }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}
.animate-float-delayed {
  animation: float-delayed 3s ease-in-out 0.5s infinite;
}
.animate-sway {
  animation: sway 4s ease-in-out infinite;
}
</style>
