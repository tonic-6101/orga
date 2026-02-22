// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

// src/types/frappe.d.ts
// Type definitions for Frappe globals available in Vue frontend

interface FrappeCallOptions {
  method: string
  args?: Record<string, unknown>
  async?: boolean
  freeze?: boolean
  freeze_message?: string
  callback?: (response: FrappeCallResponse) => void
  error?: (error: Error) => void
}

interface FrappeCallResponse<T = unknown> {
  message: T
  exc?: string
  exc_type?: string
  _server_messages?: string
}

interface FrappeSession {
  user: string
  user_email: string
  user_fullname: string
  user_image?: string
}

interface FrappeDatetime {
  str_to_obj: (dateString: string) => Date
  obj_to_str: (date: Date) => string
  now_datetime: () => string
  get_today: () => string
  add_days: (date: string, days: number) => string
  add_months: (date: string, months: number) => string
  get_diff: (date1: string, date2: string) => number
}

interface FrappeUtils {
  is_null: (value: unknown) => boolean
  now: () => string
  today: () => string
  get_url: (path?: string) => string
  escape_html: (text: string) => string
  format_date: (date: string, format?: string) => string
  format_datetime: (datetime: string, format?: string) => string
  format_time: (time: string, format?: string) => string
  format_currency: (value: number, currency?: string) => string
}

interface FrappeModel {
  get_new_doc: (doctype: string, parent_doc?: FrappeDocument, parentfield?: string) => FrappeDocument
  add_child: (parent: FrappeDocument, child: Partial<FrappeDocument>, parentfield: string) => FrappeDocument
  clear_table: (parent: FrappeDocument, parentfield: string) => void
}

interface FrappeRouter {
  current_route: string[]
  push_state: (route: string) => void
}

interface Frappe {
  call: <T = unknown>(options: FrappeCallOptions) => Promise<FrappeCallResponse<T>>
  xcall: <T = unknown>(method: string, args?: Record<string, unknown>) => Promise<T>
  throw: (message: string) => never
  msgprint: (message: string | { message: string; indicator?: string; title?: string }) => void
  show_alert: (options: { message: string; indicator?: 'green' | 'blue' | 'orange' | 'red' | 'yellow'; seconds?: number }) => void
  confirm: (message: string, onyes: () => void, onno?: () => void) => void
  prompt: (fields: unknown[], callback: (values: Record<string, unknown>) => void, title?: string, primary_label?: string) => void
  session: FrappeSession
  datetime: FrappeDatetime
  utils: FrappeUtils
  model: FrappeModel
  router: FrappeRouter
  user: string
  boot: {
    user: FrappeSession
    sysdefaults: Record<string, string>
    [key: string]: unknown
  }
  flags: Record<string, unknown>
  db: {
    get_value: <T = unknown>(doctype: string, name: string, fieldname: string) => Promise<T>
    get_list: <T = unknown>(options: { doctype: string; fields?: string[]; filters?: Record<string, unknown>; limit?: number }) => Promise<T[]>
    count: (doctype: string, filters?: Record<string, unknown>) => Promise<number>
    exists: (doctype: string, name: string) => Promise<boolean>
  }
  format: (value: unknown, df: { fieldtype: string; options?: string }, doc?: FrappeDocument) => string
  get_doc: <T = FrappeDocument>(doctype: string, name: string) => Promise<T>
  new_doc: (doctype: string) => FrappeDocument
  set_route: (...route: string[]) => void
  get_route: () => string[]
  get_route_str: () => string
}

interface FrappeDocument {
  doctype: string
  name: string
  owner: string
  creation: string
  modified: string
  modified_by: string
  docstatus: 0 | 1 | 2
  [key: string]: unknown
}

// Global declarations
declare const frappe: Frappe
declare const __: (text: string, ...args: unknown[]) => string
declare const cstr: (value: unknown) => string
declare const cint: (value: unknown) => number
declare const flt: (value: unknown, precision?: number) => number

// Augment Window interface
interface Window {
  frappe: Frappe
  csrf_token: string
  __messages: Record<string, string>
  lang: string
  __: (text: string, replace?: unknown[] | Record<string, unknown>) => string
}

// Vue template type-checking for __() global property
declare module 'vue' {
  interface ComponentCustomProperties {
    __: (text: string, replace?: unknown[] | Record<string, unknown>) => string
  }
}

// FrappeUI module declarations
declare module 'frappe-ui' {
  import { Plugin, Component, Ref } from 'vue'

  export const FrappeUI: Plugin
  export function setConfig(key: string, value: unknown): void
  export function frappeRequest(options: {
    url: string
    params?: Record<string, unknown>
    method?: string
  }): Promise<unknown>

  // Components
  export const Button: Component
  export const Input: Component
  export const Badge: Component
  export const Spinner: Component
  export const Dialog: Component
  export const Dropdown: Component
  export const Avatar: Component
  export const TextInput: Component
  export const FormControl: Component
  export const FeatherIcon: Component
  export const Tooltip: Component
  export const Popover: Component
  export const DatePicker: Component
  export const TimePicker: Component
  export const Select: Component
  export const Checkbox: Component
  export const Switch: Component
  export const Tabs: Component
  export const Tab: Component
  export const Card: Component
  export const Alert: Component
  export const Progress: Component
  export const Pagination: Component
  export const Table: Component
  export const Modal: Component

  // createResource
  interface ResourceOptions<T = unknown> {
    url: string
    params?: Record<string, unknown> | (() => Record<string, unknown>)
    auto?: boolean
    cache?: string | string[]
    transform?: (data: unknown) => T
    onSuccess?: (data: T) => void
    onError?: (error: Error) => void
  }

  interface Resource<T = unknown> {
    data: Ref<T | null>
    loading: Ref<boolean>
    error: Ref<Error | null>
    fetch: (params?: Record<string, unknown>) => Promise<T>
    reload: () => Promise<T>
    reset: () => void
  }

  export function createResource<T = unknown>(options: ResourceOptions<T>): Resource<T>
}

declare module 'frappe-ui/vite' {
  import { Plugin } from 'vite'

  interface FrappeUIViteOptions {
    frappeProxy?: boolean
    lucideIcons?: boolean
    jinjaBootData?: boolean
  }

  export default function frappeUIVite(options?: FrappeUIViteOptions): Plugin
}
