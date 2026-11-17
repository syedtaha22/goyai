"use client";

import { ArrowLeftIcon, ArrowRightIcon } from "@/components/Icons";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import PersonalWordEditor from "@/components/PersonalWordEditor";
import CategoryTabs from "@/components/CategoryTabs";
import PictogramTile from "@/components/PictogramTile";
import TileLabels from "@/components/TileLabels";
import { categories } from "@/data/categories";
import { tiles } from "@/data/tiles";
import { relatedTiles } from "@/data/relatedTiles";
import type { Tile } from "@/types/aac";
import { usePersonalWords } from "@/services/personalWords";

// Shortest height of a tile row, so that the larger text fits without clipping.
const MIN_ROW_HEIGHT = 150;

function SelectedTile({ tile, onRemove }: { tile: Tile; onRemove: (id: string) => void }) {
  return (
    <div className="relative flex min-h-[88px] w-[210px] shrink-0 items-center gap-2 rounded-xl border-2 border-line bg-surface px-2 pr-9">
      <button type="button" onClick={() => onRemove(tile.id)} aria-label={`Remove ${tile.english}`}
        className="absolute right-1 top-1 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-accent text-base font-bold text-surface">
        ×
      </button>
      <div className="relative h-14 w-14 shrink-0">
        <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt={tile.english} fill sizes="56px" className="object-contain" />
      </div>
      <TileLabels tile={tile} compact />
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const { labels: personalLabels, setLabels: setPersonalLabels, storageError } = usePersonalWords();
  const [editingTile, setEditingTile] = useState<Tile | null>(null);
  const [personalNotice, setPersonalNotice] = useState("");
  const tileGrid = useRef<HTMLDivElement>(null);
  const [fittedRows, setFittedRows] = useState(3);
  const [activeCategory, setActiveCategory] = useState("person");
  const [selectedTiles, setSelectedTiles] = useState<Tile[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [layout, setLayout] = useState<"phone" | "portrait" | "landscape">("landscape");

  useEffect(() => {
    const phoneQuery = window.matchMedia("(max-width: 767px)");
    const portraitQuery = window.matchMedia("(min-width: 768px) and (max-width: 1535px) and (orientation: portrait)");
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
    function fitRows() {
      if (!window.matchMedia("(min-width: 768px)").matches) return;
      const style = window.getComputedStyle(grid!);
      const gap = parseFloat(style.rowGap) || 0;
      const usableHeight = grid!.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
      setFittedRows(Math.max(2, Math.min(3, Math.floor((usableHeight + gap) / (MIN_ROW_HEIGHT + gap)))));
    }
    const observer = new ResizeObserver(fitRows);
    observer.observe(grid);
    fitRows();
    return () => observer.disconnect();
  }, []);

  const columns = layout === "phone" ? 2 : layout === "portrait" ? 3 : 4;
  const rows = layout === "phone" ? 2 : fittedRows;
  const tilesPerPage = columns * rows;
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

  function selectTile(tile: Tile) {
    if (selectedTiles.length >= 6 || selectedTiles.some((selected) => selected.id === tile.id)) return;
    setSelectedTiles([...selectedTiles, tile]);
  }
  function savePersonalWord(label?: { english: string; urdu: string }) {
    if (!editingTile) return;
    const next = { ...personalLabels };
    if (label) next[editingTile.id] = label;
    else delete next[editingTile.id];
    setPersonalLabels(next);
    const base = tiles.find((tile) => tile.id === editingTile.id)!;
    setSelectedTiles(selectedTiles.map((tile) => tile.id === base.id
      ? (label ? { ...base, ...label, customLabel: true, originalLabel: { english: base.english, urdu: base.urdu } } : base) : tile));
    setPersonalNotice(label ? "Personal word updated for this tab." : "Original word restored.");
    setEditingTile(null);
  }
  function removeTile(id: string) {
    setSelectedTiles(selectedTiles.filter((tile) => tile.id !== id));
  }
  function goToReview() {
    if (selectedTiles.length === 0) return;
    sessionStorage.setItem("goyai-selected-tiles", JSON.stringify(selectedTiles));
    router.push("/review");
  }

  return (
    <main className="flex min-h-screen flex-col overflow-x-hidden bg-surface px-2 py-1 text-ink md:h-dvh md:min-h-0 md:overflow-hidden md:px-3">
      <header className="flex h-9 shrink-0 items-center px-2 md:px-6">
        <h1 className="text-xl font-bold tracking-wide">GOYAI</h1>
      </header>
      <div className="mx-auto flex w-full max-w-[1400px] flex-col md:min-h-0 md:w-[96%] md:flex-1">
        <section className="flex min-w-0 flex-col md:min-h-0 md:flex-1 md:overflow-hidden">
          <div className="shrink-0 border-b border-line-soft px-3 py-1">
            <CategoryTabs categories={categories} activeCategory={activeCategory}
              onCategoryChange={(id) => { setActiveCategory(id); setCurrentPage(1); }} />
          </div>
          <p role="status" className="sr-only">{personalNotice}</p>
          {storageError && <p role="alert" className="px-4 py-2 text-base text-danger">{storageError}</p>}
          <div className="flex min-h-0 flex-col bg-surface px-2 py-1 md:flex-1 md:px-4">
            <div className="flex min-h-11 shrink-0 items-center gap-3 pb-0.5">
              <h3 className="text-2xl font-bold">{selectedCategory?.name}</h3>
              <span className="text-xl font-semibold text-ink-soft" dir="rtl" lang="ur">{selectedCategory?.urduName}</span>
              {activeCategory === "personal" && (
                <button type="button" disabled={Object.keys(personalLabels).length === 0}
                  onClick={() => { setPersonalLabels({}); setSelectedTiles(selectedTiles.filter((tile) => tile.category !== "personal")); setPersonalNotice("Personal words reset for the next user."); }}
                  className="ml-auto h-9 rounded-lg border border-line bg-surface px-4 text-base font-semibold disabled:opacity-40">Reset personal words</button>
              )}
            </div>
            <div ref={tileGrid}
              style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`, gridTemplateRows: layout === "phone" ? undefined : `repeat(${rows}, minmax(0, 1fr))` }}
              className="grid gap-2 rounded-[14px] bg-accent-tint p-1.5 max-md:auto-rows-[170px] md:min-h-0 md:flex-1 md:gap-1.5">
              {visibleTiles.map((tile) => <PictogramTile key={tile.id} tile={tile} onSelect={selectTile}
                onEdit={tile.category === "personal" ? setEditingTile : undefined} />)}
            </div>
          </div>
          <div className="flex min-h-[56px] shrink-0 items-center justify-between gap-2 border-t border-line-soft bg-surface px-2 md:px-4">
            <button type="button" onClick={() => setCurrentPage(Math.max(safePage - 1, 1))}
              disabled={safePage === 1} {...{ autoComplete: "off" }} className="flex h-12 min-w-[110px] items-center justify-center gap-2 rounded-lg bg-accent px-3 text-base font-semibold text-surface disabled:opacity-40 md:min-w-[130px]"><ArrowLeftIcon /> Previous</button>
            <span className="text-xl font-semibold">{safePage} / {totalPages}</span>
            <button type="button" onClick={() => setCurrentPage(Math.min(safePage + 1, totalPages))}
              disabled={safePage === totalPages} {...{ autoComplete: "off" }} className="flex h-12 min-w-[110px] items-center justify-center gap-2 rounded-lg bg-accent px-3 text-base font-semibold text-surface disabled:opacity-40 md:min-w-[130px]">Next <ArrowRightIcon /></button>
          </div>
          {suggestedTiles.length > 0 && (
            <div className="shrink-0 border-t border-line-soft px-3 py-1">
              <p className="mb-1 text-base font-semibold text-ink-soft">More pictures</p>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {suggestedTiles.slice(0, 5).map((tile) => (
                  <button type="button" key={tile.id} onClick={() => selectTile(tile)}
                    className="min-h-12 shrink-0 rounded-lg border border-line bg-surface px-4 text-lg font-semibold">
                    {tile.originalLabel ? `${tile.originalLabel.english}: ${tile.english}` : tile.english} · {tile.originalLabel ? `${tile.originalLabel.urdu}: ${tile.urdu}` : tile.urdu}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="shrink-0 border-t border-line-soft bg-surface px-2 py-2 md:px-4">
            {selectedTiles.length === 6 && <p role="status" className="mb-1 text-base text-ink-soft">Six words selected. Press GO, or remove a word to choose another.</p>}
            <div className="flex items-center gap-2">
              <div className="hidden shrink-0 md:block">
                <p className="text-lg font-bold">Selected words ({selectedTiles.length}/6)</p>
                <p className="text-base text-ink-soft" lang="ur" dir="rtl">منتخب الفاظ</p>
              </div>
              <div className="flex min-w-0 w-full flex-1 items-center gap-2 overflow-x-auto py-1">
                {selectedTiles.length === 0 ? (
                  <div>
                    <p className="text-lg text-ink-soft">Tap a picture to start</p>
                    <p className="text-lg text-ink-soft" dir="rtl" lang="ur">شروع کرنے کے لیے تصویر دبائیں</p>
                  </div>
                ) : selectedTiles.map((tile) => <SelectedTile key={tile.id} tile={tile} onRemove={removeTile} />)}
              </div>
              {selectedTiles.length > 0 && (
                <button type="button" onClick={() => setSelectedTiles([])}
                  className="h-14 shrink-0 rounded-lg border border-line bg-surface px-4 text-lg font-semibold">Clear</button>
              )}
              <button type="button" {...{ autoComplete: "off" }} onClick={goToReview} disabled={selectedTiles.length === 0}
                className="flex h-16 w-auto min-w-[110px] shrink-0 items-center justify-center gap-2 rounded-xl bg-accent px-6 text-2xl font-bold text-surface disabled:cursor-not-allowed disabled:opacity-50 md:min-w-[130px]">GO <ArrowRightIcon /></button>
            </div>
          </div>
        </section>
      </div>
      {editingTile && <PersonalWordEditor key={editingTile.id} tile={editingTile}
        onSave={savePersonalWord} onReset={() => savePersonalWord()} onClose={() => setEditingTile(null)} />}
    </main>
  );
}
