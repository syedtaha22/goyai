"use client";

import { Category } from "@/types/aac";

type CategoryTabsProps = {
  categories: Category[];
  activeCategory: string;
  onCategoryChange: (categoryId: string) => void;
};

export default function CategoryTabs({
  categories,
  activeCategory,
  onCategoryChange,
}: CategoryTabsProps) {
  return (
    <div className="grid grid-cols-2 gap-1.5 md:grid-cols-4">
      {categories.map((category) => {
        const isActive =
          activeCategory === category.id;

        return (
          <button
            key={category.id}
            type="button"
            onClick={() =>
              onCategoryChange(category.id)
            }
            className={`min-h-[64px] rounded-xl border-2 px-3 py-1 text-center transition ${
              isActive
                ? "border-ink shadow-sm"
                : "border-transparent"
            }`}
            style={{
              backgroundColor: category.color,
            }}
          >
            <span className="block text-xl font-bold leading-tight text-ink">
              {category.name}
            </span>

            <span
              className="mt-0.5 block text-xl font-semibold leading-tight text-ink-soft"
              dir="rtl"
              lang="ur"
            >
              {category.urduName}
            </span>
          </button>
        );
      })}
    </div>
  );
}