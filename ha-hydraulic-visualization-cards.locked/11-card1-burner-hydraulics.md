# Hydraulic Visualization Cards 02: Card 1 — Burner Hydraulics

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da004d202f208e9e161fb5b1ccd0effa8ad5596fa101414dcf36852b2bcb61a2`

Depends on: Chunk 10 (evidence model, Vaillant boiler reference — especially
component inventory and pipe order from Section 2).

Scope: Card 1 SVG layout, visual element inventory, entity mapping, card
configuration schema, validation rules, `boiler_type` gating, reactive
behavior, temperature-to-color mapping, CSS animations, sections-view support.

Idempotence contract: Reapplying this chunk must not alter the entity mapping
table, add entities not in the integration source, or change the configuration
schema.

Falsifiability gate: A review fails this chunk if any entity ID does not match
the actual `_attr_name` slugification in sensor.py/binary_sensor.py, if the
SVG layout contradicts the Vaillant reference in Chunk 10, or if the DHW path
is modeled as a closed loop.

Coverage: Section 3 from the source plan.

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
