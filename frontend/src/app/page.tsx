"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import CategoryTabs from "@/components/CategoryTabs";
import PictogramTile from "@/components/PictogramTile";
import { categories } from "@/data/categories";
import { tiles } from "@/data/tiles";
import { relatedTiles } from "@/data/relatedTiles";
import type { Tile } from "@/types/aac";

function SelectedTile({ tile, onRemove }: { tile: Tile; onRemove: (id: string) => void }) {
  return (
    <div className="relative flex h-[70px] min-w-[125px] shrink-0 items-center gap-2 rounded-xl border-2 border-[#E7D2BE] bg-white px-2 pr-7">
      <button type="button" onClick={() => onRemove(tile.id)} aria-label={`Remove ${tile.english}`}
        className="absolute right-1 top-1 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-[#E76F51] text-xs font-bold text-white">
        ×
      </button>
      <div className="relative h-11 w-11 shrink-0">
        <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt={tile.english} fill sizes="44px" className="object-contain" />
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-bold text-[#3F241C]">{tile.english}</p>
        <p className="truncate text-sm font-semibold text-[#8A6557]" dir="rtl" lang="ur">{tile.urdu}</p>
      </div>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
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

  const tilesPerPage = layout === "phone" ? 4 : layout === "portrait" ? 9 : 12;
  const selectedCategory = categories.find((category) => category.id === activeCategory);
  const categoryTiles = tiles.filter((tile) => tile.category === activeCategory);
  const totalPages = Math.max(1, Math.ceil(categoryTiles.length / tilesPerPage));
  const safePage = Math.min(currentPage, totalPages);
  const visibleTiles = categoryTiles.slice((safePage - 1) * tilesPerPage, safePage * tilesPerPage);
  const lastSelected = selectedTiles[selectedTiles.length - 1];
  const relatedIds = lastSelected ? relatedTiles[lastSelected.id] ?? [] : [];
  const suggestedTiles = relatedIds
    .map((id) => tiles.find((tile) => tile.id === id))
    .filter((tile): tile is Tile => tile !== undefined)
    .filter((tile) => !selectedTiles.some((selected) => selected.id === tile.id));

  function selectTile(tile: Tile) {
    setSelectedTiles((current) => current.some((selected) => selected.id === tile.id) ? current : [...current, tile]);
  }
  function removeTile(id: string) {
    setSelectedTiles((current) => current.filter((tile) => tile.id !== id));
  }
  function goToReview() {
    if (selectedTiles.length === 0) return;
    sessionStorage.setItem("goyai-selected-tiles", JSON.stringify(selectedTiles));
    router.push("/review");
  }

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#FFFDF9] px-2 py-1 text-[#3F241C] md:h-dvh md:min-h-0 md:overflow-hidden md:px-3">
      <div className="mx-auto flex w-full max-w-[1400px] flex-col md:h-full md:w-[94%]">
        <header className="flex h-7 shrink-0 items-center justify-center gap-3">
          <h1 className="text-base font-bold tracking-wide">GOYAI</h1>
          <span className="text-xs text-[#8A6557]">Communication Board</span>
        </header>
        <section className="flex min-w-0 flex-col rounded-[18px] border-2 border-[#E7D2BE] bg-[#FFFCF8] shadow-sm md:min-h-0 md:flex-1 md:overflow-hidden">
          <div className="flex h-[50px] shrink-0 items-center justify-between border-b border-[#EEDFD1] px-4">
            <div className="flex items-center gap-2">
              <span className="text-lg text-[#E76F51]">⌂</span>
              <div>
                <h2 className="text-lg font-bold leading-tight">My Talker</h2>
                <p className="text-sm font-semibold leading-tight text-[#9B7A6D]" dir="rtl" lang="ur">میری آواز</p>
              </div>
            </div>
          </div>
          <div className="shrink-0 border-b border-[#EEDFD1] px-3 py-1">
            <CategoryTabs categories={categories} activeCategory={activeCategory}
              onCategoryChange={(id) => { setActiveCategory(id); setCurrentPage(1); }} />
          </div>
          <div className="flex min-h-0 flex-col bg-[#FFF9F5] px-2 py-1 md:flex-1 md:px-4">
            <div className="flex h-8 shrink-0 items-center gap-3">
              <h3 className="text-lg font-bold">{selectedCategory?.name}</h3>
              <span className="text-base font-semibold text-[#8A6557]" dir="rtl" lang="ur">{selectedCategory?.urduName}</span>
            </div>
            <div className="grid grid-cols-2 grid-rows-2 gap-2 rounded-[14px] bg-[#FFF0EB] p-1.5 max-md:auto-rows-[135px] md:min-h-0 md:flex-1 md:grid-rows-3 md:gap-1.5 md:portrait:grid-cols-3 md:landscape:grid-cols-4 2xl:grid-cols-4">
              {visibleTiles.map((tile) => <PictogramTile key={tile.id} tile={tile} onSelect={selectTile} />)}
            </div>
          </div>
          <div className="flex h-[44px] shrink-0 items-center justify-between gap-2 border-t border-[#EEDFD1] bg-[#FFFCF8] px-2 md:px-4">
            <button type="button" onClick={() => setCurrentPage((page) => Math.max(page - 1, 1))}
              disabled={safePage === 1} className="h-9 min-w-[85px] rounded-lg bg-[#E76F51] px-2 text-xs font-semibold text-white disabled:opacity-40 md:min-w-[100px]">← Previous</button>
            <span className="text-sm font-semibold">{safePage} / {totalPages}</span>
            <button type="button" onClick={() => setCurrentPage((page) => Math.min(page + 1, totalPages))}
              disabled={safePage === totalPages} className="h-9 min-w-[85px] rounded-lg bg-[#E76F51] px-2 text-xs font-semibold text-white disabled:opacity-40 md:min-w-[100px]">Next →</button>
          </div>
          {suggestedTiles.length > 0 && (
            <div className="shrink-0 border-t border-[#EEDFD1] px-3 py-1">
              <p className="mb-1 text-xs font-semibold text-[#8A6557]">Related pictograms</p>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {suggestedTiles.slice(0, 5).map((tile) => (
                  <button type="button" key={tile.id} onClick={() => selectTile(tile)}
                    className="min-h-10 shrink-0 rounded-lg border border-[#E7D2BE] bg-white px-3 text-sm font-semibold">
                    {tile.english} · {tile.urdu}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="shrink-0 border-t border-[#EEDFD1] bg-[#FFFCF8] px-2 py-2 md:px-4">
            <div className="flex items-center gap-2">
              <div className="hidden shrink-0 md:block">
                <p className="text-sm font-bold">Selected words</p>
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
                <button type="button" onClick={() => setSelectedTiles([])}
                  className="h-11 shrink-0 rounded-lg border border-[#E7D2BE] bg-white px-3 text-sm font-semibold">Clear</button>
              )}
              <button type="button" onClick={goToReview} disabled={selectedTiles.length === 0}
                className="h-12 w-auto min-w-[90px] shrink-0 rounded-xl bg-[#E76F51] px-5 text-lg font-bold text-white disabled:cursor-not-allowed disabled:opacity-50 md:min-w-[105px]">GO →</button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
