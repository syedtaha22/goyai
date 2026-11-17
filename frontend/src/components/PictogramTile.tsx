"use client";

import Image from "next/image";
import type { Tile } from "@/types/aac";
import TileLabels from "@/components/TileLabels";

type PictogramTileProps = {
  tile: Tile;
  onSelect: (tile: Tile) => void;
  onEdit?: (tile: Tile) => void;
};

export default function PictogramTile({ tile, onSelect, onEdit }: PictogramTileProps) {
  const selection = (
    <button type="button" onClick={() => onSelect(tile)}
      className={`flex w-full min-w-0 flex-col items-center justify-center gap-2 bg-surface text-center transition hover:bg-surface focus-visible:outline-2 focus-visible:outline-accent md:landscape:flex-row md:landscape:text-left ${onEdit ? "flex-1 rounded-t-xl px-3 py-2" : "h-full min-h-0 rounded-xl border-2 border-line px-3 py-3 hover:border-accent hover:shadow-sm"}`}>
      <div className="relative h-[72px] w-[72px] shrink-0 md:portrait:h-[96px] md:portrait:w-[96px] xl:h-[96px] xl:w-[96px]">
        <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt="" fill
          sizes="(max-width: 1279px) 72px, 96px" className="object-contain" />
      </div>
      <TileLabels tile={tile} />
    </button>
  );
  if (!onEdit) return selection;
  return (
    <div className="flex h-full min-h-0 min-w-0 flex-col rounded-xl border-2 border-line bg-surface">
      {selection}
      <button type="button" aria-label={`Edit word: ${tile.originalLabel?.english ?? tile.english}`} onClick={() => onEdit(tile)}
        className="min-h-12 shrink-0 rounded-b-xl border-t border-line bg-surface px-2 py-2 text-base font-semibold text-ink-soft focus-visible:outline-2 focus-visible:outline-accent">Edit word ✎</button>
    </div>
  );
}
