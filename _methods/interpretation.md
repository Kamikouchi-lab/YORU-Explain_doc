---
title: Reading the results
order: 4
description: What a map does and does not say, and what to report with it.
---

## Three things, kept apart

| | Comes from | Says |
|---|---|---|
| **Attribution** | Grad-CAM | where, at one layer, the score's gradient weights active features |
| **Perturbation effect** | occlusion | how the score changes when a region is replaced by a baseline |
| **Biological interpretation** | &mdash; | which body part or behaviour matters to the animal |

YORU-Explain produces the first two and **never the third**. Both are statements about one model's score for one detection. A claim about body parts needs independently measured features and controls; named regions such as wings, head or legs, with matched-area random controls, are planned ([Roadmap]({{ '/devnotes/roadmap/' | relative_url }})).

## Do not tune until it looks right

Choose the settings before looking at the maps, and report the maps as they come out. A map that does not highlight the wings or the legs is a measurement of the model, not a failure of the method &mdash; and adjusting the patch size or the baseline until it does would make the figure say what you expected rather than what the model does.

## Settings change the numbers

- **Baseline, patch size, stride.** On the copulation event of YORU's test video, the largest score change was 0.055 with hot-pink patches and 0.523 with black ones ([Baselines]({{ '/methods/occlusion/' | relative_url }}#baselines)). Name the baseline in every figure, and show more than one before making a claim.
- **Identity mode.** Fixed-candidate and re-detection answer different questions and give different per-patch numbers ([Identity modes]({{ '/methods/what-is-measured/' | relative_url }}#identity-modes)).
- **Batch size and device.** Batch size 1 reproduces YORU exactly; larger batches have a noise floor of about 2.7 &times; 10<sup>&minus;3</sup> ([Batch size]({{ '/methods/occlusion/' | relative_url }}#batch-size)). CUDA (fp16 autocast, as YORU runs) and the CPU (fp32) give slightly different scores, e.g. 0.857316 and 0.857245 for the same detection.

## Frames are not independent samples

Consecutive frames of one video, one animal, one day are not independent replicates. The *Statistics* tab is descriptive and runs no test. A group analysis that treats videos, animals and days as the units is planned.

## What to report with a figure

Everything below is written to every run's `config.json` and `manifest.json`:

- the method, the score type and the identity mode;
- for occlusion: the baseline, the patch size, the stride, the region and the batch size;
- for Grad-CAM: the layer and the precision;
- the device, the model file's SHA-256, and the versions of YORU-Explain and YORU;
- the identity check against YORU.

## About the figures on this site

The examples come from YORU's test video (`test_video_fly_copulation.mp4`) and a YOLOv5 model trained with YORU's training script on 900 frames of that same video, as a test fixture for YORU-Explain. They describe that fixture model's score. They are not findings about flies.
