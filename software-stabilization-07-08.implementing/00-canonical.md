# Helianthus: programul software 0.7 → 0.8 → 1.0

Mandat Board, 4 septembrie 2026. Document de lucru pentru execuție din starea GitHub curentă; nu este un motor de workflow și nu acordă autoritate suplimentară. Numele produsului rămâne provizoriu.

## Rezultatul urmărit

**0.7:** închidem și integrăm software-ul deja început, cu arhitectură semantică comună, fluxuri north–south complete, Portal utilizabil și extensibil, suprafețe publice coerente și redenumirea gateway-ului. Urmează auditul adversarial Daybreak Blue, remedierea constatărilor și testarea exhaustivă pe hardware real. Release-ul nu este declarat acceptat înaintea acestor rezultate.

**0.8:** mutăm descrierile potrivite din cod în limbajul descriptiv/IR și generare deterministă, păstrând comportamentul verificat în 0.7. Repetăm Daybreak Blue, remedierea și testarea exhaustivă pe hardware. Reducerea de la aproximativ 1,2 milioane la 200.000 de linii este o aspirație a Board-ului, nu o măsurătoare verificată sau un criteriu care permite eliminarea funcționalității.

**1.0:** destinația rămâne featureset-ul complet discutat. Nu este redefinit ca pilot sau ca intersecție minimă între protocoale. Criteriile suplimentare de lansare 1.0 se reconciliază după 0.8, fără funcții speculative adăugate acum.

Hardware-ul nou și viitoarele componente kernel/FlexPort aparțin unui proiect privat separat, în repo-ul privat dedicat hardware-ului. Software-ul folosește adaptoarele existente, fără FlexPort. Ieșirile software Matter/eeBUS nu sunt mutate în acel repo hardware și nu pot crea o dependență privată pentru build-ul public.

## Baza verificată

Snapshot GitHub: 2026-09-04 20:16:40 UTC, 27 repo-uri inspectate, 39 issues și 4 PR-uri deschise. Acesta este un inventar datat; fiecare intervenție verifică din nou remote HEAD și acceptance-ul curent.

Auditul nativ a verificat **25/25 checks GitHub reușite la HEAD-urile a 9 repo-uri**. Nu a rerulat suite locale, nu a dat un verdict nou de review și nu a testat hardware. Add-on 0.6.56 fixează gateway `a759efd7f72a099288f1fc2b7cf20236d37cfa0b`, în timp ce gateway main inspectat este `16903f04ee7be107fd8770eec23860e40a06f420`.

| Domeniu | Există | Rămâne pentru integrare |
|---|---|---|
| Vaillant/eBUS | Transport, registru, providers, MCP, GraphQL/HA, DriverManager eBUS | Regresii deschise, migrare semantică și UX; VRC Explorer rămâne produs independent activ |
| SunSpec/Fronius | Achiziție TCP, calificare/refresh, profil GEN24 observat, PV MCP și GraphQL/HA | Convergență în semreg, observabilitate și calificare fizică pe profilul exact |
| Huawei | Identitate/inventar și mecanisme offline separate SmartLogger, EMMA, S-Dongle | Dovezi de calificare, achiziție conectată, capabilități și proiecții; EMMA identity nu înseamnă suport complet |
| Growatt Modbus/BMS, Tesla Gen3/legacy, OutBack | Profile și decodoare native, unele MCP-uri injectabile | Achiziție normală în gateway, lifecycle, semantică și consumeri |
| Gree CAN și Growatt CAN | Transport receive-only, candidați/mapări Gree, Growatt LV V1.04 | Compoziție gateway și proiecții; V1.05 nu este echivalentul V1.04 |
| eeBUS | Runtime SHIP/SPINE, registry, pairing și promovare semantică limitată | Discovery/pending pairing, integrare semantică deplină, binding de ieșire distinct |
| Semantic Layer | Designuri și donații existente eBUS/PV; semreg încă absent | Contract protocol-neutral și implementare completă pentru domeniile începute |
| Portal | UI și trasee de produs existente | Design nou și extensibilitate prin contribuțiile driverelor |
| Matter / eeBUS output | Matter este placeholder; intenții de binding în planuri | Mapping, implementare și conformance proprii fiecărei ieșiri |
| Prometheus | Instrumentare predominant eBUS și surse native utile | Exporter comun runtime/transport și semantică, etichete limitate, fără I/O la scrape |

„Modul implementat”, „conectat în binar”, „validat offline” și „verificat fizic” sunt stări diferite.

