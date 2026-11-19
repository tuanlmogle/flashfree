/* Google sign-in and Firestore sync. Loaded only when firebase-config.js is filled in.
   The SDK comes from the official gstatic CDN as ES modules. No build step. */

import { firebaseConfig, firebaseReady } from "./firebase-config.js";
import { chunkMap, mergeStates, unchunkMap } from "./progress.js";

const VERSION = "12.4.0";
const CDN = `https://www.gstatic.com/firebasejs/${VERSION}`;

let hooks = null;
let user = null;
let db = null;
let auth = null;
let authMod = null;
let googleProvider = null;
let timer = 0;
let pushing = false;
let ready = false;
let booting = null;

export function accountEnabled() {
  return firebaseReady();
}

export function firebaseCdn() {
  return CDN;
}

export function currentUser() {
  return user;
}

export function bindAccount(next) {
  hooks = next;
  if (!firebaseReady()) return Promise.resolve(false);
  return boot().catch((error) => {
    console.error(error);
    ready = false;
    return false;
  });
}

async function boot() {
  if (ready) return true;
  if (booting) return booting;
  booting = bootOnce().then(() => {
    ready = true;
    return true;
  }).catch((error) => {
    booting = null;
    throw error;
  });
  return booting;
}

async function bootOnce() {
  const [{ initializeApp, getApps }, loadedAuth, firestoreMod] = await Promise.all([
    import(`${CDN}/firebase-app.js`),
    import(`${CDN}/firebase-auth.js`),
    import(`${CDN}/firebase-firestore.js`),
  ]);
  authMod = loadedAuth;
  const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
  auth = authMod.getAuth(app);
  googleProvider = new authMod.GoogleAuthProvider();
  googleProvider.setCustomParameters({ prompt: "select_account" });
  try {
    db = firestoreMod.initializeFirestore(app, {
      localCache: firestoreMod.persistentLocalCache({
        tabManager: firestoreMod.persistentMultipleTabManager(),
      }),
    });
  } catch {
    db = firestoreMod.getFirestore(app);
  }
  authMod.onAuthStateChanged(auth, (next) => {
    user = next || null;
    if (hooks && hooks.onUser) hooks.onUser(publicUser());
    if (user) syncDown().catch((error) => console.error(error));
  });
  try {
    await authMod.getRedirectResult(auth);
  } catch {
    /* An old redirect that the browser blocked should not stop sign-in. */
  }
  return true;
}

export function prepareSignIn() {
  if (!firebaseReady()) return Promise.resolve(false);
  return boot().then(() => true).catch(() => false);
}

export async function ensureFirebaseApp() {
  if (!firebaseReady()) return null;
  try {
    await boot();
  } catch {
    return null;
  }
  const { getApps } = await import(`${CDN}/firebase-app.js`);
  return getApps()[0] || null;
}

export async function saveAiNote(id, note) {
  if (!db || !user || !id || !note) return;
  const { doc, setDoc } = await import(`${CDN}/firebase-firestore.js`);
  const data = {};
  for (const key of ["word", "pos", "ipa", "meaning", "explain", "level", "examples", "emoji", "at"]) {
    if (note[key] !== undefined) data[key] = note[key];
  }
  await setDoc(doc(db, "users", user.uid, "ai", String(id).slice(0, 60)), data);
}

export async function loadAiNotes() {
  if (!db || !user) return [];
  const { getDocs, collection } = await import(`${CDN}/firebase-firestore.js`);
  const snap = await getDocs(collection(db, "users", user.uid, "ai"));
  const out = [];
  snap.forEach((item) => out.push(item.data() || {}));
  return out;
}

export function publicUser() {
  if (!user) return null;
  return {
    uid: user.uid,
    name: user.displayName || "",
    email: user.email || "",
    photo: user.photoURL || "",
  };
}

function redirectSignIn() {
  return authMod.signInWithRedirect(auth, googleProvider).then(
    () => ({ ok: true, redirect: true }),
    (error) => ({ ok: false, reason: error && error.code ? error.code : "redirect" }),
  );
}

function popupFailure(error) {
  const code = error && error.code ? error.code : "popup";
  if (code === "auth/popup-blocked") return redirectSignIn();
  return { ok: false, reason: code };
}

// Must call signInWithPopup in the same turn as the tap. Awaiting the SDK
// first makes iOS drop the popup.
export function signInGoogle() {
  if (!firebaseReady()) return Promise.resolve({ ok: false, reason: "disabled" });
  if (!auth || !authMod || !googleProvider) {
    return Promise.resolve({ ok: false, reason: "load" });
  }
  let pending;
  try {
    pending = authMod.signInWithPopup(auth, googleProvider);
  } catch (error) {
    return Promise.resolve(popupFailure(error));
  }
  return Promise.resolve(pending).then(() => ({ ok: true }), popupFailure);
}

