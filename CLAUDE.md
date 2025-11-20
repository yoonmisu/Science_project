# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Verde is a biodiversity data visualization web application for specific regions. It's a React/Vite frontend that displays species data across different countries and categories (Animals, Plants, Insects, Marine Life).

## Development Commands

```bash
# Start development server (localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Architecture

### Tech Stack
- **Frontend**: React 19 + Vite 7 + Styled-components
- **Icons**: Lucide React
- **Build**: Vite with React SWC plugin

### Application Flow
- Entry: `src/main.jsx` → `src/App.jsx` → `src/pages/home.jsx`
- `App.jsx` handles backend connectivity (expects API at `http://127.0.0.1:8000/`)
- `home.jsx` (726 lines) contains the complete UI: interactive map, category filters, species modals

### Data Structure
Countries: Korea, Japan, USA, China, Russia
Categories: 동물 (Animals), 식물 (Plants), 곤충 (Insects), 해양생물 (Marine Life)

Sample data is embedded directly in `home.jsx` with species information per country/category.

### Styling
- Inline CSS with styled-components
- Color-coded category theming
- Font: Pretendard

## Commit Convention

```
feat     : New feature
fix      : Bug fix
docs     : Documentation
style    : CSS/Design changes
refactor : Code improvement
```

## Notes

- Backend files are currently deleted (was FastAPI). Frontend has sample data embedded.
- No test suite configured
- Korean used in UI text and comments, English in code
- Single-page app without routing library - uses React hooks for state