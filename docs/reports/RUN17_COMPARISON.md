# Run 17: gentle fine-tuning results

Run 17 restarted from the original published YOLOv8s RDD2022 seed-0 checkpoint, not the regressed run-16 weights. It preserved the exact 8,999 team-v2 training images and 1,977 China MotorBike validation images from run 14. All image hashes and the training manifest matched.

Compared with run 16, lr0 and warmup_bias_lr were set to 0.0001, patience to 5 and the epoch-boundary training budget to 30 minutes. Resolution 640, batch 16, seed 42, AdamW and augmentations were retained. This is a recipe pilot, not a single-variable E3 ablation. Training completed 7 epochs; best epoch was 2; total notebook runtime was 17m 43s.

| Candidate | Detection mAP50 | Detection mAP50-95 |
| --- | ---: | ---: |
| Original published checkpoint (15) | 0.961963 | 0.671253 |
| Run 16 fine-tuned | 0.793760 | 0.446713 |
| Run 17 gentle fine-tuned | 0.959300 | 0.657899 |

Run 17 improves over run 16 by 21.12 percentage points in mAP50-95, but remains 1.34 points below the original. The saved selection therefore retains the original as a candidate. Its score must not be presented as a fine-tuning gain.

| Run-17 metric | Value |
| --- | ---: |
| Detection precision | 0.917367 |
| Detection recall | 0.925576 |
| Image Macro-F1, fixed confidence 0.5 | 0.962431 |
| Image Macro-F1, validation-tuned (optimistic) | 0.980070 |
| CPU median seconds/image | 0.190736 |
| CPU p95 seconds/image | 0.194863 |

Detection metrics evaluate class and bounding-box localization. Image metrics evaluate class presence regardless of box location; they are not interchangeable. CPU latency uses 20 images, 3 warm-ups and 2 threads, and excludes the full application.

## Per-class detection

| Class | AP50 | AP50-95 |
| --- | ---: | ---: |
| D00 | 0.940279 | 0.662192 |
| D10 | 0.929384 | 0.603965 |
| D20 | 0.981268 | 0.733816 |
| D40 | 0.986269 | 0.631623 |

## Image presence at confidence 0.5

| Class | Precision | Recall | F1 | AUROC |
| --- | ---: | ---: | ---: | ---: |
| D00 | 0.996995 | 0.935166 | 0.965091 | 0.997893 |
| D10 | 0.987823 | 0.879404 | 0.930466 | 0.996199 |
| D20 | 0.957576 | 0.975309 | 0.966361 | 0.998258 |
| D40 | 0.987805 | 0.987805 | 0.987805 | 0.999657 |

## Interpretation and limitations

The metrics are promising on this development set, but external pretraining overlap is unknown. China selected the best epoch and tuned image thresholds; these are diagnostic results, not independent accuracy or evidence of Saudi-road generalization. No US or personal-photo evaluation was run. Freeze the final recipe before an independently collected, labeled local test.

The original, fine-tuned and selected checkpoints remain in the saved Kaggle output under `run17_model_comparison/`, alongside `run17_results.json`, `selection.json` and `SHA256.json`; the archive is `run17_model_comparison.zip`. This GitHub export contains the executed notebook, results and documentation, not binary weights or dataset images. The pending run-14/run-16 `v2-yolo` release remains separate.

Published initialization: [SreekarAditya/yolo-rdd2022-benchmark](https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark), publisher CC BY 4.0; dataset RDD2022, Arya et al.; team sample Sara. Preserve attribution and applicable Ultralytics terms.

[Saved Kaggle run 17, Version 1](https://www.kaggle.com/code/rimasabunasser/17-roadscan-gentle-finetuning?scriptVersionId=362779073).
