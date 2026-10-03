export type Category = {
  id: string;
  name: string;
  urduName: string;
  color: string;
};

export type Tile = {
  id: string;
  category: string;
  english: string;
  urdu: string;

  // Optional: only use this if the normal English
  // label does not search ARASAAC properly.
  searchTerm?: string;
};