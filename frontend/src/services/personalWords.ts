"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import { tiles } from "@/data/tiles";

type Labels = Record<string, { english: string; urdu: string }>;
const KEY = "goyai-personal-words";
const CHANGED = "goyai-personal-words-changed";
let memoryFallback = "";
let storageUnavailable = false;

function subscribe(notify: () => void) {
  window.addEventListener(CHANGED, notify);
  window.addEventListener("storage", notify);
  return () => {
    window.removeEventListener(CHANGED, notify);
    window.removeEventListener("storage", notify);
  };
}
function snapshot() {
  if (storageUnavailable) return memoryFallback;
  try { return window.sessionStorage.getItem(KEY) ?? memoryFallback; }
  catch { return memoryFallback; }
}
function serverSnapshot() { return ""; }
function parse(saved: string): Labels {
  try {
    const value: unknown = JSON.parse(saved || "{}");
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    const allowed = new Set(tiles.filter((tile) => tile.category === "personal").map((tile) => tile.id));
    return Object.fromEntries(Object.entries(value).filter(([id, label]) =>
      allowed.has(id) && label && typeof label === "object" &&
      typeof label.english === "string" && typeof label.urdu === "string" &&
      label.english.trim().length > 0 && [...label.english].length <= 60 &&
      label.urdu.trim().length > 0 && [...label.urdu].length <= 60,
    ));
  } catch { return {}; }
}

// Tab-scoped storage survives refresh. No database or localStorage is used.
export function usePersonalWords() {
  const saved = useSyncExternalStore(subscribe, snapshot, serverSnapshot);
  const labels = useMemo(() => parse(saved), [saved]);
  const [storageError, setStorageError] = useState("");
  function setLabels(next: Labels) {
    memoryFallback = Object.keys(next).length ? JSON.stringify(next) : "";
    try {
      if (memoryFallback) window.sessionStorage.setItem(KEY, memoryFallback);
      else window.sessionStorage.removeItem(KEY);
      storageUnavailable = false;
      setStorageError("");
    } catch {
      storageUnavailable = true;
      setStorageError("Browser storage is unavailable. These words may be lost on refresh.");
    }
    window.dispatchEvent(new Event(CHANGED));
  }
  return { labels, setLabels, storageError };
}
