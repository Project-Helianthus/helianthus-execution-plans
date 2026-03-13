# Hydraulic Visualization Lovelace Cards

Revision: `v0.5-post-adversarial-r4`
Date: `2026-03-13`
Status: `Locked`

## Summary

- This plan adds two read-only SVG-based Lovelace cards to the Helianthus HA
  integration that visualize HVAC hydraulic topology in real time.
- **Card 1 — Burner Hydraulics:** shows the internal hydraulics of the heat
  source: heat exchanger, 3-way diverter valve, burner modulation, fan speed,
  flame state, CH pump, flow/return temperatures.
- **Card 2 — System Hydraulics:** shows the full installation topology: heat
  source, primary circuit, heating circuits with VDM pumps, cylinder(s), solar
  collectors, DHW recirculation, outdoor temperature.
- Both cards consume exclusively HA entity states (`hass.states`). They do not
  call the gateway GraphQL API directly.
- Both cards are read-only. No writes, no setpoint changes, no mode toggles.
- Both are standard Lovelace custom cards (`LitElement` web components) that
  users place on any dashboard. No `panel_custom:` registration, no sidebar
  entry, no custom routing. Both cards implement `getGridOptions()` for correct
  sizing in the HA 2025+ sections-view layout.
- All required entity data already exists in the Helianthus HA integration.
  No gateway-side semantic additions are needed for v1.
- Code lives in the `helianthus-ha-integration` repository.
- The cards are bundled as a compiled JS file committed to the integration
  repository, served via a static HTTP path registered at integration-level
  `async_setup` (not per-entry), and auto-registered in the HA Lovelace
  resource collection (storage-mode dashboards) so they appear in the card
  picker without manual configuration.
- Delivery order: build pipeline first, then Card 1 (simpler), then Card 2
  (topology-adaptive).

## 1. Evidence and Unknowns

### 1.1 Proven

- The Helianthus HA integration exposes all data points needed for both cards
  as HA entities (sensors and binary sensors). Specifically:
  - **Boiler:** flow temperature, return temperature, DHW temperature, DHW
    storage temperature, burner modulation (%), diverter valve position (%),
    fan speed (RPM), storage load pump (%), water pressure (system-level).
  - **Boiler binary:** flame active, gas valve active, CH pump, external pump,
    circulation pump.
  - **Circuits:** per-circuit flow temperature, per-circuit pump active, circuit
    state, circuit type, has-mixer flag.
  - **Solar:** collector temperature, return temperature, pump active, solar
    enabled.
  - **Cylinders:** per-cylinder temperature, max setpoint, charge hysteresis.
  - **DHW:** current temperature, target temperature, operating mode.
  - **System:** outdoor temperature, outdoor 24h average, system flow
    temperature, water pressure, system scheme, VR71 module configuration.
- HA Lovelace custom cards are `LitElement` web components registered with
  `customElements.define()`. They consume `hass.states[entity_id]` for live
  data. This is the established community pattern.
- SVG with `viewBox` scales responsively to any container size. This is the
  standard approach for HVAC visualization cards in HA (e.g. ha-floorplan,
  custom:mini-graph-card, various boiler cards in the community).
- The Helianthus integration already serves frontend assets from
  `custom_components/helianthus/`. HA integrations can serve static JS
  bundles via `async_register_static_paths()` and auto-register them
  as Lovelace module resources via the storage-mode resource collection.
  This is the pattern used by several community integrations (e.g.
  `custom_components/hacs/`, `custom_components/mushroom/`).

### 1.2 Hypothesis

- A single compiled JS bundle for both cards is acceptable for the v1 delivery
  size budget (gate: ≤150 KB gzipped).

### 1.3 Unknown

- Whether `returnTemperatureC` reports `null` when the boiler is idle on the
  target hardware. The live snapshot showed the field absent from the MCP
  response while the boiler was off, but it is registered as an HA entity
  (`BoilerTemperatureField`). Card 1 must handle null/unavailable gracefully.
- The optimal SVG layout dimensions and aspect ratios for both cards. These
  will be determined during implementation through iterative design.

## 2. Vaillant Boiler Internal Reference

This section documents the physical layout and component inventory of Vaillant
ecoTEC boilers. The information comes from the Vaillant trainer manual
(`docs/Regulators/336598177-Trainer-Vaillant.docx`) and serves as the
authoritative reference for the Card 1 SVG layout.

