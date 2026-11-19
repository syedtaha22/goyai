"use client";

import { ArrowLeftIcon, SpeakerIcon } from "@/components/Icons";
import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { fetchSuggestions } from "@/services/backend";
import type { Tile } from "@/types/aac";

type Suggestion = { urdu: string; english?: string | null };
type Stage = "suggestions" | "edit" | "confirmed";
type Status = "loading" | "ready" | "error";
type Origin = { source: "llm" | "fallback"; model: string | null; latencyMs: number };

const KEY = "goyai-selected-tiles";

function subscribe() {
  return () => {};
}

function readSelection(): string | null {
  return sessionStorage.getItem(KEY) ?? "";
}

function readSelectionOnServer(): string | null {
  return null;
}

function parseTiles(saved: string): Tile[] {
  try {
    const parsed: unknown = saved ? JSON.parse(saved) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((x): x is Tile =>
      !!x && typeof x === "object" &&
      typeof x.id === "string" &&
      typeof x.english === "string" &&
      typeof x.urdu === "string" &&
      typeof x.category === "string"
    );
  } catch {
    return [];
  }
}

export default function ReviewPage() {
  const router = useRouter();
  const saved = useSyncExternalStore(subscribe, readSelection, readSelectionOnServer);
  const loaded = saved !== null;
  const selected = useMemo(() => parseTiles(saved ?? ""), [saved]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [origin, setOrigin] = useState<Origin | null>(null);
  const shown = useRef<string[]>([]);
  const request = useRef<AbortController | null>(null);
  const [choice, setChoice] = useState<number | null>(null);
  const [stage, setStage] = useState<Stage>("suggestions");
  const [draftEnglish, setDraftEnglish] = useState("");
  const [draftUrdu, setDraftUrdu] = useState("");
  const [finalSentence, setFinalSentence] = useState<Suggestion | null>(null);
  const [speechLanguage, setSpeechLanguage] = useState<"ur-PK" | "en-US">("ur-PK");
  const [speechMessage, setSpeechMessage] = useState("");

  const requestSuggestions = useCallback(
    (mode: "default" | "different", controller: AbortController) => {
      fetchSuggestions(selected, { mode, exclude: shown.current, signal: controller.signal })
        .then((result) => {
          shown.current.push(...result.suggestions.map((item) => item.urdu));
          setSuggestions(result.suggestions);
          setOrigin({ source: result.source, model: result.model, latencyMs: result.latencyMs });
          setStatus("ready");
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setErrorMessage(error instanceof Error ? error.message : "Suggestions could not be loaded.");
          setStatus("error");
        });
    },
    [selected],
  );

  useEffect(() => {
    if (!loaded || selected.length === 0) return;
    const controller = new AbortController();
    request.current = controller;
    requestSuggestions("default", controller);
    return () => controller.abort();
  }, [loaded, selected, requestSuggestions]);

  function reloadSuggestions(mode: "default" | "different") {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setStatus("loading");
    setChoice(null);
    requestSuggestions(mode, controller);
  }

  function selectSuggestion(index: number) {
    setChoice(index);
    setSpeechMessage("");
  }

  function editSuggestion() {
    if (choice === null) return;
    setDraftEnglish(suggestions[choice].english ?? "");
    setDraftUrdu(suggestions[choice].urdu);
    setStage("edit");
  }

  function confirmSuggestion() {
    if (choice === null) return;
    setFinalSentence(suggestions[choice]);
    setStage("confirmed");
  }

  function saveCorrection() {
    if (!draftEnglish.trim() && !draftUrdu.trim()) return;
    setFinalSentence({ english: draftEnglish.trim(), urdu: draftUrdu.trim() });
    setStage("confirmed");
  }

  function tryDifferent() {
    setStage("suggestions");
    reloadSuggestions("different");
  }

  function writeOwn() {
    setDraftEnglish("");
    setDraftUrdu("");
    setStage("edit");
  }

  const finalEnglish = finalSentence?.english
    ?? suggestions.find((item) => item.urdu === finalSentence?.urdu)?.english ?? null;

  function speak() {
    const sentence = finalSentence;
    if (!sentence) return;
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setSpeechMessage("Speech is not supported in this browser.");
      return;
    }
    const text = speechLanguage === "ur-PK" ? sentence.urdu : (finalEnglish ?? "");
    if (!text) {
      setSpeechMessage("No text available in this language.");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechLanguage;
    utterance.rate = 0.85;
    const voices = window.speechSynthesis.getVoices();
    const matchingVoice = voices.find((v) => v.lang.toLowerCase().startsWith(speechLanguage.slice(0, 2)));
    if (matchingVoice) utterance.voice = matchingVoice;
    if (!matchingVoice && speechLanguage === "ur-PK") {
      setSpeechMessage("No Urdu voice detected. Pronunciation may be incorrect.");
    } else {
      setSpeechMessage("");
    }
    utterance.onerror = () => setSpeechMessage("Speech could not play. Try English or check installed voices.");
    window.speechSynthesis.speak(utterance);
  }

  const btn = "min-h-14 rounded-xl px-6 py-3 text-xl font-bold focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-ink";
  if (!loaded) return <main className="p-8 text-ink">Loading review…</main>;

  return (
    <main className="min-h-dvh bg-surface px-3 py-5 text-ink sm:px-6">
      <div className="mx-auto max-w-5xl space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-extrabold">GOYAI</h1>
            <p className="text-lg text-ink-soft">Your message · آپ کا پیغام</p>
          </div>
          <button type="button" onClick={() => { window.speechSynthesis?.cancel(); router.push("/"); }}
            className={`${btn} flex items-center gap-2 border-2 border-line bg-surface`}><ArrowLeftIcon /> Back to pictures</button>
        </header>

        {selected.length === 0 ? (
          <section className="rounded-2xl border-2 border-line bg-surface p-6 text-center">
            <h2 className="text-2xl font-bold">No pictures chosen</h2>
            <p className="my-3 text-xl">Go back and choose pictures first.</p>
            <button type="button" onClick={() => router.push("/")} className={`${btn} bg-accent text-surface`}>Choose pictures</button>
          </section>
        ) : (
          <>
            <section className="rounded-2xl border-2 border-line bg-surface p-4">
              <h2 className="mb-3 text-xl font-bold">Your pictures</h2>
              <div className="flex flex-wrap gap-3">
                {selected.map((tile, i) => (
                  <div key={`${tile.id}-${i}`} className="flex min-w-[140px] items-center gap-3 rounded-xl bg-accent-tint p-3">
                    <div className="relative h-16 w-16 shrink-0">
                      <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt={tile.english} fill sizes="64px" className="object-contain" />
                    </div>
                    <div><p className="text-xl font-bold">{tile.english}</p><p className="text-2xl" lang="ur" dir="rtl">{tile.urdu}</p></div>
                  </div>
                ))}
              </div>
            </section>

            {stage === "suggestions" && (
              <section className="space-y-4 rounded-2xl border-2 border-line bg-surface p-4">
                <div>
                  <h2 className="text-2xl font-bold">Pick a sentence</h2>
                  <p role="status" className="text-base text-ink-soft">
                    {status === "loading" && "Writing sentences…"}
                    {status === "error" && errorMessage}
                    {status === "ready" && origin?.source === "llm" && `Written by ${origin.model} in ${origin.latencyMs} ms`}
                    {status === "ready" && origin?.source === "fallback" && "The language model is not available. These are example sentences for your pictures."}
                  </p>
                </div>
                <div className="grid gap-3">
                  {status === "ready" && suggestions.length === 0 && (
                    <p className="rounded-xl border-2 border-line bg-surface p-4 text-xl">No sentences were found for these pictures.</p>
                  )}
                  {status === "ready" && suggestions.map((item, i) => (
                    <button key={item.urdu} type="button" onClick={() => selectSuggestion(i)}
                      aria-pressed={choice === i}
                      className={`min-h-28 rounded-xl border-2 p-5 text-left focus-visible:outline-4 focus-visible:outline-ink ${choice === i ? "border-accent bg-accent-tint" : "border-line bg-surface"}`}>
                      <span className="text-base font-bold text-ink-soft">Sentence {i + 1}{choice === i ? " (chosen)" : ""}</span>
                      <p dir="rtl" lang="ur" className="mt-1 text-right text-3xl font-bold leading-relaxed">{item.urdu}</p>
                      <p className={`mt-2 text-2xl ${item.english ? "" : "text-ink-soft"}`}>{item.english ?? "English translation appears here"}</p>
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={confirmSuggestion} disabled={choice === null || status !== "ready"}
                    className={`${btn} bg-accent text-surface disabled:opacity-40`}>Use this</button>
                  <button type="button" onClick={editSuggestion} disabled={choice === null}
                    className={`${btn} border-2 border-line bg-surface disabled:opacity-40`}>Change words ✎</button>
                  <button type="button" onClick={tryDifferent} disabled={status === "loading"}
                    className={`${btn} border-2 border-line bg-surface disabled:opacity-40`}>Show other sentences</button>
                  {status === "error" && (
                    <button type="button" onClick={() => reloadSuggestions("default")}
                      className={`${btn} border-2 border-line bg-surface`}>Try again</button>
                  )}
                  <button type="button" onClick={writeOwn}
                    className={`${btn} border-2 border-line bg-surface`}>Type my own</button>
                  <button type="button" onClick={() => router.push("/")}
                    className={`${btn} border-2 border-line bg-surface`}>Change pictures</button>
                </div>
              </section>
            )}

            {stage === "edit" && (
              <section className="space-y-4 rounded-2xl border-2 border-line bg-surface p-4">
                <h2 className="text-2xl font-bold">Change your sentence</h2>
                <p className="text-base text-ink-soft">A helper can type for you.</p>
                <label className="block text-lg font-semibold">Urdu
                  <textarea dir="rtl" lang="ur" value={draftUrdu} onChange={(e) => setDraftUrdu(e.target.value)}
                    rows={3} className="mt-2 w-full rounded-xl border-2 border-line p-3 text-3xl" />
                </label>
                <label className="block text-lg font-semibold">English
                  <textarea value={draftEnglish} onChange={(e) => setDraftEnglish(e.target.value)}
                    rows={3} className="mt-2 w-full rounded-xl border-2 border-line p-3 text-2xl" />
                </label>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={saveCorrection} disabled={!draftEnglish.trim() && !draftUrdu.trim()}
                    className={`${btn} bg-accent text-surface disabled:opacity-40`}>Save</button>
                  <button type="button" onClick={() => setStage("suggestions")} className={`${btn} border-2 border-line`}>Cancel</button>
                </div>
              </section>
            )}

            {stage === "confirmed" && finalSentence && (
              <section className="space-y-4 rounded-2xl border-2 border-line bg-surface p-5 text-center">
                <h2 className="text-2xl font-bold">Your sentence</h2>
                <p dir="rtl" lang="ur" className="text-4xl font-bold leading-relaxed">{finalSentence.urdu}</p>
                {finalEnglish && <p className="text-3xl">{finalEnglish}</p>}
                <fieldset className="flex justify-center gap-4">
                  <legend className="mb-2 w-full text-xl font-semibold">Speak in</legend>
                  <label className="flex items-center gap-2 text-xl"><input className="h-6 w-6" type="radio" name="speech-lang" checked={speechLanguage === "ur-PK"} onChange={() => setSpeechLanguage("ur-PK")} /> Urdu</label>
                  <label className="flex items-center gap-2 text-xl"><input className="h-6 w-6" type="radio" name="speech-lang" checked={speechLanguage === "en-US"} disabled={!finalEnglish} onChange={() => setSpeechLanguage("en-US")} /> English</label>
                </fieldset>
                <div className="flex flex-wrap justify-center gap-3">
                  <button type="button" onClick={speak} className={`${btn} flex items-center gap-2 bg-accent text-surface`}><SpeakerIcon /> Speak</button>
                  <button type="button" onClick={() => window.speechSynthesis?.cancel()} className={`${btn} border-2 border-line`}>Stop</button>
                  <button type="button" onClick={() => { setStage("suggestions"); setChoice(null); setFinalSentence(null); }} className={`${btn} border-2 border-line`}>Pick again</button>
                  <button type="button" onClick={() => router.push("/")} className={`${btn} border-2 border-line`}>New message</button>
                </div>
                {speechMessage && <p role="status" className="text-base text-ink-soft">{speechMessage}</p>}
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}
