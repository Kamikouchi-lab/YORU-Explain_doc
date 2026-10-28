---
title: Supported models
order: 1
description: Every YORU detection backend has an adapter that runs the model the way YORU runs it and exposes what is underneath; anything else runs as a black box.
---

| YORU backend | Models | Adapter | Candidate | Identity modes | Score YORU reports | Grad-CAM |
|---|---|---|---|---|---|---|
| `yolov5` | YOLOv5 checkpoints (every YORU v1 model) | `yoru-yolov5` | anchor slot (level, anchor, cell) | fixed-candidate, re-detection | `obj_x_cls` = &sigma;(obj)&middot;&sigma;(cls) | yes |
| `ultralytics` | YOLOv8, YOLO11, YOLOv5u, YOLOv10 (YOLOv9 runs too, not verified); detect, **OBB**, segment, pose | `yoru-ultralytics` | anchor point (level, cell) | fixed-candidate, re-detection | `cls_prob` = &sigma;(cls) | yes |
| `rtdetr` | RT-DETR | `yoru-rtdetr` | decoder query | re-detection | `cls_prob` = &sigma;(cls) | yes (the query on its frame) |
| `torchvision` | Faster R-CNN, Mask R-CNN (boxes) | `yoru-torchvision` | region proposal | re-detection | `cls_softmax` | yes (the proposal on its frame) |
| `torchvision` | SSD300 | `yoru-torchvision` | default box (level, cell, aspect) | fixed-candidate, re-detection | `cls_softmax` | yes |
| `onnx` | ONNX exports of YOLOv5 / YOLOv8 / YOLO11 | `yoru-onnx` | output row | fixed-candidate, re-detection | `obj_x_cls` or `cls_prob` | no (ONNX Runtime has no gradients) |
| any | anything YORU's `get_detector` loads | `yoru-detector` (black box) | none | re-detection | `confidence` | no |

`confidence` is offered by every adapter and is always the number YORU reports. The model type `auto` asks YORU which backend its own `get_detector("auto", ...)` would pick for the file, so the explanation is of the model family YORU runs.

## What every adapter guarantees

- **The detections are YORU's.** The identity check loads YORU's own detector and compares every box, confidence and class &mdash; and the rotated box of OBB models. A run checks this on its first frame and stops if it fails.
- **A candidate's readout is its detection.** Reading a detection's candidate on the unchanged frame gives its reported confidence bit for bit.
- **The gradient pass is the inference pass.** Grad-CAM is offered only when a probe on the loaded model passed, and a map is made only when the gradient-pass score equals the inference score. Weights are never changed and modules never put in training mode.
- **Fixed-candidate mode only where a candidate is a fixed slot.** RT-DETR's queries and Faster R-CNN's proposals are chosen anew for every input; those adapters refuse fixed-candidate mode before a run starts and offer re-detection.

## The families

### YOLOv5 (`yoru-yolov5`)

Built with YORU's own loader and run step by step as YORU's YOLOv5 detector runs it: YORU's colour-order rule, the bundled `letterbox`, the forward pass under `inference_mode` and CUDA autocast, the bundled NMS, the confidence threshold after NMS, `scale_boxes`. NMS is called once per image, as YORU calls it. Because it calls YORU's bundled functions rather than copies, the detections are YORU's by construction.

### ultralytics: YOLOv8, YOLO11, YOLOv5u, YOLOv10 (`yoru-ultralytics`)

Calls ultralytics' own predictor preprocessing, the fused model, ultralytics' `non_max_suppression` (with the index of every kept candidate) and `scale_boxes`, one image per NMS call as YORU does. Detect, OBB, segmentation and pose models are supported; for pose models the score is read before the keypoints are decoded, with the values YORU reports. YOLOv10's end-to-end head is followed through its one-to-one branch.

- **Not explained here**: exported ultralytics formats (TorchScript, TensorRT, OpenVINO, ...) &mdash; they run in the black box; classification models.
- **YOLO26 with ultralytics 8.3.222**: this ultralytics ignores the checkpoint's end-to-end flag and runs YOLO26 with NMS, so YORU reports different boxes than the model was made for. YORU-Explain reproduces YORU exactly, explains that output, and warns that a newer ultralytics may be needed.

### RT-DETR (`yoru-rtdetr`)

The frame is stretched to 640 &times; 640 (no padding); the decoder's 300 queries give the detections, without NMS. A query on a changed frame is not "the same candidate", because the queries are re-selected from the encoder's scores for every input: RT-DETR is followed by **re-detection only**. On its own frame a query is well defined, so Grad-CAM is offered. On CUDA its scores move with the batch size (1.6 &times; 10<sup>&minus;3</sup> between batch sizes 1 and 2); use batch size 1 for exact work.

### torchvision: Faster R-CNN, Mask R-CNN, SSD300 (`yoru-torchvision`)

