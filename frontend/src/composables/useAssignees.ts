// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic
//
// Composable for the Owner + Collaborators picker.
// Spec: ecosystem.localhost/spec/apps/orga/features/community/task-assignment.md
//
// Identity is the Frappe Contact. Orga Resource is enrichment only — never
// created as a side effect of assignment.

import { ref } from 'vue'
import { frappeRequest } from 'frappe-ui'

async function call<T>(
  method: string,
  args: Record<string, unknown> = {},
  httpMethod: 'GET' | 'POST' = 'GET',
): Promise<T> {
  const response = await frappeRequest({
    url: '/api/method/' + method,
    method: httpMethod,
    params: args,
  })
  return response as T
}

export interface Assignable {
  contact: string // Contact name — authoritative id
  name: string
  avatar: string | null
  email: string | null
  is_internal: boolean // Contact.user IS NOT NULL
  role_label: string
  resource: string | null // Orga Resource name, enrichment only
  last_assigned: string | null
}

export interface AssigneeSelection {
  contacts: string[]
}

export function useAssignees() {
  const results = ref<Assignable[]>([])
  const loading = ref(false)

  let seq = 0
  async function search(params: { query: string; project?: string | null }) {
    const mine = ++seq
    loading.value = true
    try {
      const rows = await call('orga.orga.api.assignment.search_assignable', {
        query: params.query,
        project: params.project ?? null,
        limit: 20,
      })
      if (mine !== seq) return // stale response
      results.value = (rows as Assignable[]) ?? []
    } finally {
      if (mine === seq) loading.value = false
    }
  }

  async function commit(task: string, selection: AssigneeSelection) {
    return call(
      'orga.orga.api.assignment.set_assignees',
      { task, contacts: JSON.stringify(selection.contacts) },
      'POST',
    )
  }

  interface CurrentAssignee {
    contact: string
    name: string
    avatar: string | null
    email: string | null
    is_internal: boolean
  }
  interface CurrentAssignees {
    task: string
    assignees: CurrentAssignee[]
  }

  async function load(task: string): Promise<CurrentAssignees> {
    return (await call('orga.orga.api.assignment.get_task_assignees', { task })) as CurrentAssignees
  }

  return { results, loading, search, commit, load }
}
