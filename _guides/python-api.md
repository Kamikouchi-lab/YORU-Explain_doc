---
title: Python API
order: 6
description: Everything the window does, without the window. The GUI calls these same functions, so a script and a click give the same files.
---

## The workflow in a script

```python
from yoru_explain import api

adapter = api.load_model("best.pt", device="auto")      # any YORU model; backend as YORU picks it
project = api.Project.open_or_create("my_project")
src = project.add_source("video.mp4")
mdl = project.add_model("best.pt", adapter.name)
ev = api.add_event(project, adapter, mdl.model_id, src["source_id"], frame_index=6450, detection_index=0)
project.save()
outcome = api.run_analysis(project, adapter, mdl.model_id, [ev], api.AnalysisRequest("occlusion"))
print(outcome.status, outcome.identity_check)
```

`outcome.run_dir` is the run folder, laid out as in [Output files]({{ '/reference/output-files/' | relative_url }}); the project now lists the run, and the window shows it.

## Loading a model

```python
adapter = api.load_model("best.pt", backend="auto", device="auto",
                         conf_thresh=0.25, iou_thresh=0.45)
```

| Argument | Meaning |
|---|---|
| `backend` | A YORU backend: `auto` (what YORU's `get_detector("auto", ...)` would pick), `yolov5`, `ultralytics`, `rtdetr`, `torchvision`, `onnx` |
| `device` | `auto`, `cuda` or `cpu` |
| `black_box=True` | Explain YORU's `detect()` only: re-detection, no Grad-CAM, for any model YORU loads |
| `conf_thresh`, `iou_thresh` | As YORU applies them |
| `rgb_input` | YOLOv5 only: `None` follows YORU's rule, `False` BGR (YORU v1), `True` RGB |

`adapter.capabilities` says what the model offers: `family`, `candidate_kind`, `identity_modes`, `score_types`, `gradients` and its reason, `batch_invariant`, `warnings`. `api.load_adapter(name, weights, ...)` loads a named adapter directly, e.g. `api.load_adapter("toy-grid", device="cpu")` for the synthetic detector.

## Settings

Settings are dataclasses with `to_dict()` / `from_dict()`, so they can be kept in JSON; `from_dict` refuses unknown keys. Every field has the default the window shows.

```python
request = api.AnalysisRequest(
    method="occlusion",                       # or "gradcam"
    occlusion=api.OcclusionConfig(
        patch_size=(32, 32), stride=(16, 16),
        baseline=api.BaselineSpec(kind="constant", value=(180, 105, 255)),   # B,G,R: hot pink
        region="context", context_scale=3.0,
        score=api.ScoreDefinition(score_type="confidence", identity_mode="fixed_candidate",
                                  iou_threshold=0.5),
        batch_size=1, seed=0, include_ambiguous=False),
    gradcam=api.GradCamConfig(layer="auto", score_type="confidence", precision="inference"),
    verify_identity=True, use_cache=True, write_previews=True)
```

A run's `config.json` holds its request: `api.AnalysisRequest.from_dict(config["request"])` re-creates it exactly.

## Events from a YORU CSV

```python
added = api.add_events_from_detections_csv(project, src["source_id"], "video_detections.csv",
                                           model_id=mdl.model_id, class_names=["copulation"],
                                           limit=100)
project.save()
```

Such events carry neither a pre-NMS candidate nor a frame hash. The run decodes the frame, runs the detector and must find each box again (same class, IoU &ge; 0.9), or reports `target_not_reproduced`.

## Reading a run

```python
reader = api.RunReader(outcome.run_dir)
for row in reader.typed_results():            # results.csv, numbers as numbers, empty cells as None
    print(row["event_id"], row["status"], row["original_score"], row["delta_score"])

row = reader.result(ev)
maps = reader.load_map(row["map_file"])       # the NPZ arrays, plus "meta"
delta = maps["delta_map"]                     # float32 H x W, NaN where no patch was counted
patches = reader.perturbations(ev)            # perturbations.csv rows of this event
```

The NPZ files open with NumPy alone as well: `numpy.load(path, allow_pickle=False)`.

## One frame, no files

`api.explain(adapter, image, target, request)` runs one method on one image in memory and returns the result object (the map, the patches, the controls), writing nothing. `api.target_from_detection(detection, index, image)` makes the target from a detection of `adapter.detect(image)`.

## Example scripts

The repository's `examples/` folder has three complete scripts; each has a `CONFIG` at the top to edit.

| Script | Does |
|---|---|
| `synthetic_occlusion.py` | Occlusion and Grad-CAM on the synthetic detector, where the answer is known. No weights or video needed. |
| `yolov5_video_event.py` | One YOLOv5 detection on one video frame: occlusion and Grad-CAM, saved as a project |
| `any_model_image.py` | One detection of a model of any YORU backend on one image |

```bash
uv run python examples/synthetic_occlusion.py
```

There is deliberately no command-line interface: settings live in dataclasses and JSON, and `yoru_explain.app.main()` takes its options as function arguments.
