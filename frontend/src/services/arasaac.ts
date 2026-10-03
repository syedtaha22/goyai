export type ArasaacPictogram = {
  _id: number;
  keywords?: {
    keyword: string;
  }[];
};

/*
  Cache ARASAAC results.

  This means if "mother" has already been searched,
  we do not need to search it again during the same session.
*/
const pictogramCache = new Map<string, number | null>();

/*
  Search ARASAAC
*/
export async function searchArasaac(
  word: string
): Promise<ArasaacPictogram[]> {
  const response = await fetch(
    `https://api.arasaac.org/api/pictograms/en/search/${encodeURIComponent(
      word
    )}`
  );

  if (!response.ok) {
    throw new Error(
      `ARASAAC search failed for: ${word}`
    );
  }

  return response.json();
}

/*
  Create image URL from ARASAAC ID
*/
export function getArasaacImageUrl(
  id: number
): string {
  return `https://static.arasaac.org/pictograms/${id}/${id}_500.png`;
}

/*
  Automatically find one pictogram for a word.
*/
export async function getPictogramId(
  word: string
): Promise<number | null> {
  const normalizedWord = word
    .trim()
    .toLowerCase();

  /*
    Already searched?
  */
  if (pictogramCache.has(normalizedWord)) {
    return pictogramCache.get(normalizedWord) ?? null;
  }

  try {
    const results =
      await searchArasaac(word);

    if (results.length === 0) {
      pictogramCache.set(
        normalizedWord,
        null
      );

      return null;
    }

    /*
      For now use first result automatically.

      Later, if a few words get the wrong pictogram,
      we can fix ONLY those words.
    */
    const id = results[0]._id;

    pictogramCache.set(
      normalizedWord,
      id
    );

    return id;
  } catch (error) {
    console.error(
      `Could not load ARASAAC pictogram for "${word}"`,
      error
    );

    pictogramCache.set(
      normalizedWord,
      null
    );

    return null;
  }
}