### 2.1 Model Naming Convention

```
V U W  2 4 2 / 3 - 5
│ │ │  │ │ │   │   └─ variant: 3=PRO, 5=PLUS
│ │ │  │ │ │   └───── generation (2, 3, 5)
│ │ │  │ │ └───────── flue type: 0=ATMO, 2=TURBO (forced draft fan),
│ │ │  │ │                        6=ECO (condensing)
│ │ │  └─┴─────────── rated output (kW)
│ │ └──────────────── W = combi (plate DHW exchanger, no storage)
│ └────────────────── U = heating
└──────────────────── V = Vaillant
```

- `VU` = system boiler (heating only, external DHW cylinder)
- `VUW` = combi boiler (integrated plate heat exchanger for instant DHW)

### 2.2 Internal Components by Power Class

| Component | ≤35 kW (ecoTEC PRO/PLUS) | 46–65 kW (ecoTEC PLUS) | 80–150 kW (BIG) |
| --- | --- | --- | --- |
| Primary heat exchanger | stainless steel plates (PRO: 13, PLUS: 19) | stainless steel (656: double exchanger) | stainless steel |
| 3-way diverter valve | yes (PRO: composite, PLUS: brass) | **no** | **no** |
| CH pump | yes (PRO: 2-speed electronic auto, PLUS: PWM) | yes | **no** |
| Expansion vessel | yes (PRO: 8 L, PLUS: 10 L) | **no** | **no** |
| Gas valve | PRO: pneumatic, PLUS: ELGA (stepper motor) | ELGA | pneumatic |
| Forced-draft fan | yes (condensing models) | yes | yes |
| DHW plate exchanger | yes (combi VUW only) | n/a (VU only) | n/a (VU only) |

Key observations for SVG layout:
- The **v1 target is ≤35 kW ecoTEC** (the most common residential model).
  All internal components are present: heat exchanger, 3-way valve, pump,
  expansion vessel, fan, gas valve.
- Models ≥46 kW omit the 3-way valve and expansion vessel and must be
  installed with a hydraulic separator (Weishaupt WH400/WH95/WH160/WH280).
  These are out of scope for v1.
- Models ≥80 kW additionally omit the internal pump. Out of scope for v1.

### 2.3 PRO vs PLUS Differences (Relevant to Visualization)

| Aspect | PRO | PLUS |
| --- | --- | --- |
| Pump type | 2-speed electronic auto | PWM modulating |
| 3-way valve material | composite | brass |
| Gas valve technology | pneumatic | ELGA stepper motor |
| Heat exchanger plates | 13 | 19 |
| Expansion vessel | 8 L | 10 L |
| Comfort function | no | yes (keeps exchanger warm for faster DHW) |
| DHW outlet sensor | no | yes (constant flow regulation) |

The SVG layout does not visually differentiate PRO from PLUS in v1. The same
schematic applies to both; only the data values differ.

### 2.4 Pipe Order Under the Boiler

Vaillant standard connection order (viewed from the front, right to left):

```
RETURN — COLD WATER IN — GAS — HOT WATER OUT — FLOW
```

This ordering informs the bottom-edge pipe placement in the Card 1 SVG.

### 2.5 Comfort Function (PLUS Models)

The PLUS comfort function (`C` on display) keeps the secondary DHW heat
exchanger warm so hot water arrives faster at the tap. When active:
- The CH pump may run intermittently even without a heating demand.
- The 3-way valve may cycle to the DHW position briefly.
- The `dhw_demand_active` entity may show `true` without actual tap draw.

Card 1 should not misrepresent comfort-function activity as a real DHW
demand. However, since v1 is read-only visualization of raw entity states,
no special handling is needed; the card faithfully shows whatever the
entities report.

## 3. Card 1: Burner Hydraulics

### 3.1 SVG Layout Specification

The card renders an SVG diagram of the boiler's internal hydraulics. The
layout follows the physical arrangement of a Vaillant ecoTEC ≤35 kW boiler,
oriented as a front cross-section view.

**Vertical zones (top to bottom):**

1. **Flue / exhaust zone** — top edge. Fan element with RPM label.
2. **Heat exchanger zone** — central area. Stylized plate heat exchanger,
   color-coded by flow temperature. The primary (gas-side) and secondary
   (water-side) surfaces are visually distinct.