export async function signOutGoogle() {
  if (!auth) {
    user = null;
    if (hooks && hooks.onUser) hooks.onUser(null);
    return;
  }
  const authMod = await import(`${CDN}/firebase-auth.js`);
  await authMod.signOut(auth);
}

export function scheduleSync() {
  if (!firebaseReady() || !user || !hooks) return;
  window.clearTimeout(timer);
  timer = window.setTimeout(() => {
    pushState().catch((error) => console.error(error));
  }, 1200);
}

function snapshot() {
  return hooks && hooks.snapshot ? hooks.snapshot() : null;
}

async function syncDown() {
  const local = snapshot();
  if (!local || !db || !user) return;
  const { doc, getDoc, getDocs, collection } = await import(`${CDN}/firebase-firestore.js`);
  const ref = doc(db, "users", user.uid);
  const main = await getDoc(ref);
  const cloud = main.exists() ? main.data() : null;
  const progressSnap = await getDocs(collection(db, "users", user.uid, "progress"));
  const prefsSnap = await getDocs(collection(db, "users", user.uid, "prefs"));
  const cards = {};
  const picPrefs = {};
  progressSnap.forEach((item) => Object.assign(cards, item.data() || {}));
  prefsSnap.forEach((item) => Object.assign(picPrefs, item.data() || {}));
  let merged = local;
  if (cloud) {
    merged = mergeStates(local, {
      ...cloud,
      cards,
      picPrefs: { ...picPrefs, ...(cloud.picPrefs || {}) },
    }, hooks.today());
  }
  if (hooks.apply) hooks.apply(merged);
  if (hooks.onAi) {
    try { hooks.onAi(await loadAiNotes()); } catch (error) { console.error(error); }
  }
  await claimReferral();
  await refreshInvites();
  await pushState();
}

async function claimReferral() {
  if (!db || !user || !hooks) return;
  let refId = "";
  try { refId = sessionStorage.getItem("latu-ref") || ""; } catch { /* ignore */ }
  refId = String(refId || "").trim();
  if (!refId || refId === user.uid) return;
  const { doc, setDoc, serverTimestamp } = await import(`${CDN}/firebase-firestore.js`);
  try {
    await setDoc(doc(db, "users", refId, "referrals", user.uid), {
      at: serverTimestamp(),
    });
  } catch {
    /* create-only: a second sign-in, or a ref that is not a real account, is ignored */
  }
  try { sessionStorage.removeItem("latu-ref"); } catch { /* ignore */ }
}

async function refreshInvites() {
  if (!db || !user || !hooks) return;
  const { getDocs, collection } = await import(`${CDN}/firebase-firestore.js`);
  try {
    const snap = await getDocs(collection(db, "users", user.uid, "referrals"));
    if (hooks.setInvites) hooks.setInvites(snap.size);
  } catch (error) {
    console.error(error);
  }
}

async function pushState() {
  if (!db || !user || pushing) return;
  const state = snapshot();
  if (!state) return;
  pushing = true;
  try {
    const { doc, setDoc, getDocs, collection, deleteDoc } = await import(`${CDN}/firebase-firestore.js`);
    const { cards, picPrefs, ...rest } = state;
    await setDoc(doc(db, "users", user.uid), {
      ...rest,
      name: user.displayName || "",
      email: user.email || "",
      photo: user.photoURL || "",
    });
    const cardChunks = chunkMap(cards || {});
    const prefChunks = chunkMap(picPrefs || {});
    const writes = [];
    for (const [id, value] of Object.entries(cardChunks)) {
      writes.push(setDoc(doc(db, "users", user.uid, "progress", id), value));
    }
    for (const [id, value] of Object.entries(prefChunks)) {
      writes.push(setDoc(doc(db, "users", user.uid, "prefs", id), value));
    }
    for (const folder of ["progress", "prefs"]) {
      const live = folder === "progress" ? cardChunks : prefChunks;
      const snap = await getDocs(collection(db, "users", user.uid, folder));
      snap.forEach((item) => {
        if (!live[item.id]) writes.push(deleteDoc(item.ref));
      });
    }
    await Promise.all(writes);
  } finally {
    pushing = false;
  }
}

export function flattenChunks(chunks) {
  return unchunkMap(chunks);
}
