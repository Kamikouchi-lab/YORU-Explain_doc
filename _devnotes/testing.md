---
title: Tests
order: 2
description: How to run the test suite, which model files the integration tests need, and what continuous integration runs.
---

## Running the tests

```bash
uv run pytest
```

This runs everything: unit tests, the integration tests of every backend, and the window built in the test process without a viewport. It takes about 2 minutes with every model fixture present and about 25 seconds without them; tests whose fixtures are missing are skipped, not failed.

```powershell
$env:YORU_EXPLAIN_GUI_WINDOW = "1"     # cmd: set YORU_EXPLAIN_GUI_WINDOW=1
uv run pytest tests/gui
```

`YORU_EXPLAIN_GUI_WINDOW=1` adds a test that opens the real window for a moment and saves a screenshot. It needs a desktop.

## Test models

| Fixture | Where | How |
|---|---|---|
| `yolov5s.pt` | `.cache/models/` (or `YORU_EXPLAIN_YOLOV5_WEIGHTS`) | downloaded |
| ultralytics' small models (YOLO11n, YOLOv8n, YOLOv5nu, YOLOv10n, OBB, seg, pose), RT-DETR-L | `.cache/models/` | downloaded |
| COCO Faster R-CNN, Mask R-CNN, SSD300 in YORU's checkpoint layout | `.cache/models/` | built from torchvision's weights (about 1 GB) |
| ONNX exports of `yolov5s.pt` and `yolo11n.pt` | `.cache/models/` | exported |
| the fly model, `fly_copulation_yolov5s.pt` | `.cache/models/` (or `YORU_EXPLAIN_FLY_WEIGHTS`) | trained with YORU's training script on YORU's test video; not public |

```bash
uv run --with onnx python -m tests.prepare_models
```

fetches or builds them into `.cache/models/`, which git ignores. The integration tests on video frames also need YORU's test video, `YORU/test_data/test_video_fly_copulation.mp4`.

## What the tests establish

The suite contains synthetic known-answer tests (a detector of squares whose every score is known), real-model integration tests for every backend (bit-for-bit identity with YORU on CPU and CUDA), and tests of the window. What each group establishes is listed in [Validation]({{ '/reference/validation/' | relative_url }}).

A boundary test pins which YORU names YORU-Explain may use outside YORU's documented API, checks that YORU never imports YORU-Explain, that there is no `argparse`, that the core imports without PyTorch or a GUI toolkit, and that DearPyGui and tkinter are imported only in `gui/`.

## Continuous integration

Every push and pull request runs the tests on Windows (`windows-latest`), modelled on YORU Tracker's CI:

1. YORU-Explain and YORU are checked out side by side; YORU at the ref in the repository variable `YORU_REF`, or else its `yoru-tracker-lite` branch. A manual run can name any YORU ref.
2. `uv sync --locked` installs the locked environment; it fails if `uv.lock` no longer matches `pyproject.toml`.
3. The public test models are fetched and exported (not the torchvision COCO models, and not the fly model, so their tests skip).
4. `uv run pytest`.
