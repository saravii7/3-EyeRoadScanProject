# Run 21: reviewed country comparison and error analysis

Completed Kaggle run 21 Version 1 (363199933). The original executed outputs and raw JSON are preserved. **Use this reviewed report, country_comparison.csv and country_error_reviewed.json for conclusions.**

| Country | Images | Labeled boxes | Supported classes | mAP50 | mAP50-95 | Micro-F1 at 0.46 | Pothole recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| China_MotorBike | 1977 | 4650 | 4 | 95.93% | 65.79% | 86.80% | 96.60% |
| United_States | 4804 | 11010 | 4 | 76.44% | 49.73% | 76.05% | 31.85% |
| Japan | 500 | 479 | 2 | 82.28% | 50.53% | 72.90% | N/A |
| India | 500 | 42 | 2 | 62.03% | 40.28% | 56.10% | N/A |
| Czech | 500 | 0 | 0 | N/A | N/A | N/A | N/A |

## Main engineering findings

At frozen confidence 0.46 US pothole recall is 43/135 = 31.85% (92 missed); China development pothole recall is 227/235 = 96.60%. Do not tune on the now-inspected US set or claim this proves local robustness.

The training sample was enriched for damage. Its remaining same-country complement is depleted of positives: Japan supports only D00/D20; India has 42 boxes; Czech has zero boxes. These are selected-complement diagnostics, not representative country performance. No resampling after viewing scores.

Czech has zero annotated damage boxes. Official evaluator zero placeholders do not mean zero detection ability; reviewed AP/recall/F1 are null. Historical notebook outputs and raw result JSON are retained unchanged. There were 26 detections across 500 empty-label Czech images (5.2 per 100 images), evaluated as FP relative to the supplied labels. This is neither a verified healthy-road cohort nor a test of damage recall.

US mAP50-95 differs from China by -16.06 percentage points. China was used for development and threshold selection; US was not part of our fine-tuning. This descriptive gap can reflect domain, class mix and label differences; it is not a pure causal country effect.

China_MotorBike: D00 has the largest missed-box count (463 of 2678 labels); recall 82.71%. Counts depend on class support, so also inspect per-class recall.

India: D00 has the largest missed-box count (11 of 21 labels); recall 47.62%. Counts depend on class support, so also inspect per-class recall.

Japan: D00 has the largest missed-box count (99 of 186 labels); recall 46.77%. Counts depend on class support, so also inspect per-class recall.

United_States: D00 has the largest missed-box count (1694 of 6747 labels); recall 74.89%. Counts depend on class support, so also inspect per-class recall.

China_MotorBike: the largest geometric error category is FN / no_matching_detection_above_threshold (560 boxes). Review the gallery and original labels before assigning a visual cause.

United_States: the largest geometric error category is FN / no_matching_detection_above_threshold (2618 boxes). Review the gallery and original labels before assigning a visual cause.

Japan: the largest geometric error category is FN / no_matching_detection_above_threshold (147 boxes). Review the gallery and original labels before assigning a visual cause.

India: the largest geometric error category is FN / no_matching_detection_above_threshold (16 boxes). Review the gallery and original labels before assigning a visual cause.

Czech: the largest geometric error category is FP / background_or_annotation_review (26 boxes). Review the gallery and original labels before assigning a visual cause.

1784/4122 missed boxes cover less than 1% of their image. This is an error-size description, not proof that small size caused each miss.

## Visual review

Manually reviewed the original US and Czech galleries. US examples show unmatched small/fragmented labels and large predicted crack boxes spanning several labels. This is consistent with localization/label-granularity errors in those examples, not a verified population-level cause. Several Czech predictions overlap possible road joints/cracks despite empty labels, so they need annotation review; do not call all of them proven model false alarms or all empty-label images healthy roads. These galleries deliberately select high-error cases, so visual observations are not prevalence estimates.

## Protocol and limits

Exact adopted run17 checkpoint SHA-256 25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f; confidence 0.46, resolution 640, NMS IoU 0.7, max_det 300. Official mAP uses confidence floor 0.001. Operating-point counts use descending-confidence same-class greedy one-to-one IoU >=0.5; they are separate from official mAP. Missing classes have undefined recall/F1 and are excluded from supported-class Macro-F1.

China is reused development data and was used to choose confidence. US is excluded from team fine-tuning, but external pretraining exposure is unknown. Other cohorts exclude the exact team training images while their countries were represented in fine-tuning. One exact evaluation duplicate was excluded; near-duplicates and route overlap remain unresolved. Country gaps also reflect class/support and sampling differences; do not infer a pure causal country effect.

Keep run17_best_finetuned.pt and confidence 0.46 as the frozen project candidate; cross-country failure remains unresolved. Local evaluation must report performance honestly. Any future tuning needs separate development data and a new untouched test set. No training, threshold retuning or local-image evaluation occurred. This completes this country/error study, not the local part of E4 or all project experiments.

## Attribution

RDD2022, Arya et al.; team YOLO conversion Sara; published initialization SreekarAditya/yolo-rdd2022-benchmark (CC BY 4.0 according to publisher); retain applicable Ultralytics terms.
