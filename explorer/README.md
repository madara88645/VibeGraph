# VibeGraph Explorer (Frontend)

The React 19 + Vite single-page app for [VibeGraph](../README.md) — it renders the
interactive call graph, the AI explanation panel, chat, learning path, and the
Ghost Runner.

This directory is the frontend only. For the full project overview, backend
setup, and deployment, see the [root README](../README.md).

## Prerequisites

- **Node.js 18+**

## Getting started

```bash
npm install     # install dependencies
npm run dev     # start the Vite dev server (http://localhost:5173)
```

The dev server expects the FastAPI backend to be reachable so that `/api/*`
requests resolve. Start it from the project root with `python serve.py`.

## Scripts

| Command | What it does |
|---------|--------------|
| `npm run dev` | Start the Vite dev server with hot module reload |
| `npm run build` | Build the production bundle into `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Lint the source with ESLint |
| `npm run test` | Run the Vitest unit tests once |

## Project layout

```
explorer/
├── src/
│   ├── components/   # GraphViewer, ChatDrawer, CodePanel, ProjectUpload, ...
│   ├── hooks/        # useGraphData, useGhostRunner, useTheme, ...
│   ├── utils/        # layout, aiClient, exportGraph, ...
│   └── App.jsx       # app shell
├── vite.config.js
└── eslint.config.js
```
