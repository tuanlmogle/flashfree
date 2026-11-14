/* Paste the Web app config from the Firebase console.
   Leave the strings empty and the app stays a guest-only flashcard deck.
   Do not put a secret here. The Firebase web config is public by design,
   and security is the job of firestore.rules. */

export const firebaseConfig = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  storageBucket: "",
  messagingSenderId: "",
  appId: "",
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
