# Mission 22 — Back-camera stateless comparator contract

Prepared 2026-11-05, America/New_York. Status: technical contract specified; activation blocked by one scientific definition. No comparator has been enabled.

`B0_back_stateless` is an adopted condition label in M19-METH-04/Mission20, not a complete class-to-command rule. The existing frozen stateful controller uses history. Copying its counter, dwell, clearance or class priority into a supposedly memoryless comparator would silently define a new scientific condition. The constructed camera orchestrator continues to reject this condition. `B0_back` remains the frozen stateful primary; back audio remains deferred.

## Input and representation

Each input is an explicitly constructed or separately authorized back-camera frame, qualified physical-event ID, `crossing_A`, exact native integer microseconds, retained original timestamp, frozen producer/config identity and full simultaneous vision detections. Front-camera, fused, audio and unknown-source inputs are outside this contract. Ground truth and synchronization offsets cannot alter input timestamps or commands.

The perceptual state is the complete presence mask over the producer's three frozen train classes (front/side/rear), after its already frozen confidence/filter rules. This has eight possible masks, including empty. Classifier classes do not prove physical travel direction. The record retains all detections and mask; input order within a simultaneous set cannot select an arbitrary winner.

There is no decision-history state: no confirmation count, EMA, dwell, last detected class, inferred passage phase or prior command in the decision function. An admission cursor may retain only the last accepted timestamp and request IDs to reject duplicate/out-of-order input. Physical actuator state remains separate from perceptual decision state.

## Single pending scientific definition: M22-COMP-MAPPING

The decision-maker must adopt or supply one complete frozen per-frame mapping contract: all eight presence masks to LOWER/RAISE/HOLD (or explicit unavailable), including conflict/tie treatment and absent, missing, stale or unknown observations. Include the exact producer/config references and explanation of the intended comparator interpretation. No particular entries of that table are adopted or guessed here. This is one definition decision with a complete table, not separate requests to reselect cameras, metrics or the condition label.

Formally, once that complete versioned mapping `F` is adopted, `command(t) = F(mask(t), explicitly classified availability(t))`. The same admitted input and frozen mapping must produce the same command independently of earlier detections. Missing decoding/evidence is distinguishable from a successfully observed empty mask. Until `F` is adopted, both states produce `UNAVAILABLE: COMPARATOR_MAPPING_NOT_ADOPTED`; they do not imply RAISE, HOLD, a clear crossing, zero M4 or zero M5.

## Transitions, ties, initialization and errors

Valid perceptual transitions are any mask to any mask because no previous mask is consulted. Simultaneous classes form one set; set ordering cannot break ties. Resolving conflicting classes belongs entirely to the pending mapping. No highest-confidence or class-priority default is supplied.

ARRIVAL admission rejects duplicate and decreasing timestamps with traceable request IDs and no command side effect. OFFLINE may only be explicitly selected under the existing stable-sort/prevalidation timing contract; it is never an automatic fallback. Invalid clock/source/schema or inconsistent frozen configuration refuses the run or marks an incomplete prefix under that contract; no absent evidence is imputed.

Initialization/reset clears the admission cursor and selects the adopted actuator initial angle90°, closing3s/opening3s. Actuation follows the already selected Convention B: old command advances to a boundary, new zero-latency command affects future positive intervals. HOLD can retain physical angle without making the decision function stateful. Reset does not supply missing mapping entries or scientific evidence.

Outputs must retain exact local time, mask/availability, mapping version/hash, command, applied command, angle and strict blocked≤45 separately. Determinism is conditional on the complete retained input/configuration/mapping. Missing mapping, unsupported availability state or unknown class refuses computable comparator outcomes with an explicit reason. A future implementation must test all eight masks, permutation invariance, no decision-history dependence, all availability cases, reset, timestamp admission and separation from actuator history before activation.

This specification preserves independent cameras, supporting-only audio, frozen primary policy, M4/M5 scope and deferred occupancy. It establishes no empirical comparator results, back-audio scope, model access or execution permission.
