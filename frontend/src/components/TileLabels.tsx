import type { Tile } from "@/types/aac";

export default function TileLabels({ tile, compact = false }: { tile: Tile; compact?: boolean }) {
  const title = tile.originalLabel ?? tile;
  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1 [overflow-wrap:anywhere]">
      <span className={`block font-bold leading-snug text-[#3F241C] ${compact ? "text-sm" : "text-sm md:text-base"}`}>{title.english}</span>
      <span className={`block font-semibold leading-relaxed text-[#8A6557] ${compact ? "text-sm" : "text-base md:text-lg"}`} dir="rtl" lang="ur">{title.urdu}</span>
      {tile.customLabel && tile.originalLabel && <div className="mt-1 border-t border-[#E7D2BE] pt-1">
        <span className={`block font-bold leading-snug text-[#3F241C] ${compact ? "text-sm" : "text-base"}`}>{tile.english}</span>
        {tile.urdu !== tile.english && <span className={`block leading-relaxed text-[#8A6557] ${compact ? "text-sm" : "text-lg"}`} dir="rtl" lang="ur">{tile.urdu}</span>}
      </div>}
    </div>
  );
}