3. **Burner zone** — below the heat exchanger. Flame element with modulation
   percentage label. Flame height and intensity scale with modulation value.
   Gas valve indicator dot adjacent.
4. **Hydraulic zone** — lower area. Contains the 3-way diverter valve, CH
   pump, and pipe routing.
5. **Connection zone** — bottom edge. Five pipe stubs matching the Vaillant
   connection order (right to left): Return, Cold Water In, Gas, Hot Water
   Out, Flow.

**Hydraulic zone detail:**

The CH loop and DHW path are physically separate circuits in the boiler:

- The **CH loop** is a closed primary loop: the heat exchanger heats CH water,
  which flows through the 3-way valve (CH position) → CH pump → flow pipe out
  to the installation → return pipe back to the heat exchanger.
- The **DHW path** (combi models only) is an open potable-water path: cold
  mains water enters the DHW plate exchanger, is heated by primary-side water
  diverted via the 3-way valve (DHW position), and exits as hot water to taps.
  There is no return pipe from the taps back to the boiler — this is a single-
  pass open circuit.

```
                  ┌─────────────────┐
                  │  Heat Exchanger  │
                  │  (plate stack)   │
                  └────────┬────────┘
                           │ primary flow out
                     ┌─────┴─────┐
                     │  3-way    │
                     │  valve    │
                     └──┬────┬──┘
                 CH     │    │     DHW (primary side)
              ┌─────────┘    └─────────┐
              │                        │
         ┌────┴────┐            ┌──────┴──────┐
         │ CH Pump │            │ DHW plate   │ ← cold mains water IN
         │  (PWM)  │            │ exchanger   │ → hot water OUT (to taps)
         └────┬────┘            └─────────────┘
              │                   (open potable-water path,
              ▼                    no return to boiler)
         ── FLOW ──
              ▲
              │
         ── RETURN ─── (CH return from installation)
              │
              └──── back to Heat Exchanger
```

Key topology rules:
- The CH return pipe goes back to the heat exchanger. It does NOT share a
  return path with the DHW side.
- The DHW plate exchanger has two sides: the primary side carries CH water
  from the 3-way valve; the secondary side carries potable cold water in
  and hot water out. Only the secondary-side temperatures are displayed
  (DHW temperature sensor).
- When `boiler_type: system`, the entire DHW branch (3-way valve DHW path,
  plate exchanger) is hidden because system boilers have no internal DHW
  exchanger.

**Visual element inventory:**

- **Heat exchanger** — central element, stylized as a plate stack or shell
  representation. Color-coded by flow temperature (blue → red gradient).
- **Burner** — positioned below the heat exchanger. Shows flame state
  (animated flicker when active, grey when off). Displays modulation
  percentage as a label and as flame height/intensity.
- **Fan** — positioned at the top near the flue outlet. Displays current RPM.
  Rotation animation when active (CSS transform).
- **3-way diverter valve** — positioned at the flow outlet of the heat
  exchanger, at the junction where CH and DHW branches split. Visual
  indicator of position: CH direction vs DHW direction. Percentage label.
  Color-coded by position (0% = full CH, 100% = full DHW).
- **CH pump** — on the CH flow branch below the 3-way valve. Animated spin
  when active, static when off.
- **DHW plate exchanger** — on the DHW branch (combi models only). Shown as
  a smaller secondary exchanger element with cold-water-in and hot-water-out
  stubs. Hidden when `boiler_type: system`.
- **Flow pipe** — from heat exchanger through diverter valve to CH pump and
  out. Color-coded by flow temperature.
- **Return pipe** — CH return back to heat exchanger (closed loop). Color-
  coded by return temperature.
- **Temperature labels** — flow temperature, return temperature, DHW
  temperature positioned on or near the relevant pipe segments.
- **Water pressure** — displayed as a numeric label in the hydraulic zone.
  This is the system-level water pressure sensor (physically on the
  controller, but represents the boiler circuit pressure).
- **Status badges** — gas valve state, flame state as small indicator dots.
- **Expansion vessel** — small schematic element connected to the return
  circuit. Decorative in v1 (no dedicated entity), provides visual
  completeness.
