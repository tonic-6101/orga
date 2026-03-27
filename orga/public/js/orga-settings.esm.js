import { ref as b, computed as Z, onUnmounted as K, h as I, defineComponent as Q, onMounted as W, openBlock as f, createElementBlock as h, createElementVNode as e, createVNode as M, unref as t, toDisplayString as r, Fragment as q, renderList as ee, normalizeClass as y, createTextVNode as R, createCommentVNode as v, withDirectives as S, vModelSelect as V, vModelText as N, createBlock as F } from "/assets/dock/js/vendor/vue.esm.js";
function te(i) {
  let s = Object.assign({}, i);
  if (!s.url)
    throw new Error("[request] options.url is required");
  s.transformRequest && (s = s.transformRequest(i)), s.responseType || (s.responseType = "json"), s.method || (s.method = "GET");
  let c = s.url, l;
  if (s.params)
    if (s.method === "GET") {
      let d = new URLSearchParams();
      for (let o in s.params)
        d.append(o, s.params[o]);
      c = s.url + "?" + d.toString();
    } else
      l = JSON.stringify(s.params);
  return fetch(c, {
    method: s.method || "GET",
    headers: s.headers,
    body: l
  }).then((d) => {
    if (s.transformResponse)
      return s.transformResponse(d, s);
    if (d.status >= 200 && d.status < 300)
      return s.responseType === "json" ? d.json() : d;
    {
      let o = new Error(d.statusText);
      throw o.response = d, o;
    }
  }).catch((d) => {
    if (s.transformError)
      return s.transformError(d);
    throw d;
  });
}
let se = {};
function ae(i) {
  return se[i] ?? null;
}
function re(i) {
  return te({
    ...i,
    transformRequest: (s = {}) => {
      if (!s.url)
        throw new Error("[frappeRequest] options.url is required");
      let c = Object.assign(
        {
          Accept: "application/json",
          "Content-Type": "application/json; charset=utf-8",
          "X-Frappe-Site-Name": window.location.hostname
        },
        s.headers || {}
      );
      return window.csrf_token && window.csrf_token !== "{{ csrf_token }}" && (c["X-Frappe-CSRF-Token"] = window.csrf_token), !s.url.startsWith("/") && !s.url.startsWith("http") && (s.url = "/api/method/" + s.url), {
        ...s,
        method: s.method || "POST",
        headers: c
      };
    },
    transformResponse: async (s, c) => {
      let l = c.url;
      if (s.ok) {
        const d = await s.json();
        if (d.docs || l === "/api/method/login")
          return d;
        if (d.exc)
          try {
            console.groupCollapsed(l), console.log(c);
            let o = JSON.parse(d.exc);
            for (let p of o)
              console.log(p);
            console.groupEnd();
          } catch (o) {
            console.warn("Error printing debug messages", o);
          }
        if (d._server_messages) {
          let o = ae("serverMessagesHandler") || c.onServerMessages || null;
          o && o(JSON.parse(d?._server_messages) || []);
        }
        return d.message;
      } else {
        let d = await s.text(), o, p;
        try {
          o = JSON.parse(d);
        } catch {
        }
        let C = [
          [c.url, o?.exc_type, o?._error_message].filter(Boolean).join(" ")
        ];
        if (o.exc) {
          p = o.exc;
          try {
            p = JSON.parse(p)[0], console.log(p);
          } catch {
          }
        }
        let _ = new Error(C.join(`
`));
        throw _.exc_type = o.exc_type, _.exc = p, _.response = s, _.status = d.status, _.messages = o._server_messages ? JSON.parse(o._server_messages) : [], _.messages = _.messages.concat(o.message), _.messages = _.messages.map((x) => {
          try {
            return JSON.parse(x).message;
          } catch {
            return x;
          }
        }), _.messages = _.messages.filter(Boolean), _.messages.length || (_.messages = o._error_message ? [o._error_message] : ["Internal Server Error"]), c.onError && c.onError(_), _;
      }
    },
    transformError: (s) => {
      throw i.onError && i.onError(s), s;
    }
  });
}
function z() {
  const i = b(!1), s = b(null);
  async function c(l, d = {}) {
    i.value = !0, s.value = null;
    try {
      return await re({
        url: "/api/method/" + l,
        params: d
      });
    } catch (o) {
      const p = o instanceof Error ? o.message : "An error occurred";
      throw s.value = p, console.error(`API Error [${l}]:`, o), o;
    } finally {
      i.value = !1;
    }
  }
  return { call: c, loading: i, error: s };
}
function oe() {
  const { call: i, loading: s, error: c } = z();
  return {
    loading: s,
    error: c,
    call: i,
    getSettings: () => i("orga.orga.api.settings.get_settings"),
    updateSettings: (l) => i("orga.orga.api.settings.update_settings", { data: JSON.stringify(l) })
  };
}
const k = b(null), j = b(!1), T = b(null), L = "orga_update_dismissed_version";
function ne() {
  try {
    return localStorage.getItem(L);
  } catch {
    return null;
  }
}
const ie = Z(() => {
  if (!k.value?.update_available) return !1;
  const i = ne();
  return !(i && i === k.value.latest_version);
});
let J = !1;
function le() {
  const { call: i } = z();
  async function s() {
    if (!j.value) {
      j.value = !0, T.value = null;
      try {
        const o = await i(
          "orga.orga.api.settings.get_update_info"
        );
        o && o.current_version && (k.value = o);
      } catch {
      } finally {
        j.value = !1;
      }
    }
  }
  async function c() {
    j.value = !0, T.value = null;
    try {
      const o = await i(
        "orga.orga.api.settings.check_updates_now"
      );
      o && o.current_version && (k.value = o);
    } catch (o) {
      T.value = o.message || "Check failed";
    } finally {
      j.value = !1;
    }
  }
  function l() {
    k.value?.latest_version && (localStorage.setItem(L, k.value.latest_version), k.value = { ...k.value });
  }
  function d() {
    localStorage.removeItem(L), k.value && (k.value = { ...k.value });
  }
  return J || (J = !0, s()), K(() => {
  }), {
    updateInfo: k,
    updateAvailable: ie,
    isChecking: j,
    checkError: T,
    fetchUpdateInfo: s,
    forceCheck: c,
    dismissUpdate: l,
    undismissUpdate: d
  };
}
function a(i, s) {
  let l = (window.__messages || {})[i] || i;
  if (s)
    if (Array.isArray(s))
      for (let d = 0; d < s.length; d++)
        l = l.replace(new RegExp(`\\{${d}\\}`, "g"), String(s[d]));
    else
      for (const [d, o] of Object.entries(s))
        l = l.replace(new RegExp(`\\{${d}\\}`, "g"), String(o));
  return l;
}
const de = "0.15.4";
const ce = (i) => {
  for (const s in i)
    if (s.startsWith("aria-") || s === "role" || s === "title")
      return !0;
  return !1;
};
const B = (i) => i === "";
const ue = (...i) => i.filter((s, c, l) => !!s && s.trim() !== "" && l.indexOf(s) === c).join(" ").trim();
const G = (i) => i.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const ge = (i) => i.replace(
  /^([A-Z])|[\s-_]+(\w)/g,
  (s, c, l) => l ? l.toUpperCase() : c.toLowerCase()
);
const _e = (i) => {
  const s = ge(i);
  return s.charAt(0).toUpperCase() + s.slice(1);
};
var E = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": 2,
  "stroke-linecap": "round",
  "stroke-linejoin": "round"
};
const fe = ({
  name: i,
  iconNode: s,
  absoluteStrokeWidth: c,
  "absolute-stroke-width": l,
  strokeWidth: d,
  "stroke-width": o,
  size: p = E.width,
  color: C = E.stroke,
  ..._
}, { slots: x }) => I(
  "svg",
  {
    ...E,
    ..._,
    width: p,
    height: p,
    stroke: C,
    "stroke-width": B(c) || B(l) || c === !0 || l === !0 ? Number(d || o || E["stroke-width"]) * 24 / Number(p) : d || o || E["stroke-width"],
    class: ue(
      "lucide",
      _.class,
      ...i ? [`lucide-${G(_e(i))}-icon`, `lucide-${G(i)}`] : ["lucide-icon"]
    ),
    ...!x.default && !ce(_) && { "aria-hidden": "true" }
  },
  [...s.map((n) => I(...n)), ...x.default ? [x.default()] : []]
);
const A = (i, s) => (c, { slots: l, attrs: d }) => I(
  fe,
  {
    ...d,
    ...c,
    iconNode: s,
    name: i
  },
  l
);
const xe = A("circle-arrow-up", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m16 12-4-4-4 4", key: "177agl" }],
  ["path", { d: "M12 16V8", key: "1sbj14" }]
]);
const me = A("circle-check", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m9 12 2 2 4-4", key: "dzmm74" }]
]);
const he = A("loader-circle", [
  ["path", { d: "M21 12a9 9 0 1 1-6.219-8.56", key: "13zald" }]
]);
const pe = A("rotate-ccw", [
  ["path", { d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8", key: "1357e3" }],
  ["path", { d: "M3 3v5h5", key: "1xhq8a" }]
]);
const H = A("triangle-alert", [
  [
    "path",
    {
      d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",
      key: "wmoenq"
    }
  ],
  ["path", { d: "M12 9v4", key: "juzpu7" }],
  ["path", { d: "M12 17h.01", key: "p32p05" }]
]), ye = {
  key: 0,
  class: "flex items-center justify-center py-20"
}, ke = {
  key: 1,
  class: "max-w-md"
}, be = { class: "rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-center" }, ve = { class: "text-sm font-medium text-red-800 dark:text-red-300 mb-2" }, we = { class: "text-xs text-red-600 dark:text-red-400 mb-4" }, Ce = { class: "flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6" }, Se = ["onClick"], je = {
  key: 0,
  class: "absolute bottom-0 left-0 right-0 h-0.5 bg-accent-600 dark:bg-accent-400 rounded-full"
}, Ee = {
  key: 0,
  class: "max-w-2xl space-y-6"
}, Ae = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, Oe = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Ue = { class: "mb-4 text-xs text-gray-400 dark:text-gray-500" }, Me = { class: "space-y-5" }, Re = { class: "flex items-center gap-4" }, Te = { class: "flex-1" }, Pe = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, De = { class: "text-xs text-gray-400 dark:text-gray-500" }, Ve = { value: "Open" }, Ne = { value: "In Progress" }, Ie = { class: "flex items-center gap-4" }, Le = { class: "flex-1" }, $e = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, qe = { class: "text-xs text-gray-400 dark:text-gray-500" }, Fe = { value: "Planning" }, Je = { value: "Active" }, Be = { class: "flex items-center gap-4" }, Ge = { class: "flex-1" }, He = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, ze = { class: "text-xs text-gray-400 dark:text-gray-500" }, Ye = { class: "flex items-center gap-4" }, Xe = { class: "flex-1" }, Ze = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, Ke = { class: "text-xs text-gray-400 dark:text-gray-500" }, Qe = { value: "Low" }, We = { value: "Medium" }, et = { value: "High" }, tt = { value: "Urgent" }, st = {
  key: 1,
  class: "max-w-2xl space-y-6"
}, at = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, rt = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, ot = { class: "mb-4 text-xs text-gray-400 dark:text-gray-500" }, nt = { class: "space-y-5" }, it = { class: "flex items-center gap-4" }, lt = { class: "flex-1" }, dt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, ct = { class: "text-xs text-gray-400 dark:text-gray-500" }, ut = ["aria-checked"], gt = { class: "flex items-center gap-4" }, _t = { class: "flex-1" }, ft = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, xt = { class: "text-xs text-gray-400 dark:text-gray-500" }, mt = ["aria-checked"], ht = { class: "flex items-center gap-4" }, pt = { class: "flex-1" }, yt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, kt = { class: "text-xs text-gray-400 dark:text-gray-500" }, bt = ["aria-checked"], vt = { class: "flex items-center gap-4" }, wt = { class: "flex-1" }, Ct = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, St = { class: "text-xs text-gray-400 dark:text-gray-500" }, jt = { class: "flex items-center gap-1.5" }, Et = { class: "text-xs text-gray-400 dark:text-gray-500" }, At = {
  key: 2,
  class: "max-w-2xl space-y-6"
}, Ot = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, Ut = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Mt = { class: "mb-4 text-xs text-gray-400 dark:text-gray-500" }, Rt = { class: "space-y-5" }, Tt = { class: "flex items-center gap-4" }, Pt = { class: "flex-1" }, Dt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, Vt = { class: "text-xs text-gray-400 dark:text-gray-500" }, Nt = ["aria-checked"], It = { class: "flex items-center gap-4" }, Lt = { class: "flex-1" }, $t = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, qt = { class: "text-xs text-gray-400 dark:text-gray-500" }, Ft = ["aria-checked"], Jt = { class: "flex items-center gap-4" }, Bt = { class: "flex-1" }, Gt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, Ht = { class: "text-xs text-gray-400 dark:text-gray-500" }, zt = ["aria-checked"], Yt = { class: "flex items-center gap-4" }, Xt = { class: "flex-1" }, Zt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, Kt = { class: "text-xs text-gray-400 dark:text-gray-500" }, Qt = { class: "flex items-center gap-1.5" }, Wt = { class: "text-xs text-gray-400 dark:text-gray-500" }, es = {
  key: 3,
  class: "max-w-2xl space-y-6"
}, ts = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, ss = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, as = { class: "space-y-5" }, rs = { class: "flex items-center gap-4" }, os = { class: "flex-1" }, ns = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, is = { class: "text-xs text-gray-400 dark:text-gray-500" }, ls = { class: "text-sm font-mono text-gray-900 dark:text-white" }, ds = {
  key: 0,
  class: "flex items-center gap-4"
}, cs = { class: "flex-1" }, us = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, gs = { class: "text-xs text-gray-400 dark:text-gray-500" }, _s = {
  key: 0,
  class: "rounded-lg border border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 p-5"
}, fs = { class: "flex items-start gap-3" }, xs = { class: "flex-1" }, ms = { class: "text-sm font-semibold text-amber-800 dark:text-amber-300" }, hs = { class: "text-sm text-amber-700 dark:text-amber-400 mt-1" }, ps = {
  key: 0,
  class: "mt-3 text-xs text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded-lg p-3 max-h-40 overflow-y-auto whitespace-pre-wrap"
}, ys = { key: 0 }, ks = { class: "mt-3 flex items-center gap-3" }, bs = ["href"], vs = {
  key: 1,
  class: "rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-5"
}, ws = { class: "flex items-center gap-3" }, Cs = { class: "text-sm font-semibold text-green-800 dark:text-green-300" }, Ss = { class: "text-xs text-green-700 dark:text-green-400 mt-1" }, js = {
  key: 2,
  class: "text-xs text-red-500"
}, Es = ["disabled"], As = {
  key: 4,
  class: "flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4 mt-6"
}, Os = ["disabled"], Rs = /* @__PURE__ */ Q({
  __name: "Settings",
  setup(i) {
    const { getSettings: s, updateSettings: c } = oe(), { updateInfo: l, isChecking: d, checkError: o, forceCheck: p, dismissUpdate: C } = le(), _ = [
      { label: a("Defaults") },
      { label: a("Features") },
      { label: a("Notifications") },
      { label: a("Updates") }
    ], x = b(0), n = b({
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
    }), P = b(!0), O = b(!1), U = b(null), w = b(null);
    async function $() {
      P.value = !0, U.value = null;
      try {
        const m = await s();
        n.value = {
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
        U.value = m.message || a("Failed to load settings");
      } finally {
        P.value = !1;
      }
    }
    async function Y() {
      O.value = !0, w.value = null;
      try {
        await c(n.value), w.value = { type: "success", text: a("Saved") }, setTimeout(() => {
          w.value = null;
        }, 2500);
      } catch (m) {
        w.value = { type: "error", text: m.message || a("Failed to save") };
      } finally {
        O.value = !1;
      }
    }
    function X() {
      n.value = {
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
    return W($), (m, u) => P.value ? (f(), h("div", ye, [...u[14] || (u[14] = [
      e("div", { class: "h-6 w-6 animate-spin rounded-full border-2 border-accent-600 border-t-transparent" }, null, -1)
    ])])) : U.value ? (f(), h("div", ke, [
      e("div", be, [
        M(t(H), {
          class: "w-8 h-8 text-red-500 mx-auto mb-3",
          "aria-hidden": "true"
        }),
        e("h3", ve, r(t(a)("Error loading settings")), 1),
        e("p", we, r(U.value), 1),
        e("button", {
          class: "rounded-lg border border-red-300 dark:border-red-700 px-4 py-2 text-sm font-medium text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors",
          onClick: $
        }, r(t(a)("Try Again")), 1)
      ])
    ])) : (f(), h(q, { key: 2 }, [
      e("nav", Ce, [
        (f(), h(q, null, ee(_, (g, D) => e("button", {
          key: g.label,
          class: y(["relative px-3 py-2 text-sm font-medium transition-colors", x.value === D ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"]),
          onClick: (Us) => x.value = D
        }, [
          R(r(g.label) + " ", 1),
          x.value === D ? (f(), h("span", je)) : v("", !0)
        ], 10, Se)), 64))
      ]),
      x.value === 0 ? (f(), h("div", Ee, [
        e("div", Ae, [
          e("h2", Oe, r(t(a)("Default Values")), 1),
          e("p", Ue, r(t(a)("Configure default values for new projects and tasks")), 1),
          e("div", Me, [
            e("div", Re, [
              e("div", Te, [
                e("label", Pe, r(t(a)("Default Task Status")), 1),
                e("p", De, r(t(a)("Status assigned to new tasks")), 1)
              ]),
              S(e("select", {
                "onUpdate:modelValue": u[0] || (u[0] = (g) => n.value.default_task_status = g),
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, [
                e("option", Ve, r(t(a)("Open")), 1),
                e("option", Ne, r(t(a)("In Progress")), 1)
              ], 512), [
                [V, n.value.default_task_status]
              ])
            ]),
            e("div", Ie, [
              e("div", Le, [
                e("label", $e, r(t(a)("Default Project Status")), 1),
                e("p", qe, r(t(a)("Status assigned to new projects")), 1)
              ]),
              S(e("select", {
                "onUpdate:modelValue": u[1] || (u[1] = (g) => n.value.default_project_status = g),
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, [
                e("option", Fe, r(t(a)("Planning")), 1),
                e("option", Je, r(t(a)("Active")), 1)
              ], 512), [
                [V, n.value.default_project_status]
              ])
            ]),
            e("div", Be, [
              e("div", Ge, [
                e("label", He, r(t(a)("Project Code Prefix")), 1),
                e("p", ze, r(t(a)("Prefix for auto-generated project codes (e.g., ORG-2026-0001)")), 1)
              ]),
              S(e("input", {
                "onUpdate:modelValue": u[2] || (u[2] = (g) => n.value.project_code_prefix = g),
                type: "text",
                maxlength: "10",
                class: "w-32 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [N, n.value.project_code_prefix]
              ])
            ]),
            e("div", Ye, [
              e("div", Xe, [
                e("label", Ze, r(t(a)("Default Priority")), 1),
                e("p", Ke, r(t(a)("Priority assigned to new tasks")), 1)
              ]),
              S(e("select", {
                "onUpdate:modelValue": u[3] || (u[3] = (g) => n.value.default_priority = g),
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, [
                e("option", Qe, r(t(a)("Low")), 1),
                e("option", We, r(t(a)("Medium")), 1),
                e("option", et, r(t(a)("High")), 1),
                e("option", tt, r(t(a)("Urgent")), 1)
              ], 512), [
                [V, n.value.default_priority]
              ])
            ])
          ])
        ])
      ])) : x.value === 1 ? (f(), h("div", st, [
        e("div", at, [
          e("h2", rt, r(t(a)("Features")), 1),
          e("p", ot, r(t(a)("Enable or disable optional features")), 1),
          e("div", nt, [
            e("div", it, [
              e("div", lt, [
                e("label", dt, r(t(a)("Auto Calculate Progress")), 1),
                e("p", ct, r(t(a)("Automatically calculate project progress from task completion")), 1)
              ]),
              e("button", {
                class: y(["relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2", n.value.auto_calculate_progress ? "bg-accent-600 dark:bg-accent-400" : "bg-gray-200 dark:bg-gray-600"]),
                role: "switch",
                "aria-checked": !!n.value.auto_calculate_progress,
                onClick: u[4] || (u[4] = (g) => n.value.auto_calculate_progress = n.value.auto_calculate_progress ? 0 : 1)
              }, [
                e("span", {
                  class: y(["pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200", n.value.auto_calculate_progress ? "translate-x-4" : "translate-x-0"])
                }, null, 2)
              ], 10, ut)
            ]),
            e("div", gt, [
              e("div", _t, [
                e("label", ft, r(t(a)("Auto Set Missed Milestones")), 1),
                e("p", xt, r(t(a)("Automatically mark milestones as missed when overdue")), 1)
              ]),
              e("button", {
                class: y(["relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2", n.value.auto_set_missed_milestones ? "bg-accent-600 dark:bg-accent-400" : "bg-gray-200 dark:bg-gray-600"]),
                role: "switch",
                "aria-checked": !!n.value.auto_set_missed_milestones,
                onClick: u[5] || (u[5] = (g) => n.value.auto_set_missed_milestones = n.value.auto_set_missed_milestones ? 0 : 1)
              }, [
                e("span", {
                  class: y(["pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200", n.value.auto_set_missed_milestones ? "translate-x-4" : "translate-x-0"])
                }, null, 2)
              ], 10, mt)
            ]),
            e("div", ht, [
              e("div", pt, [
                e("label", yt, r(t(a)("Enable Time Tracking")), 1),
                e("p", kt, r(t(a)("Allow users to log time against tasks")), 1)
              ]),
              e("button", {
                class: y(["relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2", n.value.enable_time_tracking ? "bg-accent-600 dark:bg-accent-400" : "bg-gray-200 dark:bg-gray-600"]),
                role: "switch",
                "aria-checked": !!n.value.enable_time_tracking,
                onClick: u[6] || (u[6] = (g) => n.value.enable_time_tracking = n.value.enable_time_tracking ? 0 : 1)
              }, [
                e("span", {
                  class: y(["pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200", n.value.enable_time_tracking ? "translate-x-4" : "translate-x-0"])
                }, null, 2)
              ], 10, bt)
            ]),
            e("div", vt, [
              e("div", wt, [
                e("label", Ct, r(t(a)("Default Weekly Capacity")), 1),
                e("p", St, r(t(a)("Default hours per week for contact capacity planning")), 1)
              ]),
              e("div", jt, [
                S(e("input", {
                  "onUpdate:modelValue": u[7] || (u[7] = (g) => n.value.default_capacity_hours = g),
                  type: "number",
                  min: "1",
                  max: "168",
                  class: "w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white text-right focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                }, null, 512), [
                  [
                    N,
                    n.value.default_capacity_hours,
                    void 0,
                    { number: !0 }
                  ]
                ]),
                e("span", Et, r(t(a)("hours")), 1)
              ])
            ])
          ])
        ])
      ])) : x.value === 2 ? (f(), h("div", At, [
        e("div", Ot, [
          e("h2", Ut, r(t(a)("Email Notifications")), 1),
          e("p", Mt, r(t(a)("Configure email notification settings")), 1),
          e("div", Rt, [
            e("div", Tt, [
              e("div", Pt, [
                e("label", Dt, r(t(a)("Task Assignment")), 1),
                e("p", Vt, r(t(a)("Send notification when a task is assigned to a user")), 1)
              ]),
              e("button", {
                class: y(["relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2", n.value.notify_on_task_assignment ? "bg-accent-600 dark:bg-accent-400" : "bg-gray-200 dark:bg-gray-600"]),
                role: "switch",
                "aria-checked": !!n.value.notify_on_task_assignment,
                onClick: u[8] || (u[8] = (g) => n.value.notify_on_task_assignment = n.value.notify_on_task_assignment ? 0 : 1)
              }, [
                e("span", {
                  class: y(["pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200", n.value.notify_on_task_assignment ? "translate-x-4" : "translate-x-0"])
                }, null, 2)
              ], 10, Nt)
            ]),
            e("div", It, [
              e("div", Lt, [
                e("label", $t, r(t(a)("Status Changes")), 1),
                e("p", qt, r(t(a)("Send notification when task status changes")), 1)
              ]),
              e("button", {
                class: y(["relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2", n.value.notify_on_status_change ? "bg-accent-600 dark:bg-accent-400" : "bg-gray-200 dark:bg-gray-600"]),
                role: "switch",
                "aria-checked": !!n.value.notify_on_status_change,
                onClick: u[9] || (u[9] = (g) => n.value.notify_on_status_change = n.value.notify_on_status_change ? 0 : 1)
              }, [
                e("span", {
                  class: y(["pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200", n.value.notify_on_status_change ? "translate-x-4" : "translate-x-0"])
                }, null, 2)
              ], 10, Ft)
            ]),
            e("div", Jt, [
              e("div", Bt, [
                e("label", Gt, r(t(a)("Due Date Reminders")), 1),
                e("p", Ht, r(t(a)("Send reminder before task due date")), 1)
              ]),
              e("button", {
                class: y(["relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2", n.value.notify_on_due_date ? "bg-accent-600 dark:bg-accent-400" : "bg-gray-200 dark:bg-gray-600"]),
                role: "switch",
                "aria-checked": !!n.value.notify_on_due_date,
                onClick: u[10] || (u[10] = (g) => n.value.notify_on_due_date = n.value.notify_on_due_date ? 0 : 1)
              }, [
                e("span", {
                  class: y(["pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200", n.value.notify_on_due_date ? "translate-x-4" : "translate-x-0"])
                }, null, 2)
              ], 10, zt)
            ]),
            e("div", Yt, [
              e("div", Xt, [
                e("label", Zt, r(t(a)("Reminder Lead Time")), 1),
                e("p", Kt, r(t(a)("Days before due date to send reminder")), 1)
              ]),
              e("div", Qt, [
                S(e("input", {
                  "onUpdate:modelValue": u[11] || (u[11] = (g) => n.value.due_date_reminder_days = g),
                  type: "number",
                  min: "1",
                  max: "30",
                  class: "w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white text-right focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                }, null, 512), [
                  [
                    N,
                    n.value.due_date_reminder_days,
                    void 0,
                    { number: !0 }
                  ]
                ]),
                e("span", Wt, r(t(a)("days")), 1)
              ])
            ])
          ])
        ])
      ])) : x.value === 3 ? (f(), h("div", es, [
        e("div", ts, [
          e("h2", ss, r(t(a)("App Updates")), 1),
          e("div", as, [
            e("div", rs, [
              e("div", os, [
                e("label", ns, r(t(a)("Installed Version")), 1),
                e("p", is, r(t(a)("Currently running version")), 1)
              ]),
              e("span", ls, " v" + r(t(l)?.current_version || t(de)), 1)
            ]),
            t(l) ? (f(), h("div", ds, [
              e("div", cs, [
                e("label", us, r(t(a)("Latest Version")), 1),
                e("p", gs, r(t(a)("Last checked:")) + " " + r(t(l).checked_at ? new Date(t(l).checked_at).toLocaleString() : t(a)("Never")), 1)
              ]),
              e("span", {
                class: y(["text-sm font-mono", t(l).update_available ? "text-amber-600 dark:text-amber-400 font-semibold" : "text-green-600 dark:text-green-400"])
              }, " v" + r(t(l).latest_version), 3)
            ])) : v("", !0)
          ])
        ]),
        t(l)?.update_available ? (f(), h("div", _s, [
          e("div", fs, [
            M(t(xe), {
              class: "w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0",
              "aria-hidden": "true"
            }),
            e("div", xs, [
              e("h3", ms, r(t(a)("Update Available")), 1),
              e("p", hs, r(t(a)("Version {0} is available. You are running {1}.", [t(l).latest_version, t(l).current_version])), 1),
              t(l).release_notes ? (f(), h("div", ps, [
                R(r(t(l).release_notes.substring(0, 500)), 1),
                t(l).release_notes.length > 500 ? (f(), h("span", ys, "...")) : v("", !0)
              ])) : v("", !0),
              e("div", ks, [
                e("a", {
                  href: t(l).release_url,
                  target: "_blank",
                  rel: "noopener noreferrer",
                  class: "rounded-lg bg-amber-600 hover:bg-amber-700 px-4 py-2 text-sm font-medium text-white transition-colors no-underline"
                }, r(t(a)("View Release")), 9, bs),
                e("button", {
                  onClick: u[12] || (u[12] = //@ts-ignore
                  (...g) => t(C) && t(C)(...g)),
                  class: "rounded-lg px-3 py-1.5 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors"
                }, r(t(a)("Dismiss")), 1)
              ])
            ])
          ])
        ])) : t(l) && !t(l).update_available ? (f(), h("div", vs, [
          e("div", ws, [
            M(t(me), {
              class: "w-5 h-5 text-green-500",
              "aria-hidden": "true"
            }),
            e("div", null, [
              e("h3", Cs, r(t(a)("Up to Date")), 1),
              e("p", Ss, r(t(a)("You are running the latest version of Orga.")), 1)
            ])
          ])
        ])) : v("", !0),
        t(o) ? (f(), h("p", js, [
          M(t(H), {
            class: "w-3.5 h-3.5 inline mr-1",
            "aria-hidden": "true"
          }),
          R(" " + r(t(a)("Update check failed:")) + " " + r(t(o)), 1)
        ])) : v("", !0),
        e("button", {
          onClick: u[13] || (u[13] = //@ts-ignore
          (...g) => t(p) && t(p)(...g)),
          disabled: t(d),
          class: "flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
        }, [
          t(d) ? (f(), F(t(he), {
            key: 0,
            class: "w-4 h-4 animate-spin",
            "aria-hidden": "true"
          })) : (f(), F(t(pe), {
            key: 1,
            class: "w-4 h-4",
            "aria-hidden": "true"
          })),
          R(" " + r(t(d) ? t(a)("Checking...") : t(a)("Check for Updates")), 1)
        ], 8, Es)
      ])) : v("", !0),
      x.value !== 3 ? (f(), h("div", As, [
        e("button", {
          onClick: Y,
          disabled: O.value,
          class: "rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
        }, r(O.value ? t(a)("Saving…") : t(a)("Save")), 9, Os),
        e("button", {
          onClick: X,
          class: "rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        }, r(t(a)("Reset to Defaults")), 1),
        w.value ? (f(), h("span", {
          key: 0,
          class: y(["text-xs", w.value.type === "success" ? "text-green-600 dark:text-green-400" : "text-red-500"])
        }, r(w.value.text), 3)) : v("", !0)
      ])) : v("", !0)
    ], 64));
  }
});
export {
  Rs as OrgaSettings
};
