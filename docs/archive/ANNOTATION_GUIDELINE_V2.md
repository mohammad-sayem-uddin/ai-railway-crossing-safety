# Annotation Guideline V2

## Vision Viewpoint Labels and Quality Assurance

**Status:** Proposed pending double-annotation pilot.  
**Purpose:** Produce consistent Layer A training labels and contextual Layer B visual labels. This guide does not assert that the three-class taxonomy is reliable; the pilot decides whether it is adequate.

## 1. Object and box policy

Annotate one bounding box around one continuous visible train target. Do not create a box per coach. The box should be reasonably tight around visible train pixels and must not deliberately include large unrelated scenery, sky, ground, grass, or track merely to capture distant coaches. A box may touch an image boundary when the train extends beyond the image.

Record whether the object is truncated, occluded, small/distant, abnormal geometry, or ambiguous. These flags are not new detection classes.

## 2. Viewpoint labels

| Label | Use when | Do not use when |
|---|---|---|
| `front` | The leading locomotive/head/nose is clearly identifiable facing the camera. Side visibility is allowed if the leading end is the dominant identifiable endpoint. | The end is not identifiable or the image only suggests travel direction. |
| `side` | Train is predominantly viewed from the side and neither front nor rear endpoint is the dominant identifiable viewpoint. | A clearly identifiable leading or final end dominates the visible target. |
| `rear` | The final coach/end is clearly identifiable facing the camera. Side visibility is allowed if the final end is the dominant identifiable endpoint. | The final end cannot be distinguished from a front/other coach end. |

Each object receives exactly one of these labels only when it meets the rules. Use `ambiguous` as an annotation-review disposition, not a fourth train-model class, until a documented research decision changes the taxonomy.

## 3. Decision rules for difficult cases

| Case | Rule |
|---|---|
| Front + side visible | Label `front` only if the leading end is clearly identifiable and dominant; otherwise `side` or review-ambiguous. |
| Rear + side visible | Label `rear` only if the final end is clearly identifiable and dominant; otherwise `side` or review-ambiguous. |
| Partial occlusion | Box only visible train extent; retain viewpoint only if endpoint evidence remains clear; otherwise review-ambiguous. |
| Truncation at image boundary | Box may touch boundary; do not infer endpoint identity from presumed off-frame content. |
| Multiple trains | Annotate each separable train with its own box/label and flag `multiple_trains`; exclude from initial single-train system ODD unless separately supported. |
| Overlapping trains | Annotate only separable targets; otherwise flag overlap/unusable according to review policy. |
| Very distant/small train | Annotate only when class and box can be assigned reliably under the stated minimum visible-pixel policy, which must be piloted; otherwise mark review/exclude. |
| Abnormal geometry | Flag it; do not force a viewpoint label based solely on assumed travel direction. |
| Ambiguous viewpoint | Do not guess. Send to review, record reason, and retain an `ambiguous` disposition. |

## 4. Negative and context images

Include explicitly labeled no-train images and hard negatives: empty tracks/crossings, buses/trucks, road vehicles, people, barriers, vegetation, rain/fog/night scenes, and visually train-like structures. A missing label file must not automatically mean a valid negative; use an explicit negative-image policy.

## 5. Annotation-quality study

Before full annotation:

1. Select a representative stratified subset across crossings, conditions, distances, and candidate viewpoints.
2. Have two annotators independently create labels/boxes without seeing one another’s labels or model outputs.
3. Match boxes using a predeclared IoU rule and calculate viewpoint agreement on matched targets; report confusion/disagreement matrix.
4. Report box agreement (IoU distribution) separately from viewpoint agreement.
5. Categorize disagreements: endpoint ambiguity, occlusion, truncation, small target, geometry, multiple train, box extent, or annotator error.
6. Adjudicate by a named reviewer using this guideline; retain original labels, adjudication rationale, and guideline version.
7. Decide whether taxonomy/collection quality is adequate before bulk annotation/training.

No unsupported numerical agreement threshold is imposed here; the research lead must set it after piloting and document the rationale.

## 6. Versioning and review

Every annotation export records source tool, export date, guideline version, class mapping, annotator/reviewer identifiers or pseudonyms, and QA status. Revisions create a new dataset version; do not overwrite labels used in reported experiments.
