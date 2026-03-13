# Hydraulic Visualization Cards 04: Frontend Architecture

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da004d202f208e9e161fb5b1ccd0effa8ad5596fa101414dcf36852b2bcb61a2`

Depends on: Chunk 10 (evidence model — the frontend architecture serves the
entities proven in Section 1), Chunks 11-12 (card specifications that the
frontend delivers).

Scope: Technology stack, component structure, artifact supply chain, Lovelace
resource registration (async_setup, static path, storage-mode auto-registration,
cache busting), card picker self-registration, HA integration contract.

Idempotence contract: Reapplying this chunk must not create duplicate Lovelace
resources, double-register static paths, or alter the existing
`async_setup_entry` behavior.

Falsifiability gate: A review fails this chunk if it uses deprecated
`register_static_path`, accesses `hass.data[LOVELACE_DOMAIN]` as a dict,
performs synchronous I/O in async context, or registers resources in
`async_setup_entry` instead of `async_setup`.

Coverage: Section 5 from the source plan.

## 5. Frontend Architecture

### 5.1 Technology Stack

- **Framework:** LitElement 3.x (same as HA core frontend)
- **Language:** TypeScript
- **SVG:** inline SVG within LitElement `render()` templates using `lit-html`
  `svg` tagged template literals
- **Build:** Rollup (matching HA community card conventions) producing a
  single minified JS bundle
- **Output:** `custom_components/helianthus/frontend/helianthus-cards.js`

### 5.2 Component Structure

```
custom_components/helianthus/
  frontend/
    src/
      helianthus-burner-hydraulics-card.ts   # Card 1 LitElement
      helianthus-system-hydraulics-card.ts   # Card 2 LitElement
      svg/
        burner-layout.ts    # SVG template fragments for Card 1
        system-layout.ts    # SVG template fragments for Card 2
        colors.ts           # Temperature-to-color mapping
        animations.ts       # CSS animation definitions
      types.ts              # TypeScript interfaces (CardConfig, etc.)
      utils.ts              # Shared helpers (entity state parsing, etc.)
    rollup.config.mjs       # Build configuration
    package.json            # LitElement, Rollup dependencies
    tsconfig.json           # TypeScript config
    helianthus-cards.js     # Compiled output — COMMITTED to the repo
```

The `helianthus-cards.js` bundle lives alongside `src/`, `rollup.config.mjs`,
etc. inside the single `frontend/` directory.

### 5.3 Artifact Supply Chain

- The compiled JS bundle `frontend/helianthus-cards.js` is **committed to
  the integration repository**. This is the delivery model: developers build
  locally, commit the output, and the addon deploys the repo as-is.
- The `.gitignore` must NOT exclude `frontend/helianthus-cards.js`.
- **CI gate:** `npm run build` must succeed without errors AND the committed
  `helianthus-cards.js` file size must be within 10% of the freshly-built
  bundle size. This catches gross staleness without requiring bit-for-bit
  deterministic builds (which Rollup+Terser do not guarantee across minor
  version updates).
- Developers rebuild via `cd frontend && npm ci && npm run build` and commit
  the updated bundle alongside any source changes.
- There is no separate release pipeline. The addon copies the integration
  directory including the prebuilt bundle.

### 5.4 Lovelace Resource Registration

The integration registers the card bundle at integration-level setup (not
per-entry) and auto-registers it in the Lovelace resource collection for
storage-mode dashboards.

**Step 1 — Serve the bundle via a static HTTP path (in `async_setup`):**

```python
import hashlib
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import DOMAIN as LOVELACE_DOMAIN

FRONTEND_PATH = "custom_components/helianthus/frontend/helianthus-cards.js"
FRONTEND_URL_BASE = "/helianthus/helianthus-cards.js"

