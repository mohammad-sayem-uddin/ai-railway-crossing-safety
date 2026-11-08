# Mission 18A-R2 — Researcher selection and adoption record

**Documentation task: COMPLETE. Selection status: SUBMITTED — AUTHORITY UNVERIFIED. Formal adoption: NOT_ADOPTED_PENDING_AUTHORITY_VERIFICATION. Mission 18A: BLOCKED.**

Repository baseline: `46ed0d6999cb04ce7be6d48bc2b3476641f86b94`, branch `main`. Scope is documentation and authorization verification only. The current instruction explicitly prohibits implementation and Mission 18B.

## Original user-originated statement

Source: the user message in this conversation headed **“MISSION 18A-R2 — Record Researcher Selection of All 14 Option A Decisions”**. The following statement and selection are copied verbatim from that message:

```text
The researcher has explicitly selected Option A for all 14 decisions in the Mission 18A-R decision packet:

R01=A, R02=A, R03=A, R04=A, R05=A, R06=A, R07=A, R08=A, R09=A, R10=A, R11=A, R12=A, R13=A, R14=A.
```

The same user instruction states:

> Do not start Mission 18A implementation or Mission 18B.

The selection is verified as user-originated conversational content. The assertion that it is the researcher's selection is preserved as submitted; it does not independently identify or authenticate that researcher.

## Recorded choices

Exact option wording and detailed scope remain in the [18A-R decision packet](MISSION_18A_R_RESEARCHER_DECISION_PREPARATION.md). Its R01–R14 definition sections, including all options and recommendations, are unchanged. The labels below are an index, not replacement definitions.

| Packet decision | Submitted choice | Subject | Decision status |
|---|---|---|---|
| 18A-R/R01 | A | Explicit B entrypoint on the existing runner | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R02 | A | Exact bounded source/test/report scope | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R03 | A | Exact synthetic clock and checked frame time | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R04 | A | ARRIVAL primary; explicitly selected OFFLINE support | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R05 | A | Existing zero-latency forward-causal command semantics | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R06 | A | 90° initial angle; 3s closing/opening baseline | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R07 | A | Separate event, continuous and optional fixed-grid estimates | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R08 | A | NONE watchdog for the integrated baseline | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R09 | A | Last accepted input/default horizon, optional cutoff, diagnostic prefixes | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R10 | A | Preserve A and return a separate B result | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R11 | A | Current controller on constructed evidence with native rejections | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R12 | A | Input/settings snapshots and full detached-result replay verification | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R13 | A | Full selected synthetic acceptance and bounded workload | SUBMITTED — AUTHORITY UNVERIFIED |
| 18A-R/R14 | A | Limited synthetic-stage disposition with type analysis unresolved | SUBMITTED — AUTHORITY UNVERIFIED |

Consistency anchor: SHA256 **`04b9aad7928ea85319097c972792bbf71582283194f8a82194e583c55f7dae66`** over the packet's exact UTF-8 substring starting at `## R01 —` and ending immediately before `## Coverage of the blockers`. This records the unchanged definitions; it is not a signature, authenticated approval or evidence of researcher authority.

## Provenance and adoption verification

| Field | What is genuinely supplied or verified |
|---|---|
| Submitter/source | User message in the current conversation, referenced by its actual mission heading above |
| Claimed decision origin | The user states that “The researcher” selected all A options; preserved without substituting a named person |
| Named original decision-maker | NOT SUPPLIED / NOT VERIFIED |
| Project role, authority or applicable delegation | NOT SUPPLIED / NOT VERIFIED for this statement |
| Original decision date/time | NOT SUPPLIED; not inferred from the packet's preparation date, current date, Git timestamps or filesystem metadata |
| Original source reference | This conversation and the actual user-message heading are available; no external decision reference or immutable message identifier was supplied |
| PI approval, signature or external authorization | None supplied or verified for this selection; none created |
| R14 limited-stage disposition | A was explicitly selected; authority/adoption is unverified, so this is not an effective verified type-analysis waiver |
| Implementation permission | Not granted by this mission; the user explicitly prohibits implementation |

Process inspected: `docs/RESEARCH_DECISIONS.md` specifies decision/date/reason/alternatives/evidence/status/reconsideration fields and preservation of historical records. The historical [17A approval register](MISSION_17A_PI_APPROVAL_REGISTER.md), [17C3 release gate](MISSION_17C3_RESEARCHER_DECISION_AND_RELEASE_GATE.md), [17E checklist](MISSION_17E_RESEARCHER_RELEASE_GATE_CHECKLIST.md) and [17I dependency register](MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md) distinguish scoped decisions, genuine authority/adoption and execution. Their broader approvals are not established by this submission. The tracked legacy governance authorization has a different bounded legacy-notice scope and no reference to 18A or Convention B; it provides no authority for this selection. That protected record was not modified.

Mapped to the existing decision-log format: **DATE** not supplied; **DECISION** the exact all-A submission above; **REASON** recording is explicitly requested by the user, while no new researcher rationale beyond the packet is claimed; **ALTERNATIVES** the unchanged packet's options; **EVIDENCE** the quoted user statement and unchanged definitions; **STATUS** Under Review, specifically SUBMITTED — AUTHORITY UNVERIFIED; **RECONSIDERATION** a genuine correction/superseding researcher statement or verified authority/adoption evidence. This is a scoped documentation record, not an amendment of scientific protocols or the protected governance store.

## Remaining authorization blockers

1. Establish the actual original decision-maker and their applicable project authority or genuine delegation, with evidence linking that person to this submitted statement. A user account, filesystem name, Git author or a PI named in an older register does not establish that link.
2. Complete the scoped adoption provenance from genuine source evidence, including the actual decision date if available or an explicitly unresolved date under the accepted process. Preserve the current conversation as the available submission reference; do not fabricate an external reference, signature or timestamp. Adoption must bind the unchanged all-A definitions and bounded scope.
3. Keep execution paused: this mission is documentation/verification only. Even if authority is later established, implementation requires a later explicit instruction consistent with the adopted scope. Mission 18B remains outside it.

No option selection is missing. Do not ask for R01–R14 to be chosen again. No new signing scheme, authorization token, identity infrastructure or unrelated real-resource permission is imposed by this record. If the required authority evidence is unavailable, retain the submitted choices and BLOCKED disposition.

## Documentation delivery and preservation

Updated the choice/status portions of the [decision packet](MISSION_18A_R_RESEARCHER_DECISION_PREPARATION.md), the [18A blocker report](MISSION_18A_CONVENTION_B_SYNTHETIC_INTEGRATION_REPORT.md) and [acceptance record](MISSION_18A_INTEGRATION_ACCEPTANCE_RECORD.md); appended a scoped R2 update to the [17I dependency register](MISSION_17I_MISSION18_ACCEPTANCE_AND_DEPENDENCY_REGISTER.md). Earlier register content and all option definitions are preserved. These local 18A-R IDs do not supersede the older R01–R08 scientific/governance IDs or approve their broader subjects.

No implementation, test, scientific protocol, protected record, permission list or dependency was modified. No runtime test, protected operation, staging, commit or push was performed. Existing local work is preserved. The all-A submission is recorded; verified adoption and implementation acceptance remain outstanding.
