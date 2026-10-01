import json
from pathlib import Path

from pydantic import BaseModel

from app.schemas import Label

PERSONALIZATION = "personalization"


class UnknownTileError(ValueError):
    """
    Raised when a request names tile IDs that are not in the tile bank.
    """

    def __init__(self, tile_ids: list[str]) -> None:
        super().__init__(f"unknown tile ids: {tile_ids}")
        self.tile_ids = tile_ids


class Tile(BaseModel):
    """
    One entry of the tile bank.

    The pictogram is shown to the user. The Urdu and English labels are the semantic
    labels used by the software and the language model.
    """

    tile_id: str
    category: str
    english: str
    urdu: str
    arasaac_id: int | None = None


class TileBank:
    """
    The set of all tiles, indexed by tile_id.
    """

    def __init__(self, tiles: list[Tile]) -> None:
        self._by_id = {t.tile_id: t for t in tiles}
        if len(self._by_id) != len(tiles):
            raise ValueError("duplicate tile_id in tile bank")
        self._tiles = tiles

    @classmethod
    def load(cls, path: Path) -> "TileBank":
        """
        Load a tile bank from a JSON file containing a list of tile records.
        """
        records = json.loads(path.read_text(encoding="utf-8"))
        return cls([Tile(**r) for r in records])

    @property
    def tiles(self) -> list[Tile]:
        return list(self._tiles)

    def __len__(self) -> int:
        return len(self._tiles)

    def __contains__(self, tile_id: object) -> bool:
        return tile_id in self._by_id

    def resolve(
        self, tile_ids: list[str], custom_labels: dict[str, Label] | None = None
    ) -> list[Tile]:
        """
        Look up tiles in selection order and apply personalization labels.

        Args:
            tile_ids: Tile IDs in selection order. Repeats are kept.
            custom_labels: Labels that replace the placeholder labels of personalization tiles.

        Returns:
            The tiles in the same order as tile_ids.

        Raises:
            UnknownTileError: If any ID is not in the bank, or if a custom label targets a
                tile outside the personalization category.
        """
        custom_labels = custom_labels or {}
        unknown = [t for t in tile_ids if t not in self._by_id]
        unknown += [
            t
            for t in custom_labels
            if t not in self._by_id or self._by_id[t].category != PERSONALIZATION
        ]
        if unknown:
            raise UnknownTileError(sorted(set(unknown)))

        resolved = []
        for tile_id in tile_ids:
            tile = self._by_id[tile_id]
            label = custom_labels.get(tile_id)
            if label is not None:
                tile = tile.model_copy(update={"urdu": label.urdu, "english": label.english})
            resolved.append(tile)
        return resolved
