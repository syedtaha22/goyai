# Goyai frontend

Next.js app with the tile board (`/`) and the sentence review screen (`/review`). The review screen
requests sentences from the [backend](../backend/README.md).

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # optional, the defaults already match a local backend
```

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL of the backend |

## Run

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The backend should be running, and its
`GOYAI_CORS_ORIGINS` should include the origin of the page (for example
`["http://localhost:3000","http://192.168.18.253:3000"]` when opening the app from a tablet).

## Checks

```bash
npm run lint
npm run build
```

## Structure

- `src/app/page.tsx`: the tile board.
- `src/app/review/page.tsx`: suggested sentences, editing and speaking.
- `src/services/backend.ts`: the client of the backend, including the mapping from board tile ids to
  backend tile ids.
- `src/data/`: the tile and category definitions. Pictograms are in `public/pictograms/`.
