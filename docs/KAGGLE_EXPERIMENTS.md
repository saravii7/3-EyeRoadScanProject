# RoadScan Kaggle experiments


## Saved runs


- [14: team v2 controlled training, Version 1](https://www.kaggle.com/code/rimasabunasser/14-roadscan-team-v2-training?scriptVersionId=361531048)
- [15: published RDD2022 weights, Version 4](https://www.kaggle.com/code/rimasabunasser/15-roadscan-rdd-pretrained-yolov8s?scriptVersionId=361594990)


- [16: RDD2022 YOLOv8s fine-tuning, Version 1](https://www.kaggle.com/code/rimasabunasser/16-roadscan-rdd-finetuning?scriptVersionId=362759525)

- [17: gentle RDD2022 YOLOv8s fine-tuning, Version 1](https://www.kaggle.com/code/rimasabunasser/17-roadscan-gentle-finetuning?scriptVersionId=362779073)

The exported notebooks retain their original English explanations, executed outputs and result interpretations. Data and model binaries remain on Kaggle or the original model host.


| Run | Training provenance | China diagnostic/development mAP50 | mAP50-95 | Image Macro-F1 |
| --- | --- | --- | --- | --- |
| 14 | COCO-pretrained YOLO11s; exact 8,999-image team sample | 0.227095 | 0.087325 | 0.244475 at 0.5; 0.722955 after validation tuning |
| 15 | Externally trained YOLOv8s RDD2022 checkpoint; no additional training | 0.961963 | 0.671253 | 0.945031 at fixed 0.5 |
| 16 | Published RDD2022 YOLOv8s fine-tuned on the same 8,999 team images using run-14 explicit hyperparameters | 0.793760 | 0.446713 | 0.573603 at 0.5; 0.915322 after validation tuning |


| 17 | Original RDD2022 YOLOv8s; gentle recipe on the same 8,999 team images; lr0/warmup_bias_lr 0.0001, patience 5 | 0.959300 | 0.657899 | 0.962431 at 0.5; 0.980070 after validation tuning |

**These rows are not a controlled model comparison.** Run 14 trains on Japan/India/Czech and uses 1,977 China MotorBike images for development. Run 15 evaluates the same 1,977 images, but overlap with its external pretraining images has not been excluded. Its high scores do not establish unseen-country or Saudi-road generalization. Neither run evaluates local images; these remain reserved for the final frozen-model test. Run 14 stopped after 64 epochs; its best checkpoint was at epoch 49.


## Reproduce on Kaggle


For notebook 14, attach `sarvii7/roadscan-03-sample9000-v2` saved notebook output; this requires access to the team source. Enable a GPU. The notebook validates its exact 8,999 training and 1,977 validation images, trains, and evaluates. It may take several hours.


For notebook 15, attach the successful Version 1 output of `rimasabunasser/14-roadscan-team-v2-training`, preserving its `team_v2_data` and `artifacts_team_v2/manifest.csv` folders. Enable GPU and Internet. The notebook downloads the original checkpoint, validates its SHA-256 and semantic class order, then evaluates. It separately measures CPU prediction latency using a fresh CPU model instance.


Install Python dependencies listed in `../requirements.txt` when needed. Exact runtime versions are recorded in saved notebook outputs and result JSON files. Kaggle paths must be adjusted for another environment. Do not re-split the data randomly or use the final local test set for tuning.


## External weights and attribution


Run 15 uses [SreekarAditya/yolo-rdd2022-benchmark](https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark), file `yolo-rdd2022-benchmark/yolov8s_seed0_best.pt`, published under CC BY 4.0 according to its model card. Credit the publisher and the RDD2022 dataset authors. The original model is not claimed as team-trained work.


Checkpoint SHA-256: `565aae6915e34e4f7f4c44dac0bdcf9fff21b83c4adc74cc97ca09cc31882ce8`.


Class IDs: 0 longitudinal_crack = D00; 1 transverse_crack = D10; 2 alligator_crack = D20; 3 pothole = D40.


The notebook contains the checkpoint download URL and verifies the digest before loading. Team-trained weights for run 14 are saved in its Kaggle output under `artifacts_team_v2/best.pt`. No dataset images or weight binaries are embedded in this export.



## Run 16 outcome and release preparation

Run 16 completed successfully in 39m 16s (17 epochs; best checkpoint at epoch 2, patience 15). It verifies every image hash against run 14 and reuses the same explicit optimizer, resolution, schedule and augmentation settings. Architecture and pretraining differ from run 14; external pretraining overlap is unknown. No personal photos or US images are evaluated.

Run 16 improves on run 14 but regresses against the original published checkpoint in run 15: mAP50 0.793760 vs 0.961963 and mAP50-95 0.446713 vs 0.671253. Keep the original checkpoint as a candidate; fine-tuning did not improve this diagnostic set. See [RUN16_COMPARISON.md](reports/RUN16_COMPARISON.md) and [run-16 JSON](../results/run16/16-roadscan-rdd-finetuning-results.json). Validation-tuned image F1 is optimistic, not independent accuracy.

The saved run-16 Kaggle output contains both best weights in `release_v2_yolo/` and `v2_yolo_release_assets.zip`: `run14_yolo11s_best.pt`, `run16_yolov8s_rdd_best.pt`, JSON results and SHA-256 hashes. The team subsequently published the binary assets in GitHub release `v2-yolo`. Confusion matrices and F1-confidence curves were confirmed in the completed output.

## Run 17 outcome

Run 17 completed successfully in 17m 43s (7 epochs; best epoch 2). It restarted from the original published checkpoint and preserved the frozen run-14 split. The gentle recipe raised mAP50-95 from run 16's 0.446713 to 0.657899, but did not exceed the original 0.671253 (-1.34 percentage points). The historical automated selected candidate is the original published checkpoint. The team later adopted `run17_best_finetuned.pt`; see MODEL_SELECTION.md. This does not claim a training improvement. Image Macro-F1 at 0.5 is 0.962431; validation-tuned F1 is optimistic. No independent local generalization claim is supported because external pretraining overlap is unknown. See [RUN17_COMPARISON.md](reports/RUN17_COMPARISON.md) and [run-17 JSON](../results/run17/17-roadscan-gentle-finetuning-results.json). Binary weights remain in the saved Kaggle output `run17_model_comparison/` and `run17_model_comparison.zip`.

To reproduce run 17, attach run 14 Version 1 outputs (361531048), enable GPU and Internet, and run the exported notebook. It verifies original checkpoint SHA-256, measures the unmodified checkpoint before training and keeps both original and fine-tuned weights.

## Run 19: confidence frozen before local testing

[Saved run 19](https://www.kaggle.com/code/rimasabunasser/19-roadscan-confidence-selection?scriptVersionId=363182180) uses the adopted run-17 checkpoint and all 1,977 China validation images; no retraining, local or US testing. Confidence **0.46** was selected by predeclared box Macro-F1 optimization with pothole recall >=90% if feasible. The recall floor was met. Box Macro-F1 89.56%, micro precision 89.29%, micro recall 84.45%, pothole recall 96.60%. Default inference and model_config agree, with actual CPU verification. These are tuned development scores, not independent accuracy; see [THRESHOLD_SELECTION.md](reports/THRESHOLD_SELECTION.md).

## Run 20: completed E3 augmentation ablation

[Executed run 20, Version 1](https://www.kaggle.com/code/rimasabunasser/20-roadscan-e3-augmentation?scriptVersionId=363195760) completed successfully in 67m 27s. Four arms restart from the same original RDD2022 YOLOv8s weights and use the frozen 8,999/1,977 team split, seed 42, resolution 640 and seven fixed epochs. The primary endpoint is the final epoch, not each arm's best checkpoint. mAP50-95: all-on 0.653027, no Mosaic 0.645853, no HSV 0.652511, no horizontal flip 0.650502. Retain the current augmentation recipe; the 0.05-point HSV difference is not strong evidence from one seed. See [E3_AUGMENTATION.md](reports/E3_AUGMENTATION.md), e3_comparison.csv, e3_per_class.csv, e3_results.json and e3_augmentation_comparison.png. No US/local data or model replacement.

## Run 21: completed frozen-model country and error study

[Executed run 21, Version 1](https://www.kaggle.com/code/rimasabunasser/21-roadscan-country-error-analysis?scriptVersionId=363199933) completed successfully in 8m 23s using adopted run17_best_finetuned.pt at frozen confidence 0.46, resolution 640 and NMS IoU 0.7. Evaluated 8,281 images after excluding one exact duplicate: China 1,977; US 4,804; Japan/India/Czech 500 each. No training or threshold tuning. China development mAP50-95 0.657899 vs US 0.497268. US pothole recall is 43/135 = 31.85%, an unresolved generalization weakness.

**Post-run review:** the selected Czech complement contains no annotated damage boxes: AP/recall/F1 are N/A, not zero-performance estimates. Japan has two supported classes; India has only 42 labeled boxes. These complements are depleted of positives because the team training sample was enriched for damage. They do not represent country-wide prevalence or directly comparable four-class performance. External pretraining overlap and near-duplicates remain unresolved. Original outputs and raw JSON are retained, with an explicit post-run review appended to the exported notebook. Use [COUNTRY_ERROR_ANALYSIS.md](reports/COUNTRY_ERROR_ANALYSIS.md), country_error_reviewed.json and country_comparison.csv for conclusions. Country/per-class tables, error categories and five galleries are archived. Local independent evaluation is still pending; this does not complete the local part of E4 or all project experiments.


## YOLO closeout — 2026-11-01

Run17 fine-tuned remains adopted at confidence 0.46 /640. This update supersedes earlier pending-local notes, without rewriting historical results.

| Run | Work and outcome | Kaggle elapsed |
| --- | --- | --- |
| 22 | 190 local images /333 boxes /56 healthy; Run17 AP50 .262451 / AP50–95 .131487; P .5000 / R .174174 / F1 .258352 at .46. Run14: AP50 .320965 / AP50–95 .132172; P .611940 / R .123123. | Actual execution unknown;11s Quick save is not runtime |
| 23 | COCO YOLO11s native C2PSA vs YOLOv8s; China AP50–95 .088539 vs .070675. 45vs47 epochs;1.5h budget each. New11s selected only within new candidates, not over Run17. | 3h16m25s; training arms91.32/90.64min |
| 24 | Run17 960 continuation,10epochs; new960 AP50–95 .495591 vs reference17@640 .657899. final_weights.pt is copied reference17. | 1h8m7s; training about29.1min |
| 25 | Actual YOLO11m960 despite internal run24 names;39epochs; AP50–95 .101472@640 / .079107@960. No replacement. | 6h35m39s; training6.015h |
| 26 | USA tiling failed before scoring: missing RDD input / StopIteration. No tiling metrics. | 2m19s failed |
| 27 | Run23 on same local cohort: AP50 .242832 / AP50–95 .122501; at .46 P .711111 / R .096096 / F1 .169312. At predeclared .001:16740 FP and alarms on all56 healthy images. No training/tuning. | 3m31s |
| 28 | Executed Python journey covering03–27;18 charts, comparisons, runtimes and done/partial/failed register. Aggregate-only, no model execution. | Not a training experiment |

[Visual journey notebook](../notebooks/yolo/28-roadscan-yolo-journey-summary.ipynb) · [Closeout report](reports/YOLO_CLOSEOUT.md) · [Data, tables and figures](../results/run28/README.md). Source notebooks22–27 are under notebooks/yolo; Run22 personal-photo image outputs are omitted.

The190 local images were AI-assisted annotated, team-reviewed and already inspected/reused. These are diagnostic comparisons, not a fresh independent final holdout; new initialization does not erase prior exposure. External RDD training overlap remains unknown. E2 is partial, E3 is complete, attention is not causally isolated, Run26 failed, and WBF improvement has no completed saved result. E1/E5 and application checks have separate team evidence. Frozen Run17 settings remain unchanged.
