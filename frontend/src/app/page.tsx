"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import SentencePanel from "@/components/SentencePanel";
import PersonalWordEditor from "@/components/PersonalWordEditor";
import CategoryTabs from "@/components/CategoryTabs";
import PictogramTile from "@/components/PictogramTile";
import TileLabels from "@/components/TileLabels";
import { categories } from "@/data/categories";
import { tiles } from "@/data/tiles";
import { relatedTiles } from "@/data/relatedTiles";
import type { Tile } from "@/types/aac";
import { usePersonalWords } from "@/services/personalWords";

function SelectedTile({ tile, onRemove }: { tile: Tile; onRemove: (id: string) => void }) {
  return (
    <div className="relative flex min-h-[70px] w-[165px] shrink-0 items-center gap-2 rounded-xl border-2 border-[#E7D2BE] bg-white px-2 pr-7">
      <button type="button" onClick={() => onRemove(tile.id)} aria-label={`Remove ${tile.english}`}
        className="absolute right-1 top-1 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-[#E76F51] text-xs font-bold text-white">
        ×
      </button>
      <div className="relative h-11 w-11 shrink-0">
        <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt={tile.english} fill sizes="44px" className="object-contain" />
      </div>
      <TileLabels tile={tile} compact />
    </div>
  );
}

