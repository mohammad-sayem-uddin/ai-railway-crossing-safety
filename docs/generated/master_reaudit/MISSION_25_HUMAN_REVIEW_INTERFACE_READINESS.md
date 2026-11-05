# Mission 25 — Human-review interface readiness

Prepared 2026-11-05, America/New_York. Metadata/software infrastructure only; no genuine reviewer, observation, adjudication, source access or promotion established.

The existing CLI now provides a bounded review-batch inspection interface:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application review interface
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application review demo --output /tmp/mission25-review --code-identity <40-character-producing-commit>
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application review verify --output /tmp/mission25-review
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application review dashboard --output /tmp/mission25-review
```

Use a new outside-checkout output directory. Dashboard exposes assignments, exact source/boundary observations, correction history, risk/comparison requirements, batch completeness and audit history. It is explicitly constructed. Immutable domain methods supply batch validation, assignment, sessions, observation/correction submission, completion, comparison, separate adjudication and receipt-validation contracts. No source player or arbitrary file intake is introduced.

Genuine mode, authenticated views, live database adapter and publisher remain disabled. Connect an independently governed EvidenceVerifier implementing fail-closed kind/subject-digest/reference/principal/time/scope/revocation verification; supply authenticated human submissions and canonical schema acceptance. Wire a neutral permitted source player preserving PTS/local clocks, disable candidate/comparison exposure during first pass, record later exposure and require independent qualified people at the selected triggers. Provide a durable authenticated journal/publication adapter with expected-prefix, idempotence and create-only semantics; do not reuse the constructed journal as a genuine service.

No browser or fake login is shipped. The existing command architecture supports fixture inspection; institutional identity integration, actual participant qualifications/consent, live usability acceptance and accessibility assessment require the real people and deployment context. These are explicit integration contracts, not missing researcher policy reselections.
