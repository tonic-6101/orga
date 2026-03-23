import { ref as k, computed as J, onUnmounted as G, defineComponent as $, onMounted as B, openBlock as y, createElementBlock as b, createElementVNode as e, toDisplayString as s, unref as t, Fragment as O, renderList as H, withModifiers as W, normalizeClass as S, createTextVNode as j, createCommentVNode as v, withDirectives as p, vModelSelect as D, vModelText as M, vModelCheckbox as C } from "/assets/dock/js/vendor/vue.esm.js";
function Y(g) {
  let o = Object.assign({}, g);
  if (!o.url)
    throw new Error("[request] options.url is required");
  o.transformRequest && (o = o.transformRequest(g)), o.responseType || (o.responseType = "json"), o.method || (o.method = "GET");
  let _ = o.url, d;
  if (o.params)
    if (o.method === "GET") {
      let l = new URLSearchParams();
      for (let n in o.params)
        l.append(n, o.params[n]);
      _ = o.url + "?" + l.toString();
    } else
      d = JSON.stringify(o.params);
  return fetch(_, {
    method: o.method || "GET",
    headers: o.headers,
    body: d
  }).then((l) => {
    if (o.transformResponse)
      return o.transformResponse(l, o);
    if (l.status >= 200 && l.status < 300)
      return o.responseType === "json" ? l.json() : l;
    {
      let n = new Error(l.statusText);
      throw n.response = l, n;
    }
  }).catch((l) => {
    if (o.transformError)
      return o.transformError(l);
    throw l;
  });
}
let X = {};
function z(g) {
  return X[g] ?? null;
}
function K(g) {
  return Y({
    ...g,
    transformRequest: (o = {}) => {
      if (!o.url)
        throw new Error("[frappeRequest] options.url is required");
      let _ = Object.assign(
        {
          Accept: "application/json",
          "Content-Type": "application/json; charset=utf-8",
          "X-Frappe-Site-Name": window.location.hostname
        },
        o.headers || {}
      );
      return window.csrf_token && window.csrf_token !== "{{ csrf_token }}" && (_["X-Frappe-CSRF-Token"] = window.csrf_token), !o.url.startsWith("/") && !o.url.startsWith("http") && (o.url = "/api/method/" + o.url), {
        ...o,
        method: o.method || "POST",
        headers: _
      };
    },
    transformResponse: async (o, _) => {
      let d = _.url;
      if (o.ok) {
        const l = await o.json();
        if (l.docs || d === "/api/method/login")
          return l;
        if (l.exc)
          try {
            console.groupCollapsed(d), console.log(_);
            let n = JSON.parse(l.exc);
            for (let f of n)
              console.log(f);
            console.groupEnd();
          } catch (n) {
            console.warn("Error printing debug messages", n);
          }
        if (l._server_messages) {
          let n = z("serverMessagesHandler") || _.onServerMessages || null;
          n && n(JSON.parse(l?._server_messages) || []);
        }
        return l.message;
      } else {
        let l = await o.text(), n, f;
        try {
          n = JSON.parse(l);
        } catch {
        }
        let R = [
          [_.url, n?.exc_type, n?._error_message].filter(Boolean).join(" ")
        ];
        if (n.exc) {
          f = n.exc;
          try {
            f = JSON.parse(f)[0], console.log(f);
          } catch {
          }
        }
        let c = new Error(R.join(`
`));
        throw c.exc_type = n.exc_type, c.exc = f, c.response = o, c.status = l.status, c.messages = n._server_messages ? JSON.parse(n._server_messages) : [], c.messages = c.messages.concat(n.message), c.messages = c.messages.map((w) => {
          try {
            return JSON.parse(w).message;
          } catch {
            return w;
          }
        }), c.messages = c.messages.filter(Boolean), c.messages.length || (c.messages = n._error_message ? [n._error_message] : ["Internal Server Error"]), _.onError && _.onError(c), c;
      }
    },
    transformError: (o) => {
      throw g.onError && g.onError(o), o;
    }
  });
}
function F() {
  const g = k(!1), o = k(null);
  async function _(d, l = {}) {
    g.value = !0, o.value = null;
    try {
      return await K({
        url: "/api/method/" + d,
        params: l
      });
    } catch (n) {
      const f = n instanceof Error ? n.message : "An error occurred";
      throw o.value = f, console.error(`API Error [${d}]:`, n), n;
    } finally {
      g.value = !1;
    }
  }
  return { call: _, loading: g, error: o };
}
function Q() {
  const { call: g, loading: o, error: _ } = F();
  return {
    loading: o,
    error: _,
    call: g,
    getSettings: () => g("orga.orga.api.settings.get_settings"),
    updateSettings: (d) => g("orga.orga.api.settings.update_settings", { data: JSON.stringify(d) })
  };
}
const x = k(null), E = k(!1), T = k(null), P = "orga_update_dismissed_version";
function Z() {
  try {
    return localStorage.getItem(P);
  } catch {
    return null;
  }
}
const ee = J(() => {
  if (!x.value?.update_available) return !1;
  const g = Z();
  return !(g && g === x.value.latest_version);
});
let I = !1;
function te() {
  const { call: g } = F();
  async function o() {
    if (!E.value) {
      E.value = !0, T.value = null;
      try {
        const n = await g(
          "orga.orga.api.settings.get_update_info"
        );
        n && n.current_version && (x.value = n);
      } catch {
      } finally {
        E.value = !1;
      }
    }
  }
  async function _() {
    E.value = !0, T.value = null;
    try {
      const n = await g(
        "orga.orga.api.settings.check_updates_now"
      );
      n && n.current_version && (x.value = n);
    } catch (n) {
      T.value = n.message || "Check failed";
    } finally {
      E.value = !1;
    }
  }
  function d() {
    x.value?.latest_version && (localStorage.setItem(P, x.value.latest_version), x.value = { ...x.value });
  }
  function l() {
    localStorage.removeItem(P), x.value && (x.value = { ...x.value });
  }
  return I || (I = !0, o()), G(() => {
  }), {
    updateInfo: x,
    updateAvailable: ee,
    isChecking: E,
    checkError: T,
    fetchUpdateInfo: o,
    forceCheck: _,
    dismissUpdate: d,
    undismissUpdate: l
  };
}
function r(g, o) {
  let d = (window.__messages || {})[g] || g;
  if (o)
    if (Array.isArray(o))
      for (let l = 0; l < o.length; l++)
        d = d.replace(new RegExp(`\\{${l}\\}`, "g"), String(o[l]));
    else
      for (const [l, n] of Object.entries(o))
        d = d.replace(new RegExp(`\\{${l}\\}`, "g"), String(n));
  return d;
}
const re = "0.15.0", se = { class: "p-6 bg-white dark:bg-gray-950 min-h-full" }, ae = { class: "mb-6" }, oe = { class: "text-2xl font-semibold text-gray-900 dark:text-gray-100 m-0" }, ne = {
  key: 0,
  class: "flex items-center justify-center py-20"
}, le = { class: "text-center" }, de = { class: "text-gray-500 dark:text-gray-400" }, ie = {
  key: 1,
  class: "flex items-center justify-center py-20"
}, ue = { class: "bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center" }, ge = { class: "text-red-800 dark:text-red-300 font-medium mb-2" }, ce = { class: "text-red-600 dark:text-red-400 text-sm mb-4" }, _e = {
  key: 2,
  class: "flex gap-6"
}, me = { class: "w-60 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg py-3 shrink-0" }, ye = ["onClick"], be = { class: "flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg" }, fe = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, pe = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, xe = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, ke = { class: "p-6" }, he = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, ve = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, we = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Se = { value: "Open" }, je = { value: "In Progress" }, Ce = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Ee = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ue = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Oe = { value: "Planning" }, Re = { value: "Active" }, Ve = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Te = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ae = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, De = { class: "flex justify-between items-center py-3" }, Me = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Pe = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ne = { value: "Low" }, Ie = { value: "Medium" }, Fe = { value: "High" }, Le = { value: "Urgent" }, qe = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, Je = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, Ge = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, $e = { class: "p-6" }, Be = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, He = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, We = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ye = { class: "relative inline-block w-11 h-6" }, Xe = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, ze = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ke = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Qe = { class: "relative inline-block w-11 h-6" }, Ze = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, et = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, tt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, rt = { class: "relative inline-block w-11 h-6" }, st = { class: "flex justify-between items-center py-3" }, at = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, ot = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, nt = { class: "flex items-center gap-2" }, lt = { class: "text-sm text-gray-500 dark:text-gray-400" }, dt = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, it = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, ut = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, gt = { class: "p-6" }, ct = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, _t = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, mt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, yt = { class: "relative inline-block w-11 h-6" }, bt = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, ft = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, pt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, xt = { class: "relative inline-block w-11 h-6" }, kt = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, ht = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, vt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, wt = { class: "relative inline-block w-11 h-6" }, St = { class: "flex justify-between items-center py-3" }, jt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ct = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Et = { class: "flex items-center gap-2" }, Ut = { class: "text-sm text-gray-500 dark:text-gray-400" }, Ot = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, Rt = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, Vt = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, Tt = { class: "p-6" }, At = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Dt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Mt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Pt = { class: "text-sm font-mono text-gray-900 dark:text-gray-100" }, Nt = {
  key: 0,
  class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700"
}, It = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ft = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Lt = {
  key: 1,
  class: "mt-4 p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg"
}, qt = { class: "flex items-start gap-3" }, Jt = { class: "flex-1" }, Gt = { class: "text-sm font-semibold text-amber-800 dark:text-amber-300 m-0" }, $t = { class: "text-sm text-amber-700 dark:text-amber-400 mt-1 mb-0" }, Bt = {
  key: 0,
  class: "mt-3 text-xs text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded p-3 max-h-40 overflow-y-auto whitespace-pre-wrap"
}, Ht = { key: 0 }, Wt = { class: "mt-3 flex items-center gap-3" }, Yt = ["href"], Xt = {
  key: 2,
  class: "mt-4 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg"
}, zt = { class: "flex items-center gap-3" }, Kt = { class: "text-sm font-semibold text-green-800 dark:text-green-300 m-0" }, Qt = { class: "text-sm text-green-700 dark:text-green-400 mt-1 mb-0" }, Zt = {
  key: 3,
  class: "mt-4 p-4 bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-600 rounded-lg text-center"
}, er = { class: "text-sm text-gray-500 dark:text-gray-400 m-0" }, tr = {
  key: 4,
  class: "mt-3 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400"
}, rr = { class: "mt-6 pt-4 border-t border-gray-100 dark:border-gray-700" }, sr = ["disabled"], ar = {
  key: 5,
  class: "p-4 bg-gray-50 dark:bg-gray-700/50 flex justify-end gap-3 border-t border-gray-200 dark:border-gray-700"
}, or = ["disabled"], nr = {
  key: 0,
  class: "fa-solid fa-spinner fa-spin"
}, ir = /* @__PURE__ */ $({
  __name: "Settings",
  setup(g) {
    const { getSettings: o, updateSettings: _ } = Q(), { updateInfo: d, isChecking: l, checkError: n, forceCheck: f, dismissUpdate: R } = te(), c = k("defaults"), w = [
      { id: "defaults", name: r("Defaults"), icon: "sliders" },
      { id: "features", name: r("Features"), icon: "toggle-on" },
      { id: "notifications", name: r("Notifications"), icon: "bell" },
      { id: "updates", name: r("Updates"), icon: "arrow-up-from-bracket" }
    ], u = k({
      default_task_status: "Open",
      default_project_status: "Planning",
      project_code_prefix: "ORG",
      default_priority: "Medium",
      auto_calculate_progress: 1,
      auto_set_missed_milestones: 1,
      enable_time_tracking: 0,
      default_capacity_hours: 40,
      notify_on_task_assignment: 1,
      notify_on_status_change: 0,
      notify_on_due_date: 1,
      due_date_reminder_days: 1
    }), A = k(!0), U = k(!1), V = k(null), h = k(null);
    async function N() {
      A.value = !0, V.value = null;
      try {
        const m = await o();
        u.value = {
          default_task_status: m.default_task_status || "Open",
          default_project_status: m.default_project_status || "Planning",
          project_code_prefix: m.project_code_prefix || "ORG",
          default_priority: m.default_priority || "Medium",
          auto_calculate_progress: m.auto_calculate_progress ? 1 : 0,
          auto_set_missed_milestones: m.auto_set_missed_milestones ? 1 : 0,
          enable_time_tracking: m.enable_time_tracking ? 1 : 0,
          default_capacity_hours: m.default_capacity_hours || 40,
          notify_on_task_assignment: m.notify_on_task_assignment ? 1 : 0,
          notify_on_status_change: m.notify_on_status_change ? 1 : 0,
          notify_on_due_date: m.notify_on_due_date ? 1 : 0,
          due_date_reminder_days: m.due_date_reminder_days || 1
        };
      } catch (m) {
        console.error("Failed to load settings:", m), V.value = m.message || r("Failed to load settings");
      } finally {
        A.value = !1;
      }
    }
    async function L() {
      U.value = !0, h.value = null;
      try {
        await _(u.value), h.value = { type: "success", text: r("Settings saved successfully") }, setTimeout(() => {
          h.value = null;
        }, 3e3);
      } catch (m) {
        console.error("Failed to save settings:", m), h.value = { type: "error", text: m.message || r("Failed to save settings") };
      } finally {
        U.value = !1;
      }
    }
    function q() {
      u.value = {
        default_task_status: "Open",
        default_project_status: "Planning",
        project_code_prefix: "ORG",
        default_priority: "Medium",
        auto_calculate_progress: 1,
        auto_set_missed_milestones: 1,
        enable_time_tracking: 0,
        default_capacity_hours: 40,
        notify_on_task_assignment: 1,
        notify_on_status_change: 0,
        notify_on_due_date: 1,
        due_date_reminder_days: 1
      };
    }
    return B(N), (m, a) => (y(), b("div", se, [
      e("div", ae, [
        e("h1", oe, s(t(r)("Settings")), 1)
      ]),
      A.value ? (y(), b("div", ne, [
        e("div", le, [
          a[14] || (a[14] = e("i", { class: "fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3" }, null, -1)),
          e("p", de, s(t(r)("Loading settings...")), 1)
        ])
      ])) : V.value ? (y(), b("div", ie, [
        e("div", ue, [
          a[15] || (a[15] = e("i", { class: "fa-solid fa-exclamation-triangle text-red-500 text-3xl mb-3" }, null, -1)),
          e("h3", ge, s(t(r)("Error loading settings")), 1),
          e("p", ce, s(V.value), 1),
          e("button", {
            onClick: N,
            class: "px-4 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/60"
          }, s(t(r)("Try Again")), 1)
        ])
      ])) : (y(), b("div", _e, [
        e("nav", me, [
          (y(), b(O, null, H(w, (i) => e("a", {
            key: i.id,
            href: "#",
            class: S([
              "flex items-center gap-3 px-5 py-3 text-sm transition-all no-underline",
              c.value === i.id ? "text-orga-500 dark:text-orga-400 bg-orga-50 dark:bg-orga-950/30 border-l-[3px] border-orga-500 dark:border-orga-400" : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
            ]),
            onClick: W((lr) => c.value = i.id, ["prevent"])
          }, [
            e("i", {
              class: S(["fa-solid", `fa-${i.icon}`, "w-5 text-center"])
            }, null, 2),
            e("span", null, s(i.name), 1)
          ], 10, ye)), 64))
        ]),
        e("div", be, [
          h.value ? (y(), b("div", {
            key: 0,
            class: S([
              "px-4 py-3 text-sm",
              h.value.type === "success" ? "bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-b border-green-200 dark:border-green-800" : "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 border-b border-red-200 dark:border-red-800"
            ])
          }, [
            e("i", {
              class: S(["fa-solid mr-2", h.value.type === "success" ? "fa-check-circle" : "fa-exclamation-circle"])
            }, null, 2),
            j(" " + s(h.value.text), 1)
          ], 2)) : v("", !0),
          c.value === "defaults" ? (y(), b(O, { key: 1 }, [
            e("div", fe, [
              e("h3", pe, s(t(r)("Default Values")), 1),
              e("p", xe, s(t(r)("Configure default values for new projects and tasks")), 1)
            ]),
            e("div", ke, [
              e("div", he, [
                e("div", null, [
                  e("h4", ve, s(t(r)("Default Task Status")), 1),
                  e("p", we, s(t(r)("Status assigned to new tasks")), 1)
                ]),
                p(e("select", {
                  "onUpdate:modelValue": a[0] || (a[0] = (i) => u.value.default_task_status = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [
                  e("option", Se, s(t(r)("Open")), 1),
                  e("option", je, s(t(r)("In Progress")), 1)
                ], 512), [
                  [D, u.value.default_task_status]
                ])
              ]),
              e("div", Ce, [
                e("div", null, [
                  e("h4", Ee, s(t(r)("Default Project Status")), 1),
                  e("p", Ue, s(t(r)("Status assigned to new projects")), 1)
                ]),
                p(e("select", {
                  "onUpdate:modelValue": a[1] || (a[1] = (i) => u.value.default_project_status = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [
                  e("option", Oe, s(t(r)("Planning")), 1),
                  e("option", Re, s(t(r)("Active")), 1)
                ], 512), [
                  [D, u.value.default_project_status]
                ])
              ]),
              e("div", Ve, [
                e("div", null, [
                  e("h4", Te, s(t(r)("Project Code Prefix")), 1),
                  e("p", Ae, s(t(r)("Prefix for auto-generated project codes (e.g., ORG-2026-0001)")), 1)
                ]),
                p(e("input", {
                  "onUpdate:modelValue": a[2] || (a[2] = (i) => u.value.project_code_prefix = i),
                  type: "text",
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-32 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400",
                  maxlength: "10"
                }, null, 512), [
                  [M, u.value.project_code_prefix]
                ])
              ]),
              e("div", De, [
                e("div", null, [
                  e("h4", Me, s(t(r)("Default Priority")), 1),
                  e("p", Pe, s(t(r)("Priority assigned to new tasks")), 1)
                ]),
                p(e("select", {
                  "onUpdate:modelValue": a[3] || (a[3] = (i) => u.value.default_priority = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [
                  e("option", Ne, s(t(r)("Low")), 1),
                  e("option", Ie, s(t(r)("Medium")), 1),
                  e("option", Fe, s(t(r)("High")), 1),
                  e("option", Le, s(t(r)("Urgent")), 1)
                ], 512), [
                  [D, u.value.default_priority]
                ])
              ])
            ])
          ], 64)) : c.value === "features" ? (y(), b(O, { key: 2 }, [
            e("div", qe, [
              e("h3", Je, s(t(r)("Features")), 1),
              e("p", Ge, s(t(r)("Enable or disable optional features")), 1)
            ]),
            e("div", $e, [
              e("div", Be, [
                e("div", null, [
                  e("h4", He, s(t(r)("Auto Calculate Progress")), 1),
                  e("p", We, s(t(r)("Automatically calculate project progress from task completion")), 1)
                ]),
                e("label", Ye, [
                  p(e("input", {
                    "onUpdate:modelValue": a[4] || (a[4] = (i) => u.value.auto_calculate_progress = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [C, u.value.auto_calculate_progress]
                  ]),
                  a[16] || (a[16] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  a[17] || (a[17] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Xe, [
                e("div", null, [
                  e("h4", ze, s(t(r)("Auto Set Missed Milestones")), 1),
                  e("p", Ke, s(t(r)("Automatically mark milestones as missed when overdue")), 1)
                ]),
                e("label", Qe, [
                  p(e("input", {
                    "onUpdate:modelValue": a[5] || (a[5] = (i) => u.value.auto_set_missed_milestones = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [C, u.value.auto_set_missed_milestones]
                  ]),
                  a[18] || (a[18] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  a[19] || (a[19] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Ze, [
                e("div", null, [
                  e("h4", et, s(t(r)("Enable Time Tracking")), 1),
                  e("p", tt, s(t(r)("Allow users to log time against tasks")), 1)
                ]),
                e("label", rt, [
                  p(e("input", {
                    "onUpdate:modelValue": a[6] || (a[6] = (i) => u.value.enable_time_tracking = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [C, u.value.enable_time_tracking]
                  ]),
                  a[20] || (a[20] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  a[21] || (a[21] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", st, [
                e("div", null, [
                  e("h4", at, s(t(r)("Default Weekly Capacity")), 1),
                  e("p", ot, s(t(r)("Default hours per week for contact capacity planning")), 1)
                ]),
                e("div", nt, [
                  p(e("input", {
                    "onUpdate:modelValue": a[7] || (a[7] = (i) => u.value.default_capacity_hours = i),
                    type: "number",
                    min: "1",
                    max: "168",
                    class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                  }, null, 512), [
                    [
                      M,
                      u.value.default_capacity_hours,
                      void 0,
                      { number: !0 }
                    ]
                  ]),
                  e("span", lt, s(t(r)("hours")), 1)
                ])
              ])
            ])
          ], 64)) : c.value === "notifications" ? (y(), b(O, { key: 3 }, [
            e("div", dt, [
              e("h3", it, s(t(r)("Notifications")), 1),
              e("p", ut, s(t(r)("Configure email notification settings")), 1)
            ]),
            e("div", gt, [
              e("div", ct, [
                e("div", null, [
                  e("h4", _t, s(t(r)("Task Assignment")), 1),
                  e("p", mt, s(t(r)("Send notification when a task is assigned to a user")), 1)
                ]),
                e("label", yt, [
                  p(e("input", {
                    "onUpdate:modelValue": a[8] || (a[8] = (i) => u.value.notify_on_task_assignment = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [C, u.value.notify_on_task_assignment]
                  ]),
                  a[22] || (a[22] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  a[23] || (a[23] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", bt, [
                e("div", null, [
                  e("h4", ft, s(t(r)("Status Changes")), 1),
                  e("p", pt, s(t(r)("Send notification when task status changes")), 1)
                ]),
                e("label", xt, [
                  p(e("input", {
                    "onUpdate:modelValue": a[9] || (a[9] = (i) => u.value.notify_on_status_change = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [C, u.value.notify_on_status_change]
                  ]),
                  a[24] || (a[24] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  a[25] || (a[25] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", kt, [
                e("div", null, [
                  e("h4", ht, s(t(r)("Due Date Reminders")), 1),
                  e("p", vt, s(t(r)("Send reminder before task due date")), 1)
                ]),
                e("label", wt, [
                  p(e("input", {
                    "onUpdate:modelValue": a[10] || (a[10] = (i) => u.value.notify_on_due_date = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [C, u.value.notify_on_due_date]
                  ]),
                  a[26] || (a[26] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  a[27] || (a[27] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", St, [
                e("div", null, [
                  e("h4", jt, s(t(r)("Reminder Lead Time")), 1),
                  e("p", Ct, s(t(r)("Days before due date to send reminder")), 1)
                ]),
                e("div", Et, [
                  p(e("input", {
                    "onUpdate:modelValue": a[11] || (a[11] = (i) => u.value.due_date_reminder_days = i),
                    type: "number",
                    min: "1",
                    max: "30",
                    class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                  }, null, 512), [
                    [
                      M,
                      u.value.due_date_reminder_days,
                      void 0,
                      { number: !0 }
                    ]
                  ]),
                  e("span", Ut, s(t(r)("days")), 1)
                ])
              ])
            ])
          ], 64)) : c.value === "updates" ? (y(), b(O, { key: 4 }, [
            e("div", Ot, [
              e("h3", Rt, s(t(r)("App Updates")), 1),
              e("p", Vt, s(t(r)("Check for new versions of Orga")), 1)
            ]),
            e("div", Tt, [
              e("div", At, [
                e("div", null, [
                  e("h4", Dt, s(t(r)("Installed Version")), 1),
                  e("p", Mt, s(t(r)("Currently running version")), 1)
                ]),
                e("span", Pt, " v" + s(t(d)?.current_version || t(re)), 1)
              ]),
              t(d) ? (y(), b("div", Nt, [
                e("div", null, [
                  e("h4", It, s(t(r)("Latest Version")), 1),
                  e("p", Ft, s(t(r)("Last checked: {0}", [t(d).checked_at ? new Date(t(d).checked_at).toLocaleString() : t(r)("Never")])), 1)
                ]),
                e("span", {
                  class: S([
                    "text-sm font-mono",
                    t(d).update_available ? "text-amber-600 dark:text-amber-400 font-semibold" : "text-green-600 dark:text-green-400"
                  ])
                }, " v" + s(t(d).latest_version), 3)
              ])) : v("", !0),
              t(d)?.update_available ? (y(), b("div", Lt, [
                e("div", qt, [
                  a[29] || (a[29] = e("i", { class: "fa-solid fa-circle-up text-amber-500 text-xl mt-0.5" }, null, -1)),
                  e("div", Jt, [
                    e("h4", Gt, s(t(r)("Update Available")), 1),
                    e("p", $t, s(t(r)("Version {0} is available. You are running {1}.", [t(d).latest_version, t(d).current_version])), 1),
                    t(d).release_notes ? (y(), b("div", Bt, [
                      j(s(t(d).release_notes.substring(0, 500)) + " ", 1),
                      t(d).release_notes.length > 500 ? (y(), b("span", Ht, "...")) : v("", !0)
                    ])) : v("", !0),
                    e("div", Wt, [
                      e("a", {
                        href: t(d).release_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        class: "inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded transition-colors no-underline"
                      }, [
                        a[28] || (a[28] = e("i", { class: "fa-brands fa-github text-xs" }, null, -1)),
                        j(" " + s(t(r)("View Release")), 1)
                      ], 8, Yt),
                      e("button", {
                        onClick: a[12] || (a[12] = //@ts-ignore
                        (...i) => t(R) && t(R)(...i)),
                        class: "px-3 py-1.5 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 rounded transition-colors"
                      }, s(t(r)("Dismiss")), 1)
                    ])
                  ])
                ])
              ])) : t(d) && !t(d).update_available ? (y(), b("div", Xt, [
                e("div", zt, [
                  a[30] || (a[30] = e("i", { class: "fa-solid fa-circle-check text-green-500 text-xl" }, null, -1)),
                  e("div", null, [
                    e("h4", Kt, s(t(r)("Up to Date")), 1),
                    e("p", Qt, s(t(r)("You are running the latest version of Orga.")), 1)
                  ])
                ])
              ])) : (y(), b("div", Zt, [
                e("p", er, s(t(r)("No update information available yet.")), 1)
              ])),
              t(n) ? (y(), b("div", tr, [
                a[31] || (a[31] = e("i", { class: "fa-solid fa-exclamation-triangle mr-1" }, null, -1)),
                j(" " + s(t(r)("Update check failed: {0}", [t(n)])), 1)
              ])) : v("", !0),
              e("div", rr, [
                e("button", {
                  onClick: a[13] || (a[13] = //@ts-ignore
                  (...i) => t(f) && t(f)(...i)),
                  disabled: t(l),
                  class: "px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                }, [
                  e("i", {
                    class: S(["fa-solid", t(l) ? "fa-spinner fa-spin" : "fa-rotate"])
                  }, null, 2),
                  j(" " + s(t(l) ? t(r)("Checking...") : t(r)("Check for Updates")), 1)
                ], 8, sr)
              ])
            ])
          ], 64)) : v("", !0),
          c.value !== "updates" ? (y(), b("div", ar, [
            e("button", {
              onClick: q,
              class: "px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors"
            }, s(t(r)("Reset to Defaults")), 1),
            e("button", {
              onClick: L,
              disabled: U.value,
              class: "px-4 py-2 bg-orga-500 hover:bg-orga-600 dark:bg-orga-600 dark:hover:bg-orga-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            }, [
              U.value ? (y(), b("i", nr)) : v("", !0),
              j(" " + s(U.value ? t(r)("Saving...") : t(r)("Save Changes")), 1)
            ], 8, or)
          ])) : v("", !0)
        ])
      ]))
    ]));
  }
});
export {
  ir as OrgaSettings
};
