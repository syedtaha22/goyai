"use client";

import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { fetchSuggestions } from "@/services/backend";
import type { Tile } from "@/types/aac";

type Suggestion = { urdu: string; english: string };
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
    setDraftEnglish(suggestions[choice].english);
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

  function speak() {
    const sentence = finalSentence;
    if (!sentence) return;
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setSpeechMessage("Speech is not supported in this browser.");
      return;
    }
    const text = speechLanguage === "ur-PK" ? sentence.urdu : sentence.english;
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

  const btn = "min-h-12 rounded-xl px-5 py-3 text-base font-bold focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-[#3F241C]";
  if (!loaded) return <main className="p-8 text-[#3F241C]">Loading review…</main>;

  return (
    <main className="min-h-dvh bg-[#FFFDF9] px-3 py-5 text-[#3F241C] sm:px-6">
      <div className="mx-auto max-w-5xl space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold">GOYAI</h1>
            <p className="text-[#8A6557]">Review your message · اپنا پیغام دیکھیں</p>
          </div>
          <button type="button" onClick={() => { window.speechSynthesis?.cancel(); router.push("/"); }}
            className={`${btn} border-2 border-[#E7D2BE] bg-white`}>← Back to board</button>
        </header>

        {selected.length === 0 ? (
          <section className="rounded-2xl border-2 border-[#E7D2BE] bg-white p-6 text-center">
            <h2 className="text-xl font-bold">No pictograms selected</h2>
            <p className="my-3">Go back and choose some pictures first.</p>
            <button type="button" onClick={() => router.push("/")} className={`${btn} bg-[#E76F51] text-white`}>Choose pictograms</button>
          </section>
        ) : (
          <>
            <section className="rounded-2xl border-2 border-[#E7D2BE] bg-white p-4">
              <h2 className="mb-3 text-lg font-bold">Your selected pictograms</h2>
              <div className="flex flex-wrap gap-3">
                {selected.map((tile, i) => (
                  <div key={`${tile.id}-${i}`} className="flex min-w-[110px] items-center gap-2 rounded-xl bg-[#FFF0EB] p-2">
                    <div className="relative h-12 w-12 shrink-0">
                      <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt={tile.english} fill sizes="48px" className="object-contain" />
                    </div>
                    <div><p className="font-bold">{tile.english}</p><p lang="ur" dir="rtl">{tile.urdu}</p></div>
                  </div>
                ))}
              </div>
            </section>

            {stage === "suggestions" && (
              <section className="space-y-4 rounded-2xl border-2 border-[#E7D2BE] bg-[#FFFCF8] p-4">
                <div>
                  <h2 className="text-xl font-bold">Choose a suggestion</h2>
                  <p role="status" className="text-sm text-[#8A6557]">
                    {status === "loading" && "Writing suggestions…"}
                    {status === "error" && errorMessage}
                    {status === "ready" && origin?.source === "llm" && `Written by ${origin.model} in ${origin.latencyMs} ms`}
                    {status === "ready" && origin?.source === "fallback" && "The language model is not available. These are example sentences for the selected pictograms."}
                  </p>
                </div>
                <div className="grid gap-3">
                  {status === "ready" && suggestions.length === 0 && (
                    <p className="rounded-xl border-2 border-[#E7D2BE] bg-white p-4">No suggestions were returned for these pictograms.</p>
                  )}
                  {status === "ready" && suggestions.map((item, i) => (
                    <button key={item.urdu} type="button" onClick={() => selectSuggestion(i)}
                      aria-pressed={choice === i}
                      className={`min-h-24 rounded-xl border-2 p-4 text-left focus-visible:outline-4 focus-visible:outline-[#3F241C] ${choice === i ? "border-[#E76F51] bg-[#FFF0EB]" : "border-[#E7D2BE] bg-white"}`}>
                      <span className="text-xs font-bold text-[#8A6557]">Option {i + 1}{choice === i ? " ✓ Selected" : ""}</span>
                      <p dir="rtl" lang="ur" className="mt-1 text-right text-xl font-bold leading-relaxed">{item.urdu}</p>
                      {item.english && <p className="mt-1 text-base">{item.english}</p>}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={confirmSuggestion} disabled={choice === null || status !== "ready"}
                    className={`${btn} bg-[#E76F51] text-white disabled:opacity-40`}>Confirm ✓</button>
                  <button type="button" onClick={editSuggestion} disabled={choice === null}
                    className={`${btn} border-2 border-[#E7D2BE] bg-white disabled:opacity-40`}>Correct / Edit ✎</button>
                  <button type="button" onClick={tryDifferent} disabled={status === "loading"}
                    className={`${btn} border-2 border-[#E7D2BE] bg-white disabled:opacity-40`}>Try Different ↻</button>
                  {status === "error" && (
                    <button type="button" onClick={() => reloadSuggestions("default")}
                      className={`${btn} border-2 border-[#E7D2BE] bg-white`}>Try again</button>
                  )}
                  <button type="button" onClick={writeOwn}
                    className={`${btn} border-2 border-[#E7D2BE] bg-white`}>Write my own</button>
                  <button type="button" onClick={() => router.push("/")}
                    className={`${btn} border-2 border-[#E7D2BE] bg-white`}>Change pictograms</button>
                </div>
              </section>
            )}

            {stage === "edit" && (
              <section className="space-y-4 rounded-2xl border-2 border-[#E7D2BE] bg-white p-4">
                <h2 className="text-xl font-bold">Correct your sentence</h2>
                <p className="text-sm text-[#8A6557]">A caregiver may assist with typing.</p>
                <label className="block font-semibold">Urdu
                  <textarea dir="rtl" lang="ur" value={draftUrdu} onChange={(e) => setDraftUrdu(e.target.value)}
                    rows={3} className="mt-2 w-full rounded-xl border-2 border-[#E7D2BE] p-3 text-xl" />
                </label>
                <label className="block font-semibold">English
                  <textarea value={draftEnglish} onChange={(e) => setDraftEnglish(e.target.value)}
                    rows={3} className="mt-2 w-full rounded-xl border-2 border-[#E7D2BE] p-3 text-lg" />
                </label>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={saveCorrection} disabled={!draftEnglish.trim() && !draftUrdu.trim()}
                    className={`${btn} bg-[#E76F51] text-white disabled:opacity-40`}>Save and Confirm ✓</button>
                  <button type="button" onClick={() => setStage("suggestions")} className={`${btn} border-2 border-[#E7D2BE]`}>Cancel</button>
                </div>
              </section>
            )}

            {stage === "confirmed" && finalSentence && (
              <section className="space-y-4 rounded-2xl border-2 border-[#E7D2BE] bg-white p-5 text-center">
                <h2 className="text-xl font-bold">Your confirmed message ✓</h2>
                <p dir="rtl" lang="ur" className="text-2xl font-bold leading-relaxed">{finalSentence.urdu}</p>
                <p className="text-lg">{finalSentence.english}</p>
                <fieldset className="flex justify-center gap-4">
                  <legend className="mb-2 w-full font-semibold">Speech language</legend>
                  <label className="flex items-center gap-2"><input type="radio" name="speech-lang" checked={speechLanguage === "ur-PK"} onChange={() => setSpeechLanguage("ur-PK")} /> Urdu</label>
                  <label className="flex items-center gap-2"><input type="radio" name="speech-lang" checked={speechLanguage === "en-US"} onChange={() => setSpeechLanguage("en-US")} /> English</label>
                </fieldset>
                <div className="flex flex-wrap justify-center gap-3">
                  <button type="button" onClick={speak} className={`${btn} bg-[#E76F51] text-white`}>🔊 Speak</button>
                  <button type="button" onClick={() => window.speechSynthesis?.cancel()} className={`${btn} border-2 border-[#E7D2BE]`}>Stop speech</button>
                  <button type="button" onClick={() => { setStage("suggestions"); setChoice(null); setFinalSentence(null); }} className={`${btn} border-2 border-[#E7D2BE]`}>Review again</button>
                  <button type="button" onClick={() => router.push("/")} className={`${btn} border-2 border-[#E7D2BE]`}>New message</button>
                </div>
                {speechMessage && <p role="status" className="text-sm text-[#8A6557]">{speechMessage}</p>}
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}