- **External pump** — the boiler exposes an `externalPumpActive` relay
  output. This drives external loads (buffer tank charging, etc.) that are
  physically outside the boiler casing. It is excluded from the Card 1
  burner-internal view. It appears only in Card 2 (system-level view).

### 3.2 Entity Mapping

Entity IDs shown below are the actual slugified names produced by the
Helianthus HA integration. The integration does NOT set `has_entity_name`,
so HA derives `entity_id` from the `_attr_name` value. All example IDs
below are verified against the current sensor.py and binary_sensor.py source.

| Visual Element | Config Key | HA Entity ID (example) | Type | Unit |
| --- | --- | --- | --- | --- |
| Flow temperature (pipe color + label) | `flow_temperature` | `sensor.boiler_flow_temperature` | sensor | °C |
| Return temperature (pipe color + label) | `return_temperature` | `sensor.boiler_return_temperature` | sensor | °C |
| DHW temperature (label, combi only) | `dhw_temperature` | `sensor.boiler_dhw_temperature` | sensor | °C |
| Burner modulation (flame intensity + label) | `modulation` | `sensor.burner_modulation` | sensor | % |
| Fan speed (label + animation) | `fan_speed` | `sensor.burner_fan_speed` | sensor | RPM |
| Diverter valve position (visual + label) | `diverter_valve` | `sensor.hydraulics_diverter_valve_position` | sensor | % |
| CH pump (animation) | `ch_pump` | `binary_sensor.hydraulics_ch_pump` | binary_sensor | on/off |
| Flame state (flame visual) | `flame` | `binary_sensor.burner_flame_active` | binary_sensor | on/off |
| Gas valve (status dot) | `gas_valve` | `binary_sensor.burner_gas_valve_active` | binary_sensor | on/off |
| Water pressure (label) | `water_pressure` | `sensor.system_water_pressure` | sensor | bar |
| Storage load pump (label) | `storage_load_pump` | `sensor.hydraulics_storage_load_pump` | sensor | % |

Note: there is no `boiler_water_pressure` entity. The water pressure sensor
is registered as a system-level entity on the regulator device (VR_71) with
name "System Water Pressure". This is semantically correct — the pressure
sensor is on the controller, not the boiler.

### 3.3 Card Configuration

The card is configured in the Lovelace YAML with explicit entity ID mappings:

```yaml
type: custom:helianthus-burner-hydraulics-card
layout: ecotec_35kw          # required — v1 only supports this value
boiler_type: combi            # required — "combi" (VUW) or "system" (VU)
entities:
  flow_temperature: sensor.boiler_flow_temperature           # required
  return_temperature: sensor.boiler_return_temperature       # optional
  dhw_temperature: sensor.boiler_dhw_temperature             # optional (combi only)
  modulation: sensor.burner_modulation                       # optional
  fan_speed: sensor.burner_fan_speed                         # optional
  diverter_valve: sensor.hydraulics_diverter_valve_position  # optional
  ch_pump: binary_sensor.hydraulics_ch_pump                  # optional
  flame: binary_sensor.burner_flame_active                   # optional
  gas_valve: binary_sensor.burner_gas_valve_active           # optional
  water_pressure: sensor.system_water_pressure               # optional
  storage_load_pump: sensor.hydraulics_storage_load_pump     # optional
```

Design rules:
- **`layout` is required.** The only accepted value in v1 is `ecotec_35kw`.
  If `layout` is missing or unrecognized, the card renders a static error
  message: "Unsupported layout: [value]. Supported: ecotec_35kw". This
  prevents rendering a physically incorrect schematic on unsupported models.
  Future versions may add `ecotec_46kw`, `ecotec_big`, etc.
- **`boiler_type` is required.** Accepted values: `combi` (VUW — has internal
  DHW plate exchanger) or `system` (VU — external DHW cylinder, no internal
  exchanger). This field controls DHW branch visibility. Using entity presence
  as a discriminator would be ambiguous because a system boiler with an
  external cylinder can still expose `dhwStorageTemperatureC`. The explicit
  config field removes all ambiguity. If `boiler_type` is missing or
  unrecognized, the card renders a config error.
- **`flow_temperature` is required.** The card renders a configuration error
  if this entity is omitted. All other entities are optional.
- Entity IDs are explicit, not auto-discovered. The user specifies which
  entities map to which visual elements. This avoids fragile naming
  assumptions.
