# Adopted RoadScan model: run 17 fine-tuned

The team decision on 2026-10-28 is to use **run17_best_finetuned.pt** as the project model. This checkpoint was fine-tuned from published RDD2022 YOLOv8s weights on the frozen **8,999-image** team sample. The published checkpoint is retained for reference, with source attribution.

## Integration checkpoint

- Saved source: Kaggle run 17 Version 1 (362779073).
- Path: `run17_model_comparison/run17_best_finetuned.pt`.
- SHA-256: `25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f`.
- Use the explicit fine-tuned path in `INFERENCE_USAGE.md`; machine-readable metadata is in `../configs/model_config.json`.
- `selected_candidate.pt` in the historical Kaggle archive is the original published checkpoint. Its automated mAP-based choice predates the team decision. Do not silently substitute that file or rewrite the historical result.

## Actual integration verification

[Run 18 Version 2](https://www.kaggle.com/code/rimasabunasser/18-roadscan-inference-smoke?scriptVersionId=363150764) passed in **57.1 seconds** on CPU with **15 development images** and **44 detections**. All four codes D00/D10/D20/D40, original-image pixel boxes, confidence values and local-path/PIL-RGB/numpy-BGR input routes passed.

The exact detector module remained unchanged. Version 1 checks of the original reference remain archived separately. The current executed notebook and summary are `../notebooks/yolo/18-roadscan-inference-smoke-v2-run17.ipynb` and `../results/run18/18-roadscan-inference-smoke-v2-run17-results.json`.

## Engineering interpretation

Run 17 diagnostic validation mAP50-95 is 0.657899 versus the original 0.671253. Adoption is a documented team choice to use its fine-tuned model, not evidence that fine-tuning improved that metric. No additional training or final local testing occurred in this verification. External pretraining overlap remains unknown; independent local-road evaluation is still pending. Confidence 0.46 is now frozen on China development validation; see [THRESHOLD_SELECTION.md](reports/THRESHOLD_SELECTION.md).

The model binaries remain in Kaggle. The team published the weights as [v2-yolo](https://github.com/saravii7/3-EyeRoadScanProject/releases/tag/v2-yolo). The original tag/source archive predates confidence freezing; use the current configuration and detector supplied with the threshold update.

Attribution: published initialization SreekarAditya / yolo-rdd2022-benchmark, publisher CC BY 4.0; RDD2022, Arya et al.; team sample Sara. Preserve applicable Ultralytics terms.

## Frozen-country evaluation outcome (run 21)

The adopted checkpoint and confidence 0.46 remain unchanged. US was excluded from our run-17 fine-tuning, but external pretraining overlap is unknown. On 4,804 US images, mAP50 is 0.764357, mAP50-95 is 0.497268, and pothole recall is only **43/135 = 31.85%** at the frozen threshold. This is an unresolved failure case, not validated local-road readiness. Do not silently tune on these now-inspected US test results. See [COUNTRY_ERROR_ANALYSIS.md](reports/COUNTRY_ERROR_ANALYSIS.md) for reviewed cohort limits, per-class results and error examples. Independent labeled local evaluation remains pending.

Run 20 completed the E3 augmentation study. Retain the current recipe; no new checkpoint is adopted from that single-seed seven-epoch experiment.


## YOLO closeout update — 2026-11-01

Run17 fine-tuned remains the explicit team-adopted checkpoint: run17_best_finetuned.pt, SHA256 25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f; imgsz640, confidence0.46, NMS IoU0.7, max_det300. No new candidate replaces it. Run23 selected new11s only among its new candidates; final_weights.pt in24/25 is a reference Run17 copy.

Local evaluation is now completed on the previously inspected/reused190-image cohort, not a fresh independent holdout. Run17 at.46: AP50 .262451, AP50–95 .131487, precision .500000, recall .174174, F1 .258352;58TP/58FP/275FN. Low local recall remains unresolved. New initialization cannot reset exposure. Earlier pending-local notes describe their historical state.

[Executed visual journey](../notebooks/yolo/28-roadscan-yolo-journey-summary.ipynb) · [Closeout report](reports/YOLO_CLOSEOUT.md) · [Aggregate evidence](../results/run28/README.md). This summary performs no model execution, retraining or local threshold search and does not change model_config.json.
