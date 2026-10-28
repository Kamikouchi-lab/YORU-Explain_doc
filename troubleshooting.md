---
layout: page
title: Q and A
order: 2
description: Common questions and what the messages mean. When something fails, look at the logs first.
---

## Where are the logs?

`~/.yoru/logs/yoru_explain.log` (on Windows `C:\Users\<you>\.yoru\logs\`), next to YORU's own log; the `YORU_HOME` environment variable moves both. Each run writes `logs/run.log` in its run folder, with tracebacks. **Help &rarr; Open log folder** and **Settings &rarr; Open log folder** open the folder. For a bug report, add the text from **Settings &rarr; Versions, adapters and the loaded model**.

## Starting

**`python -m yoru_explain` does nothing, or opens the Microsoft Store.**

> On some Windows machines `python` is the Store stub, not the environment's Python. Use `uv run python -m yoru_explain`, or `.venv\Scripts\python.exe -m yoru_explain`.

**`uv sync` cannot find YORU.**

> YORU-Explain installs YORU from the folder next to it, `../YORU`. Check that `YORU-dev/YORU` and `YORU-dev/YORU-Explain` are siblings ([Install]({{ '/guides/install/' | relative_url }})).

**A YOLOv5 model does not load.**

> YORU-Explain runs YOLOv5 models with YORU's bundled YOLOv5 code, `yoru/libs/yolov5`, which not every YORU 2.0 version contains (the `v2.0.0-beta.3` release does not). Use the {{ site.yoru_requirement }} release or later ([Install]({{ '/guides/install/' | relative_url }})).

## Grad-CAM

**Grad-CAM is not in the method list.**

> It is offered only when the loaded model passed the gradient probe; the reason is shown in amber under the methods on the *Analyze* tab. ONNX models and black-box models have no gradients, so they never offer it.

**A Grad-CAM map is bright on another animal too.**

> With YOLOv5 at its default layer, the score's gradient reaches exactly one cell of the feature map; the map then shows where the channels of that cell are active anywhere in the frame, on other animals of the same class as well. That is the measurement, not a failure ([Where the gradient reaches]({{ '/methods/gradcam/' | relative_url }}#gradient-support)).

## Identity modes and statuses

**`fixed_candidate` is not offered for my model.**

> RT-DETR's queries and Faster / Mask R-CNN's proposals are chosen anew for every input, so "the same candidate" on a changed frame does not exist. These models are followed by re-detection only ([What is measured]({{ '/methods/what-is-measured/' | relative_url }}#identity-modes)).

**Many patches are `disappeared`, and the map has holes.**

> In re-detection mode a patch after which the detection is not found again has no score, and pixels covered only by such patches have no value. That is reported, not hidden: the counts are in *Statistics*, `lost_fraction` in the map file shows where. Fixed-candidate mode, where the model offers it, gives a score for every patch.

## Runs that stop or fail

**`identity_check_failed`: the run stopped at once.**

> On its first frame, the adapter's detections were compared with YORU's own detector and differed. Check that YORU-Explain's environment uses the YORU next to it (`uv sync`), and report the case with the log: no result is written when the check fails.

**`frame_mismatch`.**

> The decoded frame's pixels differ from those the event was made from &mdash; the video file changed, or a different file now sits at its path. **Verify files** on the *Project* tab shows which.

**`target_not_reproduced`.**

> The event's detection was not found again on its frame with the loaded model (the same candidate and class with IoU &ge; 0.9, or the same class with IoU &ge; 0.9). Typical causes: another model or other thresholds than the event was made with, or events imported from a CSV of another model.

**`cuda_oom`.**

> The GPU ran out of memory. Lower **batch size** on the *Analyze* tab; batch size 1 is also the exact one.

## Seeking

**"Seeking is not exact for this video".**

> *Check seeking* found frames for which seeking lands on another frame than decoding in order (some files state a frame rate their frames do not have). Results are not affected: analysis runs always read frames in order and compare each frame's hash, and *Explore* seeks only through a presentation-time index and verifies where each seek landed.

## Other

**Paths in the window show `¥` instead of `\`.**

> The window uses YORU's Japanese-capable font, in which the backslash is drawn as a yen sign. The paths themselves are unchanged.

**Results differ slightly between the GPU and the CPU.**

> CUDA runs with fp16 autocast, as YORU does, and the CPU in fp32, so scores differ in the last digits (e.g. 0.857316 and 0.857245). Every run records its device; compare runs made on the same one.
