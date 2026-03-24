<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePortalApi } from '@/composables/usePortalApi'
import { useAuth } from '@/composables/useAuth'
import { __ } from '@/composables/useTranslate'
import { Headset, CircleCheck, AlertCircle, Info, Loader2, Send, ArrowLeft, Mail } from 'lucide-vue-next'
import type { PortalProject } from '@/types/portal'

const route = useRoute()
const { getClientProjects, submitSupportRequest, loading } = usePortalApi()
const { user } = useAuth()

// Form state
const subject = ref('')
const message = ref('')
const selectedProject = ref('')
const projects = ref<PortalProject[]>([])

// Submission state
const isSubmitting = ref(false)
const submitted = ref(false)
const submitError = ref('')

/**
 * Load projects list for dropdown
 */
onMounted(async () => {
  try {
    projects.value = await getClientProjects()

    // Pre-select project from query param
    const projectParam = route.query.project as string
    if (projectParam && projects.value.some(p => p.name === projectParam)) {
      selectedProject.value = projectParam
    }
  } catch (e) {
    console.error('Failed to load projects:', e)
  }
})

/**
 * User's email for display
 */
const userEmail = computed(() => user.value?.email || __('your registered email'))

/**
 * Form validation
 */
const isFormValid = computed(() => {
  return subject.value.trim().length > 0 && message.value.trim().length > 0
})

/**
 * Handle form submission
 */
async function handleSubmit() {
  if (!isFormValid.value || isSubmitting.value) return

  isSubmitting.value = true
  submitError.value = ''

  try {
    await submitSupportRequest(
      subject.value.trim(),
      message.value.trim(),
      selectedProject.value || undefined
    )

    // Success
    submitted.value = true
    subject.value = ''
    message.value = ''
    selectedProject.value = ''

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    submitError.value = __('Failed to submit request. Please try again.')
    console.error('Support request error:', e)
  } finally {
    isSubmitting.value = false
  }
}

/**
 * Reset form for new submission
 */
function resetForm() {
  submitted.value = false
  submitError.value = ''
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Page Header -->
    <div class="text-center mb-8">
      <div class="mb-4">
        <Headset class="w-12 h-12 text-accent-500 mx-auto" aria-hidden="true" />
      </div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">{{ __('Contact Support') }}</h1>
      <p class="text-gray-500">
        {{ __('Have a question or need assistance? Fill out the form below and our team will get back to you.') }}
      </p>
    </div>

    <!-- Success Message -->
    <div
      v-if="submitted"
      class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6"
    >
      <div class="flex items-center gap-3">
        <CircleCheck class="w-6 h-6 text-green-500" aria-hidden="true" />
        <div>
          <h3 class="text-green-800 font-medium">{{ __('Request Submitted!') }}</h3>
          <p class="text-green-600 text-sm">
            {{ __("Your support request has been submitted successfully. We'll get back to you shortly.") }}
          </p>
        </div>
      </div>
      <button
        @click="resetForm"
        class="mt-4 px-4 py-2 bg-green-100 text-green-700 rounded hover:bg-green-200"
      >
        {{ __('Submit Another Request') }}
      </button>
    </div>

    <!-- Error Message -->
    <div
      v-if="submitError"
      class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6"
    >
      <div class="flex items-center gap-3">
        <AlertCircle class="w-4 h-4 text-red-500" aria-hidden="true" />
        <span class="text-red-600">{{ submitError }}</span>
      </div>
    </div>

    <!-- Support Form -->
    <div v-if="!submitted" class="bg-white rounded-lg border border-gray-200 shadow-sm">
      <form @submit.prevent="handleSubmit" class="p-6 space-y-6">
        <!-- Project Selection -->
        <div>
          <label for="project" class="block text-sm font-medium text-gray-700 mb-1">
            {{ __('Related Project') }} <span class="text-gray-400">({{ __('optional') }})</span>
          </label>
          <select
            id="project"
            v-model="selectedProject"
            class="w-full px-3 py-2 border border-gray-200 rounded focus:border-accent-500 focus:outline-none"
          >
            <option value="">{{ __('-- Select a project --') }}</option>
            <option v-for="p in projects" :key="p.name" :value="p.name">
              {{ p.project_name }}
            </option>
          </select>
          <p class="text-xs text-gray-500 mt-1">
            {{ __('Select a project if your request is related to a specific project.') }}
          </p>
        </div>

        <!-- Subject -->
        <div>
          <label for="subject" class="block text-sm font-medium text-gray-700 mb-1">
            {{ __('Subject') }} <span class="text-red-500">*</span>
          </label>
          <input
            id="subject"
            v-model="subject"
            type="text"
            required
            :placeholder="__('Brief description of your request')"
            class="w-full px-3 py-2 border border-gray-200 rounded focus:border-accent-500 focus:outline-none"
          />
        </div>

        <!-- Message -->
        <div>
          <label for="message" class="block text-sm font-medium text-gray-700 mb-1">
            {{ __('Message') }} <span class="text-red-500">*</span>
          </label>
          <textarea
            id="message"
            v-model="message"
            rows="6"
            required
            :placeholder="__('Please describe your question or issue in detail...')"
            class="w-full px-3 py-2 border border-gray-200 rounded focus:border-accent-500 focus:outline-none resize-none"
          ></textarea>
        </div>

        <!-- Contact Info (read-only) -->
        <div class="bg-gray-50 rounded p-3">
          <p class="text-sm text-gray-500">
            <Info class="w-3.5 h-3.5 inline mr-1" aria-hidden="true" />
            {{ __("We'll respond to:") }} <strong class="text-gray-700">{{ userEmail }}</strong>
          </p>
        </div>

        <!-- Submit Button -->
        <div class="space-y-3 pt-4 border-t border-gray-200">
          <button
            type="submit"
            :disabled="!isFormValid || isSubmitting"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-accent-500 text-white rounded-lg hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" aria-hidden="true" /><Send v-else class="w-4 h-4" aria-hidden="true" />
            {{ isSubmitting ? __('Submitting...') : __('Submit Request') }}
          </button>

          <router-link
            to="/orga/portal"
            class="block w-full text-center px-4 py-2 text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 no-underline"
          >
            <ArrowLeft class="w-4 h-4 inline mr-2" aria-hidden="true" />
            {{ __('Back to Portal') }}
          </router-link>
        </div>
      </form>
    </div>

    <!-- Contact Info Footer -->
    <div class="text-center mt-8">
      <p class="text-gray-500 text-sm mb-1">
        <Mail class="w-3.5 h-3.5 inline mr-1" aria-hidden="true" />
        {{ __('Or email us directly at') }}
        <a href="mailto:support@orga.localhost" class="text-accent-500 hover:underline">
          support@orga.localhost
        </a>
      </p>
      <p class="text-gray-400 text-xs">
        {{ __('Typical response time: 1-2 business days') }}
      </p>
    </div>
  </div>
</template>
