# YOLO closeout — 1 November 2026

[Executed journey notebook](../../notebooks/yolo/28-roadscan-yolo-journey-summary.ipynb): Arabic explanation before Python and interpretation afterward; runs03–27, 18 figures, comparison tables, times, decisions and unfinished items. [Standalone HTML](../../results/run28/roadscan_yolo_journey.html) can be downloaded and opened locally.

## Adopted model

Run17 fine-tuned remains adopted: `run17_best_finetuned.pt`; SHA256 `25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f`. Frozen confidence .46, imgsz640, NMS IoU .7, max_det300. D00/D10/D20/D40. Existing weights14/16/17 remain in release `v2-yolo`. No checkpoint or inference setting is replaced by this update.

| Local metric, same190 images /333 boxes /56 healthy | Run14 | Run17 adopted | Run23 new11s |
| --- | ---: | ---: | ---: |
| mAP50 | .320965 | .262451 | .242832 |
| mAP50–95 | .132172 | .131487 | .122501 |
| Precision @.46 | .611940 | .500000 | .711111 |
| Recall @.46 | .123123 | .174174 | .096096 |
| F1 @.46 | .205000 | .258352 | .169312 |
| TP / FP / FN | 41/26/292 | 58/58/275 | 32/13/301 |

Run17's D00/D10 misses are223/275. The local cohort was AI-assisted annotated, team-reviewed and already inspected/reused: diagnostic evidence, **not an untouched independent final holdout**. New model initialization does not erase exposure. No local training or threshold search is performed by this closeout. Low local recall remains unresolved; adoption is not a claim of readiness.

## Completed / partial / failed

Completed detector work: data/pilot diagnosis, team-v2 training, published-weight evaluation and fine-tuning, D-code helper verification, threshold freezing, confusion/F1 outputs, E3 four-arm augmentation, country/error analysis, local comparisons and new architecture/resolution alternatives. Run28 only analyzes saved aggregates.

E2 is partial: historical Nano/Small pilots plus23–25 provide evidence, but the full controlled Nano/Small ×640/960 grid on v2 was not completed. Run23 compares native C2PSA YOLO11s with YOLOv8s at1.5h each (45vs47 epochs); it is not a causal attention ablation. Run24 new960 AP50–95=.495591 did not beat Run17@640=.657899. Run25 is actually YOLO11m despite internal run24 names; AP50–95=.101472@640/.079107@960. `final_weights.pt` in24/25 is copied reference Run17.

Run26 failed with missing RDD input/StopIteration before tiling evaluation. No WBF improvement is evidenced. E1 needs matched classifier results; E5 and full app latency/privacy/end-to-end checks have separate team evidence and are not certified by detector-only testing.

## Interpretation limits

China development was repeatedly reused. Published RDD upstream overlap remains unknown. Country21 uses4,804 deduplicated US images; Run23 uses4,805, so do not pool them. Japan/India complements support only2 classes; Czech has no labeled boxes, so AP/recall/F1 are N/A. At Run23's predeclared .001 threshold, Run27 had16,740 FP and alarms on all56 healthy images. Lowering confidence is not a sufficient fix.

AP-curve precision/recall, fixed-confidence box micro metrics and image-level macro-F1 are different. Modern experiments lack repeated seeds. Kaggle durations include setup/evaluation; Quick saves are not training times. Unknown durations stay null. The notebook's known-event elapsed subtotal is not complete GPU billing or human effort.

## Evidence bundle

- [summary_data.json](../../results/run28/summary_data.json): exact aggregate snapshot embedded in notebook.
- [times.csv](../../results/run28/times.csv), [journey.csv](../../results/run28/journey.csv), [archive versions](../../results/run28/archive_version_inventory.csv).
- [historical output tables](../../results/run28/historical_output_tables.json):81 tables with original notebook/version identity.
- [source checksums](../../results/run28/notebook_export_manifest.json).
- `results/run28/run22_table_*.csv` through `run27_table_*.csv`: direct saved-output tables; display precision may be rounded.
- `results/run28/figure_01.png` through `figure_18.png`: aggregate charts; no personal photographs.
- `notebooks/yolo/22…27`: saved source and outputs; personal-photo image outputs omitted from22.

Source notebooks retain historical names/decisions. Keep original JSON history and read current model adoption separately. Attribute initialization to SreekarAditya/yolo-rdd2022-benchmark and data to RDD2022 authors; fine-tuning is the team's contribution, not a claim of training from scratch.
