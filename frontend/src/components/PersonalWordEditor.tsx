"use client";

import { useEffect, useRef, useState } from "react";
import type { Tile } from "@/types/aac";

export default function PersonalWordEditor({ tile, onSave, onReset, onClose }: {
  tile: Tile;
  onSave: (label: { english: string; urdu: string }) => void;
  onReset: () => void;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [english, setEnglish] = useState(tile.customLabel ? tile.english : "");
  const [urdu, setUrdu] = useState(tile.customLabel ? tile.urdu : "");
  const [error, setError] = useState("");
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  const input = "mt-2 w-full rounded-xl border-2 border-[#E7D2BE] bg-white p-3 text-lg focus-visible:outline-2 focus-visible:outline-[#E76F51]";
  const button = "min-h-12 rounded-xl border-2 border-[#E7D2BE] px-4 py-2 font-bold focus-visible:outline-2 focus-visible:outline-[#E76F51]";
  return (
    <dialog ref={dialog} onCancel={onClose} aria-labelledby="personal-word-heading"
      className="fixed inset-0 m-auto max-h-[90dvh] w-[min(92vw,480px)] overflow-y-auto rounded-2xl border-2 border-[#E7D2BE] bg-[#FFFDF9] p-5 text-[#3F241C] shadow-xl backdrop:bg-black/30">
      <form onSubmit={(event) => {
        event.preventDefault();
        const en = english.trim();
        const ur = urdu.trim();
        if (!en && !ur) { setError("Enter at least one word or name."); return; }
        const invalid = /[\p{Cc}\p{Cf}]/u;
        if ([en, ur].some((value) => invalid.test(value.replaceAll("\u200c", "")))) {
          setError("Please remove hidden formatting characters from the label."); return;
        }
        if ([en, ur].some((value) => [...value].length > 60)) { setError("Use 60 characters or fewer in each label."); return; }
        onSave({ english: en || ur, urdu: ur || en });
      }}>
        <h2 id="personal-word-heading" className="text-xl font-bold">Edit personal word</h2>
        <p className="mt-2 text-sm text-[#8A6557]">{tile.originalLabel?.english ?? tile.english} · <span lang="ur" dir="rtl">{tile.originalLabel?.urdu ?? tile.urdu}</span></p>
        <p className="mt-3 text-sm">Enter your own word or name. If you leave one language blank, the same text is used in both.</p>
        <label className="mt-4 block font-semibold">English label
          <input autoFocus autoComplete="off" maxLength={60} value={english} onChange={(event) => setEnglish(event.target.value)} className={input} />
        </label>
        <label className="mt-4 block font-semibold">Urdu label
          <input autoComplete="off" maxLength={60} lang="ur" dir="rtl" value={urdu} onChange={(event) => setUrdu(event.target.value)} className={input} />
        </label>
        <p className="mt-3 text-sm text-[#8A6557]">Words stay after refresh in this tab. Use Restore original word to remove this label, or Reset personal words before the next person uses the board.</p>
        {error && <p role="alert" className="mt-3 font-semibold text-red-700">{error}</p>}
        <div className="mt-5 flex flex-wrap gap-2">
          <button className={`${button} border-[#E76F51] bg-[#E76F51] text-white`} type="submit">Use this word</button>
          <button className={button} type="button" onClick={onClose}>Cancel</button>
          {tile.customLabel && <button className={button} type="button" onClick={onReset}>Restore original word</button>}
        </div>
      </form>
    </dialog>
  );
}
