import type { Tile } from "@/types/aac";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Tiles whose id on the board differs from their id in the backend tile bank.
const BACKEND_TILE_IDS: Record<string, string> = {
  person_me: "person_i_me",
  action_dislike: "action_do_not_like",
  food_icecream: "food_ice_cream",
  social_dont_know: "social_i_do_not_know",
  personal_comfort_item: "personalization_comfort_item",
  personal_favorite_activity: "personalization_favorite_activity",
  personal_favorite_food: "personalization_favorite_food",
  personal_favorite_person: "personalization_favorite_person",
  personal_favorite_toy: "personalization_favorite_toy",
  personal_sibling_name: "personalization_sibling_name",
  personal_specific_place: "personalization_specific_place",
  personal_teacher_name: "personalization_teacher_name",
  personal_therapist_name: "personalization_therapist_name",
};

// The backend accepts at most 20 excluded sentences per request.
const MAX_EXCLUDED = 20;
const CANDIDATES_PER_REQUEST = 3;

export type Suggestion = {
  urdu: string;
  english: string;
  style: "urdu" | "code_mixed";
};

export type SuggestionResult = {
  suggestions: Suggestion[];
  source: "llm" | "fallback";
  model: string | null;
  latencyMs: number;
};

type SuggestResponse = {
  candidates: Suggestion[];
  source: "llm" | "fallback";
  model: string | null;
  latency_ms: number;
};

export function backendTileId(tile: Tile): string {
  return BACKEND_TILE_IDS[tile.id] ?? tile.id;
}

type SuggestionOptions = {
  mode?: "default" | "different";
  exclude?: string[];
  signal?: AbortSignal;
};

export async function fetchSuggestions(
  tiles: Tile[],
  { mode = "default", exclude = [], signal }: SuggestionOptions = {},
): Promise<SuggestionResult> {
  let response: Response;

  try {
    response = await fetch(`${API_URL}/v1/suggest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tiles: tiles.map(backendTileId),
        exclude: exclude.slice(-MAX_EXCLUDED),
        n: CANDIDATES_PER_REQUEST,
        mode,
      }),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new Error(`The suggestion service at ${API_URL} could not be reached.`);
  }

  if (!response.ok) {
    throw new Error(`The suggestion service answered with status ${response.status}.`);
  }

  const body: SuggestResponse = await response.json();

  return {
    suggestions: body.candidates,
    source: body.source,
    model: body.model,
    latencyMs: body.latency_ms,
  };
}