## Cele trei decizii de design pentru 0.7

1. **Semantic Layer inspirat de IOKit.** Un echipament poate avea mai multe surse și perspective: comunicație, fizică, electrică, hidraulică, senzori, energie și firmware. Identitatea, serviciile/capabilitățile, relațiile și contractele versionate păstrează provenance, cantități exacte, timp, freshness, conflict și unknown. Kernelul semantic nu importă protocoale/vendor/gateway. Matching-ul depinde de model, versiune, features și configurație; nu devine scanare universală.
2. **Fluxurile north–south.** În sus: observație nativă → calificare → facts/capabilities → proiecții. În jos: intenție → autoritate/capabilitate/precondiții/deadline → driver și endpoint/generație exactă → operație nativă → ACK/readback/outcome → stare publică. Timeout, ACK și confirmare de stare rămân distincte. Refolosim DriverManager și mecanismele native existente. Controlul autonom/optimizatorul nu este adăugat acestui program.
3. **Portal extensibil, furnizat de drivere.** Driverele contribuie descrieri versionate de valori, grupuri, relații, diagnostic, acțiuni și componente specifice când sunt necesare. Portalul deține navigarea, căutarea, perspectivele, accesibilitatea și coerența vizuală. Nu decodează registre și nu decide singur semantica. Demonstrația de extensibilitate adaugă un driver-fixture și UI-ul lui fără un switch central nou pe producător.

