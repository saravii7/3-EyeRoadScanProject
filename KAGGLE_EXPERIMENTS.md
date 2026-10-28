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


Install Python dependencies listed in `kaggle_requirements.txt` when needed. Exact runtime versions are recorded in saved notebook outputs and result JSON files. Kaggle paths must be adjusted for another environment. Do not re-split the data randomly or use the final local test set for tuning.


## External weights and attribution


Run 15 uses [SreekarAditya/yolo-rdd2022-benchmark](https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark), file `yolo-rdd2022-benchmark/yolov8s_seed0_best.pt`, published under CC BY 4.0 according to its model card. Credit the publisher and the RDD2022 dataset authors. The original model is not claimed as team-trained work.


Checkpoint SHA-256: `565aae6915e34e4f7f4c44dac0bdcf9fff21b83c4adc74cc97ca09cc31882ce8`.


Class IDs: 0 longitudinal_crack = D00; 1 transverse_crack = D10; 2 alligator_crack = D20; 3 pothole = D40.


The notebook contains the checkpoint download URL and verifies the digest before loading. Team-trained weights for run 14 are saved in its Kaggle output under `artifacts_team_v2/best.pt`. No dataset images or weight binaries are embedded in this export.



## Run 16 outcome and release preparation

Run 16 completed successfully in 39m 16s (17 epochs; best checkpoint at epoch 2, patience 15). It verifies every image hash against run 14 and reuses the same explicit optimizer, resolution, schedule and augmentation settings. Architecture and pretraining differ from run 14; external pretraining overlap is unknown. No personal photos or US images are evaluated.

Run 16 improves on run 14 but regresses against the original published checkpoint in run 15: mAP50 0.793760 vs 0.961963 and mAP50-95 0.446713 vs 0.671253. Keep the original checkpoint as a candidate; fine-tuning did not improve this diagnostic set. See [RUN16_COMPARISON.md](RUN16_COMPARISON.md) and [run-16 JSON](16-roadscan-rdd-finetuning-results.json). Validation-tuned image F1 is optimistic, not independent accuracy.

The saved run-16 Kaggle output contains both best weights in `release_v2_yolo/` and `v2_yolo_release_assets.zip`: `run14_yolo11s_best.pt`, `run16_yolov8s_rdd_best.pt`, JSON results and SHA-256 hashes. The intended GitHub release is `v2-yolo`; binary asset publication is pending transfer and must be verified separately. Confusion matrices and F1-confidence curves were confirmed in the completed output.

## Run 17 outcome

Run 17 completed successfully in 17m 43s (7 epochs; best epoch 2). It restarted from the original published checkpoint and preserved the frozen run-14 split. The gentle recipe raised mAP50-95 from run 16's 0.446713 to 0.657899, but did not exceed the original 0.671253 (-1.34 percentage points). The selected candidate is explicitly the original published checkpoint, not a training improvement. Image Macro-F1 at 0.5 is 0.962431; validation-tuned F1 is optimistic. No independent local generalization claim is supported because external pretraining overlap is unknown. See [RUN17_COMPARISON.md](RUN17_COMPARISON.md) and [run-17 JSON](17-roadscan-gentle-finetuning-results.json). Binary weights remain in the saved Kaggle output `run17_model_comparison/` and `run17_model_comparison.zip`.

To reproduce run 17, attach run 14 Version 1 outputs (361531048), enable GPU and Internet, and run the exported notebook. It verifies original checkpoint SHA-256, measures the unmodified checkpoint before training and keeps both original and fine-tuned weights.
