# Hydraulic Visualization Cards 05: Delivery, Scope, Risks, and Implementation Notes

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da004d202f208e9e161fb5b1ccd0effa8ad5596fa101414dcf36852b2bcb61a2`

Depends on: All prior chunks. The delivery order references Card 1 (Chunk 11),
Card 2 (Chunk 12), and frontend architecture (Chunk 13). Scope boundaries and
risks apply to the entire plan.

Scope: Milestone delivery order (M0-M3) with pass/fail gates, scope boundaries,
non-goals, risk register, and implementation notes (LitElement/build, render
performance, SVG/theme integration, entity edge cases).

Idempotence contract: Reapplying this chunk must not alter milestone ordering,
add milestones, change pass/fail gates, or expand the scope boundary.

Falsifiability gate: A review fails this chunk if it changes the milestone
order, weakens pass/fail gates to be non-falsifiable, or silently moves
non-goals into scope.

Coverage: Sections 6-9 from the source plan.

## 6. Delivery Order

### M0 — Build Pipeline

- Set up the frontend build toolchain in `helianthus-ha-integration`:
  `package.json`, `rollup.config.mjs`, `tsconfig.json`, LitElement dependency.
- Update `manifest.json` to declare `"homeassistant": "2024.7.0"` (required
  for `async_register_static_paths` and storage-mode resource collection).
- Add `async_setup()` to `__init__.py` with static path registration and
  Lovelace resource auto-registration.
- Add a minimal "hello world" card that renders a static SVG with one entity
  temperature to prove the full pipeline: build → static path → Lovelace
  resource → card render.
- Commit the compiled bundle to the repo.
- **Target repo:** `helianthus-ha-integration`
- **Pass/fail gates:**
  - `npm run build` produces `frontend/helianthus-cards.js` without errors.
  - Bundle size ≤150 KB gzipped.
  - On the target HA instance (RPi4, ≥2024.7), with the integration installed
    from scratch, `custom:helianthus-hello-card` appears in the "Add Card"
    picker without manual resource YAML (storage-mode dashboard).
  - The hello card renders a temperature value from a live boiler entity.
  - `getGridOptions()` returns valid sizing: card sizes correctly in
    sections-view.
  - The integration loads without errors after a config entry reload.
  - HA startup logs show no `Frontend bundle not found` error for the
    Helianthus integration.

### M1 — Card 1: Burner Hydraulics

- Implement the full burner hydraulics SVG layout per section 3.1.
- Implement entity mapping and reactive rendering.
- Implement temperature-to-color mapping.
- Implement CSS animations for flame, pump, fan.
- Implement card configuration schema and validation.
- Implement dark/light theme support.
- **Target repo:** `helianthus-ha-integration`
- **Pass/fail gates:**
  - Card renders with all entities configured (full config): flow temp,
    return temp, DHW temp, modulation, fan, valve, pump, flame, gas valve,
    pressure, storage load pump — all show live data.
  - Card renders with only `flow_temperature` + `layout` + `boiler_type`
    configured (minimum config) — all optional elements show greyed-out
    with `—` labels.
  - Card renders `boiler_type: combi` → DHW branch visible.
  - Card renders `boiler_type: system` → DHW branch hidden.
  - Card shows error message when `layout` is missing or unsupported.
  - Card shows error message when `boiler_type` is missing or unsupported.
  - Card shows error message when `flow_temperature` is missing.
  - Playwright screenshot: idle state (boiler off, pump off, flame off)
    differs from active state (boiler firing, pump on, flame on).
  - All CSS animations use `transform` or `opacity` only (GPU-composited)
    and use `animation-play-state: paused` when entity is off.
  - Card renders in both HA light and dark themes without broken colors.
  - Card returns valid `getGridOptions()` and sizes correctly in
    sections-view.

### M2 — Card 2: System Hydraulics

- Implement the system hydraulics SVG layout with topology-adaptive rendering.
- Implement circuit, cylinder, solar, DHW recirculation sections.
- Implement dynamic layout adjustment based on configured entity count.
- Implement card configuration schema and validation.
- **Target repo:** `helianthus-ha-integration`
- **Pass/fail gates:**
  - Card renders with the target topology: 3 circuits, 1 cylinder, solar
    present, circulation pump present.
  - Card renders with a minimal topology: 1 circuit, no cylinder, no solar,
    no DHW recirculation.
  - Config error when `solar` is configured without `cylinders`.
  - Config error when `dhw_recirculation` is configured without `cylinders`.
  - Circuit state coloring: `"heating"` → orange, `"standby"` → grey,
    `"cooling"` → blue, `"unknown_3"` → grey (fallback).
  - Circuit state falls back to pump-derived coloring when `state` is omitted.
  - HA `unavailable` entity state → greyed-out treatment.
  - Card shows error when `circuits` is missing or empty.
  - Card shows error when any circuit is missing `flow_temperature`.
  - Card logs console warning and renders first 6 when >6 circuits configured.
  - Card returns valid `getGridOptions()` and sizes correctly in
    sections-view.

### M3 — Polish and Documentation

- Refine SVG visual design for both cards.
- Add card preview images for the Lovelace card picker.
- Add configuration examples to integration documentation.
- **Target repo:** `helianthus-ha-integration`
- **Pass/fail gates:**
  - Final bundle size ≤150 KB gzipped.
  - Both cards render without visible jank on a modern browser (Chrome/
    Firefox). No sustained animation CPU usage when all animated entities
    are off (paused animations).
  - Both cards appear in the card picker with name, description, and live
    preview (via `getStubConfig()` + `preview: true`). The
    `window.customCards` payload includes `type`, `name`, `description`,
    and `preview` fields.
  - Configuration examples in docs match the actual entity IDs from the
    integration.

## 7. Scope Boundaries and Non-Goals

### In Scope

- Two read-only Lovelace cards with live SVG visualization.
- Entity-state-driven rendering from existing Helianthus HA entities.
- Responsive SVG layout that scales to any dashboard container.
- `getGridOptions()` for HA 2025+ sections-view compatibility.
- Dark and light theme support.
- Graceful handling of unavailable/null entities.

### Not In Scope (v1)

- **Writes or interaction.** No clicking on elements to change setpoints,
  toggle modes, or control valves.
- **VDM diverter valves.** The target installation does not have diverter
  valves on circuits. Circuit branches show pumps only. Mixer-valve
  visualization is deferred to a future version if a system with mixers
  becomes available for testing.
- **Auto-discovery of entities.** Entity IDs are user-configured. Automatic
  matching by naming patterns or device registry queries is a potential v2
  improvement.
- **Animated fluid flow.** Pipe color reflects temperature; animated flowing
  particles or moving dashes are not in v1 scope.
- **Historical data or graphs.** The cards show current state only. Mini-graphs
  or trend lines are a separate concern.
- **Multiple heat sources.** Card 2 assumes a single heat source. Cascade or
  hybrid systems are not modeled.
- **High-power boiler variants.** The Card 1 SVG layout assumes a standard
  ecoTEC ≤35 kW boiler with all internal components present (3-way valve, CH
  pump, expansion vessel). Vaillant 46–65 kW models (no 3-way valve, no
  expansion vessel) and 80–150 kW BIG models (no pump, no 3-way valve, no
  expansion vessel) require different SVG layouts and are out of scope for v1.
- **Gateway-side changes.** No new MCP tools, GraphQL fields, or semantic
  extensions are needed.
- **Localization.** Labels are English-only in v1. i18n is a v2 concern.
- **Visual card configuration editor (`getConfigElement`).** Users configure
  cards via YAML. A visual editor is a v2 improvement.
- **HACS distribution.** The cards ship as part of the Helianthus integration.
  Standalone HACS distribution is not planned for v1. The `FRONTEND_PATH`
  constant assumes the standard `custom_components/` location resolved by
  `hass.config.path()`. Non-standard install paths (symlinks, HACS virtual
  locations) are not supported in v1.
- **Lovelace resource cleanup on removal.** See section 5.4 unload note.
- **YAML-mode dashboard auto-registration.** Only storage-mode dashboards
  get auto-registration. YAML-mode users must add the resource manually.

## 8. Risks

- **SVG complexity vs. maintainability.** Hand-crafted SVG templates in
  TypeScript can become hard to maintain. Mitigation: keep SVG fragments
  modular in separate template files, avoid deeply nested inline SVG.
- **Performance on low-end devices.** The target HA instance runs on RPi4.
  CSS animations should be tested for CPU overhead. Mitigation: use
  `transform`-based animations that trigger GPU compositing, use
  `animation-play-state: paused` for inactive entities, avoid re-rendering
  the entire SVG on every state change (use targeted LitElement property
  bindings).
- **Entity ID fragility.** If the Helianthus integration changes entity naming
  conventions, users must update card configurations. Mitigation: entity IDs
  are already stable in the integration; the card does not depend on naming
  patterns.
- **HA API evolution.** The `async_register_static_paths` and Lovelace
  resource collection APIs may change in future HA versions. Mitigation:
  pin minimum HA version in `manifest.json`, manual resource fallback
  documented.

## 9. Implementation Notes

This section captures critical implementation guidance from the enrichment
review. These are not plan requirements but high-value tips that prevent
common mistakes.

### 9.1 LitElement / Build Pipeline

- **Use `svg` tagged template literal** (`import { svg } from 'lit'`) for all
  SVG fragment functions. Nested SVG primitives inside `html\`...\`` are created
  in the HTML namespace and silently fail to render. Embed SVG via
  `html\`<ha-card>${svg\`<svg>...\`}</ha-card>\``.
