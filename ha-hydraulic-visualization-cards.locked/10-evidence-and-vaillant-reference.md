# Hydraulic Visualization Cards 01: Evidence and Vaillant Reference

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `da004d202f208e9e161fb5b1ccd0effa8ad5596fa101414dcf36852b2bcb61a2`

Depends on: None. This chunk defines the evidence model, unknowns, and Vaillant
boiler hardware reference that all subsequent chunks import.

Scope: Proven entity surface, open unknowns, Vaillant ecoTEC model naming,
component inventory by power class, pipe ordering, PRO vs PLUS differences.

Idempotence contract: Declarative-only. Reapplying this chunk must not alter the
entity surface, create new entities, or change any hardware assumptions.

Falsifiability gate: A review fails this chunk if it claims entities exist that
are not in sensor.py/binary_sensor.py source, misidentifies the Vaillant model
naming scheme, or conflates VU (system) and VUW (combi) boiler types.

Coverage: Summary; Sections 1-2 from the source plan.

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
  - Boiler temperatures: flow, return, DHW (sensor.py `BoilerTemperatureSensor`)
  - Boiler state: burner modulation %, fan speed RPM, storage load pump %,
    diverter valve position % (sensor.py `BoilerStateSensor`)
  - Boiler binary: flame active, gas valve active, CH pump, external pump,
    circulation pump (binary_sensor.py `BoilerStateBinarySensor`)
  - Circuit: flow temperature, state (sensor.py `CircuitSensor`)
  - Circuit binary: pump active (binary_sensor.py `CircuitPumpBinarySensor`)
  - System: water pressure, outdoor temperature, system flow temperature
    (sensor.py `SystemSensor`)
  - Solar: collector temperature, return temperature (sensor.py `SolarSensor`)
  - Solar binary: pump active, enabled, function mode
    (binary_sensor.py `SolarBinarySensor`)
  - Cylinder: temperature (sensor.py `CylinderSensor`)
- Entity IDs are stable — the integration does not set `has_entity_name`, so
  HA derives `entity_id` from the `_attr_name` value via slugification.
- HA Lovelace custom cards use `LitElement` and register via
  `customElements.define()`.
- The Helianthus integration already ships a `manifest.json` and uses
  `async_setup_entry` for config entry setup.

### 1.2 Unknowns

- **Exact SVG dimensions for visual clarity on RPi4.** The aspect ratio and
  `viewBox` values are specified (4:3 for Card 1, 3:4 for Card 2) but actual
  SVG element placement will be refined during M1/M2 implementation.
- **Rollup bundle size.** Estimated ≤150 KB gzipped, but actual size depends on
  LitElement tree-shaking effectiveness and SVG template verbosity. Measured at
  M0 and gated at M3.
- **GPU compositing behavior on RPi4 Chromium.** CSS `transform`-based
  animations are expected to be GPU-composited, but actual frame rates are
  validated at M1/M2 via Playwright screenshot comparison.

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
