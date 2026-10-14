## Architectural direction (operator, 2026-10-14)

The gateway is a host for protocol drivers, not a protocol implementation. Before 1.0, every protocol-specific element moves into its driver, and the gateway offers only the abilities a driver needs:

- register itself as **northbound**, **southbound** or **both**;
- extend the MCP surface with driver-specific tools;
- present its setup elements through hooks (configuration and onboarding);
- extend the Portal;
- extend the semantic layer with the projections the driver chooses to publish.

eBUS is a driver of the gateway, not part of it. Today it is southbound only; it can become northbound once native eBUS without latency exists (a real UART on the Raspberry Pi, not a Wi-Fi adapter, whose latency is too high). eeBUS is both northbound and southbound. Modbus can be both: a virtual smart meter exposed on Modbus, an EV charging station exposed to a photovoltaic inverter, or a Gree LV CAN battery pack converted to LV RS-485 with a given flavour. CAN can be both: an RS-485 battery pack exposed on CAN to an inverter that does not know it, a Growatt CAN battery presented as Pylontech CAN, or several JKBMS packs aggregated into one virtual Growatt CAN battery.

The direction is reached across 0.7 and 0.8 and must hold before 1.0. The first slices are INT-06 (gateway #1024 hub, G5 runtime control with the managed-runtime contract) and INT-07 (provider registry); the eBUS raw-evidence stores (gateway #1021) move under the eBUS driver as part of that program.
