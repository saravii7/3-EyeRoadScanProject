# 3-EyeRoadScanProject

Road damage detection and duplicate finding for municipalities. Olo Academy AIEP capstone, **Track A: RoadScan**.

## Start here

- [Adopted model and limitations](docs/MODEL_SELECTION.md)
- [Single-image detector usage](docs/INFERENCE_USAGE.md)
- [Kaggle experiment log](docs/KAGGLE_EXPERIMENTS.md)
- [E3 augmentation results](docs/reports/E3_AUGMENTATION.md)
- [Reviewed country evaluation and errors](docs/reports/COUNTRY_ERROR_ANALYSIS.md)
- [Repository folders and file migration map](docs/REPOSITORY_STRUCTURE.md)

## Current detector

Use **run17_best_finetuned.pt**, fine-tuned YOLOv8s on the frozen **8,999-image** team sample. Confidence **0.46**, image size **640**, NMS IoU **0.7**, max_det **300**. The machine-readable settings are in [configs/model_config.json](configs/model_config.json). Do not substitute the historical original `selected_candidate.pt`.

Weights for runs 14, 16 and 17 remain in [release v2-yolo](https://github.com/saravii7/3-EyeRoadScanProject/releases/tag/v2-yolo). Baseline releases [v1-baseline](https://github.com/saravii7/3-EyeRoadScanProject/releases/tag/v1-baseline) and [v2-baseline](https://github.com/saravii7/3-EyeRoadScanProject/releases/tag/v2-baseline) remain available. Dataset images are on Kaggle, not in this repository. The original release tag/source archive predates later confidence and folder updates; use current main for current code and paths.

## Run the detector

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

```python
from src.roadscan_detector import RoadDamageDetector

detector = RoadDamageDetector('/path/to/run17_best_finetuned.pt', device='cpu')
detections = detector.detect_damage('/path/to/road.jpg')
# Each result: damage_code (D00/D10/D20/D40), bbox_xyxy in original pixels, confidence.
```

Root compatibility modules preserve existing `from roadscan_detector import ...`, `import priority`, and `import duplicates` imports. Model inference and thresholds are unchanged by the folder reorganization. The tests use fake model outputs to check the software contract; actual checkpoint checks are archived in notebooks 18/19. No real-weight inference or training is rerun merely to move folders.

For Kaggle, use the saved source/input versions listed in the [experiment log](docs/KAGGLE_EXPERIMENTS.md). Notebook `/kaggle/input` and `/kaggle/working` paths belong to Kaggle and are intentionally unchanged. The current detector notebook is [run 17](notebooks/yolo/17-roadscan-gentle-finetuning.ipynb); [run 18 v2](notebooks/yolo/18-roadscan-inference-smoke-v2-run17.ipynb) verifies integration; [run 19](notebooks/yolo/19-roadscan-confidence-selection.ipynb) freezes confidence.

## Layout

| Folder | Contents |
| --- | --- |
| `notebooks/baseline/` | Baseline classifier notebooks |
| `notebooks/yolo/` | Saved YOLO training/evaluation notebooks 14–21 |
| `experiments/attempts/` | Previous attempts, statuses and original saved versions |
| `src/` | Detector, priority formula and duplicate finder implementations |
| `scripts/data/` | Conversion, class counting, country splitting and sampling scripts |
| `configs/` | Adopted model settings and dataset YAML files |
| `data/manifests/` | Image filename lists; no dataset images |
| `results/run14/` through `results/run21/` | JSON metrics, CSV tables and figures grouped by run |
| `results/manifests/` | Historical export/checksum records |
| `docs/` | Model choice, usage, experiment log, reports and protocols |
| `tests/` | Detector contract tests |
| `artifacts/` | Existing baseline weight downloader; release binaries stay external |

Priority and duplicate finder modules retain their current draft interfaces. They expect `cls/x/y/w/h/conf` dictionaries, while the detector returns `damage_code/bbox_xyxy/confidence`; their integration adapter is a separate task. Duplicate thresholds are placeholders pending pair-based validation. An end-to-end application is not claimed by this layout update.

## Evaluation status

| Study | Status |
| --- | --- |
| E3: Mosaic / HSV / horizontal-flip ablation | Completed and documented; single seed, seven epochs per arm |
| Frozen country/error study | Completed; independent local part of E4 still pending |
| E2: detector size or input resolution | Pending |
| E1: baseline vs detector | Requires coordinated comparable evaluation; not claimed complete |
| E5: duplicate methods | Team task; not claimed complete |
| Independent labeled local road test | Pending |

China development mAP50-95 is **65.79%**, versus **49.73%** on 4,804 US images. US pothole recall at the frozen operating point is **43/135 = 31.85%**, an unresolved failure. These results do not establish local Saudi-road readiness. External pretraining overlap is unknown. Japan/India selected complements have limited class support; the Czech complement has no annotated damage boxes, so its AP/recall/F1 are **N/A**. See the reviewed report rather than treating raw evaluator zero placeholders as zero detection ability.

## Data versions

| | v1 | v2 |
| --- | --- | --- |
| Training images | 600 (200 per country) | 8,999 (Japan 4,000 / India 3,500 / Czech 1,499) |
| Validation | China MotorBike 1,977 | Same China development set |
| Sampling script | [make_sample.py](scripts/data/make_sample.py) | [make_sample_v2.py](scripts/data/make_sample_v2.py) |
| Seed | 42 | 42 |

The v2 sample was enriched for rare damage classes. Keep the original country assignments and do not randomly re-split the data. US country evaluation has now been performed with the frozen model. Independent local photos remain reserved for final testing. Historical notes in saved attempts remain records of their original experiment, not current adoption instructions.

## Team

- Sara-albahesh (saravii7)
- rimas-al-abunasser
- fajer-alshahrani

## Data and model attribution

RDD2022, Deeksha Arya et al., [dataset source](https://figshare.com/articles/dataset/RDD2022_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547), CC BY 4.0. Published initialization: SreekarAditya / yolo-rdd2022-benchmark; retain publisher attribution and applicable Ultralytics terms. The team's contribution includes fine-tuning, controlled studies, threshold selection and evaluation; published initialization is not claimed as original team training.
