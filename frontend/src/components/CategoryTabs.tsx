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
            className={`h-[52px] rounded-xl border-2 px-3 py-0.5 text-center transition ${
              isActive
                ? "border-gray-800 shadow-sm"
                : "border-transparent"
            }`}
            style={{
              backgroundColor: category.color,
            }}
          >
            <span className="block text-base font-bold leading-tight text-gray-900">
              {category.name}
            </span>

            <span
              className="mt-0.5 block text-base font-semibold leading-tight text-gray-700"
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