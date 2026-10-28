# Frozen confidence for the adopted run-17 model

Confidence **0.46** is frozen on **1,977 China MotorBike development images** before the independent local test. Checkpoint: `run17_best_finetuned.pt`, SHA-256 `25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f`. Resolution 640, class-aware NMS IoU 0.7, max_det 300. Matching IoU for threshold evaluation: 0.5.

Policy declared before evaluation: maximize unweighted mean box F1 across D00/D10/D20/D40 among candidate thresholds with pothole recall >=90%, if feasible. Grid: 0.001 plus 0.01 through 0.95. Ties favor higher pothole recall, then higher confidence. If infeasible, prioritize maximum pothole recall then Macro-F1 and explicitly report that the floor was not met. **Recall floor met: True.** The 90% target is an engineering criterion, not a local-road guarantee.

| Metric | Previous confidence 0.25 | Frozen confidence 0.46 |
| --- | ---: | ---: |
| Box Macro-F1 | 86.27% | 89.56% |
| Micro precision | 75.30% | 89.29% |
| Micro recall | 92.62% | 84.45% |
| Pothole precision | 87.69% | 94.19% |
| Pothole recall | 97.02% | 96.60% |
| False positives | 1413 | 471 |
| False negatives | 343 | 723 |

## Per-class results at the frozen operating point

| Class | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| D00 | 2215 | 270 | 463 | 89.13% | 82.71% | 85.80% |
| D10 | 869 | 140 | 227 | 86.12% | 79.29% | 82.57% |
| D20 | 616 | 47 | 25 | 92.91% | 96.10% | 94.48% |
| D40 | 227 | 14 | 8 | 94.19% | 96.60% | 95.38% |

## Evaluation protocol and practical limits

Predictions were collected once above confidence 0.001 with fixed NMS. For each image, descending-confidence predictions were matched greedily to the best remaining same-class ground-truth box at IoU >=0.5. A label is matched once; duplicate/wrong-class detections are false positives and unmatched labels are false negatives. Synthetic cases checked duplicates, class mismatch, backgrounds and IoU before the full run. This documented operating-point evaluator is not the official mAP evaluator and is not image-level presence F1. Threshold selection does not improve or change saved run-17 mAP values.

The default in `roadscan_detector.py` and the configuration agree. Actual CPU inference on the adopted checkpoint verified that default-confidence and explicit-confidence outputs are identical. Do not keep passing `confidence=0.25` from an old application call: use the frozen configuration or the new default.

No weights were retrained, and no local or US test images were opened. These scores were tuned on the same development set and are optimistic; external pretraining overlap is unknown. Freeze the checkpoint, preprocessing, resolution, NMS and confidence before final independent local evaluation. If the final test exposes a failure, report it; do not tune on those same test images and present the result as untouched testing.

Model initialization attribution: SreekarAditya / yolo-rdd2022-benchmark; dataset RDD2022, Arya et al.; preserve publisher CC BY 4.0 attribution and applicable Ultralytics terms.

[Executed Kaggle experiment 19](https://www.kaggle.com/code/rimasabunasser/19-roadscan-confidence-selection?scriptVersionId=363182180). Full sweep and matched detections are saved under `threshold_run17/` in Kaggle.