export default function Home() {
  const { labels: personalLabels, setLabels: setPersonalLabels, storageError } = usePersonalWords();
  const [editingTile, setEditingTile] = useState<Tile | null>(null);
  const [personalNotice, setPersonalNotice] = useState("");
  const [reviewTiles, setReviewTiles] = useState<Tile[] | null>(null);
  const [generation, setGeneration] = useState(0);
  const reviewHeading = useRef<HTMLHeadingElement>(null);
  const boardHeading = useRef<HTMLHeadingElement>(null);
  const tileGrid = useRef<HTMLDivElement>(null);
  const [fittedTileCount, setFittedTileCount] = useState(4);
  const [activeCategory, setActiveCategory] = useState("person");
  const [selectedTiles, setSelectedTiles] = useState<Tile[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [layout, setLayout] = useState<"phone" | "portrait" | "landscape">("landscape");

  useEffect(() => {
    const phoneQuery = window.matchMedia("(max-width: 767px)");
    const portraitQuery = window.matchMedia("(min-width: 768px) and (max-width: 1023px)");
    function updateLayout() {
      setLayout(phoneQuery.matches ? "phone" : portraitQuery.matches ? "portrait" : "landscape");
      setCurrentPage(1);
    }
    updateLayout();
    phoneQuery.addEventListener("change", updateLayout);
    portraitQuery.addEventListener("change", updateLayout);
    return () => {
      phoneQuery.removeEventListener("change", updateLayout);
      portraitQuery.removeEventListener("change", updateLayout);
    };
  }, []);

  useEffect(() => {
    const grid = tileGrid.current;
    if (!grid) return;
    function fitTiles() {
      if (!window.matchMedia("(min-width: 1024px)").matches) return;
      const style = window.getComputedStyle(grid!);
      const columns = style.gridTemplateColumns.split(" ").length;
      const gap = parseFloat(style.rowGap) || 0;
      const usableHeight = grid!.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
      // Leave room for wrapped Urdu/English labels and Personal's edit control.
      const rowHeight = activeCategory === "personal" ? 240 : 170;
      const rows = Math.max(1, Math.min(3, Math.floor((usableHeight + gap) / (rowHeight + gap))));
      setFittedTileCount(columns * rows);
    }
    const observer = new ResizeObserver(fitTiles);
    observer.observe(grid);
    window.addEventListener("resize", fitTiles);
    fitTiles();
    return () => { observer.disconnect(); window.removeEventListener("resize", fitTiles); };
  }, [activeCategory]);

  const tilesPerPage = layout === "phone" ? 4
    : layout === "portrait" ? (activeCategory === "personal" ? 3 : 6)
    : fittedTileCount;
  const selectedCategory = categories.find((category) => category.id === activeCategory);
  const displayTiles = tiles.map((tile) => personalLabels[tile.id]
    ? { ...tile, ...personalLabels[tile.id], customLabel: true, originalLabel: { english: tile.english, urdu: tile.urdu } } : tile);
  const categoryTiles = displayTiles.filter((tile) => tile.category === activeCategory);
  const totalPages = Math.max(1, Math.ceil(categoryTiles.length / tilesPerPage));
  const safePage = Math.min(currentPage, totalPages);
  const visibleTiles = categoryTiles.slice((safePage - 1) * tilesPerPage, safePage * tilesPerPage);
  const lastSelected = selectedTiles[selectedTiles.length - 1];
  const relatedIds = lastSelected ? relatedTiles[lastSelected.id] ?? [] : [];
  const suggestedTiles = relatedIds
    .map((id) => displayTiles.find((tile) => tile.id === id))
    .filter((tile): tile is Tile => tile !== undefined)
    .filter((tile) => !selectedTiles.some((selected) => selected.id === tile.id));

  function updateSelection(next: Tile[]) {
    window.speechSynthesis?.cancel();
    setSelectedTiles(next);
    setReviewTiles(null);
  }
  function selectTile(tile: Tile) {
    if (selectedTiles.length >= 6 || selectedTiles.some((selected) => selected.id === tile.id)) return;
    updateSelection([...selectedTiles, tile]);
  }
  function savePersonalWord(label?: { english: string; urdu: string }) {
    if (!editingTile) return;
    const next = { ...personalLabels };
    if (label) next[editingTile.id] = label;
    else delete next[editingTile.id];
    setPersonalLabels(next);
    const base = tiles.find((tile) => tile.id === editingTile.id)!;
    updateSelection(selectedTiles.map((tile) => tile.id === base.id
      ? (label ? { ...base, ...label, customLabel: true, originalLabel: { english: base.english, urdu: base.urdu } } : base) : tile));
    setPersonalNotice(label ? "Personal word updated for this tab." : "Original word restored.");
    setEditingTile(null);
  }
  function removeTile(id: string) {
    updateSelection(selectedTiles.filter((tile) => tile.id !== id));
  }
  function generateSentences() {
    if (selectedTiles.length === 0) return;
    window.speechSynthesis?.cancel();
    setReviewTiles([...selectedTiles]);
    setGeneration((value) => value + 1);
    reviewHeading.current?.focus();
    reviewHeading.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#FFFDF9] px-2 py-1 text-[#3F241C] lg:h-dvh lg:min-h-0 lg:overflow-hidden md:px-3">
      <div className="mx-auto flex w-full max-w-[1800px] flex-col lg:h-full md:w-[98%]">
        <header className="flex h-7 shrink-0 items-center justify-center gap-3">
          <h1 className="text-base font-bold tracking-wide">GOYAI</h1>
          <span className="text-xs text-[#8A6557]">Communication Board</span>
        </header>
        <div className="grid min-h-0 gap-3 lg:flex-1 lg:grid-cols-[minmax(0,1.8fr)_minmax(330px,1fr)]">
        <section className="flex min-w-0 flex-col rounded-[18px] border-2 border-[#E7D2BE] bg-[#FFFCF8] shadow-sm min-h-[650px] lg:min-h-0 lg:overflow-hidden">
          <div className="flex h-[50px] shrink-0 items-center justify-between border-b border-[#EEDFD1] px-4">
            <div className="flex items-center gap-2">
              <span className="text-lg text-[#E76F51]">⌂</span>
              <div>
                <h2 ref={boardHeading} tabIndex={-1} className="text-lg font-bold leading-tight">My Talker</h2>
                <p className="text-sm font-semibold leading-tight text-[#9B7A6D]" dir="rtl" lang="ur">میری آواز</p>
              </div>
            </div>
          </div>
          <div className="shrink-0 border-b border-[#EEDFD1] px-3 py-1 [&_button]:h-auto [&_button]:min-h-[52px]">
            <CategoryTabs categories={categories} activeCategory={activeCategory}
              onCategoryChange={(id) => { setActiveCategory(id); setCurrentPage(1); }} />
          </div>
          {activeCategory === "personal" && <div className="shrink-0 border-b border-[#EEDFD1] px-4 py-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-[#8A6557]">Use Edit word on a tile to enter your own name or word. Words stay after refresh. Use Reset for the next user.</p>
              <button type="button" disabled={Object.keys(personalLabels).length === 0}
                onClick={() => { setPersonalLabels({}); updateSelection(selectedTiles.filter((tile) => tile.category !== "personal")); setPersonalNotice("Personal words reset for the next user."); }}
                className="min-h-11 rounded-lg border border-[#E7D2BE] bg-white px-3 text-sm font-semibold disabled:opacity-40">Reset personal words</button>
            </div>
          </div>}
          <p role="status" className="sr-only">{personalNotice}</p>
          {storageError && <p role="alert" className="px-4 py-2 text-sm text-red-700">{storageError}</p>}
          <div className="flex min-h-0 flex-col bg-[#FFF9F5] px-2 py-1 md:flex-1 md:px-4">
            <div className="flex h-8 shrink-0 items-center gap-3">
              <h3 className="text-lg font-bold">{selectedCategory?.name}</h3>
              <span className="text-base font-semibold text-[#8A6557]" dir="rtl" lang="ur">{selectedCategory?.urduName}</span>
            </div>
            <div ref={tileGrid} className="grid grid-cols-2 auto-rows-max content-start items-stretch gap-2 rounded-[14px] bg-[#FFF0EB] p-1.5 md:min-h-0 md:flex-1 md:grid-cols-3 md:gap-1.5 xl:grid-cols-4">
              {visibleTiles.map((tile) => <PictogramTile key={tile.id} tile={tile} onSelect={selectTile}
                onEdit={tile.category === "personal" ? setEditingTile : undefined} />)}
            </div>
          </div>
          <div className="flex h-[44px] shrink-0 items-center justify-between gap-2 border-t border-[#EEDFD1] bg-[#FFFCF8] px-2 md:px-4">
            <button type="button" onClick={() => setCurrentPage(Math.max(safePage - 1, 1))}
              disabled={safePage === 1} className="h-9 min-w-[85px] rounded-lg bg-[#E76F51] px-2 text-xs font-semibold text-white disabled:opacity-40 md:min-w-[100px]">← Previous</button>
            <span className="text-sm font-semibold">{safePage} / {totalPages}</span>
            <button type="button" onClick={() => setCurrentPage(Math.min(safePage + 1, totalPages))}
              disabled={safePage === totalPages} className="h-9 min-w-[85px] rounded-lg bg-[#E76F51] px-2 text-xs font-semibold text-white disabled:opacity-40 md:min-w-[100px]">Next →</button>
          </div>
          {suggestedTiles.length > 0 && (
            <div className="shrink-0 border-t border-[#EEDFD1] px-3 py-1">
              <p className="mb-1 text-xs font-semibold text-[#8A6557]">Related pictograms</p>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {suggestedTiles.slice(0, 5).map((tile) => (
                  <button type="button" key={tile.id} onClick={() => selectTile(tile)}
                    className="min-h-10 shrink-0 rounded-lg border border-[#E7D2BE] bg-white px-3 text-sm font-semibold">
                    {tile.originalLabel ? `${tile.originalLabel.english}: ${tile.english}` : tile.english} · {tile.originalLabel ? `${tile.originalLabel.urdu}: ${tile.urdu}` : tile.urdu}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="shrink-0 border-t border-[#EEDFD1] bg-[#FFFCF8] px-2 py-2 md:px-4">
            {selectedTiles.length === 6 && <p role="status" className="mb-1 text-sm text-[#8A6557]">Six words selected. Press GO, or remove a word to choose another.</p>}
            <div className="flex items-center gap-2">
              <div className="hidden shrink-0 md:block">
                <p className="text-sm font-bold">Selected words ({selectedTiles.length}/6)</p>
                <p className="text-xs text-[#8A6557]" lang="ur" dir="rtl">منتخب الفاظ</p>
              </div>
              <div className="flex min-w-0 w-full flex-1 items-center gap-2 overflow-x-auto py-1">
                {selectedTiles.length === 0 ? (
                  <div>
                    <p className="text-sm text-[#9B7A6D]">Select a pictogram to begin</p>
                    <p className="text-sm text-[#9B7A6D]" dir="rtl" lang="ur">شروع کرنے کے لیے تصویر منتخب کریں</p>
                  </div>
                ) : selectedTiles.map((tile) => <SelectedTile key={tile.id} tile={tile} onRemove={removeTile} />)}
              </div>
              {selectedTiles.length > 0 && (
                <button type="button" onClick={() => updateSelection([])}
                  className="h-11 shrink-0 rounded-lg border border-[#E7D2BE] bg-white px-3 text-sm font-semibold">Clear</button>
              )}
              <button type="button" onClick={generateSentences} disabled={selectedTiles.length === 0}
                className="h-12 w-auto min-w-[90px] shrink-0 rounded-xl bg-[#E76F51] px-5 text-lg font-bold text-white disabled:cursor-not-allowed disabled:opacity-50 md:min-w-[105px]">GO →</button>
            </div>
          </div>
        </section>
        <aside className="min-w-0 rounded-[18px] border-2 border-[#E7D2BE] bg-[#FFFCF8] p-4 shadow-sm lg:min-h-0 lg:overflow-y-auto" aria-labelledby="sentence-heading">
          <h2 id="sentence-heading" ref={reviewHeading} tabIndex={-1} className="text-xl font-bold">Choose a sentence</h2>
          <p className="mb-4 text-sm text-[#8A6557]" lang="ur" dir="rtl">اپنا جملہ منتخب کریں</p>
          {reviewTiles ? (
            <SentencePanel key={generation} selected={reviewTiles}
              onChangeWords={() => { boardHeading.current?.focus(); boardHeading.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }}
              onNewMessage={() => { updateSelection([]); boardHeading.current?.focus(); boardHeading.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }} />
          ) : (
            <div className="rounded-xl border-2 border-dashed border-[#E7D2BE] bg-white px-5 py-12 text-center">
              <p className="text-lg font-bold">Your sentences will appear here</p>
              <p className="mt-3 text-sm text-[#8A6557]">Choose up to six pictograms, then press GO.</p>
              <p className="mt-3 text-sm text-[#8A6557]">Nothing is spoken until you confirm your sentence and press Speak.</p>
            </div>
          )}
        </aside>
        </div>
      </div>
      {editingTile && <PersonalWordEditor key={editingTile.id} tile={editingTile}
        onSave={savePersonalWord} onReset={() => savePersonalWord()} onClose={() => setEditingTile(null)} />}
    </main>
  );
}
