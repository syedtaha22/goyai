"use client";

import { useState } from "react";
import Image from "next/image";

import CategoryTabs from "@/components/CategoryTabs";
import PictogramTile from "@/components/PictogramTile";
import RelatedTiles from "@/components/RelatedTiles";

import { categories } from "@/data/categories";
import { tiles } from "@/data/tiles";
import { relatedTiles } from "@/data/relatedTiles";

import { Tile } from "@/types/aac";

/* ==================================================
   SELECTED TILE
================================================== */

function SelectedTile({
  tile,
  onRemove,
}: {
  tile: Tile;
  onRemove: (id: string) => void;
}) {
  const imageUrl =
    `/pictograms/${tile.category}/${tile.id}.png`;

  return (
    <div className="relative flex h-[70px] min-w-[125px] shrink-0 items-center gap-2 rounded-xl border-2 border-[#E7D2BE] bg-white px-2 pr-7">
      {/* REMOVE BUTTON */}

      <button
        type="button"
        onClick={() => onRemove(tile.id)}
        aria-label={`Remove ${tile.english}`}
        className="absolute right-1 top-1 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-[#E76F51] text-xs font-bold leading-none text-white shadow-sm"
      >
        ×
      </button>

      {/* IMAGE */}

      <div className="relative h-11 w-11 shrink-0">
        <Image
          src={imageUrl}
          alt={tile.english}
          fill
          sizes="44px"
          className="object-contain"
        />
      </div>

      {/* TEXT */}

      <div className="min-w-0">
        <p className="truncate text-sm font-bold leading-tight text-[#3F241C]">
          {tile.english}
        </p>

        <p
          className="truncate text-sm font-semibold leading-tight text-[#8A6557]"
          dir="rtl"
          lang="ur"
        >
          {tile.urdu}
        </p>
      </div>
    </div>
  );
}

/* ==================================================
   MAIN PAGE
================================================== */

