# Changelog

All notable changes to BüroKnakker. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] — 2025-10

### Added
- DAG-based planner (`ActionPlan`) with dependency resolution, parallel workstreams, critical path, and cost aggregation.
- Content layer expanded to 48 steps and 12 cities: categories, difficulty, duration, per-step cost ranges, dependencies, tips, German phrases, source URLs.
- 8-tab UI: Dashboard, Timeline (Plotly Gantt), Board (Kanban), Calendar, Cost, Search, Phrasebook, Export.
- Dark mode with palette-driven CSS, single-click toggle.
- URL-persisted progress (`?done=...`) — refresh-safe and shareable.
- Per-step notes, included in the JSON export.
- Category + completion filters applied across views.
- Book-quality PDF: cover page, table of contents, critical-path schedule, coloured category sections, checkbox glyphs, styled phrase cards, ruled notes lines, page numbers.
- Bilingual display values in the profile sidebar (values stay canonical English internally).
- Property-based tests with Hypothesis.
- Structured logging via `BK_LOG_LEVEL`.

### Changed
- `Step` extended with category, difficulty, priority, channel, duration, cost, dependencies, phrases, tips, sources.
- `UserProfile` extended with `move_reason`, `contract_type`, structured `members`.
- `resolve_steps()` is now a wrapper around `build_plan()`.
- City YAMLs include `finanzamt_url` and `kita_url`.
- Test count: 11 → 27.

### Fixed
- PDF `multi_cell` cursor reset (no overlapping text).
- Valid DejaVu TTFs bundled for full Unicode in PDF.
- Umlaut city slugs (`Düsseldorf` → `duesseldorf`).
- Pandas 3.x datetime coercion in Calendar/Cost tabs.
- Plotly `color_discrete_sequence` moved to `px` call.
- Dark-mode toggle now flips on first click.

## [1.0.0] — 2025-10

### Added
- Initial release: 13 steps, 4 cities, timeline + checklist + city info + PDF/ICS export.
- Rule engine with `AppliesTo` filters.
- Streamlit UI, DE/EN strings, pytest suite, GitHub Action.
