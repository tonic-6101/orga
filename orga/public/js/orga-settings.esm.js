import { ref as v, computed as V, onUnmounted as Z, defineComponent as q, onMounted as W, openBlock as y, createElementBlock as _, createElementVNode as e, toDisplayString as a, unref as t, Fragment as N, renderList as $, withModifiers as z, normalizeClass as C, createTextVNode as D, createCommentVNode as w, withDirectives as f, vModelSelect as K, vModelText as O, createStaticVNode as X, vModelCheckbox as R } from "/assets/dock/js/vendor/vue.esm.js";
function Q(u) {
  let o = Object.assign({}, u);
  if (!o.url)
    throw new Error("[request] options.url is required");
  o.transformRequest && (o = o.transformRequest(u)), o.responseType || (o.responseType = "json"), o.method || (o.method = "GET");
  let c = o.url, g;
  if (o.params)
    if (o.method === "GET") {
      let l = new URLSearchParams();
      for (let n in o.params)
        l.append(n, o.params[n]);
      c = o.url + "?" + l.toString();
    } else
      g = JSON.stringify(o.params);
  return fetch(c, {
    method: o.method || "GET",
    headers: o.headers,
    body: g
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
let ee = {};
function te(u) {
  return ee[u] ?? null;
}
function re(u) {
  return Q({
    ...u,
    transformRequest: (o = {}) => {
      if (!o.url)
        throw new Error("[frappeRequest] options.url is required");
      let c = Object.assign(
        {
          Accept: "application/json",
          "Content-Type": "application/json; charset=utf-8",
          "X-Frappe-Site-Name": window.location.hostname
        },
        o.headers || {}
      );
      return window.csrf_token && window.csrf_token !== "{{ csrf_token }}" && (c["X-Frappe-CSRF-Token"] = window.csrf_token), !o.url.startsWith("/") && !o.url.startsWith("http") && (o.url = "/api/method/" + o.url), {
        ...o,
        method: o.method || "POST",
        headers: c
      };
    },
    transformResponse: async (o, c) => {
      let g = c.url;
      if (o.ok) {
        const l = await o.json();
        if (l.docs || g === "/api/method/login")
          return l;
        if (l.exc)
          try {
            console.groupCollapsed(g), console.log(c);
            let n = JSON.parse(l.exc);
            for (let b of n)
              console.log(b);
            console.groupEnd();
          } catch (n) {
            console.warn("Error printing debug messages", n);
          }
        if (l._server_messages) {
          let n = te("serverMessagesHandler") || c.onServerMessages || null;
          n && n(JSON.parse(l?._server_messages) || []);
        }
        return l.message;
      } else {
        let l = await o.text(), n, b;
        try {
          n = JSON.parse(l);
        } catch {
        }
        let E = [
          [c.url, n?.exc_type, n?._error_message].filter(Boolean).join(" ")
        ];
        if (n.exc) {
          b = n.exc;
          try {
            b = JSON.parse(b)[0], console.log(b);
          } catch {
          }
        }
        let p = new Error(E.join(`
`));
        throw p.exc_type = n.exc_type, p.exc = b, p.response = o, p.status = l.status, p.messages = n._server_messages ? JSON.parse(n._server_messages) : [], p.messages = p.messages.concat(n.message), p.messages = p.messages.map((x) => {
          try {
            return JSON.parse(x).message;
          } catch {
            return x;
          }
        }), p.messages = p.messages.filter(Boolean), p.messages.length || (p.messages = n._error_message ? [n._error_message] : ["Internal Server Error"]), c.onError && c.onError(p), p;
      }
    },
    transformError: (o) => {
      throw u.onError && u.onError(o), o;
    }
  });
}
function H() {
  const u = v(!1), o = v(null);
  async function c(g, l = {}) {
    u.value = !0, o.value = null;
    try {
      return await re({
        url: "/api/method/" + g,
        params: l
      });
    } catch (n) {
      const b = n instanceof Error ? n.message : "An error occurred";
      throw o.value = b, console.error(`API Error [${g}]:`, n), n;
    } finally {
      u.value = !1;
    }
  }
  return { call: c, loading: u, error: o };
}
function B() {
  const { call: u, loading: o, error: c } = H();
  return {
    loading: o,
    error: c,
    call: u,
    getSettings: () => u("orga.orga.api.settings.get_settings"),
    updateSettings: (g) => u("orga.orga.api.settings.update_settings", { data: JSON.stringify(g) })
  };
}
const S = v("USD");
let T = !1;
function ae() {
  const { getSettings: u } = B();
  async function o() {
    try {
      const n = await u();
      S.value = n.default_currency || "USD", T = !0;
    } catch (n) {
      console.error("Failed to load currency setting:", n);
    }
  }
  function c(n) {
    return !n && n !== 0 ? new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: S.value,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(0) : new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: S.value,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(n);
  }
  T || (T = !0, o());
  const g = V(() => ({
    EUR: "€",
    USD: "$",
    GBP: "£",
    CHF: "CHF",
    JPY: "¥",
    INR: "₹",
    KRW: "₩",
    BRL: "R$",
    CNY: "¥",
    TRY: "₺",
    PLN: "zł",
    CZK: "Kč",
    HUF: "Ft",
    ZAR: "R",
    SEK: "kr",
    NOK: "kr",
    DKK: "kr"
  })[S.value] || S.value), l = V(() => ({
    USD: "fa-solid fa-dollar-sign",
    EUR: "fa-solid fa-euro-sign",
    GBP: "fa-solid fa-sterling-sign",
    JPY: "fa-solid fa-yen-sign",
    CNY: "fa-solid fa-yen-sign",
    INR: "fa-solid fa-indian-rupee-sign",
    KRW: "fa-solid fa-won-sign",
    TRY: "fa-solid fa-lira-sign",
    BRL: "fa-solid fa-brazilian-real-sign"
  })[S.value] || "fa-solid fa-coins");
  return { currency: S, formatCurrency: c, loadCurrency: o, currencySymbol: g, currencyIcon: l };
}
const k = v(null), U = v(!1), A = v(null), I = "orga_update_dismissed_version";
function se() {
  try {
    return localStorage.getItem(I);
  } catch {
    return null;
  }
}
const oe = V(() => {
  if (!k.value?.update_available) return !1;
  const u = se();
  return !(u && u === k.value.latest_version);
});
let Y = !1;
function ne() {
  const { call: u } = H();
  async function o() {
    if (!U.value) {
      U.value = !0, A.value = null;
      try {
        const n = await u(
          "orga.orga.api.settings.get_update_info"
        );
        n && n.current_version && (k.value = n);
      } catch {
      } finally {
        U.value = !1;
      }
    }
  }
  async function c() {
    U.value = !0, A.value = null;
    try {
      const n = await u(
        "orga.orga.api.settings.check_updates_now"
      );
      n && n.current_version && (k.value = n);
    } catch (n) {
      A.value = n.message || "Check failed";
    } finally {
      U.value = !1;
    }
  }
  function g() {
    k.value?.latest_version && (localStorage.setItem(I, k.value.latest_version), k.value = { ...k.value });
  }
  function l() {
    localStorage.removeItem(I), k.value && (k.value = { ...k.value });
  }
  return Y || (Y = !0, o()), Z(() => {
  }), {
    updateInfo: k,
    updateAvailable: oe,
    isChecking: U,
    checkError: A,
    fetchUpdateInfo: o,
    forceCheck: c,
    dismissUpdate: g,
    undismissUpdate: l
  };
}
function r(u, o) {
  let g = (window.__messages || {})[u] || u;
  if (o)
    if (Array.isArray(o))
      for (let l = 0; l < o.length; l++)
        g = g.replace(new RegExp(`\\{${l}\\}`, "g"), String(o[l]));
    else
      for (const [l, n] of Object.entries(o))
        g = g.replace(new RegExp(`\\{${l}\\}`, "g"), String(n));
  return g;
}
const le = "0.15.0", ie = { class: "p-6 bg-white dark:bg-gray-950 min-h-full" }, de = { class: "mb-6" }, ue = { class: "text-2xl font-semibold text-gray-900 dark:text-gray-100 m-0" }, ce = {
  key: 0,
  class: "flex items-center justify-center py-20"
}, ge = { class: "text-center" }, me = { class: "text-gray-500 dark:text-gray-400" }, ye = {
  key: 1,
  class: "flex items-center justify-center py-20"
}, _e = { class: "bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center" }, pe = { class: "text-red-800 dark:text-red-300 font-medium mb-2" }, fe = { class: "text-red-600 dark:text-red-400 text-sm mb-4" }, be = {
  key: 2,
  class: "flex gap-6"
}, xe = { class: "w-60 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg py-3 shrink-0" }, ke = ["onClick"], ve = { class: "flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg" }, he = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, we = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, Se = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, Ce = { class: "p-6" }, De = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Re = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ue = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, je = { value: "Open" }, Ne = { value: "In Progress" }, Ee = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Pe = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ke = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ae = { value: "Planning" }, Fe = { value: "Active" }, Oe = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Te = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ve = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ie = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Me = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Le = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ye = { value: "Low" }, He = { value: "Medium" }, Be = { value: "High" }, Ge = { value: "Urgent" }, Je = { class: "flex justify-between items-center py-3" }, Ze = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, qe = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, We = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, $e = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, ze = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, Xe = { class: "p-6" }, Qe = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, et = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, tt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, rt = { class: "relative inline-block w-11 h-6" }, at = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, st = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, ot = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, nt = { class: "relative inline-block w-11 h-6" }, lt = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, it = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, dt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, ut = { class: "relative inline-block w-11 h-6" }, ct = { class: "flex justify-between items-center py-3" }, gt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, mt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, yt = { class: "flex items-center gap-2" }, _t = { class: "text-sm text-gray-500 dark:text-gray-400" }, pt = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, ft = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, bt = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, xt = { class: "p-6" }, kt = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, vt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, ht = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, wt = { class: "relative inline-block w-11 h-6" }, St = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Ct = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Dt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Rt = { class: "relative inline-block w-11 h-6" }, Ut = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, jt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Nt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Et = { class: "relative inline-block w-11 h-6" }, Pt = { class: "flex justify-between items-center py-3" }, Kt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, At = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ft = { class: "flex items-center gap-2" }, Ot = { class: "text-sm text-gray-500 dark:text-gray-400" }, Tt = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, Vt = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, It = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, Mt = { class: "p-6" }, Lt = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Yt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ht = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Bt = { class: "text-sm font-mono text-gray-900 dark:text-gray-100" }, Gt = {
  key: 0,
  class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700"
}, Jt = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Zt = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, qt = {
  key: 1,
  class: "mt-4 p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg"
}, Wt = { class: "flex items-start gap-3" }, $t = { class: "flex-1" }, zt = { class: "text-sm font-semibold text-amber-800 dark:text-amber-300 m-0" }, Xt = { class: "text-sm text-amber-700 dark:text-amber-400 mt-1 mb-0" }, Qt = {
  key: 0,
  class: "mt-3 text-xs text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded p-3 max-h-40 overflow-y-auto whitespace-pre-wrap"
}, er = { key: 0 }, tr = { class: "mt-3 flex items-center gap-3" }, rr = ["href"], ar = {
  key: 2,
  class: "mt-4 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg"
}, sr = { class: "flex items-center gap-3" }, or = { class: "text-sm font-semibold text-green-800 dark:text-green-300 m-0" }, nr = { class: "text-sm text-green-700 dark:text-green-400 mt-1 mb-0" }, lr = {
  key: 3,
  class: "mt-4 p-4 bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-600 rounded-lg text-center"
}, ir = { class: "text-sm text-gray-500 dark:text-gray-400 m-0" }, dr = {
  key: 4,
  class: "mt-3 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400"
}, ur = { class: "mt-6 pt-4 border-t border-gray-100 dark:border-gray-700" }, cr = ["disabled"], gr = {
  key: 5,
  class: "p-4 bg-gray-50 dark:bg-gray-700/50 flex justify-end gap-3 border-t border-gray-200 dark:border-gray-700"
}, mr = ["disabled"], yr = {
  key: 0,
  class: "fa-solid fa-spinner fa-spin"
}, fr = /* @__PURE__ */ q({
  __name: "Settings",
  setup(u) {
    const { getSettings: o, updateSettings: c } = B(), { loadCurrency: g } = ae(), { updateInfo: l, isChecking: n, checkError: b, forceCheck: E, dismissUpdate: p } = ne(), x = v("defaults"), M = [
      { id: "defaults", name: r("Defaults"), icon: "sliders" },
      { id: "features", name: r("Features"), icon: "toggle-on" },
      { id: "notifications", name: r("Notifications"), icon: "bell" },
      { id: "updates", name: r("Updates"), icon: "arrow-up-from-bracket" }
    ], d = v({
      default_task_status: "Open",
      default_project_status: "Planning",
      project_code_prefix: "ORG",
      default_priority: "Medium",
      default_currency: "USD",
      auto_calculate_progress: 1,
      auto_set_missed_milestones: 1,
      enable_time_tracking: 0,
      default_capacity_hours: 40,
      notify_on_task_assignment: 1,
      notify_on_status_change: 0,
      notify_on_due_date: 1,
      due_date_reminder_days: 1
    }), F = v(!0), j = v(!1), P = v(null), h = v(null);
    async function L() {
      F.value = !0, P.value = null;
      try {
        const m = await o();
        d.value = {
          default_task_status: m.default_task_status || "Open",
          default_project_status: m.default_project_status || "Planning",
          project_code_prefix: m.project_code_prefix || "ORG",
          default_priority: m.default_priority || "Medium",
          default_currency: m.default_currency || "USD",
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
        console.error("Failed to load settings:", m), P.value = m.message || r("Failed to load settings");
      } finally {
        F.value = !1;
      }
    }
    async function G() {
      j.value = !0, h.value = null;
      try {
        await c(d.value), await g(), h.value = { type: "success", text: r("Settings saved successfully") }, setTimeout(() => {
          h.value = null;
        }, 3e3);
      } catch (m) {
        console.error("Failed to save settings:", m), h.value = { type: "error", text: m.message || r("Failed to save settings") };
      } finally {
        j.value = !1;
      }
    }
    function J() {
      d.value = {
        default_task_status: "Open",
        default_project_status: "Planning",
        project_code_prefix: "ORG",
        default_priority: "Medium",
        default_currency: "USD",
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
    return W(L), (m, s) => (y(), _("div", ie, [
      e("div", de, [
        e("h1", ue, a(t(r)("Settings")), 1)
      ]),
      F.value ? (y(), _("div", ce, [
        e("div", ge, [
          s[15] || (s[15] = e("i", { class: "fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3" }, null, -1)),
          e("p", me, a(t(r)("Loading settings...")), 1)
        ])
      ])) : P.value ? (y(), _("div", ye, [
        e("div", _e, [
          s[16] || (s[16] = e("i", { class: "fa-solid fa-exclamation-triangle text-red-500 text-3xl mb-3" }, null, -1)),
          e("h3", pe, a(t(r)("Error loading settings")), 1),
          e("p", fe, a(P.value), 1),
          e("button", {
            onClick: L,
            class: "px-4 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/60"
          }, a(t(r)("Try Again")), 1)
        ])
      ])) : (y(), _("div", be, [
        e("nav", xe, [
          (y(), _(N, null, $(M, (i) => e("a", {
            key: i.id,
            href: "#",
            class: C([
              "flex items-center gap-3 px-5 py-3 text-sm transition-all no-underline",
              x.value === i.id ? "text-orga-500 dark:text-orga-400 bg-orga-50 dark:bg-orga-950/30 border-l-[3px] border-orga-500 dark:border-orga-400" : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
            ]),
            onClick: z((_r) => x.value = i.id, ["prevent"])
          }, [
            e("i", {
              class: C(["fa-solid", `fa-${i.icon}`, "w-5 text-center"])
            }, null, 2),
            e("span", null, a(i.name), 1)
          ], 10, ke)), 64))
        ]),
        e("div", ve, [
          h.value ? (y(), _("div", {
            key: 0,
            class: C([
              "px-4 py-3 text-sm",
              h.value.type === "success" ? "bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-b border-green-200 dark:border-green-800" : "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 border-b border-red-200 dark:border-red-800"
            ])
          }, [
            e("i", {
              class: C(["fa-solid mr-2", h.value.type === "success" ? "fa-check-circle" : "fa-exclamation-circle"])
            }, null, 2),
            D(" " + a(h.value.text), 1)
          ], 2)) : w("", !0),
          x.value === "defaults" ? (y(), _(N, { key: 1 }, [
            e("div", he, [
              e("h3", we, a(t(r)("Default Values")), 1),
              e("p", Se, a(t(r)("Configure default values for new projects and tasks")), 1)
            ]),
            e("div", Ce, [
              e("div", De, [
                e("div", null, [
                  e("h4", Re, a(t(r)("Default Task Status")), 1),
                  e("p", Ue, a(t(r)("Status assigned to new tasks")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": s[0] || (s[0] = (i) => d.value.default_task_status = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [
                  e("option", je, a(t(r)("Open")), 1),
                  e("option", Ne, a(t(r)("In Progress")), 1)
                ], 512), [
                  [K, d.value.default_task_status]
                ])
              ]),
              e("div", Ee, [
                e("div", null, [
                  e("h4", Pe, a(t(r)("Default Project Status")), 1),
                  e("p", Ke, a(t(r)("Status assigned to new projects")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": s[1] || (s[1] = (i) => d.value.default_project_status = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [
                  e("option", Ae, a(t(r)("Planning")), 1),
                  e("option", Fe, a(t(r)("Active")), 1)
                ], 512), [
                  [K, d.value.default_project_status]
                ])
              ]),
              e("div", Oe, [
                e("div", null, [
                  e("h4", Te, a(t(r)("Project Code Prefix")), 1),
                  e("p", Ve, a(t(r)("Prefix for auto-generated project codes (e.g., ORG-2026-0001)")), 1)
                ]),
                f(e("input", {
                  "onUpdate:modelValue": s[2] || (s[2] = (i) => d.value.project_code_prefix = i),
                  type: "text",
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-32 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400",
                  maxlength: "10"
                }, null, 512), [
                  [O, d.value.project_code_prefix]
                ])
              ]),
              e("div", Ie, [
                e("div", null, [
                  e("h4", Me, a(t(r)("Default Priority")), 1),
                  e("p", Le, a(t(r)("Priority assigned to new tasks")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": s[3] || (s[3] = (i) => d.value.default_priority = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [
                  e("option", Ye, a(t(r)("Low")), 1),
                  e("option", He, a(t(r)("Medium")), 1),
                  e("option", Be, a(t(r)("High")), 1),
                  e("option", Ge, a(t(r)("Urgent")), 1)
                ], 512), [
                  [K, d.value.default_priority]
                ])
              ]),
              e("div", Je, [
                e("div", null, [
                  e("h4", Ze, a(t(r)("Default Currency")), 1),
                  e("p", qe, a(t(r)("Currency used for budgets, costs, and billing rates")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": s[4] || (s[4] = (i) => d.value.default_currency = i),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                }, [...s[17] || (s[17] = [
                  X('<option value="USD">USD — US Dollar</option><option value="EUR">EUR — Euro</option><option value="GBP">GBP — British Pound</option><option value="CHF">CHF — Swiss Franc</option><option value="JPY">JPY — Japanese Yen</option><option value="CAD">CAD — Canadian Dollar</option><option value="AUD">AUD — Australian Dollar</option><option value="INR">INR — Indian Rupee</option><option value="CNY">CNY — Chinese Yuan</option><option value="BRL">BRL — Brazilian Real</option><option value="SEK">SEK — Swedish Krona</option><option value="NOK">NOK — Norwegian Krone</option><option value="DKK">DKK — Danish Krone</option><option value="PLN">PLN — Polish Zloty</option><option value="CZK">CZK — Czech Koruna</option><option value="HUF">HUF — Hungarian Forint</option><option value="TRY">TRY — Turkish Lira</option><option value="ZAR">ZAR — South African Rand</option><option value="SGD">SGD — Singapore Dollar</option><option value="HKD">HKD — Hong Kong Dollar</option><option value="NZD">NZD — New Zealand Dollar</option><option value="MXN">MXN — Mexican Peso</option><option value="KRW">KRW — South Korean Won</option>', 23)
                ])], 512), [
                  [K, d.value.default_currency]
                ])
              ])
            ])
          ], 64)) : x.value === "features" ? (y(), _(N, { key: 2 }, [
            e("div", We, [
              e("h3", $e, a(t(r)("Features")), 1),
              e("p", ze, a(t(r)("Enable or disable optional features")), 1)
            ]),
            e("div", Xe, [
              e("div", Qe, [
                e("div", null, [
                  e("h4", et, a(t(r)("Auto Calculate Progress")), 1),
                  e("p", tt, a(t(r)("Automatically calculate project progress from task completion")), 1)
                ]),
                e("label", rt, [
                  f(e("input", {
                    "onUpdate:modelValue": s[5] || (s[5] = (i) => d.value.auto_calculate_progress = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [R, d.value.auto_calculate_progress]
                  ]),
                  s[18] || (s[18] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  s[19] || (s[19] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", at, [
                e("div", null, [
                  e("h4", st, a(t(r)("Auto Set Missed Milestones")), 1),
                  e("p", ot, a(t(r)("Automatically mark milestones as missed when overdue")), 1)
                ]),
                e("label", nt, [
                  f(e("input", {
                    "onUpdate:modelValue": s[6] || (s[6] = (i) => d.value.auto_set_missed_milestones = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [R, d.value.auto_set_missed_milestones]
                  ]),
                  s[20] || (s[20] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  s[21] || (s[21] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", lt, [
                e("div", null, [
                  e("h4", it, a(t(r)("Enable Time Tracking")), 1),
                  e("p", dt, a(t(r)("Allow users to log time against tasks")), 1)
                ]),
                e("label", ut, [
                  f(e("input", {
                    "onUpdate:modelValue": s[7] || (s[7] = (i) => d.value.enable_time_tracking = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [R, d.value.enable_time_tracking]
                  ]),
                  s[22] || (s[22] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  s[23] || (s[23] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", ct, [
                e("div", null, [
                  e("h4", gt, a(t(r)("Default Weekly Capacity")), 1),
                  e("p", mt, a(t(r)("Default hours per week for contact capacity planning")), 1)
                ]),
                e("div", yt, [
                  f(e("input", {
                    "onUpdate:modelValue": s[8] || (s[8] = (i) => d.value.default_capacity_hours = i),
                    type: "number",
                    min: "1",
                    max: "168",
                    class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                  }, null, 512), [
                    [
                      O,
                      d.value.default_capacity_hours,
                      void 0,
                      { number: !0 }
                    ]
                  ]),
                  e("span", _t, a(t(r)("hours")), 1)
                ])
              ])
            ])
          ], 64)) : x.value === "notifications" ? (y(), _(N, { key: 3 }, [
            e("div", pt, [
              e("h3", ft, a(t(r)("Notifications")), 1),
              e("p", bt, a(t(r)("Configure email notification settings")), 1)
            ]),
            e("div", xt, [
              e("div", kt, [
                e("div", null, [
                  e("h4", vt, a(t(r)("Task Assignment")), 1),
                  e("p", ht, a(t(r)("Send notification when a task is assigned to a user")), 1)
                ]),
                e("label", wt, [
                  f(e("input", {
                    "onUpdate:modelValue": s[9] || (s[9] = (i) => d.value.notify_on_task_assignment = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [R, d.value.notify_on_task_assignment]
                  ]),
                  s[24] || (s[24] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  s[25] || (s[25] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", St, [
                e("div", null, [
                  e("h4", Ct, a(t(r)("Status Changes")), 1),
                  e("p", Dt, a(t(r)("Send notification when task status changes")), 1)
                ]),
                e("label", Rt, [
                  f(e("input", {
                    "onUpdate:modelValue": s[10] || (s[10] = (i) => d.value.notify_on_status_change = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [R, d.value.notify_on_status_change]
                  ]),
                  s[26] || (s[26] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  s[27] || (s[27] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Ut, [
                e("div", null, [
                  e("h4", jt, a(t(r)("Due Date Reminders")), 1),
                  e("p", Nt, a(t(r)("Send reminder before task due date")), 1)
                ]),
                e("label", Et, [
                  f(e("input", {
                    "onUpdate:modelValue": s[11] || (s[11] = (i) => d.value.notify_on_due_date = i),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [R, d.value.notify_on_due_date]
                  ]),
                  s[28] || (s[28] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all" }, null, -1)),
                  s[29] || (s[29] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Pt, [
                e("div", null, [
                  e("h4", Kt, a(t(r)("Reminder Lead Time")), 1),
                  e("p", At, a(t(r)("Days before due date to send reminder")), 1)
                ]),
                e("div", Ft, [
                  f(e("input", {
                    "onUpdate:modelValue": s[12] || (s[12] = (i) => d.value.due_date_reminder_days = i),
                    type: "number",
                    min: "1",
                    max: "30",
                    class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                  }, null, 512), [
                    [
                      O,
                      d.value.due_date_reminder_days,
                      void 0,
                      { number: !0 }
                    ]
                  ]),
                  e("span", Ot, a(t(r)("days")), 1)
                ])
              ])
            ])
          ], 64)) : x.value === "updates" ? (y(), _(N, { key: 4 }, [
            e("div", Tt, [
              e("h3", Vt, a(t(r)("App Updates")), 1),
              e("p", It, a(t(r)("Check for new versions of Orga")), 1)
            ]),
            e("div", Mt, [
              e("div", Lt, [
                e("div", null, [
                  e("h4", Yt, a(t(r)("Installed Version")), 1),
                  e("p", Ht, a(t(r)("Currently running version")), 1)
                ]),
                e("span", Bt, " v" + a(t(l)?.current_version || t(le)), 1)
              ]),
              t(l) ? (y(), _("div", Gt, [
                e("div", null, [
                  e("h4", Jt, a(t(r)("Latest Version")), 1),
                  e("p", Zt, a(t(r)("Last checked: {0}", [t(l).checked_at ? new Date(t(l).checked_at).toLocaleString() : t(r)("Never")])), 1)
                ]),
                e("span", {
                  class: C([
                    "text-sm font-mono",
                    t(l).update_available ? "text-amber-600 dark:text-amber-400 font-semibold" : "text-green-600 dark:text-green-400"
                  ])
                }, " v" + a(t(l).latest_version), 3)
              ])) : w("", !0),
              t(l)?.update_available ? (y(), _("div", qt, [
                e("div", Wt, [
                  s[31] || (s[31] = e("i", { class: "fa-solid fa-circle-up text-amber-500 text-xl mt-0.5" }, null, -1)),
                  e("div", $t, [
                    e("h4", zt, a(t(r)("Update Available")), 1),
                    e("p", Xt, a(t(r)("Version {0} is available. You are running {1}.", [t(l).latest_version, t(l).current_version])), 1),
                    t(l).release_notes ? (y(), _("div", Qt, [
                      D(a(t(l).release_notes.substring(0, 500)) + " ", 1),
                      t(l).release_notes.length > 500 ? (y(), _("span", er, "...")) : w("", !0)
                    ])) : w("", !0),
                    e("div", tr, [
                      e("a", {
                        href: t(l).release_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        class: "inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded transition-colors no-underline"
                      }, [
                        s[30] || (s[30] = e("i", { class: "fa-brands fa-github text-xs" }, null, -1)),
                        D(" " + a(t(r)("View Release")), 1)
                      ], 8, rr),
                      e("button", {
                        onClick: s[13] || (s[13] = //@ts-ignore
                        (...i) => t(p) && t(p)(...i)),
                        class: "px-3 py-1.5 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 rounded transition-colors"
                      }, a(t(r)("Dismiss")), 1)
                    ])
                  ])
                ])
              ])) : t(l) && !t(l).update_available ? (y(), _("div", ar, [
                e("div", sr, [
                  s[32] || (s[32] = e("i", { class: "fa-solid fa-circle-check text-green-500 text-xl" }, null, -1)),
                  e("div", null, [
                    e("h4", or, a(t(r)("Up to Date")), 1),
                    e("p", nr, a(t(r)("You are running the latest version of Orga.")), 1)
                  ])
                ])
              ])) : (y(), _("div", lr, [
                e("p", ir, a(t(r)("No update information available yet.")), 1)
              ])),
              t(b) ? (y(), _("div", dr, [
                s[33] || (s[33] = e("i", { class: "fa-solid fa-exclamation-triangle mr-1" }, null, -1)),
                D(" " + a(t(r)("Update check failed: {0}", [t(b)])), 1)
              ])) : w("", !0),
              e("div", ur, [
                e("button", {
                  onClick: s[14] || (s[14] = //@ts-ignore
                  (...i) => t(E) && t(E)(...i)),
                  disabled: t(n),
                  class: "px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                }, [
                  e("i", {
                    class: C(["fa-solid", t(n) ? "fa-spinner fa-spin" : "fa-rotate"])
                  }, null, 2),
                  D(" " + a(t(n) ? t(r)("Checking...") : t(r)("Check for Updates")), 1)
                ], 8, cr)
              ])
            ])
          ], 64)) : w("", !0),
          x.value !== "updates" ? (y(), _("div", gr, [
            e("button", {
              onClick: J,
              class: "px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors"
            }, a(t(r)("Reset to Defaults")), 1),
            e("button", {
              onClick: G,
              disabled: j.value,
              class: "px-4 py-2 bg-orga-500 hover:bg-orga-600 dark:bg-orga-600 dark:hover:bg-orga-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            }, [
              j.value ? (y(), _("i", yr)) : w("", !0),
              D(" " + a(j.value ? t(r)("Saving...") : t(r)("Save Changes")), 1)
            ], 8, mr)
          ])) : w("", !0)
        ])
      ]))
    ]));
  }
});
export {
  fr as OrgaSettings
};
