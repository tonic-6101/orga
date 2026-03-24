import { ref as v, computed as xe, onUnmounted as Me, h as Z, defineComponent as fe, openBlock as k, createBlock as V, resolveDynamicComponent as je, normalizeClass as D, createCommentVNode as w, onMounted as Ce, createElementBlock as m, createElementVNode as e, toDisplayString as o, unref as a, createVNode as C, Fragment as H, renderList as ze, withModifiers as qe, createTextVNode as z, withDirectives as f, vModelSelect as G, vModelText as J, vModelCheckbox as q } from "/assets/dock/js/vendor/vue.esm.js";
function Ae(d) {
  let r = Object.assign({}, d);
  if (!r.url)
    throw new Error("[request] options.url is required");
  r.transformRequest && (r = r.transformRequest(d)), r.responseType || (r.responseType = "json"), r.method || (r.method = "GET");
  let h = r.url, i;
  if (r.params)
    if (r.method === "GET") {
      let c = new URLSearchParams();
      for (let l in r.params)
        c.append(l, r.params[l]);
      h = r.url + "?" + c.toString();
    } else
      i = JSON.stringify(r.params);
  return fetch(h, {
    method: r.method || "GET",
    headers: r.headers,
    body: i
  }).then((c) => {
    if (r.transformResponse)
      return r.transformResponse(c, r);
    if (c.status >= 200 && c.status < 300)
      return r.responseType === "json" ? c.json() : c;
    {
      let l = new Error(c.statusText);
      throw l.response = c, l;
    }
  }).catch((c) => {
    if (r.transformError)
      return r.transformError(c);
    throw c;
  });
}
let Ve = {};
function Se(d) {
  return Ve[d] ?? null;
}
function He(d) {
  return Ae({
    ...d,
    transformRequest: (r = {}) => {
      if (!r.url)
        throw new Error("[frappeRequest] options.url is required");
      let h = Object.assign(
        {
          Accept: "application/json",
          "Content-Type": "application/json; charset=utf-8",
          "X-Frappe-Site-Name": window.location.hostname
        },
        r.headers || {}
      );
      return window.csrf_token && window.csrf_token !== "{{ csrf_token }}" && (h["X-Frappe-CSRF-Token"] = window.csrf_token), !r.url.startsWith("/") && !r.url.startsWith("http") && (r.url = "/api/method/" + r.url), {
        ...r,
        method: r.method || "POST",
        headers: h
      };
    },
    transformResponse: async (r, h) => {
      let i = h.url;
      if (r.ok) {
        const c = await r.json();
        if (c.docs || i === "/api/method/login")
          return c;
        if (c.exc)
          try {
            console.groupCollapsed(i), console.log(h);
            let l = JSON.parse(c.exc);
            for (let x of l)
              console.log(x);
            console.groupEnd();
          } catch (l) {
            console.warn("Error printing debug messages", l);
          }
        if (c._server_messages) {
          let l = Se("serverMessagesHandler") || h.onServerMessages || null;
          l && l(JSON.parse(c?._server_messages) || []);
        }
        return c.message;
      } else {
        let c = await r.text(), l, x;
        try {
          l = JSON.parse(c);
        } catch {
        }
        let j = [
          [h.url, l?.exc_type, l?._error_message].filter(Boolean).join(" ")
        ];
        if (l.exc) {
          x = l.exc;
          try {
            x = JSON.parse(x)[0], console.log(x);
          } catch {
          }
        }
        let p = new Error(j.join(`
`));
        throw p.exc_type = l.exc_type, p.exc = x, p.response = r, p.status = c.status, p.messages = l._server_messages ? JSON.parse(l._server_messages) : [], p.messages = p.messages.concat(l.message), p.messages = p.messages.map((_) => {
          try {
            return JSON.parse(_).message;
          } catch {
            return _;
          }
        }), p.messages = p.messages.filter(Boolean), p.messages.length || (p.messages = l._error_message ? [l._error_message] : ["Internal Server Error"]), h.onError && h.onError(p), p;
      }
    },
    transformError: (r) => {
      throw d.onError && d.onError(r), r;
    }
  });
}
function be() {
  const d = v(!1), r = v(null);
  async function h(i, c = {}) {
    d.value = !0, r.value = null;
    try {
      return await He({
        url: "/api/method/" + i,
        params: c
      });
    } catch (l) {
      const x = l instanceof Error ? l.message : "An error occurred";
      throw r.value = x, console.error(`API Error [${i}]:`, l), l;
    } finally {
      d.value = !1;
    }
  }
  return { call: h, loading: d, error: r };
}
function Le() {
  const { call: d, loading: r, error: h } = be();
  return {
    loading: r,
    error: h,
    call: d,
    getSettings: () => d("orga.orga.api.settings.get_settings"),
    updateSettings: (i) => d("orga.orga.api.settings.update_settings", { data: JSON.stringify(i) })
  };
}
const b = v(null), A = v(!1), O = v(null), W = "orga_update_dismissed_version";
function Ue() {
  try {
    return localStorage.getItem(W);
  } catch {
    return null;
  }
}
const Ee = xe(() => {
  if (!b.value?.update_available) return !1;
  const d = Ue();
  return !(d && d === b.value.latest_version);
});
let K = !1;
function Pe() {
  const { call: d } = be();
  async function r() {
    if (!A.value) {
      A.value = !0, O.value = null;
      try {
        const l = await d(
          "orga.orga.api.settings.get_update_info"
        );
        l && l.current_version && (b.value = l);
      } catch {
      } finally {
        A.value = !1;
      }
    }
  }
  async function h() {
    A.value = !0, O.value = null;
    try {
      const l = await d(
        "orga.orga.api.settings.check_updates_now"
      );
      l && l.current_version && (b.value = l);
    } catch (l) {
      O.value = l.message || "Check failed";
    } finally {
      A.value = !1;
    }
  }
  function i() {
    b.value?.latest_version && (localStorage.setItem(W, b.value.latest_version), b.value = { ...b.value });
  }
  function c() {
    localStorage.removeItem(W), b.value && (b.value = { ...b.value });
  }
  return K || (K = !0, r()), Me(() => {
  }), {
    updateInfo: b,
    updateAvailable: Ee,
    isChecking: A,
    checkError: O,
    fetchUpdateInfo: r,
    forceCheck: h,
    dismissUpdate: i,
    undismissUpdate: c
  };
}
function s(d, r) {
  let i = (window.__messages || {})[d] || d;
  if (r)
    if (Array.isArray(r))
      for (let c = 0; c < r.length; c++)
        i = i.replace(new RegExp(`\\{${c}\\}`, "g"), String(r[c]));
    else
      for (const [c, l] of Object.entries(r))
        i = i.replace(new RegExp(`\\{${c}\\}`, "g"), String(l));
  return i;
}
const Oe = "0.15.1";
const Re = (d) => {
  for (const r in d)
    if (r.startsWith("aria-") || r === "role" || r === "title")
      return !0;
  return !1;
};
const ee = (d) => d === "";
const Te = (...d) => d.filter((r, h, i) => !!r && r.trim() !== "" && i.indexOf(r) === h).join(" ").trim();
const te = (d) => d.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const De = (d) => d.replace(
  /^([A-Z])|[\s-_]+(\w)/g,
  (r, h, i) => i ? i.toUpperCase() : h.toLowerCase()
);
const Fe = (d) => {
  const r = De(d);
  return r.charAt(0).toUpperCase() + r.slice(1);
};
var L = {
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
const Ie = ({
  name: d,
  iconNode: r,
  absoluteStrokeWidth: h,
  "absolute-stroke-width": i,
  strokeWidth: c,
  "stroke-width": l,
  size: x = L.width,
  color: j = L.stroke,
  ...p
}, { slots: _ }) => Z(
  "svg",
  {
    ...L,
    ...p,
    width: x,
    height: x,
    stroke: j,
    "stroke-width": ee(h) || ee(i) || h === !0 || i === !0 ? Number(c || l || L["stroke-width"]) * 24 / Number(x) : c || l || L["stroke-width"],
    class: Te(
      "lucide",
      p.class,
      ...d ? [`lucide-${te(Fe(d))}-icon`, `lucide-${te(d)}`] : ["lucide-icon"]
    ),
    ...!_.default && !Re(p) && { "aria-hidden": "true" }
  },
  [...r.map((u) => Z(...u)), ..._.default ? [_.default()] : []]
);
const t = (d, r) => (h, { slots: i, attrs: c }) => Z(
  Ie,
  {
    ...c,
    ...h,
    iconNode: r,
    name: d
  },
  i
);
const ae = t("arrow-down-wide-narrow", [
  ["path", { d: "m3 16 4 4 4-4", key: "1co6wj" }],
  ["path", { d: "M7 20V4", key: "1yoxec" }],
  ["path", { d: "M11 4h10", key: "1w87gc" }],
  ["path", { d: "M11 8h7", key: "djye34" }],
  ["path", { d: "M11 12h4", key: "q8tih4" }]
]);
const re = t("arrow-down", [
  ["path", { d: "M12 5v14", key: "s699le" }],
  ["path", { d: "m19 12-7 7-7-7", key: "1idqje" }]
]);
const Ne = t("arrow-left", [
  ["path", { d: "m12 19-7-7 7-7", key: "1l729n" }],
  ["path", { d: "M19 12H5", key: "x3x0zl" }]
]);
const Be = t("arrow-right", [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "m12 5 7 7-7 7", key: "xquz4c" }]
]);
const Ge = t("arrow-up-narrow-wide", [
  ["path", { d: "m3 8 4-4 4 4", key: "11wl7u" }],
  ["path", { d: "M7 4v16", key: "1glfcx" }],
  ["path", { d: "M11 12h4", key: "q8tih4" }],
  ["path", { d: "M11 16h7", key: "uosisv" }],
  ["path", { d: "M11 20h10", key: "jvxblo" }]
]);
const se = t("arrow-up-right", [
  ["path", { d: "M7 7h10v10", key: "1tivn9" }],
  ["path", { d: "M7 17 17 7", key: "1vkiza" }]
]);
const oe = t("arrow-up", [
  ["path", { d: "m5 12 7-7 7 7", key: "hav0vg" }],
  ["path", { d: "M12 19V5", key: "x0mq9r" }]
]);
const Je = t("ban", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M4.929 4.929 19.07 19.071", key: "196cmz" }]
]);
const $e = t("bell", [
  ["path", { d: "M10.268 21a2 2 0 0 0 3.464 0", key: "vwvbt9" }],
  [
    "path",
    {
      d: "M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326",
      key: "11g9vi"
    }
  ]
]);
const Xe = t("bug", [
  ["path", { d: "M12 20v-9", key: "1qisl0" }],
  ["path", { d: "M14 7a4 4 0 0 1 4 4v3a6 6 0 0 1-12 0v-3a4 4 0 0 1 4-4z", key: "uouzyp" }],
  ["path", { d: "M14.12 3.88 16 2", key: "qol33r" }],
  ["path", { d: "M21 21a4 4 0 0 0-3.81-4", key: "1b0z45" }],
  ["path", { d: "M21 5a4 4 0 0 1-3.55 3.97", key: "5cxbf6" }],
  ["path", { d: "M22 13h-4", key: "1jl80f" }],
  ["path", { d: "M3 21a4 4 0 0 1 3.81-4", key: "1fjd4g" }],
  ["path", { d: "M3 5a4 4 0 0 0 3.55 3.97", key: "1d7oge" }],
  ["path", { d: "M6 13H2", key: "82j7cp" }],
  ["path", { d: "m8 2 1.88 1.88", key: "fmnt4t" }],
  ["path", { d: "M9 7.13V6a3 3 0 1 1 6 0v1.13", key: "1vgav8" }]
]);
const Ze = t("calculator", [
  ["rect", { width: "16", height: "20", x: "4", y: "2", rx: "2", key: "1nb95v" }],
  ["line", { x1: "8", x2: "16", y1: "6", y2: "6", key: "x4nwl0" }],
  ["line", { x1: "16", x2: "16", y1: "14", y2: "18", key: "wjye3r" }],
  ["path", { d: "M16 10h.01", key: "1m94wz" }],
  ["path", { d: "M12 10h.01", key: "1nrarc" }],
  ["path", { d: "M8 10h.01", key: "19clt8" }],
  ["path", { d: "M12 14h.01", key: "1etili" }],
  ["path", { d: "M8 14h.01", key: "6423bh" }],
  ["path", { d: "M12 18h.01", key: "mhygvu" }],
  ["path", { d: "M8 18h.01", key: "lrp35t" }]
]);
const We = t("calendar-x", [
  ["path", { d: "M8 2v4", key: "1cmpym" }],
  ["path", { d: "M16 2v4", key: "4m81vk" }],
  ["rect", { width: "18", height: "18", x: "3", y: "4", rx: "2", key: "1hopcy" }],
  ["path", { d: "M3 10h18", key: "8toen8" }],
  ["path", { d: "m14 14-4 4", key: "rymu2i" }],
  ["path", { d: "m10 14 4 4", key: "3sz06r" }]
]);
const Ye = t("calendar", [
  ["path", { d: "M8 2v4", key: "1cmpym" }],
  ["path", { d: "M16 2v4", key: "4m81vk" }],
  ["rect", { width: "18", height: "18", x: "3", y: "4", rx: "2", key: "1hopcy" }],
  ["path", { d: "M3 10h18", key: "8toen8" }]
]);
const Qe = t("camera", [
  [
    "path",
    {
      d: "M13.997 4a2 2 0 0 1 1.76 1.05l.486.9A2 2 0 0 0 18.003 7H20a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1.997a2 2 0 0 0 1.759-1.048l.489-.904A2 2 0 0 1 10.004 4z",
      key: "18u6gg"
    }
  ],
  ["circle", { cx: "12", cy: "13", r: "3", key: "1vg3eu" }]
]);
const Ke = t("chart-column", [
  ["path", { d: "M3 3v16a2 2 0 0 0 2 2h16", key: "c24i48" }],
  ["path", { d: "M18 17V9", key: "2bz60n" }],
  ["path", { d: "M13 17V5", key: "1frdt8" }],
  ["path", { d: "M8 17v-3", key: "17ska0" }]
]);
const et = t("chart-no-axes-column", [
  ["path", { d: "M5 21v-6", key: "1hz6c0" }],
  ["path", { d: "M12 21V3", key: "1lcnhd" }],
  ["path", { d: "M19 21V9", key: "unv183" }]
]);
const tt = t("chart-pie", [
  [
    "path",
    {
      d: "M21 12c.552 0 1.005-.449.95-.998a10 10 0 0 0-8.953-8.951c-.55-.055-.998.398-.998.95v8a1 1 0 0 0 1 1z",
      key: "pzmjnu"
    }
  ],
  ["path", { d: "M21.21 15.89A10 10 0 1 1 8 2.83", key: "k2fpak" }]
]);
const at = t("check", [["path", { d: "M20 6 9 17l-5-5", key: "1gmf2c" }]]);
const rt = t("chevron-down", [
  ["path", { d: "m6 9 6 6 6-6", key: "qrunsl" }]
]);
const st = t("chevron-left", [
  ["path", { d: "m15 18-6-6 6-6", key: "1wnfg3" }]
]);
const ot = t("chevron-right", [
  ["path", { d: "m9 18 6-6-6-6", key: "mthhwq" }]
]);
const nt = t("chevron-up", [
  ["path", { d: "m18 15-6-6-6 6", key: "153udz" }]
]);
const E = t("circle-alert", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["line", { x1: "12", x2: "12", y1: "8", y2: "12", key: "1pkeuh" }],
  ["line", { x1: "12", x2: "12.01", y1: "16", y2: "16", key: "4dfq90" }]
]);
const ve = t("circle-arrow-up", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m16 12-4-4-4 4", key: "177agl" }],
  ["path", { d: "M12 16V8", key: "1sbj14" }]
]);
const I = t("circle-check", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m9 12 2 2 4-4", key: "dzmm74" }]
]);
const ne = t("circle-dot", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["circle", { cx: "12", cy: "12", r: "1", key: "41hilf" }]
]);
const lt = t("circle-question-mark", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3", key: "1u773s" }],
  ["path", { d: "M12 17h.01", key: "p32p05" }]
]);
const dt = t("circle-x", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m15 9-6 6", key: "1uzhvr" }],
  ["path", { d: "m9 9 6 6", key: "z0biqf" }]
]);
const it = t("circle", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }]
]);
const ct = t("clipboard-list", [
  ["rect", { width: "8", height: "4", x: "8", y: "2", rx: "1", ry: "1", key: "tgr4d6" }],
  [
    "path",
    {
      d: "M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2",
      key: "116196"
    }
  ],
  ["path", { d: "M12 11h4", key: "1jrz19" }],
  ["path", { d: "M12 16h4", key: "n85exb" }],
  ["path", { d: "M8 11h.01", key: "1dfujw" }],
  ["path", { d: "M8 16h.01", key: "18s6g9" }]
]);
const yt = t("clock", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M12 6v6l4 2", key: "mmk7yg" }]
]);
const ht = t("cloud-upload", [
  ["path", { d: "M12 13v8", key: "1l5pq0" }],
  ["path", { d: "M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242", key: "1pljnt" }],
  ["path", { d: "m8 17 4-4 4 4", key: "1quai1" }]
]);
const R = t("coins", [
  ["path", { d: "M13.744 17.736a6 6 0 1 1-7.48-7.48", key: "bq4yh3" }],
  ["path", { d: "M15 6h1v4", key: "11y1tn" }],
  ["path", { d: "m6.134 14.768.866-.5 2 3.464", key: "17snzx" }],
  ["circle", { cx: "16", cy: "8", r: "6", key: "14bfc9" }]
]);
const ut = t("columns-3", [
  ["rect", { width: "18", height: "18", x: "3", y: "3", rx: "2", key: "afitv7" }],
  ["path", { d: "M9 3v18", key: "fh3hqa" }],
  ["path", { d: "M15 3v18", key: "14nvp0" }]
]);
const le = t("compass", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  [
    "path",
    {
      d: "m16.24 7.76-1.804 5.411a2 2 0 0 1-1.265 1.265L7.76 16.24l1.804-5.411a2 2 0 0 1 1.265-1.265z",
      key: "9ktpf1"
    }
  ]
]);
const pt = t("copy", [
  ["rect", { width: "14", height: "14", x: "8", y: "8", rx: "2", ry: "2", key: "17jyea" }],
  ["path", { d: "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2", key: "zix9uf" }]
]);
const kt = t("dollar-sign", [
  ["line", { x1: "12", x2: "12", y1: "2", y2: "22", key: "7eqyqh" }],
  ["path", { d: "M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6", key: "1b0p4s" }]
]);
const gt = t("download", [
  ["path", { d: "M12 15V3", key: "m9g1x1" }],
  ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
  ["path", { d: "m7 10 5 5 5-5", key: "brsn70" }]
]);
const mt = t("euro", [
  ["path", { d: "M4 10h12", key: "1y6xl8" }],
  ["path", { d: "M4 14h9", key: "1loblj" }],
  [
    "path",
    {
      d: "M19 6a7.7 7.7 0 0 0-5.2-2A7.9 7.9 0 0 0 6 12c0 4.4 3.5 8 7.8 8 2 0 3.8-.8 5.2-2",
      key: "1j6lzo"
    }
  ]
]);
const de = t("external-link", [
  ["path", { d: "M15 3h6v6", key: "1q9fwt" }],
  ["path", { d: "M10 14 21 3", key: "gplh6r" }],
  ["path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6", key: "a6xqqp" }]
]);
const xt = t("eye", [
  [
    "path",
    {
      d: "M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0",
      key: "1nclc0"
    }
  ],
  ["circle", { cx: "12", cy: "12", r: "3", key: "1v7zrd" }]
]);
const ft = t("file-archive", [
  [
    "path",
    {
      d: "M13.659 22H18a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v11.5",
      key: "4pqfef"
    }
  ],
  ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }],
  ["path", { d: "M8 12v-1", key: "1ej8lb" }],
  ["path", { d: "M8 18v-2", key: "qcmpov" }],
  ["path", { d: "M8 7V6", key: "1nbb54" }],
  ["circle", { cx: "8", cy: "20", r: "2", key: "ckkr5m" }]
]);
const bt = t("file-image", [
  [
    "path",
    {
      d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
      key: "1oefj6"
    }
  ],
  ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }],
  ["circle", { cx: "10", cy: "12", r: "2", key: "737tya" }],
  ["path", { d: "m20 17-1.296-1.296a2.41 2.41 0 0 0-3.408 0L9 22", key: "wt3hpn" }]
]);
const vt = t("file-input", [
  [
    "path",
    {
      d: "M4 11V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.706.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1",
      key: "1q9hii"
    }
  ],
  ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }],
  ["path", { d: "M2 15h10", key: "jfw4w8" }],
  ["path", { d: "m9 18 3-3-3-3", key: "112psh" }]
]);
const _t = t("file-spreadsheet", [
  [
    "path",
    {
      d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
      key: "1oefj6"
    }
  ],
  ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }],
  ["path", { d: "M8 13h2", key: "yr2amv" }],
  ["path", { d: "M14 13h2", key: "un5t4a" }],
  ["path", { d: "M8 17h2", key: "2yhykz" }],
  ["path", { d: "M14 17h2", key: "10kma7" }]
]);
const U = t("file-text", [
  [
    "path",
    {
      d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
      key: "1oefj6"
    }
  ],
  ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }],
  ["path", { d: "M10 9H8", key: "b1mrlr" }],
  ["path", { d: "M16 13H8", key: "t4e002" }],
  ["path", { d: "M16 17H8", key: "z1uh3a" }]
]);
const ie = t("file", [
  [
    "path",
    {
      d: "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",
      key: "1oefj6"
    }
  ],
  ["path", { d: "M14 2v5a1 1 0 0 0 1 1h5", key: "wfsgrz" }]
]);
const wt = t("flag-triangle-right", [
  [
    "path",
    { d: "M6 22V2.8a.8.8 0 0 1 1.17-.71l11.38 5.69a.8.8 0 0 1 0 1.44L6 15.5", key: "kfjsu0" }
  ]
]);
const Mt = t("flag", [
  [
    "path",
    {
      d: "M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528",
      key: "1jaruq"
    }
  ]
]);
const jt = t("flame", [
  [
    "path",
    {
      d: "M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4",
      key: "1slcih"
    }
  ]
]);
const Ct = t("flask-conical", [
  [
    "path",
    {
      d: "M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2",
      key: "18mbvz"
    }
  ],
  ["path", { d: "M6.453 15h11.094", key: "3shlmq" }],
  ["path", { d: "M8.5 2h7", key: "csnxdl" }]
]);
const zt = t("folder-open", [
  [
    "path",
    {
      d: "m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",
      key: "usdka0"
    }
  ]
]);
const qt = t("folder", [
  [
    "path",
    {
      d: "M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z",
      key: "1kt360"
    }
  ]
]);
const At = t("github", [
  [
    "path",
    {
      d: "M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4",
      key: "tonef"
    }
  ],
  ["path", { d: "M9 18c-4.51 2-5-2-7-2", key: "9comsn" }]
]);
const Vt = t("grip", [
  ["circle", { cx: "12", cy: "5", r: "1", key: "gxeob9" }],
  ["circle", { cx: "19", cy: "5", r: "1", key: "w8mnmm" }],
  ["circle", { cx: "5", cy: "5", r: "1", key: "lttvr7" }],
  ["circle", { cx: "12", cy: "12", r: "1", key: "41hilf" }],
  ["circle", { cx: "19", cy: "12", r: "1", key: "1wjl8i" }],
  ["circle", { cx: "5", cy: "12", r: "1", key: "1pcz8c" }],
  ["circle", { cx: "12", cy: "19", r: "1", key: "lyex9k" }],
  ["circle", { cx: "19", cy: "19", r: "1", key: "shf9b7" }],
  ["circle", { cx: "5", cy: "19", r: "1", key: "bfqh0e" }]
]);
const St = t("headset", [
  [
    "path",
    {
      d: "M3 11h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5Zm0 0a9 9 0 1 1 18 0m0 0v5a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3Z",
      key: "12oyoe"
    }
  ],
  ["path", { d: "M21 16v2a4 4 0 0 1-4 4h-5", key: "1x7m43" }]
]);
const Ht = t("heart", [
  [
    "path",
    {
      d: "M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5",
      key: "mvr1a0"
    }
  ]
]);
const ce = t("history", [
  ["path", { d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8", key: "1357e3" }],
  ["path", { d: "M3 3v5h5", key: "1xhq8a" }],
  ["path", { d: "M12 7v5l4 2", key: "1fdv2h" }]
]);
const ye = t("hourglass", [
  ["path", { d: "M5 22h14", key: "ehvnwv" }],
  ["path", { d: "M5 2h14", key: "pdyrp9" }],
  [
    "path",
    {
      d: "M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22",
      key: "1d314k"
    }
  ],
  [
    "path",
    { d: "M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2", key: "1vvvr6" }
  ]
]);
const he = t("house", [
  ["path", { d: "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8", key: "5wwlr5" }],
  [
    "path",
    {
      d: "M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
      key: "r6nss1"
    }
  ]
]);
const Lt = t("inbox", [
  ["polyline", { points: "22 12 16 12 14 15 10 15 8 12 2 12", key: "o97t9d" }],
  [
    "path",
    {
      d: "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
      key: "oot6mr"
    }
  ]
]);
const Ut = t("indian-rupee", [
  ["path", { d: "M6 3h12", key: "ggurg9" }],
  ["path", { d: "M6 8h12", key: "6g4wlu" }],
  ["path", { d: "m6 13 8.5 8", key: "u1kupk" }],
  ["path", { d: "M6 13h3", key: "wdp6ag" }],
  ["path", { d: "M9 13c6.667 0 6.667-10 0-10", key: "1nkvk2" }]
]);
const $ = t("info", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M12 16v-4", key: "1dtifu" }],
  ["path", { d: "M12 8h.01", key: "e9boi3" }]
]);
const Et = t("japanese-yen", [
  ["path", { d: "M12 9.5V21m0-11.5L6 3m6 6.5L18 3", key: "2ej80x" }],
  ["path", { d: "M6 15h12", key: "1hwgt5" }],
  ["path", { d: "M6 11h12", key: "wf4gp6" }]
]);
const Pt = t("layers", [
  [
    "path",
    {
      d: "M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z",
      key: "zw3jo"
    }
  ],
  [
    "path",
    {
      d: "M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12",
      key: "1wduqc"
    }
  ],
  [
    "path",
    {
      d: "M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17",
      key: "kqbvx6"
    }
  ]
]);
const Ot = t("link", [
  ["path", { d: "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71", key: "1cjeqo" }],
  ["path", { d: "M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71", key: "19qd67" }]
]);
const ue = t("list-checks", [
  ["path", { d: "M13 5h8", key: "a7qcls" }],
  ["path", { d: "M13 12h8", key: "h98zly" }],
  ["path", { d: "M13 19h8", key: "c3s6r1" }],
  ["path", { d: "m3 17 2 2 4-4", key: "1jhpwq" }],
  ["path", { d: "m3 7 2 2 4-4", key: "1obspn" }]
]);
const F = t("loader-circle", [
  ["path", { d: "M21 12a9 9 0 1 1-6.219-8.56", key: "13zald" }]
]);
const Rt = t("list", [
  ["path", { d: "M3 5h.01", key: "18ugdj" }],
  ["path", { d: "M3 12h.01", key: "nlz23k" }],
  ["path", { d: "M3 19h.01", key: "noohij" }],
  ["path", { d: "M8 5h13", key: "1pao27" }],
  ["path", { d: "M8 12h13", key: "1za7za" }],
  ["path", { d: "M8 19h13", key: "m83p4d" }]
]);
const Tt = t("lock-open", [
  ["rect", { width: "18", height: "11", x: "3", y: "11", rx: "2", ry: "2", key: "1w4ew1" }],
  ["path", { d: "M7 11V7a5 5 0 0 1 9.9-1", key: "1mm8w8" }]
]);
const Dt = t("lock", [
  ["rect", { width: "18", height: "11", x: "3", y: "11", rx: "2", ry: "2", key: "1w4ew1" }],
  ["path", { d: "M7 11V7a5 5 0 0 1 10 0v4", key: "fwvmzm" }]
]);
const Ft = t("mail", [
  ["path", { d: "m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7", key: "132q7q" }],
  ["rect", { x: "2", y: "4", width: "20", height: "16", rx: "2", key: "izxlao" }]
]);
const It = t("message-square", [
  [
    "path",
    {
      d: "M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z",
      key: "18887p"
    }
  ]
]);
const Nt = t("monitor", [
  ["rect", { width: "20", height: "14", x: "2", y: "3", rx: "2", key: "48i651" }],
  ["line", { x1: "8", x2: "16", y1: "21", y2: "21", key: "1svkeh" }],
  ["line", { x1: "12", x2: "12", y1: "17", y2: "21", key: "vw1qmm" }]
]);
const Bt = t("moon", [
  [
    "path",
    {
      d: "M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401",
      key: "kfwtm"
    }
  ]
]);
const X = t("network", [
  ["rect", { x: "16", y: "16", width: "6", height: "6", rx: "1", key: "4q2zg0" }],
  ["rect", { x: "2", y: "16", width: "6", height: "6", rx: "1", key: "8cvhb9" }],
  ["rect", { x: "9", y: "2", width: "6", height: "6", rx: "1", key: "1egb70" }],
  ["path", { d: "M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3", key: "1jsf9p" }],
  ["path", { d: "M12 12V8", key: "2874zd" }]
]);
const Gt = t("palette", [
  [
    "path",
    {
      d: "M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z",
      key: "e79jfc"
    }
  ],
  ["circle", { cx: "13.5", cy: "6.5", r: ".5", fill: "currentColor", key: "1okk4w" }],
  ["circle", { cx: "17.5", cy: "10.5", r: ".5", fill: "currentColor", key: "f64h9f" }],
  ["circle", { cx: "6.5", cy: "12.5", r: ".5", fill: "currentColor", key: "qy21gx" }],
  ["circle", { cx: "8.5", cy: "7.5", r: ".5", fill: "currentColor", key: "fotxhn" }]
]);
const Jt = t("paperclip", [
  [
    "path",
    {
      d: "m16 6-8.414 8.586a2 2 0 0 0 2.829 2.829l8.414-8.586a4 4 0 1 0-5.657-5.657l-8.379 8.551a6 6 0 1 0 8.485 8.485l8.379-8.551",
      key: "1miecu"
    }
  ]
]);
const $t = t("pause", [
  ["rect", { x: "14", y: "3", width: "5", height: "18", rx: "1", key: "kaeet6" }],
  ["rect", { x: "5", y: "3", width: "5", height: "18", rx: "1", key: "1wsw3u" }]
]);
const Xt = t("pen-line", [
  ["path", { d: "M13 21h8", key: "1jsn5i" }],
  [
    "path",
    {
      d: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",
      key: "1a8usu"
    }
  ]
]);
const pe = t("pencil", [
  [
    "path",
    {
      d: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",
      key: "1a8usu"
    }
  ],
  ["path", { d: "m15 5 4 4", key: "1mk7zo" }]
]);
const Zt = t("pin", [
  ["path", { d: "M12 17v5", key: "bb1du9" }],
  [
    "path",
    {
      d: "M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z",
      key: "1nkz8b"
    }
  ]
]);
const ke = t("play", [
  [
    "path",
    {
      d: "M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z",
      key: "10ikf1"
    }
  ]
]);
const Wt = t("plus", [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "M12 5v14", key: "s699le" }]
]);
const Yt = t("pointer", [
  ["path", { d: "M22 14a8 8 0 0 1-8 8", key: "56vcr3" }],
  ["path", { d: "M18 11v-1a2 2 0 0 0-2-2a2 2 0 0 0-2 2", key: "1agjmk" }],
  ["path", { d: "M14 10V9a2 2 0 0 0-2-2a2 2 0 0 0-2 2v1", key: "wdbh2u" }],
  ["path", { d: "M10 9.5V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v10", key: "1ibuk9" }],
  [
    "path",
    {
      d: "M18 11a2 2 0 1 1 4 0v3a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15",
      key: "g6ys72"
    }
  ]
]);
const Qt = t("pound-sterling", [
  ["path", { d: "M18 7c0-5.333-8-5.333-8 0", key: "1prm2n" }],
  ["path", { d: "M10 7v14", key: "18tmcs" }],
  ["path", { d: "M6 21h12", key: "4dkmi1" }],
  ["path", { d: "M6 13h10", key: "ybwr4a" }]
]);
const Y = t("rotate-ccw", [
  ["path", { d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8", key: "1357e3" }],
  ["path", { d: "M3 3v5h5", key: "1xhq8a" }]
]);
const Kt = t("search", [
  ["path", { d: "m21 21-4.34-4.34", key: "14j7rj" }],
  ["circle", { cx: "11", cy: "11", r: "8", key: "4ej97u" }]
]);
const ea = t("send", [
  [
    "path",
    {
      d: "M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z",
      key: "1ffxy3"
    }
  ],
  ["path", { d: "m21.854 2.147-10.94 10.939", key: "12cjpa" }]
]);
const ta = t("shield", [
  [
    "path",
    {
      d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
      key: "oel41y"
    }
  ]
]);
const aa = t("skip-forward", [
  ["path", { d: "M21 4v16", key: "7j8fe9" }],
  [
    "path",
    {
      d: "M6.029 4.285A2 2 0 0 0 3 6v12a2 2 0 0 0 3.029 1.715l9.997-5.998a2 2 0 0 0 .003-3.432z",
      key: "zs4d6"
    }
  ]
]);
const ge = t("sliders-horizontal", [
  ["path", { d: "M10 5H3", key: "1qgfaw" }],
  ["path", { d: "M12 19H3", key: "yhmn1j" }],
  ["path", { d: "M14 3v4", key: "1sua03" }],
  ["path", { d: "M16 17v4", key: "1q0r14" }],
  ["path", { d: "M21 12h-9", key: "1o4lsq" }],
  ["path", { d: "M21 19h-5", key: "1rlt1p" }],
  ["path", { d: "M21 5h-7", key: "1oszz2" }],
  ["path", { d: "M8 10v4", key: "tgpxqk" }],
  ["path", { d: "M8 12H3", key: "a7s4jb" }]
]);
const ra = t("star", [
  [
    "path",
    {
      d: "M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z",
      key: "r04s7s"
    }
  ]
]);
const sa = t("sun", [
  ["circle", { cx: "12", cy: "12", r: "4", key: "4exip2" }],
  ["path", { d: "M12 2v2", key: "tus03m" }],
  ["path", { d: "M12 20v2", key: "1lh1kg" }],
  ["path", { d: "m4.93 4.93 1.41 1.41", key: "149t6j" }],
  ["path", { d: "m17.66 17.66 1.41 1.41", key: "ptbguv" }],
  ["path", { d: "M2 12h2", key: "1t8f8n" }],
  ["path", { d: "M20 12h2", key: "1q8mjw" }],
  ["path", { d: "m6.34 17.66-1.41 1.41", key: "1m8zz5" }],
  ["path", { d: "m19.07 4.93-1.41 1.41", key: "1shlcs" }]
]);
const oa = t("table-2", [
  [
    "path",
    {
      d: "M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18",
      key: "gugj83"
    }
  ]
]);
const na = t("timer", [
  ["line", { x1: "10", x2: "14", y1: "2", y2: "2", key: "14vaq8" }],
  ["line", { x1: "12", x2: "15", y1: "14", y2: "11", key: "17fdiu" }],
  ["circle", { cx: "12", cy: "14", r: "8", key: "1e1u0o" }]
]);
const la = t("toggle-right", [
  ["circle", { cx: "15", cy: "12", r: "3", key: "1afu0r" }],
  ["rect", { width: "20", height: "14", x: "2", y: "5", rx: "7", key: "g7kal2" }]
]);
const me = t("trash-2", [
  ["path", { d: "M10 11v6", key: "nco0om" }],
  ["path", { d: "M14 11v6", key: "outv1u" }],
  ["path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6", key: "miytrc" }],
  ["path", { d: "M3 6h18", key: "d0wm0j" }],
  ["path", { d: "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2", key: "e791ji" }]
]);
const da = t("trending-up", [
  ["path", { d: "M16 7h6v6", key: "box55l" }],
  ["path", { d: "m22 7-8.5 8.5-5-5L2 17", key: "1t1m79" }]
]);
const N = t("triangle-alert", [
  [
    "path",
    {
      d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",
      key: "wmoenq"
    }
  ],
  ["path", { d: "M12 9v4", key: "juzpu7" }],
  ["path", { d: "M12 17h.01", key: "p32p05" }]
]);
const ia = t("unlink", [
  [
    "path",
    {
      d: "m18.84 12.25 1.72-1.71h-.02a5.004 5.004 0 0 0-.12-7.07 5.006 5.006 0 0 0-6.95 0l-1.72 1.71",
      key: "yqzxt4"
    }
  ],
  [
    "path",
    {
      d: "m5.17 11.75-1.71 1.71a5.004 5.004 0 0 0 .12 7.07 5.006 5.006 0 0 0 6.95 0l1.71-1.71",
      key: "4qinb0"
    }
  ],
  ["line", { x1: "8", x2: "8", y1: "2", y2: "5", key: "1041cp" }],
  ["line", { x1: "2", x2: "5", y1: "8", y2: "8", key: "14m1p5" }],
  ["line", { x1: "16", x2: "16", y1: "19", y2: "22", key: "rzdirn" }],
  ["line", { x1: "19", x2: "22", y1: "16", y2: "16", key: "ox905f" }]
]);
const ca = t("user-plus", [
  ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
  ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }],
  ["line", { x1: "19", x2: "19", y1: "8", y2: "14", key: "1bvyxn" }],
  ["line", { x1: "22", x2: "16", y1: "11", y2: "11", key: "1shjgl" }]
]);
const ya = t("user-x", [
  ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
  ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }],
  ["line", { x1: "17", x2: "22", y1: "8", y2: "13", key: "3nzzx3" }],
  ["line", { x1: "22", x2: "17", y1: "8", y2: "13", key: "1swrse" }]
]);
const ha = t("user", [
  ["path", { d: "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2", key: "975kel" }],
  ["circle", { cx: "12", cy: "7", r: "4", key: "17ys0d" }]
]);
const ua = t("users", [
  ["path", { d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", key: "1yyitq" }],
  ["path", { d: "M16 3.128a4 4 0 0 1 0 7.744", key: "16gr8j" }],
  ["path", { d: "M22 21v-2a4 4 0 0 0-3-3.87", key: "kshegd" }],
  ["circle", { cx: "9", cy: "7", r: "4", key: "nufk8" }]
]);
const pa = t("wallet", [
  [
    "path",
    {
      d: "M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1",
      key: "18etb6"
    }
  ],
  ["path", { d: "M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4", key: "xoc0q4" }]
]);
const ka = t("wrench", [
  [
    "path",
    {
      d: "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z",
      key: "1ngwbx"
    }
  ]
]);
const T = t("x", [
  ["path", { d: "M18 6 6 18", key: "1bl5f8" }],
  ["path", { d: "m6 6 12 12", key: "d8bk6v" }]
]);
const ga = t("zap", [
  [
    "path",
    {
      d: "M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z",
      key: "1xq2db"
    }
  ]
]), ma = { name: "OrgaIcon" }, xa = /* @__PURE__ */ fe({
  ...ma,
  props: {
    name: {},
    spin: { type: Boolean }
  },
  setup(d) {
    const r = {
      // Status & state
      "lock-open": Tt,
      hourglass: ye,
      "hourglass-half": ye,
      eye: xt,
      check: at,
      x: T,
      xmark: T,
      times: T,
      ban: Je,
      lock: Dt,
      circle: it,
      "circle-check": I,
      "check-circle": I,
      "circle-dot": ne,
      "circle-half-stroke": ne,
      "circle-alert": E,
      "circle-question": lt,
      "circle-info": $,
      "circle-up": ve,
      "circle-x": dt,
      "exclamation-circle": E,
      "alert-circle": E,
      "exclamation-triangle": N,
      "triangle-exclamation": N,
      "info-circle": $,
      info: $,
      // Navigation & UI
      "chevron-down": rt,
      "chevron-right": ot,
      "chevron-up": nt,
      "chevron-left": st,
      "arrow-down": re,
      "arrow-up": oe,
      "arrow-left": Ne,
      "arrow-right": Be,
      "arrow-up-right-from-square": se,
      "arrow-up-right": se,
      "external-link": de,
      "arrow-down-wide-short": ae,
      "arrow-up-short-wide": Ge,
      // Actions
      plus: Wt,
      trash: me,
      "trash-can": me,
      pen: pe,
      "pen-to-square": Xt,
      pencil: pe,
      copy: pt,
      download: gt,
      "cloud-arrow-up": ht,
      search: Kt,
      undo: Y,
      rotate: Y,
      "clock-rotate-left": ce,
      history: ce,
      "paper-plane": ea,
      paperclip: Jt,
      link: Ot,
      "link-slash": ia,
      "grip-vertical": Vt,
      "hand-pointer": Yt,
      // Content & files
      file: ie,
      "file-alt": U,
      "file-lines": U,
      "file-text": U,
      "file-excel": _t,
      "file-image": bt,
      "file-pdf": ie,
      "file-word": U,
      "file-zipper": ft,
      "file-import": vt,
      "clipboard-list": ct,
      // Layout & views
      home: he,
      house: he,
      inbox: Lt,
      "folder-open": zt,
      folder: qt,
      list: Rt,
      "list-check": ue,
      columns: ut,
      "table-columns": oa,
      display: Nt,
      sliders: ge,
      // People & communication
      user: ha,
      "user-plus": ca,
      "user-slash": ya,
      users: ua,
      comments: It,
      envelope: Ft,
      headset: St,
      // Time & calendar
      clock: yt,
      calendar: Ye,
      "calendar-xmark": We,
      stopwatch: na,
      // Project & planning
      flag: Mt,
      "flag-checkered": wt,
      "compass-drafting": le,
      "drafting-compass": le,
      "project-diagram": X,
      "diagram-project": X,
      sitemap: X,
      "layer-group": Pt,
      "bars-progress": et,
      play: ke,
      "play-circle": ke,
      pause: $t,
      forward: aa,
      "right-from-bracket": de,
      // Status indicators
      fire: jt,
      bug: Xe,
      star: ra,
      flask: Ct,
      wrench: ka,
      bolt: ga,
      heart: Ht,
      thumbtack: Zt,
      bell: $e,
      "shield-halved": ta,
      moon: Bt,
      sun: sa,
      palette: Gt,
      "toggle-on": la,
      camera: Qe,
      sort: ae,
      "sort-up": oe,
      "sort-down": re,
      gear: ge,
      "check-square": ue,
      // Finance
      "dollar-sign": kt,
      "euro-sign": mt,
      "sterling-sign": Qt,
      "yen-sign": Et,
      "indian-rupee-sign": Ut,
      "won-sign": R,
      "lira-sign": R,
      "brazilian-real-sign": R,
      coins: R,
      wallet: pa,
      calculator: Ze,
      "chart-line": da,
      "chart-bar": Ke,
      "chart-pie": tt,
      // Misc
      spinner: F,
      "align-left": U,
      minus: T,
      exclamation: E,
      github: At
    }, h = d, i = xe(() => {
      const c = h.name.replace(/^fa-(solid|regular|brands)\s+/, "").replace(/^fa-/, "");
      return r[c] ?? null;
    });
    return (c, l) => i.value ? (k(), V(je(i.value), {
      key: 0,
      class: D({ "animate-spin": d.spin })
    }, null, 8, ["class"])) : w("", !0);
  }
}), fa = { class: "p-6 bg-white dark:bg-gray-950 min-h-full" }, ba = { class: "mb-6" }, va = { class: "text-2xl font-semibold text-gray-900 dark:text-gray-100 m-0" }, _a = {
  key: 0,
  class: "flex items-center justify-center py-20"
}, wa = { class: "text-center" }, Ma = { class: "text-gray-500 dark:text-gray-400" }, ja = {
  key: 1,
  class: "flex items-center justify-center py-20"
}, Ca = { class: "bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center" }, za = { class: "text-red-800 dark:text-red-300 font-medium mb-2" }, qa = { class: "text-red-600 dark:text-red-400 text-sm mb-4" }, Aa = {
  key: 2,
  class: "flex gap-6"
}, Va = { class: "w-60 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg py-3 shrink-0" }, Sa = ["onClick"], Ha = { class: "flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg" }, La = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, Ua = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, Ea = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, Pa = { class: "p-6" }, Oa = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Ra = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ta = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Da = { value: "Open" }, Fa = { value: "In Progress" }, Ia = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Na = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ba = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ga = { value: "Planning" }, Ja = { value: "Active" }, $a = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Xa = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Za = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Wa = { class: "flex justify-between items-center py-3" }, Ya = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Qa = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Ka = { value: "Low" }, er = { value: "Medium" }, tr = { value: "High" }, ar = { value: "Urgent" }, rr = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, sr = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, or = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, nr = { class: "p-6" }, lr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, dr = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, ir = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, cr = { class: "relative inline-block w-11 h-6" }, yr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, hr = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, ur = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, pr = { class: "relative inline-block w-11 h-6" }, kr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, gr = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, mr = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, xr = { class: "relative inline-block w-11 h-6" }, fr = { class: "flex justify-between items-center py-3" }, br = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, vr = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, _r = { class: "flex items-center gap-2" }, wr = { class: "text-sm text-gray-500 dark:text-gray-400" }, Mr = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, jr = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, Cr = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, zr = { class: "p-6" }, qr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Ar = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Vr = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Sr = { class: "relative inline-block w-11 h-6" }, Hr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Lr = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ur = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Er = { class: "relative inline-block w-11 h-6" }, Pr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Or = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Rr = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Tr = { class: "relative inline-block w-11 h-6" }, Dr = { class: "flex justify-between items-center py-3" }, Fr = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Ir = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Nr = { class: "flex items-center gap-2" }, Br = { class: "text-sm text-gray-500 dark:text-gray-400" }, Gr = { class: "p-6 border-b border-gray-200 dark:border-gray-700" }, Jr = { class: "text-base font-semibold text-gray-900 dark:text-gray-100 m-0" }, $r = { class: "text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0" }, Xr = { class: "p-6" }, Zr = { class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700" }, Wr = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, Yr = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, Qr = { class: "text-sm font-mono text-gray-900 dark:text-gray-100" }, Kr = {
  key: 0,
  class: "flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700"
}, e1 = { class: "text-sm font-medium text-gray-900 dark:text-gray-100 m-0" }, t1 = { class: "text-xs text-gray-500 dark:text-gray-400 m-0 mt-1" }, a1 = {
  key: 1,
  class: "mt-4 p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg"
}, r1 = { class: "flex items-start gap-3" }, s1 = { class: "flex-1" }, o1 = { class: "text-sm font-semibold text-amber-800 dark:text-amber-300 m-0" }, n1 = { class: "text-sm text-amber-700 dark:text-amber-400 mt-1 mb-0" }, l1 = {
  key: 0,
  class: "mt-3 text-xs text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded p-3 max-h-40 overflow-y-auto whitespace-pre-wrap"
}, d1 = { key: 0 }, i1 = { class: "mt-3 flex items-center gap-3" }, c1 = ["href"], y1 = {
  key: 2,
  class: "mt-4 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg"
}, h1 = { class: "flex items-center gap-3" }, u1 = { class: "text-sm font-semibold text-green-800 dark:text-green-300 m-0" }, p1 = { class: "text-sm text-green-700 dark:text-green-400 mt-1 mb-0" }, k1 = {
  key: 3,
  class: "mt-4 p-4 bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-600 rounded-lg text-center"
}, g1 = { class: "text-sm text-gray-500 dark:text-gray-400 m-0" }, m1 = {
  key: 4,
  class: "mt-3 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400"
}, x1 = { class: "mt-6 pt-4 border-t border-gray-100 dark:border-gray-700" }, f1 = ["disabled"], b1 = {
  key: 5,
  class: "p-4 bg-gray-50 dark:bg-gray-700/50 flex justify-end gap-3 border-t border-gray-200 dark:border-gray-700"
}, v1 = ["disabled"], M1 = /* @__PURE__ */ fe({
  __name: "Settings",
  setup(d) {
    const { getSettings: r, updateSettings: h } = Le(), { updateInfo: i, isChecking: c, checkError: l, forceCheck: x, dismissUpdate: j } = Pe(), p = v("defaults"), _ = [
      { id: "defaults", name: s("Defaults"), icon: "sliders-horizontal" },
      { id: "features", name: s("Features"), icon: "toggle-right" },
      { id: "notifications", name: s("Notifications"), icon: "bell" },
      { id: "updates", name: s("Updates"), icon: "arrow-up-circle" }
    ], u = v({
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
    }), B = v(!0), S = v(!1), P = v(null), M = v(null);
    async function Q() {
      B.value = !0, P.value = null;
      try {
        const g = await r();
        u.value = {
          default_task_status: g.default_task_status || "Open",
          default_project_status: g.default_project_status || "Planning",
          project_code_prefix: g.project_code_prefix || "ORG",
          default_priority: g.default_priority || "Medium",
          auto_calculate_progress: g.auto_calculate_progress ? 1 : 0,
          auto_set_missed_milestones: g.auto_set_missed_milestones ? 1 : 0,
          enable_time_tracking: g.enable_time_tracking ? 1 : 0,
          default_capacity_hours: g.default_capacity_hours || 40,
          notify_on_task_assignment: g.notify_on_task_assignment ? 1 : 0,
          notify_on_status_change: g.notify_on_status_change ? 1 : 0,
          notify_on_due_date: g.notify_on_due_date ? 1 : 0,
          due_date_reminder_days: g.due_date_reminder_days || 1
        };
      } catch (g) {
        console.error("Failed to load settings:", g), P.value = g.message || s("Failed to load settings");
      } finally {
        B.value = !1;
      }
    }
    async function _e() {
      S.value = !0, M.value = null;
      try {
        await h(u.value), M.value = { type: "success", text: s("Settings saved successfully") }, setTimeout(() => {
          M.value = null;
        }, 3e3);
      } catch (g) {
        console.error("Failed to save settings:", g), M.value = { type: "error", text: g.message || s("Failed to save settings") };
      } finally {
        S.value = !1;
      }
    }
    function we() {
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
    return Ce(Q), (g, n) => (k(), m("div", fa, [
      e("div", ba, [
        e("h1", va, o(a(s)("Settings")), 1)
      ]),
      B.value ? (k(), m("div", _a, [
        e("div", wa, [
          C(a(F), {
            class: "w-8 h-8 text-accent-500 mb-3 animate-spin",
            "aria-hidden": "true"
          }),
          e("p", Ma, o(a(s)("Loading settings...")), 1)
        ])
      ])) : P.value ? (k(), m("div", ja, [
        e("div", Ca, [
          C(a(N), {
            class: "w-8 h-8 text-red-500 mb-3",
            "aria-hidden": "true"
          }),
          e("h3", za, o(a(s)("Error loading settings")), 1),
          e("p", qa, o(P.value), 1),
          e("button", {
            onClick: Q,
            class: "px-4 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/60"
          }, o(a(s)("Try Again")), 1)
        ])
      ])) : (k(), m("div", Aa, [
        e("nav", Va, [
          (k(), m(H, null, ze(_, (y) => e("a", {
            key: y.id,
            href: "#",
            class: D([
              "flex items-center gap-3 px-5 py-3 text-sm transition-all no-underline",
              p.value === y.id ? "text-accent-500 dark:text-accent-400 bg-accent-50 dark:bg-accent-950/30 border-l-[3px] border-accent-500 dark:border-accent-400" : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
            ]),
            onClick: qe((_1) => p.value = y.id, ["prevent"])
          }, [
            C(xa, {
              name: y.icon,
              class: "w-5 h-5"
            }, null, 8, ["name"]),
            e("span", null, o(y.name), 1)
          ], 10, Sa)), 64))
        ]),
        e("div", Ha, [
          M.value ? (k(), m("div", {
            key: 0,
            class: D([
              "px-4 py-3 text-sm",
              M.value.type === "success" ? "bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-b border-green-200 dark:border-green-800" : "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 border-b border-red-200 dark:border-red-800"
            ])
          }, [
            M.value.type === "success" ? (k(), V(a(I), {
              key: 0,
              class: "w-4 h-4 inline mr-2",
              "aria-hidden": "true"
            })) : (k(), V(a(E), {
              key: 1,
              class: "w-4 h-4 inline mr-2",
              "aria-hidden": "true"
            })),
            z(" " + o(M.value.text), 1)
          ], 2)) : w("", !0),
          p.value === "defaults" ? (k(), m(H, { key: 1 }, [
            e("div", La, [
              e("h3", Ua, o(a(s)("Default Values")), 1),
              e("p", Ea, o(a(s)("Configure default values for new projects and tasks")), 1)
            ]),
            e("div", Pa, [
              e("div", Oa, [
                e("div", null, [
                  e("h4", Ra, o(a(s)("Default Task Status")), 1),
                  e("p", Ta, o(a(s)("Status assigned to new tasks")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": n[0] || (n[0] = (y) => u.value.default_task_status = y),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-accent-500 dark:focus:border-accent-400"
                }, [
                  e("option", Da, o(a(s)("Open")), 1),
                  e("option", Fa, o(a(s)("In Progress")), 1)
                ], 512), [
                  [G, u.value.default_task_status]
                ])
              ]),
              e("div", Ia, [
                e("div", null, [
                  e("h4", Na, o(a(s)("Default Project Status")), 1),
                  e("p", Ba, o(a(s)("Status assigned to new projects")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": n[1] || (n[1] = (y) => u.value.default_project_status = y),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-accent-500 dark:focus:border-accent-400"
                }, [
                  e("option", Ga, o(a(s)("Planning")), 1),
                  e("option", Ja, o(a(s)("Active")), 1)
                ], 512), [
                  [G, u.value.default_project_status]
                ])
              ]),
              e("div", $a, [
                e("div", null, [
                  e("h4", Xa, o(a(s)("Project Code Prefix")), 1),
                  e("p", Za, o(a(s)("Prefix for auto-generated project codes (e.g., ORG-2026-0001)")), 1)
                ]),
                f(e("input", {
                  "onUpdate:modelValue": n[2] || (n[2] = (y) => u.value.project_code_prefix = y),
                  type: "text",
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-32 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-accent-500 dark:focus:border-accent-400",
                  maxlength: "10"
                }, null, 512), [
                  [J, u.value.project_code_prefix]
                ])
              ]),
              e("div", Wa, [
                e("div", null, [
                  e("h4", Ya, o(a(s)("Default Priority")), 1),
                  e("p", Qa, o(a(s)("Priority assigned to new tasks")), 1)
                ]),
                f(e("select", {
                  "onUpdate:modelValue": n[3] || (n[3] = (y) => u.value.default_priority = y),
                  class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-accent-500 dark:focus:border-accent-400"
                }, [
                  e("option", Ka, o(a(s)("Low")), 1),
                  e("option", er, o(a(s)("Medium")), 1),
                  e("option", tr, o(a(s)("High")), 1),
                  e("option", ar, o(a(s)("Urgent")), 1)
                ], 512), [
                  [G, u.value.default_priority]
                ])
              ])
            ])
          ], 64)) : p.value === "features" ? (k(), m(H, { key: 2 }, [
            e("div", rr, [
              e("h3", sr, o(a(s)("Features")), 1),
              e("p", or, o(a(s)("Enable or disable optional features")), 1)
            ]),
            e("div", nr, [
              e("div", lr, [
                e("div", null, [
                  e("h4", dr, o(a(s)("Auto Calculate Progress")), 1),
                  e("p", ir, o(a(s)("Automatically calculate project progress from task completion")), 1)
                ]),
                e("label", cr, [
                  f(e("input", {
                    "onUpdate:modelValue": n[4] || (n[4] = (y) => u.value.auto_calculate_progress = y),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [q, u.value.auto_calculate_progress]
                  ]),
                  n[14] || (n[14] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-accent-500 transition-all" }, null, -1)),
                  n[15] || (n[15] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", yr, [
                e("div", null, [
                  e("h4", hr, o(a(s)("Auto Set Missed Milestones")), 1),
                  e("p", ur, o(a(s)("Automatically mark milestones as missed when overdue")), 1)
                ]),
                e("label", pr, [
                  f(e("input", {
                    "onUpdate:modelValue": n[5] || (n[5] = (y) => u.value.auto_set_missed_milestones = y),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [q, u.value.auto_set_missed_milestones]
                  ]),
                  n[16] || (n[16] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-accent-500 transition-all" }, null, -1)),
                  n[17] || (n[17] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", kr, [
                e("div", null, [
                  e("h4", gr, o(a(s)("Enable Time Tracking")), 1),
                  e("p", mr, o(a(s)("Allow users to log time against tasks")), 1)
                ]),
                e("label", xr, [
                  f(e("input", {
                    "onUpdate:modelValue": n[6] || (n[6] = (y) => u.value.enable_time_tracking = y),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [q, u.value.enable_time_tracking]
                  ]),
                  n[18] || (n[18] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-accent-500 transition-all" }, null, -1)),
                  n[19] || (n[19] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", fr, [
                e("div", null, [
                  e("h4", br, o(a(s)("Default Weekly Capacity")), 1),
                  e("p", vr, o(a(s)("Default hours per week for contact capacity planning")), 1)
                ]),
                e("div", _r, [
                  f(e("input", {
                    "onUpdate:modelValue": n[7] || (n[7] = (y) => u.value.default_capacity_hours = y),
                    type: "number",
                    min: "1",
                    max: "168",
                    class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-accent-500 dark:focus:border-accent-400"
                  }, null, 512), [
                    [
                      J,
                      u.value.default_capacity_hours,
                      void 0,
                      { number: !0 }
                    ]
                  ]),
                  e("span", wr, o(a(s)("hours")), 1)
                ])
              ])
            ])
          ], 64)) : p.value === "notifications" ? (k(), m(H, { key: 3 }, [
            e("div", Mr, [
              e("h3", jr, o(a(s)("Notifications")), 1),
              e("p", Cr, o(a(s)("Configure email notification settings")), 1)
            ]),
            e("div", zr, [
              e("div", qr, [
                e("div", null, [
                  e("h4", Ar, o(a(s)("Task Assignment")), 1),
                  e("p", Vr, o(a(s)("Send notification when a task is assigned to a user")), 1)
                ]),
                e("label", Sr, [
                  f(e("input", {
                    "onUpdate:modelValue": n[8] || (n[8] = (y) => u.value.notify_on_task_assignment = y),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [q, u.value.notify_on_task_assignment]
                  ]),
                  n[20] || (n[20] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-accent-500 transition-all" }, null, -1)),
                  n[21] || (n[21] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Hr, [
                e("div", null, [
                  e("h4", Lr, o(a(s)("Status Changes")), 1),
                  e("p", Ur, o(a(s)("Send notification when task status changes")), 1)
                ]),
                e("label", Er, [
                  f(e("input", {
                    "onUpdate:modelValue": n[9] || (n[9] = (y) => u.value.notify_on_status_change = y),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [q, u.value.notify_on_status_change]
                  ]),
                  n[22] || (n[22] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-accent-500 transition-all" }, null, -1)),
                  n[23] || (n[23] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Pr, [
                e("div", null, [
                  e("h4", Or, o(a(s)("Due Date Reminders")), 1),
                  e("p", Rr, o(a(s)("Send reminder before task due date")), 1)
                ]),
                e("label", Tr, [
                  f(e("input", {
                    "onUpdate:modelValue": n[10] || (n[10] = (y) => u.value.notify_on_due_date = y),
                    type: "checkbox",
                    "true-value": 1,
                    "false-value": 0,
                    class: "sr-only peer"
                  }, null, 512), [
                    [q, u.value.notify_on_due_date]
                  ]),
                  n[24] || (n[24] = e("span", { class: "absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-accent-500 transition-all" }, null, -1)),
                  n[25] || (n[25] = e("span", { class: "absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5" }, null, -1))
                ])
              ]),
              e("div", Dr, [
                e("div", null, [
                  e("h4", Fr, o(a(s)("Reminder Lead Time")), 1),
                  e("p", Ir, o(a(s)("Days before due date to send reminder")), 1)
                ]),
                e("div", Nr, [
                  f(e("input", {
                    "onUpdate:modelValue": n[11] || (n[11] = (y) => u.value.due_date_reminder_days = y),
                    type: "number",
                    min: "1",
                    max: "30",
                    class: "px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-accent-500 dark:focus:border-accent-400"
                  }, null, 512), [
                    [
                      J,
                      u.value.due_date_reminder_days,
                      void 0,
                      { number: !0 }
                    ]
                  ]),
                  e("span", Br, o(a(s)("days")), 1)
                ])
              ])
            ])
          ], 64)) : p.value === "updates" ? (k(), m(H, { key: 4 }, [
            e("div", Gr, [
              e("h3", Jr, o(a(s)("App Updates")), 1),
              e("p", $r, o(a(s)("Check for new versions of Orga")), 1)
            ]),
            e("div", Xr, [
              e("div", Zr, [
                e("div", null, [
                  e("h4", Wr, o(a(s)("Installed Version")), 1),
                  e("p", Yr, o(a(s)("Currently running version")), 1)
                ]),
                e("span", Qr, " v" + o(a(i)?.current_version || a(Oe)), 1)
              ]),
              a(i) ? (k(), m("div", Kr, [
                e("div", null, [
                  e("h4", e1, o(a(s)("Latest Version")), 1),
                  e("p", t1, o(a(s)("Last checked: {0}", [a(i).checked_at ? new Date(a(i).checked_at).toLocaleString() : a(s)("Never")])), 1)
                ]),
                e("span", {
                  class: D([
                    "text-sm font-mono",
                    a(i).update_available ? "text-amber-600 dark:text-amber-400 font-semibold" : "text-green-600 dark:text-green-400"
                  ])
                }, " v" + o(a(i).latest_version), 3)
              ])) : w("", !0),
              a(i)?.update_available ? (k(), m("div", a1, [
                e("div", r1, [
                  C(a(ve), {
                    class: "w-5 h-5 text-amber-500 mt-0.5",
                    "aria-hidden": "true"
                  }),
                  e("div", s1, [
                    e("h4", o1, o(a(s)("Update Available")), 1),
                    e("p", n1, o(a(s)("Version {0} is available. You are running {1}.", [a(i).latest_version, a(i).current_version])), 1),
                    a(i).release_notes ? (k(), m("div", l1, [
                      z(o(a(i).release_notes.substring(0, 500)) + " ", 1),
                      a(i).release_notes.length > 500 ? (k(), m("span", d1, "...")) : w("", !0)
                    ])) : w("", !0),
                    e("div", i1, [
                      e("a", {
                        href: a(i).release_url,
                        target: "_blank",
                        rel: "noopener noreferrer",
                        class: "inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded transition-colors no-underline"
                      }, [
                        n[26] || (n[26] = e("span", {
                          class: "text-xs",
                          "aria-hidden": "true"
                        }, "GH", -1)),
                        z(" " + o(a(s)("View Release")), 1)
                      ], 8, c1),
                      e("button", {
                        onClick: n[12] || (n[12] = //@ts-ignore
                        (...y) => a(j) && a(j)(...y)),
                        class: "px-3 py-1.5 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 rounded transition-colors"
                      }, o(a(s)("Dismiss")), 1)
                    ])
                  ])
                ])
              ])) : a(i) && !a(i).update_available ? (k(), m("div", y1, [
                e("div", h1, [
                  C(a(I), {
                    class: "w-5 h-5 text-green-500",
                    "aria-hidden": "true"
                  }),
                  e("div", null, [
                    e("h4", u1, o(a(s)("Up to Date")), 1),
                    e("p", p1, o(a(s)("You are running the latest version of Orga.")), 1)
                  ])
                ])
              ])) : (k(), m("div", k1, [
                e("p", g1, o(a(s)("No update information available yet.")), 1)
              ])),
              a(l) ? (k(), m("div", m1, [
                C(a(N), {
                  class: "w-3.5 h-3.5 inline mr-1",
                  "aria-hidden": "true"
                }),
                z(" " + o(a(s)("Update check failed: {0}", [a(l)])), 1)
              ])) : w("", !0),
              e("div", x1, [
                e("button", {
                  onClick: n[13] || (n[13] = //@ts-ignore
                  (...y) => a(x) && a(x)(...y)),
                  disabled: a(c),
                  class: "px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                }, [
                  a(c) ? (k(), V(a(F), {
                    key: 0,
                    class: "w-4 h-4 animate-spin",
                    "aria-hidden": "true"
                  })) : (k(), V(a(Y), {
                    key: 1,
                    class: "w-4 h-4",
                    "aria-hidden": "true"
                  })),
                  z(" " + o(a(c) ? a(s)("Checking...") : a(s)("Check for Updates")), 1)
                ], 8, f1)
              ])
            ])
          ], 64)) : w("", !0),
          p.value !== "updates" ? (k(), m("div", b1, [
            e("button", {
              onClick: we,
              class: "px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors"
            }, o(a(s)("Reset to Defaults")), 1),
            e("button", {
              onClick: _e,
              disabled: S.value,
              class: "px-4 py-2 bg-accent-500 hover:bg-accent-600 dark:bg-accent-600 dark:hover:bg-accent-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            }, [
              S.value ? (k(), V(a(F), {
                key: 0,
                class: "w-4 h-4 animate-spin",
                "aria-hidden": "true"
              })) : w("", !0),
              z(" " + o(S.value ? a(s)("Saving...") : a(s)("Save Changes")), 1)
            ], 8, v1)
          ])) : w("", !0)
        ])
      ]))
    ]));
  }
});
export {
  M1 as OrgaSettings
};
