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
      className={`flex w-full min-w-0 flex-col items-center justify-center gap-2 bg-white text-center transition hover:bg-[#FFF9F5] focus-visible:outline-2 focus-visible:outline-[#E76F51] md:flex-row md:text-left ${onEdit ? "flex-1 rounded-t-xl px-3 py-2" : "h-full min-h-[150px] rounded-xl border-2 border-[#E7D2BE] px-3 py-3 hover:border-[#E76F51] hover:shadow-sm"}`}>
      <div className="relative h-[64px] w-[68px] shrink-0 md:h-[76px] md:w-[76px]">
        <Image src={`/pictograms/${tile.category}/${tile.id}.webp`} alt="" fill
          sizes="(max-width: 767px) 68px, 76px" className="object-contain" />
      </div>
      <TileLabels tile={tile} />
    </button>
  );
  if (!onEdit) return selection;
  return (
    <div className="flex min-h-[150px] min-w-0 flex-col rounded-xl border-2 border-[#E7D2BE] bg-white">
      {selection}
      <button type="button" aria-label={`Edit word: ${tile.originalLabel?.english ?? tile.english}`} onClick={() => onEdit(tile)}
        className="min-h-11 shrink-0 rounded-b-xl border-t border-[#E7D2BE] bg-[#FFFCF8] px-2 py-2 text-sm font-semibold text-[#8A6557] focus-visible:outline-2 focus-visible:outline-[#E76F51]">Edit word ✎</button>
    </div>
  );
}
