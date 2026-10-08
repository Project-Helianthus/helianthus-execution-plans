# Portal configuration and optional Home Assistant embedding

Board scope addition, 8 October 2026, for **0.7.0**. This records intended
work and acceptance; execution remains paused until a new Board resume.
Existing accepted Portal, semantic and binding work is retained.

## Product outcome

The Portal is the primary setup/configuration surface for the standalone product.
Home Assistant is an optional integration, with its Ingress/header/trust and
packaging adaptation owned by the add-on. Gateway supplies generic trusted-proxy
authentication and path-prefix support, generic configuration persistence and
driver extension hooks. Native protocol and binding lifecycle logic stays with
its owner.

Ordinary configuration is limited to adapter connection, adapter/mux proxy
sharing, external GraphQL, eeBUS participation/device bindings and selective
Matter publication. MCP remains independently exposable as already required.
Separate transport (UART/TCP/UDP) from supported adapter protocol (ENS/ENH);
only supported combinations are offered. Passive observation/cache are always
on, with freshness, qualification, invalidation and last-known-good rules
preserved. Internal policy knobs are removed from ordinary setup; complete
read-only introspection remains available.

External GraphQL can be disabled without breaking the Portal or private HA
integration channel. No decorative API-key setting is offered before effective
protection exists. Native eeBUS/Matter trust is distinct from HTTP embedding
authentication. Network exposure is explicit per listener and does not imply
Internet publication.

## Owning issues and dependency order

- PORTAL-CONFIG parent: https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1002
- [0.7.0][PORTAL-01] Support generic trusted external authentication and path-prefix embedding: https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/999
- [0.7.0][PORTAL-02] Make Portal the primary configuration surface with always-on passive observation and cache: https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1000
- [0.7.0][PORTAL-03] Configure selective network sharing for adapter proxy, GraphQL, MCP and output bindings: https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1001
- [0.7.0][PORTAL-04] Add Home Assistant Ingress and minimal-install Portal onboarding: https://github.com/Project-Helianthus/helianthus-ha-addon/issues/239
- [0.7.0][PORTAL-05] Define Portal-managed eeBUS participation, trust and device bindings: https://github.com/Project-Helianthus/helianthus-eebusreg/issues/137
- [0.7.0][PORTAL-06] Define selective Portal publication, stable endpoint identity and Matter fabric lifecycle: https://github.com/Project-Helianthus/helianthus-matter-binding/issues/4

Publish owning configuration/authentication and native binding contracts first.
PORTAL-01 and PORTAL-02 supply generic embedding and configuration foundations;
PORTAL-03 composes network sharing and PORTAL-05/06 native contributions.
PORTAL-04 integrates the accepted contracts into HA packaging. These are
dependencies, not automatic issue readiness; reconcile actual current contracts
on the next explicit resume. The parent tracks integration and final acceptance.

## Required behavior and evidence

- Portal stays accessible with incomplete configuration or a disconnected
  adapter. Saved, applied and observed state remain distinct. Typed validation,
  versioned atomic persistence, edit-conflict handling, last-good recovery and
  access-change recovery prevent failed setup from stranding the user.
- Driver-provided configuration/contribution contracts preserve ownership.
  No arbitrary file/shell interface. Secrets stay masked and outside ordinary
  exports, logs and URLs. Standalone Linux/offline packaging and configurable
  persistent state remain viable; package owners handle process restarts.
- Root and multiple proxy prefixes work end to end, with streaming/reconnect
  and session expiry. Spoofed headers/untrusted peers cannot gain authority;
  sidebar visibility never replaces backend authorization. HA-specific policy
  is implemented in the add-on against current official documentation.
- Adapter sharing reuses the current mux/arbitration owner and preserves
  passive observation/coherence for externally originated traffic.
- eeBUS bindings expose participant/capability/direction/permission and
  configured/offline/incompatible/active/error states; trust is not blanket
  control, and unavailable peers never silently reassign bindings.
- Matter publication explicitly selects eligible admitted profiles, displays
  projection limits, preserves endpoint identity and distinguishes disabling
  publication from fabric removal/reset. Existing runtime/admission gates are
  not relaxed by a Portal setting.
- Preserve complete native evidence, cache/qualification, mux-client and
  binding/output introspection. Integration must not erase current capabilities.
- Existing installs migrate options/state/identities with documented precedence,
  exact accepted package pins and upgrade/rollback evidence. Test standalone
  and HA/browser/container paths, including incomplete setup and listener failures.

Required public contracts precede code merge. Apply repository-local tests,
CI and applicable transport/conformance gates, fresh independent exact-HEAD
review and P0-P2 correction. Report fixtures/packaging/browser results separately
from authorized live HA/device validation. Final Daybreak Blue and exhaustive
physical validation remain release gates on the coherent candidate.

## Scope boundary

This adds software configuration and integration work to 0.7, not the 0.8
declarative/FSM extraction. It does not start kernel, hardware design or a new
distribution-image project. Sensitive live operations retain action-time
confirmation. A guide or issue publication never resumes execution.

## Primary integration references

- [HA app presentation / Ingress](https://developers.home-assistant.io/docs/apps/presentation/)
- [HA app configuration](https://developers.home-assistant.io/docs/apps/configuration/)

The add-on issue must record the exact implemented and tested HA baseline;
these links are normative leads rather than proof of runtime compatibility.
