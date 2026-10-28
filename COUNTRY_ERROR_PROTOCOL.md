# Run 21: frozen-model country comparison and error analysis

Status: launched; results pending. Do not mark the analysis complete until the notebook emits COUNTRY_ERROR_ANALYSIS_COMPLETE.

Saved Kaggle version: https://www.kaggle.com/code/rimasabunasser/21-roadscan-country-error-analysis?scriptVersionId=363199933

Use the exact adopted run17_best_finetuned.pt (SHA-256 25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f), confidence 0.46, resolution 640, NMS IoU 0.7, max_det 300. No retraining or threshold tuning. No local photos.

| Country | Evaluation role | Selection |
| --- | --- | --- |
| China MotorBike | Reused development validation, previously used for threshold selection | Original 1,977 images, exact hashes audited |
| United States | Country excluded from run-17 fine-tuning; evaluated now with frozen settings | Available labeled US test images after exact duplicate exclusion |
| Japan / India / Czech | Images outside the exact fine-tuning sample, countries represented in fine-tuning | Up to 500 per country, deterministic filename-hash order before predictions, if available |

Exclude fine-tuning filenames and SHA-256 image hashes. Exclude exact duplicates within evaluation. Near-duplicate frames and route overlap remain unresolved because verified drive IDs/GPS are unavailable. External checkpoint pretraining overlap is unknown for every country. Do not claim guaranteed unseen-country exposure or independent Saudi accuracy.

Report official detection mAP50 and mAP50-95 at confidence floor 0.001, plus documented same-class greedy one-to-one box precision, recall and F1 at the frozen confidence 0.46 and matching IoU 0.5. Report class support and per-class results; absent classes have undefined recall/F1, and country Macro-F1 excludes unsupported classes. Different country mixtures make aggregate gaps descriptive, not causal effects.

Save cohort manifests, image/label hashes, exclusions, per-image counts, per-box error records, geometric error categories, country and per-class tables, a comparison chart, and high-error review galleries. Error categories are review candidates, not verified visual causes. English explanations precede code and real interpretations follow outputs. The adopted model remains unchanged; independent local testing is pending.

Attribution: RDD2022, Arya et al.; team YOLO conversion Sara; published initialization SreekarAditya/yolo-rdd2022-benchmark (CC BY 4.0 according to publisher). Preserve applicable Ultralytics terms.
