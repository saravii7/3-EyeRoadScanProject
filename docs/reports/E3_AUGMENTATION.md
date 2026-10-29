# E3 augmentation ablation

Completed Kaggle run 20 Version 1 (363195760).

| Arm | mAP50 | mAP50-95 | Change vs all on (pp) |
| --- | ---: | ---: | ---: |
| all_on | 95.86% | 65.30% | +0.00 |
| no_mosaic | 95.61% | 64.59% | -0.72 |
| no_hsv | 95.89% | 65.25% | -0.05 |
| no_horizontal_flip | 95.70% | 65.05% | -0.25 |

Removing mosaic reduced mAP50-95 by 0.72 percentage points relative to all-on. This is a single-seed, seven-epoch development observation, not a universal causal ranking. Removing hsv reduced mAP50-95 by 0.05 percentage points relative to all-on. This is a single-seed, seven-epoch development observation, not a universal causal ranking. Removing horizontal_flip reduced mAP50-95 by 0.25 percentage points relative to all-on. This is a single-seed, seven-epoch development observation, not a universal causal ranking.

Horizontal flips are plausible for many crack and pothole appearances but reverse traffic handedness and signs; retain only when these semantics are irrelevant. Mild HSV jitter approximates illumination changes, while extreme hue/saturation changes are unrealistic. Mosaic creates artificial seams and changes damage scale/context, so inspect its effect on small cracks. Vertical flips put road geometry upside down and are physically implausible for normal forward-facing road images; flipud remains zero. Validation and test images receive no training augmentation.

Primary endpoint: final epoch after seven fixed epochs per arm. Same original initialization, training data, split, seed and recipe except the named augmentation group. Other transformations remain fixed. Single seed, short training horizon, interactions unmeasured. China is development data; external pretraining overlap is unknown. No local/US test images were used. Adopted run17 checkpoint and confidence 0.46 remain unchanged.

**Decision.** Retain the current augmentation recipe. The all-on control had the highest primary endpoint in this short study; the HSV difference (0.05 percentage points) is too small to establish a reliable benefit from one seed. These are final-epoch seven-epoch study checkpoints, not the adopted run-17 best checkpoint. No model replacement or test-set tuning is performed.
