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
let timer = 0;
let pushing = false;
let ready = false;
let booting = null;

export function accountEnabled() {
  return firebaseReady();
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

function prefersRedirect() {
  const ua = navigator.userAgent || "";
  if (/Android|iPhone|iPad|iPod/i.test(ua)) return true;
  const narrow = window.matchMedia("(max-width: 768px)").matches;
  const coarse = window.matchMedia("(pointer: coarse)").matches;
  return narrow && coarse;
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
  const [{ initializeApp, getApps }, authMod, firestoreMod] = await Promise.all([
    import(`${CDN}/firebase-app.js`),
    import(`${CDN}/firebase-auth.js`),
    import(`${CDN}/firebase-firestore.js`),
  ]);
  const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
  auth = authMod.getAuth(app);
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
  } catch (error) {
    console.error(error);
  }
  return true;
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

export async function signInGoogle() {
  if (!firebaseReady()) return { ok: false, reason: "disabled" };
  try {
    if (!ready) await boot();
  } catch {
    return { ok: false, reason: "load" };
  }
  if (!auth) return { ok: false, reason: "load" };
  const authMod = await import(`${CDN}/firebase-auth.js`);
  const provider = new authMod.GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  const redirect = async () => {
    await authMod.signInWithRedirect(auth, provider);
    return { ok: true, redirect: true };
  };
  if (prefersRedirect()) {
    try {
      return await redirect();
    } catch (error) {
      return { ok: false, reason: error && error.code ? error.code : "redirect" };
    }
  }
  try {
    await authMod.signInWithPopup(auth, provider);
    return { ok: true };
  } catch (error) {
    const code = error && error.code ? error.code : "";
    if (code === "auth/popup-blocked" || code === "auth/operation-not-supported-in-this-environment") {
      try {
        return await redirect();
      } catch (redirectError) {
        return { ok: false, reason: redirectError && redirectError.code ? redirectError.code : "redirect" };
      }
    }
    return { ok: false, reason: code || "popup" };
  }
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
