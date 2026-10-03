"use client";

import Image from "next/image";
import { Tile } from "@/types/aac";

type PictogramTileProps = {
  tile: Tile;
  onSelect: (tile: Tile) => void;
};

export default function PictogramTile({
  tile,
  onSelect,
}: PictogramTileProps) {
  const imageUrl =
    `/pictograms/${tile.category}/${tile.id}.png`;

  return (
    <button
      type="button"
      onClick={() => onSelect(tile)}
      className="flex h-full min-h-0 items-center rounded-xl border-2 border-[#E7D2BE] bg-white px-2 py-1 text-left transition hover:border-[#E76F51] hover:shadow-sm"
    >
      <div className="flex w-[45%] shrink-0 items-center justify-center">
        <div className="relative h-[76px] w-[96px]">
          <Image
            src={imageUrl}
            alt={tile.english}
            fill
            sizes="96px"
            className="object-contain"
          />
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col items-start justify-center pl-2">
        <span className="text-lg font-bold leading-tight text-[#3F241C]">
          {tile.english}
        </span>

        <span
          className="mt-1 text-xl font-semibold leading-tight text-[#8A6557]"
          dir="rtl"
          lang="ur"
        >
          {tile.urdu}
        </span>
      </div>
    </button>
  );
}