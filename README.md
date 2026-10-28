# 3-EyeRoadScanProject

Road damage detection and duplicate finding for municipalities.
AIEP bootcamp capstone (Olo Academy), Track A: RoadScan.

## Team
- Sara-albahesh (saravii7)
- rimas-al-abunasser
- fajer-alshahrani

## Data
Dataset: RDD2022 (Road Damage Dataset 2022)

Authors: Deeksha Arya et al.

Source: https://figshare.com/articles/dataset/RDD2022_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547

License: CC BY 4.0

The data is not stored in this repository because of its size.

## Status
Work in progress.

## Model artifacts
Baseline weights and config are in the GitHub Release `v1-baseline`.
Download with one command:
`python artifacts/download_weights.py`
(Works when the repository is public.)


## Data versions (v1 vs v2)

| | v1 | v2 |
|---|---|---|
| Training sample | 600 images (200 per country) | ~9,000 images (Japan 4,000, India 3,500, Czech 1,500) |
| Why | Quick start, as advised by instructors | v1 results showed a weak baseline (near-random AUC) and a large domain gap on China, so we expanded the data |
| Validation | China_MotorBike (1,977) | China_MotorBike (1,977), unchanged |
| Test | United_States + local photos | United_States + local photos, unchanged |
| Script | `make_sample.py` | `make_sample_v2.py` |
| Seed | 42 | 42 |

Both versions keep the same rules: splits are by country (no random split), the threshold is tuned on validation only, and the test set is evaluated once at the end.

### v2 class balance (images containing each class)
D00: 2,765 | D10: 2,600 | D20: 3,456 | D40: 3,074

### Known limitations
- Japan is about 44% of the v2 training sample.
- Czech has only ~1,072 images with damage, so about 29% of its sample is images without damage.
- Extra RDD2022 classes (Repair, D44, D50, D43, ...) are ignored; only D00, D10, D20, D40 are used.
- Norway is not used. China_Drone is kept out of training (planned for a robustness test).
