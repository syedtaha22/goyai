"use client";

import { useEffect, useState } from "react";
import Image from "next/image";

type Pictogram = {
  _id: number;
};

type PersonTile = {
  tileId: string;
  search: string;
  label: string;
};

const personTiles: PersonTile[] = [
  { tileId: "person_me", search: "I", label: "I / Me" },
  { tileId: "person_you", search: "you", label: "You" },
  { tileId: "person_mom", search: "mother", label: "Mom" },
  { tileId: "person_dad", search: "father", label: "Dad" },
  { tileId: "person_brother", search: "brother", label: "Brother" },
  { tileId: "person_sister", search: "sister", label: "Sister" },
  { tileId: "person_grandmother", search: "grandmother", label: "Grandmother" },
  { tileId: "person_grandfather", search: "grandfather", label: "Grandfather" },
  { tileId: "person_teacher", search: "teacher", label: "Teacher" },
  { tileId: "person_friend", search: "friend", label: "Friend" },
  { tileId: "person_doctor", search: "doctor", label: "Doctor" },
  { tileId: "person_caregiver", search: "caregiver", label: "Caregiver" },
  { tileId: "person_baby", search: "baby", label: "Baby" },
  { tileId: "person_boy", search: "boy", label: "Boy" },
  { tileId: "person_girl", search: "girl", label: "Girl" },
  { tileId: "person_man", search: "man", label: "Man" },
  { tileId: "person_woman", search: "woman", label: "Woman" },
  { tileId: "person_family", search: "family", label: "Family" },
  { tileId: "person_people", search: "people", label: "People" },
  { tileId: "person_child", search: "child", label: "Child" },
  { tileId: "person_he", search: "he", label: "He" },
  { tileId: "person_she", search: "she", label: "She" },
  { tileId: "person_they", search: "they", label: "They" },
  { tileId: "person_classmate", search: "classmate", label: "Classmate" },
  { tileId: "person_therapist", search: "therapist", label: "Therapist" },
  { tileId: "person_visitor", search: "visitor", label: "Visitor" },
];

export default function ReviewPage() {
  const [wordIndex, setWordIndex] = useState(0);
  const [results, setResults] = useState<Pictogram[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedId, setSelectedId] =
    useState<number | null>(null);

  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");

  const currentTile = personTiles[wordIndex];

  useEffect(() => {
    async function loadOptions() {
      setLoading(true);
      setSelectedId(null);
      setMessage("");

      try {
        const response = await fetch(
          `https://api.arasaac.org/api/pictograms/en/search/${encodeURIComponent(
            currentTile.search
          )}`
        );

        if (!response.ok) {
          throw new Error("ARASAAC search failed");
        }

        const data: Pictogram[] =
          await response.json();

        setResults(data.slice(0, 6));
      } catch (error) {
        console.error(error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }

    loadOptions();
  }, [currentTile.search]);

  async function saveSelected() {
    if (selectedId === null) {
      setMessage("Please choose a pictogram first.");
      return;
    }

    setSaving(true);
    setMessage("");

    try {
      const response = await fetch(
        "/api/save-pictogram",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            tileId: currentTile.tileId,
            pictogramId: selectedId,
            category: "person",
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Save failed"
        );
      }

      setMessage(
        `✓ Saved ${currentTile.label}!`
      );
    } catch (error) {
      console.error(error);

      setMessage(
        "Could not save pictogram."
      );
    } finally {
      setSaving(false);
    }
  }

  function nextWord() {
    if (
      wordIndex <
      personTiles.length - 1
    ) {
      setWordIndex(
        (current) => current + 1
      );
    }
  }

  function previousWord() {
    if (wordIndex > 0) {
      setWordIndex(
        (current) => current - 1
      );
    }
  }

  return (
    <main className="min-h-screen bg-[#FFFDF9] p-8 text-[#3F241C]">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">
            ARASAAC Pictogram Review
          </h1>

          <p className="mt-2 text-[#8A6557]">
            Choose the clearest pictogram for each AAC concept.
          </p>
        </div>

        <div className="mb-6 flex items-center justify-between rounded-2xl bg-[#FFF0E5] p-5">
          <div>
            <p className="text-sm font-semibold text-[#9B7A6D]">
              PERSON CATEGORY
            </p>

            <h2 className="mt-1 text-3xl font-bold">
              {currentTile.label}
            </h2>

            <p className="mt-1 text-sm text-[#8A6557]">
              Searching ARASAAC for:{" "}
              {currentTile.search}
            </p>
          </div>

          <p className="font-semibold">
            {wordIndex + 1} /{" "}
            {personTiles.length}
          </p>
        </div>

        {loading ? (
          <div className="flex h-72 items-center justify-center">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-[#E7D2BE] border-t-[#E76F51]" />
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-5">
            {results.map(
              (pictogram) => {
                const imageUrl =
                  `https://static.arasaac.org/pictograms/${pictogram._id}/${pictogram._id}_500.png`;

                const selected =
                  selectedId ===
                  pictogram._id;

                return (
                  <button
                    key={
                      pictogram._id
                    }
                    type="button"
                    onClick={() =>
                      setSelectedId(
                        pictogram._id
                      )
                    }
                    className={`rounded-2xl border-4 bg-white p-5 transition ${
                      selected
                        ? "border-[#E76F51] shadow-lg"
                        : "border-[#E7D2BE] hover:border-[#F4A261]"
                    }`}
                  >
                    <div className="relative mx-auto h-40 w-40">
                      <Image
                        src={
                          imageUrl
                        }
                        alt={`${currentTile.label} pictogram`}
                        fill
                        sizes="160px"
                        className="object-contain"
                        unoptimized
                      />
                    </div>

                    <p className="mt-3 font-bold">
                      ARASAAC #
                      {
                        pictogram._id
                      }
                    </p>

                    {selected && (
                      <p className="mt-2 font-bold text-[#E76F51]">
                        ✓ Selected
                      </p>
                    )}
                  </button>
                );
              }
            )}
          </div>
        )}

        {!loading &&
          results.length === 0 && (
            <div className="rounded-xl bg-white p-10 text-center">
              No pictograms found for{" "}
              {currentTile.label}.
            </div>
          )}

        <div className="mt-7 flex flex-col items-center">
          <button
            type="button"
            onClick={saveSelected}
            disabled={
              selectedId === null ||
              saving
            }
            className="min-h-14 min-w-[260px] rounded-xl bg-[#E76F51] px-8 text-lg font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {saving
              ? "Saving..."
              : "✓ Select & Save"}
          </button>

          {message && (
            <p className="mt-3 font-bold text-[#6F4E42]">
              {message}
            </p>
          )}
        </div>

        <div className="mt-8 flex items-center justify-between">
          <button
            type="button"
            onClick={previousWord}
            disabled={
              wordIndex === 0
            }
            className="rounded-xl bg-[#E76F51] px-6 py-3 font-bold text-white disabled:opacity-40"
          >
            ← Previous
          </button>

          <p className="text-sm text-[#8A6557]">
            Choose → Save → Next
          </p>

          <button
            type="button"
            onClick={nextWord}
            disabled={
              wordIndex ===
              personTiles.length - 1
            }
            className="rounded-xl bg-[#E76F51] px-6 py-3 font-bold text-white disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>
    </main>
  );
}