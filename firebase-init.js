/**
 * Shared Firebase init + visitor count + interaction tracking.
 * Load this as type="module" on pages that need Firebase (e.g. index, projects).
 */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getDatabase, ref, push, get, set, increment, remove, child } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyBnyUJvCCDZ2txRai9akUjIkH0-qVnrwys",
  authDomain: "abby-li-website.firebaseapp.com",
  databaseURL: "https://abby-li-website-default-rtdb.firebaseio.com",
  projectId: "abby-li-website",
  storageBucket: "abby-li-website.firebastorage.app",
  messagingSenderId: "109684047786",
  appId: "1:109684047786:web:2dabbb1c8279ef4c9675d3",
  measurementId: "G-BK78DY09CP"
};

const INTERACTIONS_KEY = "smart_website_recent_views";
const USER_ID_KEY = "smart_website_user_id";
const MAX_RECENT_VIEWS = 20;

function getOrCreateUserId() {
  let uid = localStorage.getItem(USER_ID_KEY);
  if (!uid) {
    uid = "anon_" + Math.random().toString(36).slice(2) + "_" + Date.now().toString(36);
    localStorage.setItem(USER_ID_KEY, uid);
  }
  return uid;
}

function getPageId() {
  const path = typeof window !== "undefined" && window.location ? window.location.pathname : "";
  const base = path.replace(/^\//, "").replace(/\.html$/, "") || "index";
  return base === "index" ? "home" : base;
}

function appendRecentView(pageId) {
  try {
    const raw = localStorage.getItem(INTERACTIONS_KEY);
    const list = raw ? JSON.parse(raw) : [];
    list.push({ page_id: pageId, ts: Date.now() });
    const trimmed = list.slice(-MAX_RECENT_VIEWS);
    localStorage.setItem(INTERACTIONS_KEY, JSON.stringify(trimmed));
  } catch (_) {}
}

let pageLoadTime = 0;

try {
  const app = initializeApp(firebaseConfig);
  const database = getDatabase(app);
  window.firebaseApp = app;
  window.firebaseDatabase = database;
  window.firebaseRefs = { ref, push, get, set, increment, remove, child };

  const el = document.getElementById("visitorCount");
  if (el) {
    const visitsRef = ref(database, "visits");
    get(visitsRef).then((snapshot) => {
      const visits = snapshot.val() ?? 0;
      el.textContent = visits;
      set(visitsRef, increment(1));
    }).catch(() => {});
  }

  pageLoadTime = Date.now();
  const pageId = getPageId();
  const userId = getOrCreateUserId();
  appendRecentView(pageId);

  const interactionsRef = ref(database, "interactions");
  push(interactionsRef, {
    user_id: userId,
    page_id: pageId,
    event_type: "page_view",
    timestamp: new Date().toISOString()
  }).catch(() => {});

  window.addEventListener("beforeunload", () => {
    const dwellTime = Math.round((Date.now() - pageLoadTime) / 1000);
    push(interactionsRef, {
      user_id: userId,
      page_id: pageId,
      event_type: "dwell",
      timestamp: new Date().toISOString(),
      dwell_time: dwellTime
    }).catch(() => {});
  });
} catch (err) {
  console.error("Firebase init error:", err);
}
