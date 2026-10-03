import fs from "fs";
import path from "path";

const tilesFile = path.join(
  process.cwd(),
  "src",
  "data",
  "tiles.ts"
);

const source = fs.readFileSync(
  tilesFile,
  "utf8"
);

/*
  Automatically read:
  id
  category
  english

  directly from tiles.ts.

  So we do NOT manually type 200+ tiles here.
*/

const tileRegex =
  /{\s*id:\s*"([^"]+)",\s*category:\s*"([^"]+)",\s*english:\s*"([^"]+)"/g;

const tiles = [];

let match;

while (
  (match = tileRegex.exec(source)) !== null
) {
  tiles.push({
    id: match[1],
    category: match[2],
    english: match[3],
  });
}

/*
  Better search terms for concepts where
  our UI label is not ideal for ARASAAC search.
*/

const searchOverrides = {
  person_me: "I",
  person_mom: "mother",
  person_dad: "father",

  action_dislike: "dislike",

  feeling_okay: "okay",

  food_roti: "bread",
  food_dal: "lentils",
  food_paratha: "flatbread",
  food_naan: "bread",

  social_thank_you: "thank you",
  social_dont_know: "don't know",

  personal_name: "name",
  personal_age: "age",
  personal_birthday: "birthday",

  personal_favorite_person: "person",
  personal_sibling_name: "sibling",
  personal_teacher_name: "teacher",
  personal_therapist_name: "therapist",
  personal_friend_name: "friend",
  personal_caregiver_name: "caregiver",

  personal_favorite_toy: "toy",
  personal_favorite_food: "food",
  personal_favorite_drink: "drink",
  personal_favorite_activity: "play",
  personal_favorite_game: "game",
  personal_favorite_show: "television",
  personal_favorite_song: "music",
  personal_favorite_book: "book",

  personal_comfort_item: "comfort",
  personal_toy: "toy",
  personal_book: "book",
  personal_bag: "bag",
  personal_phone: "phone",
  personal_clothes: "clothes",

  personal_home: "home",
  personal_school: "school",
  personal_class: "class",
  personal_favorite_place: "place",
  personal_specific_place: "place",

  personal_morning_routine: "morning",
  personal_school_routine: "school",
  personal_therapy_routine: "therapy",
  personal_bedtime_routine: "sleep",

  personal_drawing: "drawing",
  personal_music: "music",
  personal_tv: "television",
  personal_games: "game",

  personal_custom_1: "communication",
  personal_custom_2: "communication",
  personal_custom_3: "communication",
};

function getSearchTerm(tile) {
  return (
    searchOverrides[tile.id] ||
    tile.english
  );
}

async function searchArasaac(word) {
  const url =
    `https://api.arasaac.org/api/pictograms/en/search/${encodeURIComponent(
      word
    )}`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      `Search failed: ${response.status}`
    );
  }

  return response.json();
}

async function downloadImage(
  pictogramId,
  destination
) {
  const imageUrl =
    `https://static.arasaac.org/pictograms/${pictogramId}/${pictogramId}_500.png`;

  const response = await fetch(imageUrl);

  if (!response.ok) {
    throw new Error(
      `Image failed: ${response.status}`
    );
  }

  const buffer = Buffer.from(
    await response.arrayBuffer()
  );

  fs.writeFileSync(
    destination,
    buffer
  );
}

async function processTile(
  tile,
  current,
  total
) {
  const searchTerm =
    getSearchTerm(tile);

  const directory = path.join(
    process.cwd(),
    "public",
    "pictograms",
    tile.category
  );

  fs.mkdirSync(directory, {
    recursive: true,
  });

  const destination = path.join(
    directory,
    `${tile.id}.png`
  );

  /*
    KEEP existing image.

    This is useful because Person icons
    have already been downloaded.
  */

  if (fs.existsSync(destination)) {
    console.log(
      `[${current}/${total}] SKIP ${tile.id} (already exists)`
    );

    return;
  }

  console.log(
    `[${current}/${total}] ${tile.id} → "${searchTerm}"`
  );

  try {
    const results =
      await searchArasaac(searchTerm);

    if (!results.length) {
      console.log(
        `   ❌ No result`
      );

      return;
    }

    const pictogramId =
      results[0]._id;

    await downloadImage(
      pictogramId,
      destination
    );

    console.log(
      `   ✅ ARASAAC ${pictogramId}`
    );
  } catch (error) {
    console.log(
      `   ❌ ${error.message}`
    );
  }
}

async function main() {
  console.log("\n==============================");
  console.log("GOYAI FULL ARASAAC IMPORT");
  console.log("==============================");

  console.log(
    `Found ${tiles.length} tiles in tiles.ts\n`
  );

  for (
    let i = 0;
    i < tiles.length;
    i++
  ) {
    await processTile(
      tiles[i],
      i + 1,
      tiles.length
    );

    await new Promise(
      (resolve) =>
        setTimeout(resolve, 120)
    );
  }

  console.log("\n==============================");
  console.log("IMPORT FINISHED");
  console.log("==============================");

  console.log(
    "\nImages are in public/pictograms/"
  );
}

main();