export default function Home() {
  const [activeCategory, setActiveCategory] =
    useState("person");

  const [selectedTiles, setSelectedTiles] =
    useState<Tile[]>([]);

  const [currentPage, setCurrentPage] =
    useState(1);

  const tilesPerPage = 12;

  /* ==================================================
     CURRENT CATEGORY
  ================================================== */

  const selectedCategory =
    categories.find(
      (category) =>
        category.id === activeCategory
    );

  const categoryTiles =
    tiles.filter(
      (tile) =>
        tile.category === activeCategory
    );

  /* ==================================================
     PAGINATION
  ================================================== */

  const totalPages = Math.max(
    1,
    Math.ceil(
      categoryTiles.length /
        tilesPerPage
    )
  );

  const startIndex =
    (currentPage - 1) *
    tilesPerPage;

  const visibleTiles =
    categoryTiles.slice(
      startIndex,
      startIndex + tilesPerPage
    );

  /* ==================================================
     RELATED SUGGESTIONS
  ================================================== */

  const lastSelectedTile =
    selectedTiles[
      selectedTiles.length - 1
    ];

  const relatedIds =
    lastSelectedTile
      ? relatedTiles[
          lastSelectedTile.id
        ] ?? []
      : [];

  const suggestedTiles =
    relatedIds
      .map((id) =>
        tiles.find(
          (tile) =>
            tile.id === id
        )
      )
      .filter(
        (tile): tile is Tile =>
          tile !== undefined
      )
      .filter(
        (tile) =>
          !selectedTiles.some(
            (selected) =>
              selected.id ===
              tile.id
          )
      );

  /* ==================================================
     SELECT TILE
  ================================================== */

  function handleSelectTile(
    tile: Tile
  ) {
    setSelectedTiles(
      (current) => {
        const alreadySelected =
          current.some(
            (selected) =>
              selected.id ===
              tile.id
          );

        if (alreadySelected) {
          return current;
        }

        return [
          ...current,
          tile,
        ];
      }
    );
  }

  /* ==================================================
     REMOVE TILE
  ================================================== */

  function handleRemoveTile(
    tileId: string
  ) {
    setSelectedTiles(
      (current) =>
        current.filter(
          (tile) =>
            tile.id !== tileId
        )
    );
  }

  /* ==================================================
     PAGE
  ================================================== */

  return (
    <main className="h-screen overflow-hidden bg-[#FFFDF9] px-3 py-1 text-[#3F241C]">
      <div className="mx-auto flex h-full w-[94%] max-w-[1400px] flex-col">

        {/* ==================================================
            GOYAI TITLE
        ================================================== */}

        <header className="flex h-7 shrink-0 items-center justify-center gap-3">
          <h1 className="text-base font-bold tracking-wide">
            GOYAI
          </h1>

          <span className="text-xs text-[#8A6557]">
            Communication Board
          </span>
        </header>

        {/* ==================================================
            MAIN APPLICATION
        ================================================== */}

        <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[18px] border-2 border-[#E7D2BE] bg-[#FFFCF8] shadow-sm">

          {/* ==================================================
              APP HEADER
          ================================================== */}

          <div className="flex h-[50px] shrink-0 items-center justify-between border-b border-[#EEDFD1] px-4">

            <div className="flex items-center gap-2">

              <span className="text-lg text-[#E76F51]">
                ⌂
              </span>

              <div>
                <h2 className="text-lg font-bold leading-tight">
                  My Talker
                </h2>

                <p
                  className="text-sm font-semibold leading-tight text-[#9B7A6D]"
                  dir="rtl"
                  lang="ur"
                >
                  میری آواز
                </p>
              </div>

            </div>

            <div className="flex items-center gap-2">

              <button
                type="button"
                aria-label="Settings"
                className="flex h-8 w-8 items-center justify-center rounded-full bg-[#FFF0E5] text-sm"
              >
                ⚙
              </button>

              <button
                type="button"
                aria-label="Sound"
                className="flex h-8 w-8 items-center justify-center rounded-full bg-[#FFF0E5] text-sm"
              >
                🔊
              </button>

            </div>

          </div>

          {/* ==================================================
              CATEGORY TABS
          ================================================== */}

          <div className="shrink-0 border-b border-[#EEDFD1] px-3 py-1">

            <CategoryTabs
              categories={categories}
              activeCategory={
                activeCategory
              }
              onCategoryChange={(
                categoryId
              ) => {
                setActiveCategory(
                  categoryId
                );

                setCurrentPage(1);
              }}
            />

          </div>

          {/* ==================================================
              CATEGORY NAME + MAIN TILE GRID
          ================================================== */}

          <div className="shrink-0 bg-[#FFF9F5] px-4 py-1">

            {/* CATEGORY TITLE */}

            <div className="flex h-8 items-center gap-3">

              <h3 className="text-lg font-bold">
                {selectedCategory?.name}
              </h3>

              <span
                className="text-base font-semibold text-[#8A6557]"
                dir="rtl"
                lang="ur"
              >
                {selectedCategory?.urduName}
              </span>

            </div>

            {/* TILE GRID */}

            <div className="grid h-[270px] grid-cols-4 grid-rows-3 gap-1.5 rounded-[14px] bg-[#FFF0EB] p-1.5">

              {visibleTiles.map(
                (tile) => (
                  <PictogramTile
                    key={tile.id}
                    tile={tile}
                    onSelect={
                      handleSelectTile
                    }
                  />
                )
              )}

            </div>

          </div>

          {/* ==================================================
              PAGINATION
          ================================================== */}

          <div className="flex h-[40px] shrink-0 items-center justify-between border-t border-[#EEDFD1] bg-[#FFFCF8] px-4">

            {/* PREVIOUS */}

            <button
              type="button"
              onClick={() =>
                setCurrentPage(
                  (page) =>
                    Math.max(
                      page - 1,
                      1
                    )
                )
              }
              disabled={
                currentPage === 1
              }
              className="h-8 min-w-[100px] rounded-lg bg-[#E76F51] px-3 text-xs font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              ← Previous
            </button>

            {/* PAGE NUMBER */}

            <p className="text-sm font-semibold text-[#6F4E42]">
              Page {currentPage} of{" "}
              {totalPages}
            </p>

            {/* NEXT */}

            <button
              type="button"
              onClick={() =>
                setCurrentPage(
                  (page) =>
                    Math.min(
                      page + 1,
                      totalPages
                    )
                )
              }
              disabled={
                currentPage ===
                totalPages
              }
              className="h-8 min-w-[100px] rounded-lg bg-[#E76F51] px-3 text-xs font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next →
            </button>

          </div>

          {/* ==================================================
              RELATED PICTOGRAM SUGGESTIONS
          ================================================== */}

          {suggestedTiles.length > 0 && (
            <div className="h-[66px] shrink-0">

              <RelatedTiles
                tiles={
                  suggestedTiles
                }
                onSelect={
                  handleSelectTile
                }
              />

            </div>
          )}

          {/* ==================================================
              SELECTED TILES BAR
          ================================================== */}

          <div className="shrink-0 border-t border-[#EEDFD1] bg-[#FFFCF8] p-1.5">

            <div className="flex min-h-[82px] items-center gap-3 rounded-[14px] bg-[#FFF0E5] px-3 py-1.5">

              {/* LABEL */}

              <div className="w-[125px] shrink-0">

                <p className="text-sm font-bold">
                  Selected Tiles:
                </p>

                <p
                  className="text-sm font-semibold text-[#8A6557]"
                  dir="rtl"
                  lang="ur"
                >
                  چنے ہوئے الفاظ:
                </p>

              </div>

              {/* SELECTED PICTOGRAMS */}

              <div className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto py-1">

                {selectedTiles.length ===
                0 ? (
                  <div>
                    <p className="text-sm text-[#9B7A6D]">
                      Select a pictogram to begin
                    </p>

                    <p
                      className="text-sm text-[#9B7A6D]"
                      dir="rtl"
                      lang="ur"
                    >
                      شروع کرنے کے لیے تصویر منتخب کریں
                    </p>
                  </div>
                ) : (
                  selectedTiles.map(
                    (tile) => (
                      <SelectedTile
                        key={
                          tile.id
                        }
                        tile={tile}
                        onRemove={
                          handleRemoveTile
                        }
                      />
                    )
                  )
                )}

              </div>

              {/* GO BUTTON */}

              <button
                type="button"
                disabled={
                  selectedTiles.length ===
                  0
                }
                className="h-12 min-w-[105px] shrink-0 rounded-xl bg-[#E76F51] px-5 text-lg font-bold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                GO →
              </button>

            </div>

          </div>

        </section>

      </div>
    </main>
  );
}