# Single-image road damage detection

The adopted project model is **run 17 fine-tuned**, `run17_best_finetuned.pt`. `selected_candidate.pt` in the old Kaggle package still contains the original checkpoint and must not be used as the project default. Load the local fine-tuned checkpoint once. The callable accepts one image and returns all detected damage regions using D codes. It runs inference without training or changing weights. The class mapping is checked against checkpoint names; an incompatible model raises an error.

```python
from roadscan_detector import RoadDamageDetector

# Adopted project checkpoint: run17_model_comparison/run17_best_finetuned.pt
# Fine-tuned on the 8,999-image team sample; original published weights are a reference only.
# Set the actual attached checkpoint path in your environment.
detector = RoadDamageDetector(weights='/path/to/run17_best_finetuned.pt', device='cpu')
detect_damage = detector.detect_damage
results = detect_damage('/path/to/image.jpg', confidence=0.46)
print(results)
```

Read the returned list: each entry contains `damage_code`, `bbox_xyxy` in **original-image pixels** `[x_min, y_min, x_max, y_max]`, and `confidence` in `[0, 1]`. An image may contain several boxes and damage categories. An empty list means no damage was detected above the threshold; it does not prove the road is undamaged. Invalid images raise an exception.

Illustrative schema only, not a measured prediction:

```json
[{"damage_code": "D40", "bbox_xyxy": [120.0, 200.0, 320.0, 350.0], "confidence": 0.87}]
```

| Code | Meaning |
| --- | --- |
| D00 | Longitudinal crack |
| D10 | Transverse crack |
| D20 | Alligator crack |
| D40 | Pothole |

PIL images and local image paths are accepted. OpenCV numpy input must be H x W x 3 in **BGR** order. PIL input is converted to RGB. Video, folders, URLs and batches are not accepted by this single-image interface. For a Streamlit upload, use `Image.open(uploaded_file)` and pass that PIL image.

Install the same inference dependencies as run 17: `ultralytics==8.4.177` (with PyTorch), Pillow and numpy. Use device `0` only where CUDA is available. Confidence 0.46 is frozen on China development validation before the local test; see THRESHOLD_SELECTION.md. Historical checks below used 0.25. Predictions are not evidence of independently measured Saudi-road accuracy.

## Verification

`../tests/test_roadscan_detector.py` uses an injected fake YOLO model to verify the public function contract, multiple detections, no detections, D-code mapping for reordered classes, invalid checkpoints and parameter/input errors. It does not measure real model accuracy. Run: `python -m unittest discover -s tests -v`.

Actual run-17 model metrics are recorded separately in `../results/run17/17-roadscan-gentle-finetuning-results.json`. The existing executed training notebook is preserved. This module can be imported from that notebook or the application.

Published initialization: SreekarAditya / yolo-rdd2022-benchmark (publisher CC BY 4.0); dataset RDD2022, Arya et al. Retain attribution and applicable Ultralytics terms.

## Historical verification: original checkpoint (Version 1)

On 2026-10-28, [Kaggle run 18 Version 1](https://www.kaggle.com/code/rimasabunasser/18-roadscan-inference-smoke?scriptVersionId=363140468) completed successfully in 57.8 seconds on CPU using the exact module SHA-256 `5e41fe3cbfc0b665e99f66a5f33c587b4396902b15d8151f57aed54b0d7cd103` and the run-17 selected original checkpoint. It processed 15 deterministic China development images and produced 41 detections. All four D codes, valid original-image pixel boxes and confidence values were verified. Local file paths, PIL RGB and OpenCV BGR input routes passed. No training or personal photos were used. See `../results/run18/18-roadscan-inference-smoke-results.json` and the executed notebook for actual examples. This verifies software integration, not model accuracy or generalization.

## Current verification: adopted run-17 fine-tuned checkpoint

[Kaggle run 18 Version 2](https://www.kaggle.com/code/rimasabunasser/18-roadscan-inference-smoke?scriptVersionId=363150764) passed in 57.1 seconds on CPU. It verifies the actual fine-tuned checkpoint SHA-256 `25b412ff18c05e2607f4bc61b872f39826e8d53ffdc7647654c1f419e355d15f` and the unchanged module. 15 development images produced 44 boxes; all four D codes, coordinates, confidence and path/PIL/BGR input routes passed. This is the current integration check. See `../results/run18/18-roadscan-inference-smoke-v2-run17-results.json` and its executed notebook. The earlier Version 1 files test the original reference only.

**Results interpretation.** The actual checkpoint processed **15 development images** and returned **44 detections**. All four codes D00/D10/D20/D40 appeared with valid pixel boxes and confidence values. Local paths, PIL RGB and OpenCV BGR inputs worked. The blank-image check returned 0 detections. These are implementation checks, not independent accuracy estimates or proof of Saudi-road generalization. Full outputs are saved in `inference_smoke/inference_smoke_results.json`.

## Current frozen operating point

Use confidence **0.46** with the adopted run-17 fine-tuned checkpoint. `detect_damage(image)` now uses this value by default; `../configs/model_config.json` records it. Override old application calls that explicitly pass 0.25. [Selection evidence](reports/THRESHOLD_SELECTION.md). Historical run-18 tests above document the earlier 0.25 operating point. The updated default was verified on the actual checkpoint in experiment 19.

## Repository layout

The canonical detector is [src/roadscan_detector.py](../src/roadscan_detector.py). From the repository root use `from src.roadscan_detector import RoadDamageDetector`. A root compatibility module preserves existing `from roadscan_detector import ...` imports. The inference implementation and frozen defaults are unchanged; config is [configs/model_config.json](../configs/model_config.json). Run commands from the repository root. Kaggle notebook paths still refer to Kaggle inputs/working outputs, not repository folders.
