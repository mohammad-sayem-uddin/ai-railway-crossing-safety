# Mission 37 neutral human-review execution handoff

**WORKING_TOOL_AND_PROCEDURE_PREPARED; NO_PERSON_APPOINTED; NO_ORIGINAL_PRESENTED; NO_REFERENCE_ACCEPTED.** Give the reviewer the reviewer instructions below and only the approved neutral player window. Keep this operator section, canonical source/cohort map, expected control/hard-case identities, legacy annotations and model outputs private. The researcher arranges actual people; the coding agent supplies no observations or signatures.

## Operator: one concrete viewing workflow

1. Obtain the actual named primary assignment/acceptance, existing competence/exposure/conflict/participation/access information and approval of this source-only method under AUTH35-P or the existing applicable process. Full canonical pilot activation remains distinct from a separately approved first-pass-only offline stage. Do not claim the offline stage already adopted. No repeat ownership/device declaration, new generic institution certificate or public-release permission is requested.
2. Privately bind the ten unchanged canonical source IDs/hashes/paths/video indices from [Mission36 integration](../mission36/AUTH35_V_EVIDENCE_INTEGRATION.md) to neutral display tokens, separately for each independent reviewer. Do not preassign obvious tokens that reveal case types. Keep internal IDs exact; do not rename/copy/transcode originals. Permit only assigned sources. Stop on actual identity discrepancy or withdrawn/expired access; do not repeat the completed AUTH35-V merely as paperwork.
3. Test and accept the actual local display and readable PTS overlay before real review. The project environment now includes PyAV 18.1.0 and OpenCV 5.0.0.93; future setup uses the `pts` extra. The following is an **operator-only recipe, not an invocation performed on originals by this mission**:

```sh
PYTHONPATH=src .venv/bin/python scripts/review_source_pts.py   --video "$APPROVED_SOURCE_PATH" --stream-index "$APPROVED_VIDEO_INDEX"   --token "$NEUTRAL_TOKEN"
```

Arguments and terminal are hidden from the reviewer. The operator fills these from the actual approved assignment. This command uses the existing raw-media guard; no flag in this package grants access or suppresses a refusal. Stream index is absolute, including index 1 where applicable. Visual B0 has no audio playback or model overlay. The window title contains only a neutral token; a separate readout band above the source pixels gives that token, decoded frame index, exact PTS, timebase and stream index. It covers no landmark and contains no file path, cohort, expected train/no-train answer, another rater's answers or model predictions. The window can be resized; the operator must establish readable timing text and sufficient visual detail on the actual display. Embedded visible source content itself is not erased; record actual unblinding/exposure if any.

4. Start with a paused actual frame. Keys: `n` next frame; `b` previous frame; `f` first frame at least one presentation-second forward (or actual final frame at EOF); `r` first frame at least one presentation-second backward, bounded at the real start; `q`/Escape exits. Refine candidate boundaries with n/b after coarse navigation. Backward navigation re-decodes from the beginning, which may be slow; it retains no image corpus. This is a manual frame browser, not a real-time playback or trusted clock service. Navigation times never become review-duration evidence. At EOF it keeps the final actual frame; that is not evidence of an unseen exit.
5. The actual person records the displayed exact frame/PTS/timebase and their own reasons/states in original-preserving private working notes with the existing observation fields below. Record actual session timing, tool/version, assignment/permission and source-token binding outside the blinded observation sheet. Capture real review_start_utc/review_end_utc and actual clock limits; never pad the 30-second plausibility floor or treat it as sufficiency. Do not infer a boundary from header start_pts=0. Do not retain/save rendered media unless separately permitted.
6. Seal each real independent pass before comparison: preserve original working notes and exact-source/assignment/session/method references, actual acknowledgement and a byte digest under the accepted retention method. A locally computed digest detects later changes; it does not authenticate identity or create immutable storage. No seal, signature, independently accepted service or real record is created by this mission. Keep actual corrections append-only with parent and reason.

## Reviewer: task and required observations

Inspect only the presented source and adopted visual landmarks. Record what is actually visible; there is no expected answer. T1 is approach danger-zone/frog-line timing; T3 locomotive-unit clearance; T4 final vehicle/tail clearance. T2 physical roadway entry and occupancy remain deferred; never substitute a camera/lens plane. T0/scene-clear and other assigned fields follow the existing protocol only where observable/applicable. Do not invent a new exit landmark or assume locomotive and tail clearance coincide. Use exact source-local PTS, not frame_index/FPS, rounded player seconds, another camera's clock or wall time.

