# E3: controlled augmentation ablation (run 20)

Status: launched on Kaggle; results are pending. This file does not claim experiment completion.

Saved run: https://www.kaggle.com/code/rimasabunasser/20-roadscan-e3-augmentation?scriptVersionId=363195760

| Arm | Mosaic | HSV h/s/v | Horizontal flip |
| --- | --- | --- | --- |
| all_on | 1.0 | 0.015 / 0.7 / 0.4 | 0.5 |
| no_mosaic | 0.0 | 0.015 / 0.7 / 0.4 | 0.5 |
| no_hsv | 1.0 | 0 / 0 / 0 | 0.5 |
| no_horizontal_flip | 1.0 | 0.015 / 0.7 / 0.4 | 0.0 |

All arms restart from the exact original published YOLOv8s RDD2022 weights (SHA-256 565aae6915e34e4f7f4c44dac0bdcf9fff21b83c4adc74cc97ca09cc31882ce8), with the frozen team split of 8,999 training and 1,977 China development images. Resolution 640, seed 42, batch 16, AdamW, lr0 and warmup_bias_lr 0.0001. Seven complete epochs per arm, no early stopping and no Mosaic closing. This new short control is rerun rather than compared directly against the historical run-17 schedule.

Primary endpoint: final-epoch detection mAP50-95. Secondary: mAP50 and per-class AP. Best checkpoints are retained but are not substituted for the fixed-horizon primary endpoint. Each ablation changes one augmentation group relative to the control. Other training settings remain fixed. This is a single-seed, short training study and does not estimate interactions or statistical significance. External pretraining overlap is unknown, so China scores remain development diagnostics.

The notebook saves per-arm metrics and checkpoints, then e3_comparison.csv, e3_per_class.csv, e3_results.json, e3_augmentation_comparison.png and E3_AUGMENTATION.md under artifacts_e3. English explanations precede code; actual result interpretations follow executed outputs. The final report discusses physically implausible road augmentations, including vertical flips.

The adopted run17_best_finetuned.pt and its frozen confidence 0.46 are unchanged. No US or local images are used. Model replacement is not automatic.

Attribution: published initialization SreekarAditya/yolo-rdd2022-benchmark (CC BY 4.0 according to publisher); RDD2022, Arya et al.; retain applicable Ultralytics terms.
