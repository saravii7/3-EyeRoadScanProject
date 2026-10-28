# Run 17 handoff: fine-tuned weights and plots

Use **run17_best_finetuned.pt** for the team request for the trained run-17 checkpoint. Do not substitute **selected_candidate.pt**: run 17 retained the original published checkpoint after comparing diagnostic validation mAP50-95. The inference smoke test in run 18 verified that original selected candidate; it did not verify the run-17 fine-tuned checkpoint.

## Saved Kaggle source

[Run 17 Version 1 output](https://www.kaggle.com/code/rimasabunasser/17-roadscan-gentle-finetuning/output?scriptVersionId=362779073)

- Download `run17_model_comparison.zip` (62.26 MB) for the complete existing comparison package.
- The fine-tuned checkpoint is `run17_model_comparison/run17_best_finetuned.pt` (22.52 MB), also copied as `artifacts_run17/best.pt`.
- Original and selected candidate checkpoints are separate files inside the package.
- The ZIP does not include the evaluation plots. They are provided separately here.

Verified from the rendered saved `SHA256.json`: fine-tuned run-17 SHA-256 is `25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f`; original/selected SHA-256 is `565aae6915e34e4f7f4c44dac0bdcf9fff21b83c4adc74cc97ca09cc31882ce8`.

## Original run-17 plots

| File in this repository | Original saved Kaggle path |
| --- | --- |
| [run17_confusion_matrix.png](run17_confusion_matrix.png) | `evaluation_run17/china_development/confusion_matrix.png` |
| [run17_F1_curve.png](run17_F1_curve.png) | `evaluation_run17/china_development/BoxF1_curve.png` |
| [run17_results.png](run17_results.png) | `artifacts_run17/results.png` |

The F1 image is the actual **BoxF1_curve.png**, copied unchanged under the requested F1 naming convention; it is the bounding-box confidence curve, not image-level Macro-F1. The confusion matrix and F1 curve come from final evaluation of run-17 best fine-tuned weights. `results.png` contains the training history from the same run. These are original exported PNG bytes, not recreated plots.

## Pending v2-yolo release

The requested release should include actual binary files, with clear run names:

- `run14_yolo11s_best.pt`: saved in run 16 `release_v2_yolo/`.
- `run16_yolov8s_rdd_best.pt`: saved in run 16 `release_v2_yolo/`.
- `run17_yolov8s_rdd_best.pt`: copy of run 17 `run17_model_comparison/run17_best_finetuned.pt`.

Keep model attribution, per-run result JSON and SHA-256 hashes. Run-16 output also has `v2_yolo_release_assets.zip` containing the first two checkpoints.

**Publication status: not published.** The Kaggle ZIP and individual checkpoint download controls did not start a transfer in the current browser session. Images were retrieved successfully from their previews. This handoff does not claim that model binaries were downloaded or uploaded to GitHub. Finish binary transfer and verify the three release assets before marking the release task complete.

Run-17 fine-tuned diagnostic metrics: mAP50 0.959300, mAP50-95 0.657899. External pretraining overlap is unknown; these scores do not establish independent Saudi-road generalization. Preserve SreekarAditya / yolo-rdd2022-benchmark and RDD2022 (Arya et al.) attribution and applicable Ultralytics terms.
