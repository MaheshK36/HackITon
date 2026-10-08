# ML validation report

## Result

No integrated trained model is enabled. No ML performance values are reported for this platform.

## Evidence

The integrated model loader has no committed compatible checkpoint in `models/checkpoints`, no preprocessing artifact, no dataset version manifest and no training/evaluation metadata. Existing model/result artifacts in sibling research projects are not automatically valid for this service.

## Leakage audit

The live service does not train or evaluate a model, so no integrated train/test metric can be claimed. The audit identified hard-coded/synthetic IP generation in several `attack model` dataset scripts and duplicate research pipelines; these must not be used as validation evidence. The `network model` area contains useful time-aware/leakage research utilities, but it is not currently the serving pipeline.

## Required before enabling ML

Register a model with feature schema, preprocessing version, dataset/version/hash, temporal split policy, training timestamp, calibration metrics and held-out precision/recall/F1/ROC-AUC/PR-AUC/FPR/lead-time evidence. Reject incompatible artifacts at startup.
