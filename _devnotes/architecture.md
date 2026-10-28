---
title: Architecture
order: 1
description: How the code is organised, the rules that keep the numbers trustworthy, and where YORU-Explain meets YORU.
---

## Layers

```text
gui/ (DearPyGui)              displays, dispatches, never computes an explanation
  │  calls
api.py ── core/pipeline.py    runs over a project's events, writes run folders
  │
  ├── methods/                occlusion (numpy), Grad-CAM (torch), baselines
  ├── analysis/               scoring in both identity modes, re-detection matching, summaries
  ├── io/                     frames, project, run folders, schema, YORU CSV import
  ├── visualization/          colour tables, overlays, preview PNGs
  └── adapters/               the only code that runs a model
        ├── base.py           the adapter contract, capabilities, the identity comparison
        ├── yolov5.py         YORU's YOLOv5, reproduced step by step
        ├── ultralytics.py    YOLOv8 / YOLO11 / YOLOv5u / YOLOv10 (+ OBB, seg, pose) and RT-DETR
        ├── torchvision.py    Faster R-CNN / Mask R-CNN / SSD300 checkpoints written by YORU
        ├── onnx.py           ONNX exports, as YORU's ONNX plugin runs them
        ├── blackbox.py       any YORU detector, through its detect() only
        ├── _yoru.py          the only module importing YORU internals
        └── toy.py            synthetic detector with known answers (tests, demos)
core/                         types, errors, geometry, hashing, logs, registry, environment
```

The GUI and scripts share one code path: the window calls `core/pipeline.py` through `api.py`, as a script does.

## The rules that make the numbers trustworthy

- Explain **the** detection: its pre-NMS candidate (fixed-candidate) or a unique class + IoU match (re-detection). Never the best box of the class.
- A target that is lost, ambiguous or failed has **no score** &mdash; an empty cell or NaN with a status and an error code. Never 0.
- Occlusion deltas are taken against a reference scored at the run's batch size (scores depend on it). The `noop` control stays.
- Grad-CAM only when the adapter's gradient probe passed and the gradient-pass score equals the inference score; otherwise fail with a code, no map.
- Never put a model in training mode, never change weights; gradients are taken with respect to activations, from a copy of the input.
- Every adapter stays identical to its YORU backend's `detect()`; the integration tests check each bit for bit, on CPU and CUDA. Preprocessing, NMS and thresholds change only together with those tests. Adapters call the family's own functions (ultralytics' NMS and `scale_boxes`, torchvision's pieces) rather than copies; only YORU's private ONNX steps are repeated.
- Fixed-candidate mode only where a candidate is a fixed slot: RT-DETR queries and Faster R-CNN proposals are re-detection only.
- Frames are numbered as YORU's analysis numbers them (decoding order from 0); runs read in order and compare frame hashes; seeks are verified by presentation time.
- Settings are not tuned until a map looks plausible; measurements are reported as they come out. Attribution, perturbation effect and biological interpretation stay separate in the window and in the documentation.

## The boundary with YORU

- YORU is changed only through pull requests to Kamikouchi-lab/YORU. YORU-Explain never edits YORU on its own.
- YORU names outside YORU's documented external API (`docs/external_api.md`) are used only in `adapters/_yoru.py`: YORU's YOLOv5 entry points, `torch_device`, `resolve_device` and `_auto_detect_backend`. A unit test pins that list.
- YORU never imports `yoru_explain`, and YORU's window has no branch for it. YORU-Explain does not import `yoru_tracker`.
- The window shell and base theme are YORU's documented GUI primitives (`GuiSession`, `apply_default_theme`); the screens are YORU-Explain's own.

## The adapter contract

| Method | Contract |
|---|---|
| `load_model(weights, device, **options)` | load; measure the capabilities (determinism, batch dependence, gradient probe) |
| `preprocess(images)` | frames of one shape &rarr; a batch tensor and its letterbox transform |
| `predict_raw(prepared, logits=)` | one forward pass exactly as the detector's own inference (no gradients, same autocast) |
| `postprocess(raw, prepared)` | the detections the detector reports, each with its candidate |
| `candidate_readout(raw, prepared, k, c, score_type)` | candidate *k*'s score, box and class on every image |
| `score_target(raw, prepared, target, score)` | the target's score per image, in fixed-candidate or re-detection mode |
| `identity_check(image)` | compare with the YORU detector it stands in for |
| `gradient_layers()`, `default_gradient_layer()`, `forward_with_gradients()`, `candidate_score_tensor()` | the gradient path |
| `capabilities` | family, candidate kind, identity modes, score types and their definitions, multi-label, gradients and why, layers, determinism, batch invariance, notes, warnings |

Which adapter explains a model is decided as YORU decides which backend runs it; anything else runs in the black box. A request the loaded adapter cannot honour &mdash; a score it does not have, fixed-candidate mode for queries or proposals, Grad-CAM without a verified gradient path &mdash; is refused before a run folder is written. One lock per adapter serialises forward passes between the window's threads.

## A run

```text
config.json  ← the request (written first)
manifest.json (status: running)
for each event, by source and frame:
    frame  ← decoded in order (exact numbering); hash == event's hash?    else frame_mismatch
    first frame: adapter.identity_check(frame)                           failed → stop the run
    target ← same candidate + class with IoU ≥ 0.9, or class + IoU ≥ 0.9
             (event made with another model: IoU only)                  else target_not_reproduced
    cache key = sha256(model, adapter settings, device, frame hash, target, method settings)
    hit → copy the earlier result
    else → occlusion / Grad-CAM → maps/*.npz, previews/*.png, then perturbations.csv rows,
           then the results.csv row last; a write error removes the event's files → output_failed
manifest.json (status, identity check, counts, error codes)
```

Rows are appended per event, so an interrupted run keeps valid tables of what it finished.

## Threads in the window

- The render loop runs DearPyGui's callbacks itself, so every callback is on the render thread; a callback that raises is shown in a popup and logged, and the loop goes on.
- One long task at a time &mdash; loading a model, an analysis run, a seek check &mdash; runs on its own thread; cancelling sets a flag the pipeline checks between batches and events.
- A second thread decodes frames and runs the detector for *Explore*, keeping only the latest request while the slider is dragged.
- Neither thread touches DearPyGui. They leave progress and results behind; the loop collects them once per frame.
- Closing the window during a task asks first, cancels, and keeps rendering until the task reaches its next check (at most 60 s), so its run folder is closed with a manifest.

## Logs

`~/.yoru/logs/yoru_explain.log` &mdash; YORU's log folder, found through YORU's documented `get_log_dir` &mdash; rotating at 5 MB &times; 3; each run also writes `logs/run.log`. Tests point `YORU_HOME` at a temporary folder.