async def async_setup(hass, config):
    """Integration-level setup — called once per HA startup."""
    bundle_path = Path(hass.config.path(FRONTEND_PATH))
    if not bundle_path.is_file():
        _LOGGER.error("Helianthus frontend bundle not found: %s", bundle_path)
        return True

    # Content hash for cache busting.
    # Use executor to avoid blocking I/O on the event loop (HA strict mode).
    raw = await hass.async_add_executor_job(bundle_path.read_bytes)
    content_hash = hashlib.md5(raw).hexdigest()[:8]
    url_with_hash = f"{FRONTEND_URL_BASE}?v={content_hash}"

    # Use async_register_static_paths (HA 2024.7+, replaces deprecated
    # register_static_path which is removed in HA 2025.7)
    hass.http.async_register_static_paths([
        StaticPathConfig(FRONTEND_URL_BASE, str(bundle_path), cache_headers=True)
    ])

    # Store frontend metadata in hass.data[DOMAIN].
    # NOTE: the existing async_setup_entry stores per-entry data at
    # hass.data[DOMAIN][entry.entry_id]. This async_setup uses non-colliding
    # string keys ("frontend_url", "frontend_registered"). Both functions
    # use setdefault(DOMAIN, {}), so initialization order is safe.
    hass.data.setdefault(DOMAIN, {})["frontend_url"] = url_with_hash
    hass.data[DOMAIN]["frontend_registered"] = True

    # Auto-register as Lovelace module resource (storage-mode only).
    # hass.data[LOVELACE_DOMAIN] is a LovelaceData object (not a dict);
    # access the resources attribute directly.
    try:
        lovelace_info = hass.data.get(LOVELACE_DOMAIN)
        resources = getattr(lovelace_info, "resources", None)
        if resources is not None:
            # Ensure the collection is loaded from storage before querying.
            # Without this, async_items() returns empty on cold startup
            # (before any dashboard access), causing duplicate entries.
            if not resources.loaded:
                await resources.async_load()
            existing = [
                r for r in resources.async_items()
                if r.get("url", "").startswith(FRONTEND_URL_BASE)
            ]
            if existing:
                # Update stale URL with new content hash.
                # Include res_type — async_update_item validates against
                # the resource schema which requires both fields.
                old = existing[0]
                if old.get("url") != url_with_hash:
                    await resources.async_update_item(
                        old["id"],
                        {"res_type": "module", "url": url_with_hash},
                    )
            else:
                await resources.async_create_item({
                    "res_type": "module",
                    "url": url_with_hash,
                })
        else:
            _LOGGER.warning(
                "Lovelace storage-mode resources not available; "
                "add %s manually in Configuration → Dashboards → Resources",
                url_with_hash,
            )
    except Exception:
        _LOGGER.warning(
            "Failed to auto-register Lovelace resource; "
            "add %s manually in Configuration → Dashboards → Resources",
            url_with_hash,
            exc_info=True,
        )
    return True
