# Dao De Jing — Canon Reconciliation

Updated: 2026-09-08

## Decision summary
Three artifacts previously treated as potentially competing lines do not have the same role.

### 1. v4.0 IMPRENTA — `MASTER_CANDIDATE / EDITORIAL_MATRIX_CANDIDATE`
Verified Library artifact: `2026-07-09_DAO_Dao_De_Jing_SERESARTE_ReyFilosofo_Edicion_Definitiva_v4.0_IMPRENTA(1).pdf`.

Verified structure:
- 183 pages;
- explicit v4.0 legal/editorial statement;
- received Chinese text + authorial Spanish reading + philosophical/philological apparatus;
- explicit Daojing/Dejing separation;
- reduced chapter architecture designed to remove repetitive assembly from prior versions;
- glossary, bibliography and publication/preflight section.

Why it is not yet `MASTER`:
Its own preflight requires external actions before public print sale, including real ISBN, ownership/registration checks, metadata, external sinological review, proofing, extended cover/prepress checks and physical proof. Therefore `definitiva` and `edición maestra final editorial` are internal editorial claims, not sufficient evidence of completed production/publication gates.

### 2. Edición Troncal Ampliada — `SOURCE / PREDECESSOR_MASTER_CANDIDATE`
Verified artifact: `Dao_De_Jing_SERESARTE_ReyFilosofo_Edicion_Troncal_Ampliada.pdf`.

Role:
- substantial predecessor/editorial source;
- longer doctoral-working architecture;
- preserves material and apparatus useful for lineage and future critical work;
- should not be deleted merely because v4.0 is later.

The verified v4.0 architecture explicitly states that it corrects repetitive assembly of earlier versions and concentrates comparative apparatus. This supports treating v4.0 as the later editorial candidate, while retaining Troncal as a source/predecessor rather than calling it obsolete content.

### 3. `DaoDeJing_Mini.pdf` — `OMNIBUS / AGGREGATE_EXPORT`
Verified artifact: `DaoDeJing_Mini.pdf`.

Programmatic inspection shows that it is not a small standalone Dao De Jing line: it is a very large aggregate containing the Troncal material plus multiple applied Dao books/sections. It must therefore never be selected as the canonical Dao De Jing master based on filename alone.

Role: archival/aggregate export; useful for recovery and corpus mapping, not for canonical publication of the core Dao De Jing.

### 4. v4.0 DIGITAL — `REFERENCED_NOT_LOCATED`
The Canon references a v4.0 digital line, but an exact `v4.0_DIGITAL.pdf` artifact was not located in the current Library search. A v4.0 IMPRENTA artifact was located and inspected. They must not be conflated without file evidence.

## Canonical ordering
1. **Current editorial master candidate:** v4.0 IMPRENTA.
2. **Predecessor/source:** Edición Troncal Ampliada.
3. **Aggregate export:** DaoDeJing_Mini.
4. **Referenced but not verified exact file:** v4.0 DIGITAL.

## Required gates before `MASTER`
- locate/reconcile exact DIGITAL line if it exists;
- external sinological review;
- bibliographic and translation-source audit;
- final proofreading;
- ISBN/rights/metadata where publication requires them;
- print preflight and physical proof for print master;
- explicit promotion decision and rollback reference.

## ID policy
No new ARCHIVO TOTAL canonical ID is created by this reconciliation. Existing ID `CJGR-W000154` remains the reference candidate until the exact version relationship is resolved.
