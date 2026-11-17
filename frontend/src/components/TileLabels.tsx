import type { Tile } from "@/types/aac";

export default function TileLabels({ tile, compact = false }: { tile: Tile; compact?: boolean }) {
  const title = tile.originalLabel ?? tile;
  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1 [overflow-wrap:anywhere]">
      <span className={`block font-bold leading-snug text-ink ${compact ? "text-base" : "text-lg md:portrait:text-xl xl:text-xl"}`}>{title.english}</span>
      <span className={`block font-semibold leading-relaxed text-ink-soft ${compact ? "text-lg" : "text-xl md:portrait:text-2xl xl:text-2xl"}`} dir="rtl" lang="ur">{title.urdu}</span>
      {tile.customLabel && tile.originalLabel && <div className="mt-1 border-t border-line pt-1">
        <span className={`block font-bold leading-snug text-ink ${compact ? "text-base" : "text-lg md:portrait:text-xl xl:text-xl"}`}>{tile.english}</span>
        {tile.urdu !== tile.english && <span className={`block leading-relaxed text-ink-soft ${compact ? "text-lg" : "text-xl md:portrait:text-2xl xl:text-2xl"}`} dir="rtl" lang="ur">{tile.urdu}</span>}
      </div>}
    </div>
  );
}