- **DHW branch visibility:** controlled by `boiler_type`, not by entity
  presence. When `boiler_type: combi`, the DHW plate exchanger and its piping
  are rendered. When `boiler_type: system`, the DHW branch is hidden and the
  3-way valve is shown in CH-only mode.
- **`storage_load_pump`:** in combi mode, displayed as a percentage label
  near the DHW plate exchanger area. In system mode, the storage load pump
  is hidden in Card 1 because Card 1 is a burner-internal view and system
  boilers have no internal DHW exchanger — the pump drives flow to an
  external cylinder that is only visible in Card 2. If omitted, no storage
  load pump indicator is shown.
- **Missing optional entity behavior:** the corresponding SVG element is
  rendered in a greyed-out state with a `—` label replacing the numeric
  value. The element shape remains visible so the user knows what data is
  missing. If the entity exists but reports HA-level `unavailable` or
  `unknown` state, the same greyed-out treatment applies.

### 3.4 Behavior

- The card re-renders on every `hass` state change for any subscribed entity.
  This is the standard `LitElement` reactive update via `set hass()`.
- Temperature-to-color mapping uses a fixed linear gradient:
  - `≤20°C` = blue (`#2196F3`)
  - `40°C` = green (`#4CAF50`)
  - `60°C` = orange (`#FF9800`)
  - `≥80°C` = red (`#F44336`)
  - Interpolated linearly between breakpoints. Values below 20°C (including
    negative outdoor temperatures) map to the blue endpoint. Values above
    80°C map to the red endpoint.
- Animations (pump spin, flame flicker, fan rotation) use CSS animations, not
  JS requestAnimationFrame. This ensures minimal CPU overhead when idle.
  Animations use `animation-play-state: paused` when the corresponding entity
  is off/inactive — this is both performance-correct (no GPU cycles) and
  visually correct.
- The card respects the HA theme (dark mode, light mode) by using CSS custom
  properties for backgrounds, text colors, and borders.
- SVG `viewBox` provides responsive scaling. The card fills its container
  width and maintains a fixed aspect ratio of `4:3` (`viewBox="0 0 400 300"`
  for Card 1).
- **Sections-view support:** the card implements `getGridOptions()` (a
  regular instance method on the LitElement class, not a static method)
  returning `{ columns: 6, rows: 4, min_columns: 4, min_rows: 3 }` so that
  HA 2025+ sections-view sizes the card correctly instead of defaulting to
  12 columns.
- **SVG accessibility:** the SVG root element includes `role="img"` and an
  `aria-label` attribute: `aria-label="Burner hydraulics diagram"`. No
  further ARIA attributes are needed since v1 is read-only with no
  interactive elements.

## 4. Card 2: System Hydraulics

### 4.1 Visual Elements

The card renders an SVG diagram of the complete installation hydraulic
topology. The layout is vertically oriented (top = heat source, bottom =
emitters/consumers):

- **Heat source (boiler)** — simplified box at the top. Shows flow/return
  temperatures and flame state. Does not replicate Card 1 detail; this is
  a summary view.
- **Primary circuit** — main flow/return piping from boiler to distribution
  manifold. Shows system flow temperature.
- **Heating circuits (multiple)** — branches from the primary manifold. Each
  shows:
  - Circuit label (user-supplied string from the `label` config key)
  - VDM pump (animated when active)
  - Flow temperature on the branch
  - Circuit state (standby/heating/cooling color coding)
  - No mixer valves (the target installation uses direct circuits)
- **Cylinder(s)** — drawn as a vertical tank. Shows temperature with
  gradient fill (cold bottom, hot top). Multiple cylinders rendered side by
  side if present.
- **Solar collector** — positioned to the side, connected to cylinder(s).
  Shows collector temperature, return temperature, pump state. **Requires
  at least one cylinder to be configured** — solar without a cylinder is
  physically impossible (solar heats the cylinder). If solar entities are
  configured but no cylinder is present, the card renders a config error:
  "Solar requires at least one cylinder."
- **DHW recirculation** — a recirculation loop with pump indicator, branching
  from the DHW output. **Requires at least one cylinder to be configured** —
  recirculation without a DHW storage anchor is physically impossible. If
  `dhw_recirculation` is configured but no cylinder is present, the card
  renders a config error: "DHW recirculation requires at least one cylinder."