Reads checkpoints written by YORU's `train_torchvision.py`, rebuilds the network as YORU does, and runs the model's own pieces in their own order. YORU keeps scores strictly above the confidence threshold; **YORU's IoU threshold is not used** &mdash; NMS runs inside torchvision at the model's own setting (Faster / Mask R-CNN 0.5, SSD 0.45), and the run records it as unused.

- **Faster / Mask R-CNN**: candidates are this input's region proposals: **re-detection only**; Grad-CAM of the proposal on its own frame. Mask R-CNN's mask branch is not run (YORU uses its boxes only).
- **SSD300**: candidates are fixed default boxes: fixed-candidate mode works.

### ONNX (`yoru-onnx`)

YORU's ONNX steps are private methods of YORU, so the adapter repeats them in the same float32 arithmetic and keeps each detection's output row; the identity check confirms the result on every run. Fixed-candidate mode works. YOLOv5 exports also offer `obj_x_cls`, `cls_prob` and `obj_prob`. **No gradients**, so occlusion only.

### Black box (`yoru-detector`)

YORU's `get_detector(...)` itself, through its `detect()` only. It works for every backend YORU has or will have, and for files the specific adapters do not open. No candidates, logits or gradients: re-detection with the reported confidence, no Grad-CAM. Choose **black box** on the *Project* tab, or `api.load_model(path, black_box=True)`.

## Rotated boxes (OBB models)

- A detection keeps YORU's rotated box `(cx, cy, w, h, angle)` (radians, from +x towards +y); its `box` stays the upright box around it, as YORU reports `x1 … y2`.
- Two rotated boxes overlap by the exact IoU of the two rectangles as polygons (re-detection, finding a target again, picking in *Explore*).
- The occlusion region is the upright box (scaled); the in-box summaries use the rotated box.
- `events.csv` and `results.csv` carry `obb_cx … obb_angle`; YORU's detections CSVs bring their rotated boxes along.

## Measured on the development machine

Test models (fixtures, not models of animals) on ultralytics' `bus.jpg` (1080 &times; 810), RTX 5060 Ti and CPU:

| Model | Input (h &times; w) | Forward per image: CUDA batch 1 / 8 (CPU batch 1) | Grad-CAM default layer: cells with gradient |
|---|---|---|---|
| `yolov5s.pt` | 640 &times; 480 | 4.5 / 1.2 ms (23 ms) | `model.23`: 1 |
| `yolo11n.pt` | 640 &times; 480 | 4.3 / 1.1 ms (20 ms) | `model.22`: 25 |
| `yolov8n.pt` | 640 &times; 480 | 3.4 / 1.0 ms (17 ms) | `model.21`: 25 |
| `yolov5nu.pt` | 640 &times; 480 | 3.8 / 1.0 ms (17 ms) | `model.23`: 25 |
| `yolov10n.pt` | 640 &times; 480 | 5.0 / 1.1 ms (18 ms) | `model.22`: 25 |
| `yolo11n-obb.pt` | 1024 &times; 768 | 5.3 / 3.0 ms (34 ms) | `model.16`: 15 |
| `yolo11n-seg.pt` | 640 &times; 480 | 5.1 / 1.5 ms (24 ms) | `model.22`: 25 |
| `yolo11n-pose.pt` | 640 &times; 480 | 5.6 / 1.2 ms (20 ms) | `model.22`: 25 |
| `rtdetr-l.pt` | 640 &times; 640 | 17 / 13 ms (206 ms) | `model.27`: 342 |
| COCO Faster R-CNN | 1088 &times; 800 | 40 / 41 ms (604 ms) | `backbone.fpn.2`: 280 |
| COCO Mask R-CNN (boxes) | 1088 &times; 800 | 40 / 40 ms (618 ms) | `backbone.fpn.2`: 252 |
| COCO SSD300 | 300 &times; 300 | 8.6 / 5.9 ms (85 ms) | `backbone.2`: 9 |
| `yolov5s.onnx` | 640 &times; 640 | CPU 22 ms | &mdash; |
| `yolo11n.onnx` | 640 &times; 640 | CPU 16 ms | &mdash; |

For all of them the detections equalled YORU's bit for bit, on the CPU and on CUDA, and the gradient-pass score equalled the inference score exactly ([Validation]({{ '/reference/validation/' | relative_url }})).

## Not verified

- Models trained in YORU with these backends: the test models are COCO models of ultralytics and torchvision and ONNX exports. Every run re-checks identity on its own first frame.
- YOLOv9, YOLOv3u, YOLOv6, YOLO12, YOLO-World / YOLOE; ultralytics' exported formats in the black box; ONNX Runtime's CUDA provider; an ONNX export of a torchvision model.
- YOLO26 run end to end (it needs a newer ultralytics than YORU installs).