- **Pin Lit to ^3.1.0** (matching the target HA version). Bundling Lit 4.x
  causes duplicate runtimes and broken reactive properties. In Rollup, mark
  `lit` and its subpaths as `external` so the card uses HA's runtime copy.
- **Rollup output format: `'es'`**, not `'iife'` or `'umd'`. HA loads resources
  as ES modules (`<script type="module">`).
- **Guard `customElements.define()`** against double registration:
  `if (!customElements.get('...')) { customElements.define(...); }`.
- **Terser:** use `mangle: { keep_classnames: true }` for readable stack traces.

### 9.2 Render Performance

- **Extract subscribed entity values into `@state()` properties** in `set hass()`.
  The `hass` object is reassigned on ANY entity state change system-wide. Without
  extraction, the card re-renders on every unrelated entity update.
- **`shouldUpdate()`** guard: return `false` if only `_hass` changed but no
  derived `@state()` properties changed. This is the `mushroom-*` card pattern.
- **`will-change: transform`** on animated SVG groups (pump, fan, flame) to
  promote to GPU-composited layers.
- **`transform-box: fill-box; transform-origin: center`** for SVG rotations.
  Without `transform-box: fill-box`, rotations pivot around the SVG viewport
  origin (0,0), not the element center.
- **No CSS `filter:` or SVG `<filter>` elements.** These are software-rendered
  on RPi4 and cause jank. Use opacity layering for glow effects.