- **Outdoor temperature** — displayed as a label in the upper corner,
  representing the external environment.

### 4.2 Topology Derivation

Card 2 does not hard-code a specific Vaillant `system_scheme`. Instead, it
derives the visible topology from the entities the user configures:

- **Heating circuits** are rendered for each `circuit` entry in the card
  configuration. The user lists the circuit entities they want to show.
- **Cylinders** are rendered for each `cylinder` entry in the card
  configuration.
- **Solar** is rendered only if solar entities are configured AND at least
  one cylinder is configured.
- **DHW recirculation** is rendered only if the circulation pump entity is
  configured AND at least one cylinder is configured.

Topology dependency rules (enforced at config validation time):
- `solar` requires `cylinders` to be non-empty.
- `dhw_recirculation` requires `cylinders` to be non-empty.

This makes the card usable across different Vaillant system schemes without
requiring a scheme-to-topology decoder, while preventing physically impossible
configurations.

### 4.3 Entity Mapping

| Visual Element | Config Key | HA Entity ID (example) | Type | Unit |
| --- | --- | --- | --- | --- |
| Boiler flow temperature | `boiler.flow_temperature` | `sensor.boiler_flow_temperature` | sensor | °C |
| Boiler return temperature | `boiler.return_temperature` | `sensor.boiler_return_temperature` | sensor | °C |
| Boiler flame | `boiler.flame` | `binary_sensor.burner_flame_active` | binary_sensor | on/off |
| Boiler modulation | `boiler.modulation` | `sensor.burner_modulation` | sensor | % |
| Boiler CH pump | `boiler.ch_pump` | `binary_sensor.hydraulics_ch_pump` | binary_sensor | on/off |
| System flow temperature | `system.flow_temperature` | `sensor.system_flow_temperature` | sensor | °C |
| Outdoor temperature | `system.outdoor_temperature` | `sensor.outdoor_temperature` | sensor | °C |
| Water pressure | `system.water_pressure` | `sensor.system_water_pressure` | sensor | bar |
| Circuit N flow temperature | `circuits[n].flow_temperature` | `sensor.circuit_1_heating_flow_temperature` | sensor | °C |
| Circuit N pump active | `circuits[n].pump` | `binary_sensor.circuit_1_heating_pump_active` | binary_sensor | on/off |
| Circuit N state | `circuits[n].state` | `sensor.circuit_1_heating_state` | sensor | standby/heating/cooling |
| Cylinder N temperature | `cylinders[n].temperature` | `sensor.cylinder_1_temperature` | sensor | °C |
| Solar collector temperature | `solar.collector_temperature` | `sensor.solar_collector_temperature` | sensor | °C |
| Solar return temperature | `solar.return_temperature` | `sensor.solar_return_temperature` | sensor | °C |
| Solar pump active | `solar.pump` | `binary_sensor.solar_pump_active` | binary_sensor | on/off |
| Circulation pump active | `dhw_recirculation.pump` | `binary_sensor.hydraulics_circulation_pump` | binary_sensor | on/off |
| External pump active | `system.external_pump` | `binary_sensor.hydraulics_external_pump` | binary_sensor | on/off |

