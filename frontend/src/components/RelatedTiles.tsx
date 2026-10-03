"use client";

import Image from "next/image";
import { Tile } from "@/types/aac";

type RelatedTilesProps = {
  tiles: Tile[];
  onSelect: (tile: Tile) => void;
  selectedTileIds?: string[];
};

export default function RelatedTiles({
  tiles,
  onSelect,
  selectedTileIds = [],
}: RelatedTilesProps) {
  // Remove duplicates and anything already selected.
  const visibleTiles = tiles
    .filter(
      (tile, index, array) =>
        array.findIndex((item) => item.id === tile.id) === index
    )
    .filter((tile) => !selectedTileIds.includes(tile.id))
    .slice(0, 4);

  if (visibleTiles.length === 0) {
    return null;
  }

  return (
    <section
      className="border-t border-[#EEDFD1] bg-[#FFF9F5] px-4 py-2"
      aria-label="Related pictogram suggestions"
    >
      <div className="flex min-h-[64px] items-center gap-3">
        {/* LABEL */}
        <div className="w-[145px] shrink-0">
          <p className="text-sm font-bold leading-tight text-[#6F4E42]">
            You may also want:
          </p>

          <p
            className="mt-1 text-sm font-semibold leading-tight text-[#8A6557]"
            dir="rtl"
            lang="ur"
          >
            آپ یہ بھی کہنا چاہیں:
          </p>
        </div>

        {/* RELATED TILES */}
        <div className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto py-1">
          {visibleTiles.map((tile) => {
            const imageUrl = `/pictograms/${tile.category}/${tile.id}.png`;

            return (
              <button
                key={tile.id}
                type="button"
                onClick={() => onSelect(tile)}
                aria-label={`Select ${tile.english}`}
                className="
                  flex
                  h-[58px]
                  min-w-[130px]
                  shrink-0
                  items-center
                  gap-2
                  rounded-xl
                  border-2
                  border-[#F2C9B5]
                  bg-white
                  px-2
                  text-left
                  transition
                  hover:border-[#E76F51]
                  hover:bg-[#FFF4EE]
                  focus:outline-none
                  focus-visible:ring-2
                  focus-visible:ring-[#E76F51]
                  focus-visible:ring-offset-2
                  active:scale-[0.98]
                "
              >
                {/* PICTOGRAM */}
                <div className="relative h-10 w-10 shrink-0">
                  <Image
                    src={imageUrl}
                    alt=""
                    fill
                    sizes="40px"
                    className="object-contain"
                  />
                </div>

                {/* LABELS */}
                <div className="min-w-0 flex-1">
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
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}