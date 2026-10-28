---
title: Validation
order: 3
description: What has been checked, how, and what has not. Every claim on this page is backed by a test in the repository or by a measurement summarised here.
---

Status: version 0.1.0 (2026-10-16), extended on 2026-10-17 to every YORU detection backend. `uv run pytest` runs 330 tests (plus one opt-in real-window test), all passing on 2026-10-17 on Windows 11, Python 3.10.22, torch 2.11.0+cu128, ultralytics 8.3.222, torchvision 0.26.0, onnxruntime 1.23.2, RTX 5060 Ti &mdash; about 2 minutes with every model fixture, 25 seconds without.

## What was verified

| Area | How | Result |
|---|---|---|
| Inference identical to YORU | each adapter against YORU's `get_detector(...).detect`: `zidane.jpg` with `yolov5s.pt`; frames 0, 150, 4350, 6450 and 8700 of YORU's test video with the fly model; CPU and CUDA; RGB input; conf 0.85 | equal **bit for bit** in every case |
| Every YORU backend | 13 models of the ultralytics, RT-DETR, torchvision and ONNX backends on `bus.jpg`, `zidane.jpg` and frame 150 of the test video, CPU and CUDA | detections equal YORU's bit for bit, rotated boxes included; every candidate recovered with its readout equal to its confidence |
| Candidate = detection | the readout of each detection's candidate against its reported score | bit-exact |
| Letterbox, boxes, maps | 8 frame shapes against YOLOv5's `letterbox` and `scale_boxes`; 7 shapes against ultralytics', RT-DETR's, torchvision's and YORU's ONNX transforms | input images byte-identical; boxes within 10<sup>&minus;3</sup> px; maps and feature cells land where they belong |
| Occlusion, known answer | the synthetic detector, whose every candidate reads exactly a 32&times;32 window | patches outside the window: Δ **exactly 0**; over the square: Δ &gt; 0; green inside the window: Δ &lt; 0, kept negative in the map; `noop` Δ = 0; uncovered pixels NaN |
| Following the target | two same-class squares | hiding A lowers A's score by up to 0.49 while "the best box of the class" would report no change; re-detection gives `matched`, `disappeared`, `class_changed`, `unmatched`, `ambiguous` as constructed; lost patches have no score |
| Grad-CAM, known answer | the synthetic detector | the CAM's half-maximum region is the red square in frame pixels, through letterbox padding; refuses without a probe, a candidate, with a mismatched score, a non-finite gradient or an unknown layer |
| Grad-CAM leaves the model alone | fly model, every gradient-capable test model | gradient-pass score = inference score exactly; weights (state-dict SHA-256), evaluation mode and detections unchanged; no parameter gradients |
| Reproducibility | save, re-create the request from `config.json`, run again | results, perturbations and NPZ arrays identical, on the CPU, on CUDA and across processes |
| Failure handling | a changed frame, a box not on the frame, a missing video, cancellation, a failed identity check | `frame_mismatch`, `target_not_reproduced`, `missing_data`, `cancelled` rows; the run continues; no map, no number |
| Frames | in-order numbering, seeks, flips, non-ASCII paths | seeks verified by presentation time equal the in-order frames |
| CPU only | CUDA reported missing | everything runs on the CPU |
| Rotated boxes | corners and polygon IoU against YORU's and ultralytics' | exact on known cases; re-detection tells apart rotated rods that upright boxes confuse |
| The window | the DearPyGui window built in the test process | analysis runs while the window keeps responding (no frame over 0.5 s); cancel; views and colour scale; settings export and import; a failing callback is reported, not fatal; quitting during a task waits for it |
| The boundary with YORU | an automatic check of imports | YORU internals used in one module only; YORU never imports YORU-Explain; the core imports without PyTorch or a GUI toolkit |

## Measured on YORU's test video

The YOLOv5 fly model, CUDA, 32&times;32 patches, stride 16, context &times;3, black baseline:

| Event | Frame | Class, score | Patches | Largest Δ | Mean Δ in box / outside | Grad-CAM mass in box |
|---|---|---|---|---|---|---|
| ev-0001 | 150 | solo 0.9113 | 500 | 0.146 | 0.022 / 0.0006 | 0.50 |
| ev-0002 | 150 | solo 0.8841 | 375 | 0.275 | 0.033 / 0.0023 | 0.50 |
| ev-0003 | 6450 | copulation 0.8959 | 528 | 0.523 | 0.029 / 0.0019 | 0.999 |

Time per event: 2.7&ndash;3.7 s at batch size 1, 1.4&ndash;1.9 s at batch size 8.

The same events with the default hot-pink baseline instead of black:

| Event | Black: largest Δ / mean Δ in box | Hot pink: largest Δ / mean Δ in box |
|---|---|---|
| solo, frame 150 | 0.146 / 0.022 | 0.132 / 0.013 |
| copulation, frame 6450 | 0.523 / 0.029 | **0.055** / 0.0066 |

Replacing the whole region kills the detection with either colour (score &lt; 10<sup>&minus;5</sup>). These numbers describe the fixture model's score, not flies: the model was trained on 900 frames of the same video it is tested on.

## An independent review

A separate review of the code (2026-10-17) found seven defects. All are fixed, and each has a regression test:

| Defect | Fix |
|---|---|
| an error while writing an event's files escaped the run, leaving a manifest that said `completed` with rows missing | files first, tables last; a write error removes the event's files and becomes an `output_failed` row; any other unexpected error becomes an `internal_error` row and the run continues |
| an `ambiguous` re-detection wrote the competing detection's score as the target's | the competing score is kept apart and used only when ambiguous matches are counted |
| a stored candidate index was accepted without checking the box, so an event of another model could be re-anchored to another animal | the same candidate also needs IoU &ge; 0.9; events of another model are found by IoU only |
| the bundled NMS's per-call time limit could empty later images of a batch | NMS per image |
| a failed time-index pass raised inside the Explore view | reported as `failed` |
| re-reading a frame decoded the video again from the start | the last exactly read frame is reused |
| quitting during a task could leave a thread running at exit | cancel, then wait for the task with the window responsive |

## Found while validating

- **Seeking is not exact on YORU's test video.** The file states 30.0032 fps while its frames are 33.333 ms apart; OpenCV's seek to frame 6301 decodes frame 6300. Analysis runs therefore decode in order and compare each frame's hash with the event's, and the window seeks only through a presentation-time index (one pass, 0.8 s for 9002 frames) and verifies where each seek landed.
- **On Windows, torch must be imported before PyQt5.** PyQt5's own `MSVCP140.dll` breaks a torch imported afterwards (WinError 1114 in `c10.dll`). Any process importing both has this constraint; YORU-Explain's window no longer uses PyQt5.

## Not verified

- The YORU paper's models and other YORU v1 models. Identity with YORU is shown for `yolov5s.pt` and the fixture model; every run re-checks it on its own first frame.
- Models trained in YORU with its other backends (the test models are COCO models and ONNX exports).
- Linux, macOS, Apple MPS; GPUs other than the RTX 5060 Ti.
- Variable-frame-rate, very long or high-resolution videos.
- Grad-CAM sanity checks beyond the above (weight randomisation, comparison with occlusion across many events).
- The effect of each baseline on real data beyond the runs above.
- YOLOv9, YOLOv3u, YOLOv6, YOLO12, YOLO-World / YOLOE; ultralytics' exported formats; ONNX Runtime's CUDA provider; YOLO26 run end to end.