Note on entity ID patterns: the Helianthus integration does not set
`has_entity_name`, so HA derives entity_id by slugifying `_attr_name`.
Circuit entities include the circuit type in the slug — e.g.
`sensor.circuit_1_heating_flow_temperature` (from name "Circuit 1 (Heating)
Flow Temperature"). The parenthetical type token is embedded in the slug.
Users must look up their actual entity IDs in the HA entity registry.

### 4.4 Card Configuration

```yaml
type: custom:helianthus-system-hydraulics-card
entities:
  boiler:
    flow_temperature: sensor.boiler_flow_temperature
    return_temperature: sensor.boiler_return_temperature
    flame: binary_sensor.burner_flame_active
    modulation: sensor.burner_modulation
    ch_pump: binary_sensor.hydraulics_ch_pump
  system:
    flow_temperature: sensor.system_flow_temperature
    outdoor_temperature: sensor.outdoor_temperature
    water_pressure: sensor.system_water_pressure
    external_pump: binary_sensor.hydraulics_external_pump
  circuits:
    - label: "Circuit 1 (Heating)"
      flow_temperature: sensor.circuit_1_heating_flow_temperature
      pump: binary_sensor.circuit_1_heating_pump_active
      state: sensor.circuit_1_heating_state            # optional
    - label: "Circuit 2 (Heating)"
      flow_temperature: sensor.circuit_2_heating_flow_temperature
      pump: binary_sensor.circuit_2_heating_pump_active
      state: sensor.circuit_2_heating_state            # optional
    - label: "Circuit 10 (Heating)"
      flow_temperature: sensor.circuit_10_heating_flow_temperature
      pump: binary_sensor.circuit_10_heating_pump_active
      state: sensor.circuit_10_heating_state           # optional
  cylinders:
    - temperature: sensor.cylinder_1_temperature
  solar:
    collector_temperature: sensor.solar_collector_temperature
    return_temperature: sensor.solar_return_temperature
    pump: binary_sensor.solar_pump_active
  dhw_recirculation:
    pump: binary_sensor.hydraulics_circulation_pump
```

Design rules:
- Entity IDs are explicit. No auto-discovery. The user's YAML config is the
  sole source of truth for topology — not `system_scheme` or any gateway API.
- **`circuits` is required** and must contain at least one entry. Each entry
  requires `flow_temperature`; `pump` and `state` are optional. The `label`
  field is a user-supplied string (not derived from an entity).
- **`boiler.flow_temperature` is required.** All other boiler entities are
  optional.
- The `cylinders` list determines how many tanks are drawn. If omitted, no
  cylinder is rendered.
- `solar` and `dhw_recirculation` sections are optional. If omitted, those
  visual elements are not rendered. **Topology dependency rules:**
  - `solar` requires `cylinders` to be non-empty → config error if violated.
  - `dhw_recirculation` requires `cylinders` to be non-empty → config error
    if violated.
- All individual entity references within each section are optional except
  where noted above as required.
- **Circuit cap:** the card supports a maximum of 6 configured circuits. If
  more than 6 are configured, the card renders the first 6 and logs a console
  warning. No scroll or overflow behavior. 6 circuits covers all realistic
  Vaillant system schemes.
- **Missing optional entity behavior:** same as Card 1 — greyed-out element
  with `—` label. Element shape remains visible.
- **Circuit state color coding:** if the `state` entity is configured, the
  circuit branch pipe and label use the state color. The authoritative source
  for circuit state strings is the gateway semantic layer
  (`semantic_vaillant.go`, `circuitStateToString()`). The full set of possible
  values:
  - `"standby"` (code 0) = grey
  - `"heating"` (code 1) = orange/red
  - `"cooling"` (code 2) = blue
  - `"unknown_N"` (codes 3–7, format `fmt.Sprintf("unknown_%d", raw)`) = grey
  - `""` (empty string, when raw value is nil / not yet polled) = grey
  - All values are lowercase. The card treats any value not in
    `{"standby", "heating", "cooling"}` as standby-equivalent (grey).
  - HA-level `unavailable`/`unknown` entity states (coordinator failure) =
    greyed-out treatment (same as missing entity). These are distinct from the
    gateway's `"unknown_N"` strings.
  - Comparisons use `===`.
  If `state` is omitted, the card derives a simplified state from `pump`:
  pump on = heating color, pump off = standby color. This fallback is
  documented in the card's configuration help text.

### 4.5 Behavior

- Same reactive rendering model as Card 1 (`set hass()` updates).
- Same temperature-to-color mapping.
- Same CSS animation approach for pumps, with `animation-play-state: paused`
  when the entity is off/inactive.
- SVG `viewBox` with responsive scaling. Aspect ratio `3:4`
  (`viewBox="0 0 300 400"`) for Card 2 to accommodate the vertical topology.
- **Sections-view support:** the card implements `getGridOptions()` (instance
  method) returning `{ columns: 8, rows: 5, min_columns: 6, min_rows: 4 }`
  so that HA 2025+ sections-view sizes the card correctly.
- **SVG accessibility:** the SVG root element includes `role="img"` and
  `aria-label="System hydraulics diagram"`.
- The card adjusts layout dynamically based on the configured topology:
  - 1 circuit = centered single branch
  - 2-3 circuits = evenly spaced branches
  - 4-6 circuits = compact spacing, reduced label font
  - 0-1 cylinders = single or no tank
  - 2+ cylinders = side-by-side tanks

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