### 9.3 SVG / Theme Integration

- **SVG `<text>` uses `fill`, not `color`.** Set `fill: var(--primary-text-color)`
  on all text elements. Black text on dark background is the most common dark-mode
  bug in SVG cards.
- **Use HA theme CSS variables:** `--primary-text-color`, `--secondary-text-color`,
  `--disabled-text-color` (for greyed-out unavailable state), `--divider-color`
  (for structural strokes). Never hardcode `stroke="#000"` — use theme variables.
- **Wrap in `<ha-card>`** — this is the standard HA card wrapper that automatically
  applies theme-aware borders, shadows, background, and border-radius.
- **`preserveAspectRatio="xMidYMid meet"`** — set explicitly on both SVG roots.
- **Interpolate temperature colors in HSL** (not RGB) for perceptually smooth
  gradients. Lerp hue: blue (210°) → green (120°) → orange (30°) → red (0°).
- **Use `<defs>` for reusable gradients** — define `<linearGradient>` once, update
  stop colors reactively, reference via `fill="url(#...)"`.

### 9.4 Entity Edge Cases

- **`parseFloat()` guard:** entity `.state` is always a string. The values
  `"unavailable"`, `"unknown"`, `""` all produce `NaN`. Always check against
  sentinel strings explicitly — `if (!state)` incorrectly treats `"0"` as missing.
- **Diverter valve** reports intermediate percentages during transition (34%, 67%).
  Display continuous percentage and color interpolation, not binary CH/DHW snap.
- **Fan runs during pre/post-purge** while flame is off. Drive fan animation from
  `fan_speed > 0`, not from flame state.
- **Storage load pump** is a percentage sensor (0-100%), not binary. Display the
  percentage label and drive animation from `value > 0`.
- **`getStubConfig(hass)`** receives the `hass` object — use it to auto-detect
  plausible entity IDs for the card picker preview.
- **Use SHA-256** instead of MD5 for the content hash to avoid linter warnings.