```

Key design decisions:
- **`async_setup` not `async_setup_entry`:** the static path and Lovelace
  resource are integration-level concerns, not per-config-entry. Registering
  in `async_setup` avoids the double-registration crash on entry reload.
  `async_setup` is called once per HA startup, before any entry setup.
  Adding `async_setup` to an integration that previously only had
  `async_setup_entry` is safe — HA calls `async_setup` first, and it must
  return `True`.
- **`hass.data[DOMAIN]` sharing:** `async_setup` stores frontend metadata
  at non-colliding string keys (`frontend_url`, `frontend_registered`).
  The existing `async_setup_entry` stores per-entry data at
  `hass.data[DOMAIN][entry.entry_id]`. Both use `setdefault(DOMAIN, {})`.
  **Important:** `async_unload_entry` must NOT delete the entire
  `hass.data[DOMAIN]` dict even if no entries remain — the integration-level
  frontend keys must survive entry unload cycles.
- **`async_register_static_paths`:** replaces the deprecated
  `register_static_path` which is removed in HA 2025.7. Requires importing
  `StaticPathConfig` from `homeassistant.components.http`.
- **Lovelace resource access:** `hass.data[LOVELACE_DOMAIN]` is a
  `LovelaceData` object, not a plain dict. The `resources` attribute is
  accessed via `getattr()` (not `.get()`). This is the pattern used by
  HACS and browser_mod.
- **Async I/O:** the content hash uses `hass.async_add_executor_job()` to
  read the bundle file off the event loop. This satisfies HA 2025.x strict
  mode, which logs warnings for synchronous I/O in async contexts.
- **Collection loading:** `resources.async_load()` is called before
  `async_items()` to ensure the storage-backed collection is populated.
  Without this, cold-startup queries return empty and create duplicate
  resource entries on every HA restart.
- **Cache busting with update path:** the URL includes `?v={md5_hash}`.
  On first install, a new resource entry is created. On subsequent startups
  after a bundle update, the existing entry is found via
  `startswith(FRONTEND_URL_BASE)` and its URL is updated with the new hash
  via `async_update_item()` (which requires both `res_type` and `url` fields
  per the `ResourceStorageCollection` update schema). This ensures browsers
  always load the latest bundle after an integration update.
- **Storage-mode only:** auto-registration only works for dashboards in
  storage mode. YAML-mode dashboards require manual `resources:` config.
  This is documented but not treated as a failure.
- **Graceful fallback:** if `resources` is None (storage-mode not active) or
  if registration fails for any reason, a warning is logged with the manual
  resource URL. The integration continues to function — the cards work fine
  once the resource is added manually.
- **Minimum HA version:** `manifest.json` must declare `"homeassistant":
  "2024.7.0"` to ensure `async_register_static_paths` and the storage-mode
  resource collection are available.

**Step 2 — Card self-registration for the HA card picker:**

Each card initializes the `window.customCards` array and pushes its metadata:

```js
window.customCards = window.customCards || [];
window.customCards.push({
  type: "helianthus-burner-hydraulics-card",
  name: "Helianthus Burner Hydraulics",
  description: "SVG visualization of boiler internal hydraulics",
  preview: true,
});
window.customCards.push({
  type: "helianthus-system-hydraulics-card",
  name: "Helianthus System Hydraulics",
  description: "SVG visualization of installation hydraulic topology",
  preview: true,
});
```

Each card class implements a static `getStubConfig()` method that returns
a minimal valid configuration for the card picker live preview:

```js
// Card 1
static getStubConfig() {
  return {
    layout: "ecotec_35kw",
    boiler_type: "combi",
    entities: { flow_temperature: "" },
  };
}

// Card 2
static getStubConfig() {
  return {
    entities: {
      boiler: { flow_temperature: "" },
      circuits: [{ label: "Circuit 1", flow_temperature: "" }],
    },
  };
}
```

The `preview: true` flag tells HA (2024.4+) to render the card with
`getStubConfig()` output in the card picker instead of showing a static
placeholder.

**Pass/fail gate (M0):** on a fresh HA instance (≥2024.7) with the
Helianthus integration installed via storage-mode dashboard, both
`custom:helianthus-burner-hydraulics-card` and
`custom:helianthus-system-hydraulics-card` must appear in the "Add Card"
picker without any manual resource YAML configuration.

**Unload/cleanup note:** Lovelace resource cleanup on integration removal is
not implemented in v1. If the integration is removed, the Lovelace resource
entry persists as an orphan that references a 404 URL. The user can manually
remove it from Configuration → Dashboards → Resources. This gap is common
across community integrations and is cosmetically annoying but not harmful.

### 5.5 HA Integration Contract

- The cards depend only on `hass.states` for data. They do not import or
  call any Helianthus-specific Python code, GraphQL client, or coordinator.
- The cards are pure frontend artifacts. They can technically work with any HA
  integration that exposes temperature, modulation, and pump entities —
  though entity ID patterns are Helianthus-specific in practice.
- The cards must not break if the integration is updated. Entity IDs are
  user-configured, not hard-coded in the card JS.
- **`manifest.json` must declare `"homeassistant": "2024.7.0"`** as the
  minimum HA version, ensuring `async_register_static_paths` availability.
