# Single-image road damage detection

Load the chosen local YOLO checkpoint once. The callable accepts one image and returns all detected damage regions using D codes. It runs inference without training or changing weights. The class mapping is checked against checkpoint names; an incompatible model raises an error.

```python
from roadscan_detector import RoadDamageDetector

# Kaggle run-17 saved output: run17_model_comparison/selected_candidate.pt
# This selected file contains the ORIGINAL published checkpoint, not run-17 fine-tuned weights.
# Set the actual attached checkpoint path in your environment.
detector = RoadDamageDetector(weights='/path/to/selected_candidate.pt', device='cpu')
detect_damage = detector.detect_damage
results = detect_damage('/path/to/image.jpg', confidence=0.25)
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

Install the same inference dependencies as run 17: `ultralytics==8.4.177` (with PyTorch), Pillow and numpy. Use device `0` only where CUDA is available. Confidence 0.25 is provisional; choose the operational threshold on validation before deployment. Predictions are not evidence of independently measured Saudi-road accuracy.

## Verification

`test_roadscan_detector.py` uses an injected fake YOLO model to verify the public function contract, multiple detections, no detections, D-code mapping for reordered classes, invalid checkpoints and parameter/input errors. It does not measure real model accuracy. Run: `python -m unittest test_roadscan_detector -v`.

Actual run-17 model metrics are recorded separately in `17-roadscan-gentle-finetuning-results.json`. The existing executed training notebook is preserved. This module can be imported from that notebook or the application.

Published initialization: SreekarAditya / yolo-rdd2022-benchmark (publisher CC BY 4.0); dataset RDD2022, Arya et al. Retain attribution and applicable Ultralytics terms.
