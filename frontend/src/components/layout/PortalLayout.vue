<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * Portal Layout
 *
 * Simplified layout for external clients (Orga Client role).
 * Features minimal header with logo, support link, and user menu.
 * No sidebar - clients have a streamlined experience.
 */
import PortalHeader from '@/components/layout/PortalHeader.vue'
</script>

<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <!-- Portal Header -->
    <PortalHeader />

    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto">
      <div class="max-w-6xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <slot />
      </div>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 py-4 px-4 text-center">
      <p class="text-xs text-gray-400">
        {{ __('Powered by') }}
        <a
          href="https://github.com/tonic-6101/orga"
          target="_blank"
          rel="noopener noreferrer"
          class="text-orga-500 hover:underline"
        >
          Orga
        </a>
        &middot;
        <router-link to="/orga/portal/support" class="text-gray-500 hover:text-orga-500 no-underline">
          {{ __('Need help?') }}
        </router-link>
      </p>
    </footer>
  </div>
</template>
