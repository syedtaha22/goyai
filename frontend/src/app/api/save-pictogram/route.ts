import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const { tileId, pictogramId, category } = body;

    if (!tileId || !pictogramId || !category) {
      return NextResponse.json(
        { error: "Missing required information" },
        { status: 400 }
      );
    }

    const imageUrl =
      `https://static.arasaac.org/pictograms/${pictogramId}/${pictogramId}_500.png`;

    const response = await fetch(imageUrl);

    if (!response.ok) {
      throw new Error("Could not download ARASAAC image");
    }

    const buffer = Buffer.from(
      await response.arrayBuffer()
    );

    const folder = path.join(
      process.cwd(),
      "public",
      "pictograms",
      category
    );

    fs.mkdirSync(folder, {
      recursive: true,
    });

    const filePath = path.join(
      folder,
      `${tileId}.png`
    );

    fs.writeFileSync(filePath, buffer);

    return NextResponse.json({
      success: true,
      tileId,
      pictogramId,
      path: `/pictograms/${category}/${tileId}.png`,
    });
  } catch (error) {
    console.error(error);

    return NextResponse.json(
      { error: "Could not save pictogram" },
      { status: 500 }
    );
  }
}