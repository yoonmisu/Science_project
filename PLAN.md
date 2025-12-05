# Verde Project Implementation Plan & Prompt

This document outlines the tasks required to improve the Verde project. It is designed as a prompt for an AI coding assistant (Claude Code) to understand and implement the following requirements.

## Role
You are a Senior Full-Stack Developer working on the Verde project (React Frontend + Python Backend).

## Objective
Implement the following 13 features and improvements. Do not modify files outside the scope of these tasks unless necessary for the implementation.

## Detailed Requirements

### 1. Filter for Terrestrial Vertebrates
**Goal**: The "Animal" category should not show all endangered species.
**Requirement**: Filter the data to return **only** terrestrial vertebrates.
**Target Classes**:
- Mammals
- Birds
- Reptiles
- Amphibians
**Action**: Update the backend API or frontend filtering logic to exclude other classes (e.g., fish, invertebrates) and aquatic species if possible.

### 2. Real Data Visualization on Map
**Goal**: The map currently uses demo/dummy data.
**Requirement**: Remove the demo data. Ensure the map visualization reflects the **actual data** fetched from the API for the selected region/country.
**Action**: Bind the map component to the real data source.

### 3. Smart Search Analytics
**Goal**: Prevent skewing search statistics with repeated queries.
**Requirement**: If a user (identified by IP) performs the **same search consecutively**, do not count the subsequent searches in the statistics.
**Action**: Implement logic to check the previous search term and IP before incrementing the search counter.

### 4. Fix Data Loading Issues
**Goal**: Eliminate false "No information available" states.
**Requirement**: There are cases where data exists but is not displayed. Debug and fix the data fetching/rendering flow to ensure **all available data** is shown to the user.
**Action**: Audit the API response handling and frontend state management.

### 5. Flexible & Multi-language Search
**Goal**: Improve search usability.
**Requirement**:
- Support **typo tolerance** (fuzzy search).
- Support **multi-language** input (e.g., searching in Korean should find species with English names if they match).
**Action**: Enhance the search algorithm to handle approximate matches and cross-language queries.

### 6. Fix Map Territory Assignment
**Goal**: Correct map visualization errors.
**Requirement**: Fix issues where specific regions/territories are visually attributed to the wrong country on the map.
**Action**: Verify and correct the GeoJSON data or the logic mapping coordinates/regions to countries.

### 7. Auto-Switch Category on Search
**Goal**: Seamless navigation.
**Requirement**: When a user searches for a species and selects it, automatically switch the active category tab to that species' category.
**Action**: Update the search result selection handler to trigger a category change.

### 8. Reset Search on Category Selection
**Goal**: Clean UI state.
**Requirement**: When the user manually clicks a category button, **clear** the current search input and results.
**Action**: Add a reset action to the category selection handler.

### 9. IP-Based Free Localization
**Goal**: Localize species details.
**Requirement**:
- Detect the user's country/language based on their **IP address**.
- Translate the species detailed information into that language.
- **Constraint**: Use a **free** translation method/service.
**Action**: Integrate an IP geolocation lookup and a free translation library or API.

### 10. "Species of the Day" (Empty State Top)
**Goal**: Engage users when no specific content is selected.
**Requirement**: In the "No information available" area (Top section):
- Display a **random species** that changes once every 24 hours.
- Clicking it should open the species details.
**Action**: Create a backend endpoint for the daily random species and update the UI.

### 11. "Species of the Week" (Empty State Bottom)
**Goal**: Show trending content.
**Requirement**: In the "No information available" area (Bottom section):
- Display the **most viewed species** of the last 7 days.
- Clicking it should open the species details.
- **Note**: This is based on view count (details opened), not search count.
**Action**: Implement view tracking (respecting rule #3) and an endpoint for the weekly top species.

### 12. Explicit Search Trigger Only
**Goal**: Prevent accidental searches.
**Requirement**: Disable search-as-you-type.
- **Only** trigger search when the user presses **Enter** or clicks the **Search Icon**.
**Action**: Remove `onChange` listeners that trigger the API and rely solely on `onSubmit` or `onClick`.

### 13. Remove Hardcoding
**Goal**: Improve code maintainability.
**Requirement**: Scan the entire project for hardcoded strings, IDs, or configuration values.
**Action**: Refactor these into constants, configuration files, or environment variables.

---

**Execution Strategy**:
Please address these tasks one by one or grouped logically. Verify each change before moving to the next.
