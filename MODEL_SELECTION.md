# Adopted RoadScan model: run 17 fine-tuned

The team decision on 2026-10-28 is to use **run17_best_finetuned.pt** as the project model. This checkpoint was fine-tuned from published RDD2022 YOLOv8s weights on the frozen **8,999-image** team sample. The published checkpoint is retained for reference, with source attribution.

## Integration checkpoint

- Saved source: Kaggle run 17 Version 1 (362779073).
- Path: `run17_model_comparison/run17_best_finetuned.pt`.
- SHA-256: `25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f`.
- Use the explicit fine-tuned path in `INFERENCE_USAGE.md`; machine-readable metadata is in `model_config.json`.
- `selected_candidate.pt` in the historical Kaggle archive is the original published checkpoint. Its automated mAP-based choice predates the team decision. Do not silently substitute that file or rewrite the historical result.

## Actual integration verification

[Run 18 Version 2](https://www.kaggle.com/code/rimasabunasser/18-roadscan-inference-smoke?scriptVersionId=363150764) passed in **57.1 seconds** on CPU with **15 development images** and **44 detections**. All four codes D00/D10/D20/D40, original-image pixel boxes, confidence values and local-path/PIL-RGB/numpy-BGR input routes passed.

The exact detector module remained unchanged. Version 1 checks of the original reference remain archived separately. The current executed notebook and summary are `18-roadscan-inference-smoke-v2-run17.ipynb` and `18-roadscan-inference-smoke-v2-run17-results.json`.

## Engineering interpretation

Run 17 diagnostic validation mAP50-95 is 0.657899 versus the original 0.671253. Adoption is a documented team choice to use its fine-tuned model, not evidence that fine-tuning improved that metric. No additional training or final local testing occurred in this verification. External pretraining overlap remains unknown; independent local-road evaluation is still pending. Confidence 0.25 remains provisional.

The model binaries remain in Kaggle. Publication of the requested `v2-yolo` release is still pending binary transfer; this adoption update does not claim to publish weights.

Attribution: published initialization SreekarAditya / yolo-rdd2022-benchmark, publisher CC BY 4.0; RDD2022, Arya et al.; team sample Sara. Preserve applicable Ultralytics terms.
