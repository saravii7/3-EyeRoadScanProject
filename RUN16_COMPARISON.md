# Run 16: results and decision

Run 16 version 1 completed successfully in 2,355.9 seconds (39m 16s). Early stopping ended training after 17 epochs, with the best trained checkpoint at epoch 2 (patience 15).

All runs below were evaluated on the same 1,977 China MotorBike images. Metrics describe this validation/diagnostic set; external RDD2022 pretraining overlap has not been excluded.

| Run | Pipeline | mAP50 | mAP50-95 | Image Macro-F1 at 0.5 |
| --- | --- | ---: | ---: | ---: |
| 14 | YOLO11s, COCO initialization, team v2 training | 0.227095 | 0.087325 | 0.244475 |
| 15 | Published RDD2022 YOLOv8s, no additional training | 0.961963 | 0.671253 | 0.945031 |
| 16 | Same published YOLOv8s checkpoint, fine-tuned on 8,999 team v2 images using run-14 settings | 0.793760 | 0.446713 | 0.573603 |

Run 16 improves over run 14 by 56.67 percentage points in mAP50 and 35.94 points in mAP50-95. Run 16 regresses against its starting published checkpoint (run 15) by 16.82 points in mAP50 and 22.45 points in mAP50-95. The validation-tuned image Macro-F1 for run 16 is 0.915322; it is optimistic because thresholds were selected on the same validation set and is not the fixed-threshold result.

## Engineering decision

Preserve run 16 as a completed experiment, but do not replace the original published checkpoint based on these scores: additional training did not improve this diagnostic evaluation. Keep run 15 as a candidate and run 16 as a comparison until an independent labeled evaluation supports a final choice. Comparing run 14 with run 16 changes both architecture and pretraining; the result cannot isolate either factor. No claim of Saudi-road generalization or absence of overfitting follows from this table.

Confusion matrices and F1-versus-confidence curves were confirmed in the completed run-16 output. Personal photos and US images were not opened by run 16. E2 and E3 remain separate development experiments, followed by a frozen-model independent local test.

## Saved sources

- Run 14: https://www.kaggle.com/code/rimasabunasser/14-roadscan-team-v2-training?scriptVersionId=361531048
- Run 15: https://www.kaggle.com/code/rimasabunasser/15-roadscan-rdd-pretrained-yolov8s?scriptVersionId=361594990
- Run 16: https://www.kaggle.com/code/rimasabunasser/16-roadscan-rdd-finetuning?scriptVersionId=362759525
- Published initialization: SreekarAditya, https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark (publisher CC BY 4.0); dataset attribution: RDD2022, Arya et al., CC BY 4.0.

## Release assets

The saved Kaggle output contains `v2_yolo_release_assets.zip` and `release_v2_yolo/`, including `run14_yolo11s_best.pt`, `run16_yolov8s_rdd_best.pt`, both JSON results and SHA-256 hashes. GitHub release asset publication must be verified separately; successful Kaggle packaging alone does not mean the release is published.
