# AI Model Longevity / Automatic Model Refresh

## Simple explanation

AI providers eventually rename, deprecate, and retire models. This feature moves
model IDs into one registry instead of hard-coding them throughout the engine.

Every week, the system can check provider model catalogs. If the active model is
missing, deprecated, retired, or close to shutdown, it finds a replacement from
an approved model family.

A newer model is **not** trusted automatically. It must also pass the project's
quality/safety benchmark before a proposed registry update is created.

## Demo commands

```powershell
python -m pytest tests/test_model_registry.py -q
python scripts/demo_model_longevity.py
```

Expected result:

```text
7 passed
Cases passed: 7/7
```

## Architecture

```text
Provider model catalog
        |
        v
Lifecycle checker
        |
        +---- active/healthy ----> keep current model
        |
        +---- outdated ----------> approved replacement search
                                      |
                                      v
                              Week 4/5 benchmark gate
                                 |             |
                               FAIL           PASS
                                 |             |
                              keep old      proposal
                                               |
                                               v
                                      human-reviewed PR
```

## Live provider mode

When API keys are eventually configured:

```powershell
python scripts/check_model_lifecycle.py --live
```

OpenAI's model-list endpoint can expose model IDs and shutdown dates. Anthropic's
model-list endpoint exposes lifecycle states such as active, deprecated, and
retired.

## Technical explanation

The registry creates an abstraction between model identity and application logic.
Provider-specific lifecycle metadata is normalized into a common ModelRecord.
Candidate discovery is constrained to approved prefixes, reducing the risk that a
new but incompatible model type is selected. Promotion requires a passed benchmark,
and the previous model is retained in migration history for rollback/auditability.

The included fixture mode is deliberately deterministic so the feature can be
demonstrated without API keys. Live discovery still requires provider credentials,
and live replacement should be benchmarked before merging the proposed change.