| Actual observation | Existing representation and instruction |
|---|---|
| Visible adopted boundary | OBSERVABLE with source/camera, frame_index, original PTS/timebase, point and rationale |
| Train not observed in the available recording | Explain actual absence and observation window; mark corresponding train boundaries unobservable/not applicable with null values. Never copy an expected control label or assert absence outside the recording |
| Landmark hidden or visual ambiguity | UNCERTAIN with specific visibility/ambiguity reason; no forced point |
| Event precedes/follows recorded window | CENSORED with genuine LEFT/RIGHT direction retained in working evidence; no manufactured endpoint |
| Boundary inapplicable or not observable | Domain NOT_OBSERVABLE / canonical UNOBSERVABLE_NOT_APPLICABLE with explicit actual reason, keeping absence distinct from occlusion/deferral |

Use the existing domain Observation fields: `boundary, camera, state, rationale, value_us, censoring_direction, uncertainty_us, pts_ticks, timebase, origin_us, landmark`. Existing BoundaryObservation envelope: `observation_id, reviewer_id, source_id, boundary_version, observation, previous, correction_reason, acoustic_shift_us, landmark_kind, landmark_evidence, human_statement_reference`. No new field/schema is proposed. Keep actual integer PTS and rational timebase authoritative. Exact rational microseconds may not be integral: never round to force domain validation, change the timestamp or fabricate an origin. Preserve the exact working evidence and record an actual serialization incompatibility if it arises. These domain modules describe constructed governance contracts; their fixture identities/seals are not a genuine appointment or production intake route.

Active canonical **8.1.0-stage2.1** BoundaryAdjudication fields are `state, rationale, value_s, reference_camera, frame_index`. Point states use value_s from the accepted source-clock mapping; every nonpoint state keeps value_s null under current validation. Canonical fields do not directly store exact PTS/timebase, censor direction or uncertainty bounds. Retain them in the original source-linked working evidence and rationale, and bind that evidence in the actual accepted package; do not silently discard/rename them or claim lossless canonical serialization before it is demonstrated. A required unsupported representation stops affected acceptance, not the original observation. No schema patch is introduced here.

The canonical Stage21ReviewRecord envelope remains: `schema_version, review_id, event_id, cohort, proposal_reference, reviewer_metadata, model_independence_attestation, reviewer_observed_media_hashes, boundary_adjudications, adjudication_status, adjudication_history, supersedes, supersedes_sha256, supersedes_invalidation_reason, second_review_of`. Actual reviewer-observed hashes and proposal lineage are not prefilled from AUTH35-V. The existing build_review_record helper computes front/back hashes live and requires reviewer authorization and valid full records; do not run it on a partial front pass, expose model/proposal answers, or fabricate missing back observation. No early approval/promotion is implied.

## Independence, corrections and completion

Actual primary and physically distinct independent second reviewer need existing competence, explicit assignment/acceptance, scope and exposure/conflict disposition. Preserve the six existing second-review triggers: DISPUTED/NEEDS_SECOND_REVIEW; UNCERTAIN boundary; engine T3/T4 interpretation; front/back conflict; missing/inconsistent source hash; correction from a candidate. Keep the risk-based clear-boundary audit without a new fixed percentage. Source mismatch also stops access. Seal independent observations before comparison; do not average differences or invent tolerance. Actual disputes go to a separate qualified adjudicator with independent sealed parents at that stage. Full original canonical pilot retains its appointment/completion contract; a separately approved staged first pass does not waive independent review before reference-dependent comparison.

Corrections use previous/correction_reason in working envelopes and supersedes/sha256/invalidation_reason in active canonical records as applicable; preserve originals, invalidate stale descendants and document actual reasons. No acoustic time shift. Final acceptance checks complete assigned source/boundary coverage, actual neutral tool/clock/session/source/hash linkage, real independence/participation, uncertainty/censoring/null reasons, required second review and dispute disposition, actual retention/withdrawal and operation scope. Accepted reference evidence is separately promoted only when its existing applicable conditions hold. A completed worksheet or the browser itself is not accepted GT.

## Researcher input — actual people and method, left unfilled

Supply these actual inputs once, without passwords, raw uploads or repeated ownership declarations:

| Required input | Actual supplied value |
|---|---|
| Primary attributable identity, acceptance and exact assignment | |
| Primary relevant boundary/tool competence and exposure/conflict disposition | |
| Distinct second identity, acceptance, qualification, independence and exact scope | |
| Separate adjudicator assignment/acceptance when required by chosen stage | |
| Actual source-use method choice/approval, operator, sources, viewer/version and native display acceptance | |
| Source-access scope/validity/withdrawal and any actual applicable participation/site/privacy conditions | |
| Actual clock/session method, private original-preserving record location and acknowledgement/seal method | |

Then the actual people perform the approved source-only work. Model permission/engineering is separate from reviewer acceptance; reviewers do not approve unrelated model work. Publication/raw release and optional external auditor are not universal private-review prerequisites.