Matter este ancorat la ramura indicată de Board, `AryaHassanli/connectedhomeip:dm-0.9-1.7`, SHA `29b4768a513cf566011ab8cd60df1bc495204953` (ballot 0.9, draft 1.7, PR upstream #73842). Matricea semantică folosește și cel mai nou corpus eeBUS accesibil verificat pe componente — SHIP, SPINE și fiecare use case — fără a inventa o singură versiune „eeBUS latest”. Versiunile normative din zona autentificată eeBUS sunt un punct de verificare rămas deschis; acest fapt nu blochează corectarea bugurilor independente.

## Ordinea de execuție

| Val | Livrare | Dependențe și limită |
|---|---|---|
| A — începe acum | Reconciliere issues; guvernanță; VR940f #148, probe existente SunSpec/add-on/HA | Repo-uri independente, worktree-uri separate; fiecare issue primește review la HEAD exact |
| B | Design semantic, north–south și Portal; reconciliere plan #93/PR #94 | Corectăm afirmația învechită că DriverManager nu există; alegem proprietarul public al contractelor |
| C | Semreg și migrarea contractelor existente; conectarea tuturor driverelor/profilurilor începute | Designurile B, dovezi native și compatibilitate; fără semantică universală nouă în ebusreg |
| D | MCP nativ + semantic, GraphQL, Portal, HA prin GraphQL, Prometheus, ieșiri eeBUS/Matter | Contractele C, mapping și pierdere de proiecție explicită per target; public build independent |
| E | Rename `helianthus-ebusgateway` → `helianthus-gateway`, BOM/release candidate, acceptanță offline completă | Importuri/module/CI/docs/pins migrate; ID-uri HA, pairing/trust și starea persistentă păstrate/testate |
| F | Daybreak Blue pe candidatul 0.7, remediere și reverificare; matrice hardware exhaustivă | Auditul nu certifică dispozitive. Testele fizice se pornesc numai după confirmarea operațiilor concrete |
| G — 0.8 | Inventar LOC, limbaj descriptiv/IR, codegen și migrare cu comparator | După 0.7 acceptat; runtime/FSM/I/O/concurență nu sunt mutate orbește în DSL |
| H — 0.8 | Daybreak Blue, remediere, repetarea matricei hardware și release | Paritate funcțională cu 0.7, măsurători reale de reducere și acceptanță fizică |

Valurile sunt grupe de dependențe, nu promisiuni de finalizare într-o noapte. Fiecare pachet cross-repo se desface în issues în repo-ul proprietar înaintea implementării. Un singur responsabil integrează rezultatul; merge-urile nu execută automat planul.

## Dependențe explicite și cerințe istorice păstrate

- `STD-01` are owner în docs-eeBUS și fixează corpusul normativ înainte de înghețarea mapărilor din `INT-04`/`INT-12`. Designul conceptual și bugurile independente pot avansa între timp.
- `SEMREG-BOOTSTRAP`, după alegerea ownership-ului în `INT-04`, creează repository-ul public, licența, AGENTS autonom, CI și contractele de import/documentație. Precede implementarea `INT-05`; designul north–south poate continua în paralel.
- Pachetele native închid numai capabilitățile provider-ului și probele lui. `INT-07` consumă acele artefacte și deține achiziția în gateway; `INT-08` deține suprafețele publice; `INT-17` validează compoziția integrală. Nu există dependență inversă din provider în consumer.
- `LEGACY-PERSIST`, `LEGACY-IDENTITY` și `LEGACY-MUX` păstrează assertions din planurile #27/#23/#30. Criteriile exacte sunt în `92-retained-acceptance.md` în ghidul public. Se reconciliază cu codul curent: un NO_GO istoric nu este nici PASS, nici dovadă automată de bug încă prezent. Offline înainte de ambalare; rândurile fizice la `INT-20`, înainte de release.
- Rename-ul `INT-14` așteaptă `INT-10/11/12/13/15`: Portal, metrics, bindings și HA ajung la freeze; apoi inventariem și integrăm PR-urile afectate, migrăm coordonat remote/module/importuri/pins și verificăm consumatorii. Nu mutăm numele sub ramuri active. Forward-fix ori rollback-ul este explicit în issue înaintea cutover-ului.

## Reguli pentru cruise-control

Board → Director executiv (Astra High) → Responsabili de livrare (Sol High) → Specialiști (Terra Medium/High). Auditorul independent raportează Board-ului. Maparea Anthropic și cele trei moduri de operare sunt în propunerea AGENTS. Daybreak Blue este specialistul adversarial cerut nominal pentru release-uri, separat de auditul organizațional.

Continuăm pe următorul issue cu dependențele satisfăcute, folosind GitHub, ghidurile merged și contractele repo-ului. Nu așteptăm GitHub Projects pentru a repara un bug independent. La modificări în același repo serializăm integrarea sau folosim worktree-uri disjuncte și reverificăm baza înainte de merge.

P0–P2 reale blochează; P3/P4 se repară, se înregistrează sau se justifică fără tururi ritualice. Aplicăm CI/docs/conformance/smoke conform repo-ului și un verdict independent proaspăt `NO_BLOCKING_FINDINGS` pe SHA complet. Nu tratăm tăcerea unui reviewer sau expirarea unui timer drept review pozitiv.

Starea persistentă de produs rămâne necesară: restart, migrare, continuitate, identity/pairing/trust și recuperare. Interdicția motoarelor de autorizare a planurilor nu interzice persistența produsului.

Un issue se închide ca **rezolvat** numai cu dovada acceptanței. Duplicatele/supersedările indică succesorul; munca abandonată în repo-uri deprecated se închide ca **not planned**, păstrând istoria. Hardware-only sau evidence-blocked nu se închide ca software finalizat. Gateway PR #917 rămâne exclus conform deciziei anterioare a Board-ului, până la o cerere explicită de reluare.

## Acceptanța release-urilor

`HARDWARE_TEST_READY`: configurație și achiziție reală conectate în compoziția binarului, fixture/replay prin traseul complet, semantică și consumeri, comportament degradat/restart/reconnect/cleanup, CI și review la BOM exact, procedură hardware executabilă. Un MCP injectabil nu satisface singur criteriul.

`QUALIFICATION_TEST_READY`: experiment delimitat care poate obține dovezile native lipsă; produsul rămâne incomplet semantic până la calificare și implementarea verificată. Astfel de produse rămân vizibile în scope, nu dispar din matrice.

Acceptanța hardware 0.7/0.8 trebuie să enumere toate modelele/profilurile/firmware-urile și operațiile revendicate, fluxuri normale și degradate, reconnect/restart, prospețime, identitate, control autorizat, timeout/indeterminate și recovery. Lipsa unui dispozitiv se raportează ca blocaj; nu este trecută cu fixture. Nu pretindem acoperirea tuturor combinațiilor fizice posibile dintr-o familie.

0.8 măsoară separat codul scris manual, codul generat, teste, fixtures, vendor/dependencies, documentație și artefacte RE. Reducerea liniilor păstrează funcționalitatea, performanța și dovezile; ștergerea testelor nu reprezintă productizare.

## Starea la redactare

Auditurile și propunerile sunt baza de pornire; nu sunt dovezi de implementare sau testare fizică. Issues independente pot avansa înaintea finalizării designului semantic. Rezultatele concrete ale fiecărui PR se raportează din GitHub; această secțiune nu este un registru de runtime.
