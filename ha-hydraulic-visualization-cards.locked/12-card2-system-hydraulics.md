# Hydraulic Visualization Cards 03: Card 2 — System Hydraulics

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da004d202f208e9e161fb5b1ccd0effa8ad5596fa101414dcf36852b2bcb61a2`

Depends on: Chunk 10 (evidence model), Chunk 11 (Card 1 establishes the SVG
rendering patterns, temperature-to-color mapping, and CSS animation approach
that Card 2 reuses).

Scope: Card 2 visual elements, topology derivation from config, entity mapping,
configuration schema, topology dependency rules, circuit state color coding,
dynamic layout, sections-view support.

Idempotence contract: Reapplying this chunk must not alter the entity mapping
table, add entities not in the integration source, change topology dependency
rules, or create circuit state values not in the gateway source.

Falsifiability gate: A review fails this chunk if any entity ID does not match
the actual `_attr_name` slugification, if topology dependency rules allow
physically impossible configurations (solar without cylinder), or if circuit
state strings do not match `semantic_vaillant.go circuitStateToString()`.

Coverage: Section 4 from the source plan.

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
