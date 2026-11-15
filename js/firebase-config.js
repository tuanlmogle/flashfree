/* Web app config for Firebase project flashfree-9971e.
   This config is public by design. Access control is firestore.rules,
   plus the authorized domains in the Firebase console.
   Analytics is intentionally omitted: the app does not load that SDK. */

export const firebaseConfig = {
  apiKey: "AIzaSyAjksyHRERszUj8mM4BfxkphuPPnHtJnVs",
  authDomain: "flashfree-9971e.firebaseapp.com",
  projectId: "flashfree-9971e",
  storageBucket: "flashfree-9971e.firebasestorage.app",
  messagingSenderId: "255505095210",
  appId: "1:255505095210:web:84aaaaa3a0304528644153",
};

export function firebaseReady(config = firebaseConfig) {
  const required = ["apiKey", "authDomain", "projectId", "appId"];
  return required.every((key) => {
    const value = String((config && config[key]) || "").trim();
    if (value.length < 8) return false;
    if (/your_|todo|placeholder|changeme|xxx+/i.test(value)) return false;
    return true;
  });
}
