---
title: Output files
order: 2
description: What a project folder and a run folder contain, column by column. Data schema version 0.2.0.
---

```text
my_project/
├── project.json, events.csv
└── runs/<run_id>/
    ├── config.json        the request (method, parameters, score definition, seed)
    ├── manifest.json      provenance: versions, GPU, model sha256, input ids, identity check, counts
    ├── results.csv        one row per event
    ├── perturbations.csv  one row per occluded patch
    ├── maps/*.npz         maps and per-patch arrays + metadata
    ├── previews/*.png     original | heatmap | overlay (for viewing)
    └── logs/run.log
```

`run_id` is `YYYYMMDD-HHMMSS_<method>_<6 hex>`. Videos and weights are referenced by path and hash, never copied.

## Conventions

- **Schema version.** Every file carries `schema_version` (`0.2.0`): JSON files as a key, CSV tables as their **first column on every row**, NPZ archives in their `meta_json`. A reader should refuse a different major version. Projects and runs of 0.1.0 read unchanged.
- **Coordinates** are pixels of the frame the detector was given (after any flip), origin top-left, x right, y down. Boxes are `(x1, y1, x2, y2)` exactly as YORU reports them. Rotated boxes are YORU's `(cx, cy, w, h, angle)`, angle in radians from +x towards +y; empty for upright-box models. Patches are integer half-open rectangles `[x0, x1) × [y0, y1)`. Maps are `H × W` arrays in the same pixels.
- **Missing numbers** are empty CSV cells, JSON `null` or NaN in NPZ &mdash; never 0. NaN and infinity are never written as text.
- **Floats** in CSV are written with `repr`, so they read back exactly. **Booleans** are `true` / `false`. Text is UTF-8.

## project.json

| Key | Meaning |
|---|---|
| `schema_version`, `kind` (`yoru-explain-project`), `name`, `created` | |
| `sources[]` | `source_id` (`src-001`, ...), absolute `path`, `kind` (`video` / `image`), `v_flip`, `h_flip`, `size`, a quick id (SHA-256 of the size and the first and last 8 MiB), `width`, `height`, `fps` and `frame_count` as the container states them, `fourcc`, `seek_check`, attached `detections_files[]` |
| `models[]` | `model_id` (`mdl-001`, ...), `path`, `sha256` of the whole file, `adapter`, `options` (`conf_thresh`, `iou_thresh`; `rgb_input` for YOLOv5; `backend` for the black box) |

## events.csv

One row per detection chosen for explanation.

| Column | Meaning |
|---|---|
| `event_id` | `ev-0001`, ... |
| `source_id`, `frame_index` | the frame, counted from 0 in decoding order (YORU's `frame`) |
| `timestamp_ms` | the presentation time the decoder gave |
| `frame_sha1` | SHA-1 of the decoded, flipped pixels; empty for events imported from a CSV without decoding |
| `frame_access` | how the frame was read: `sequential`, `seek_verified`, `seek`, `image`, `unread` |
| `v_flip`, `h_flip`, `frame_width`, `frame_height` | |
| `model_id`, `detection_index` | the model, and the position in that frame's detection list |
| `class_id`, `class_name`, `x1`, `y1`, `x2`, `y2`, `score` | the detection as detected |
| `obb_cx` … `obb_angle` | its rotated box (OBB models) |
| `candidate_index`, `candidate_locator` | the pre-NMS candidate, and where it sits, as JSON (YOLOv5 `{level, stride, anchor, grid_y, grid_x}`, YOLOv8 `{level, stride, grid_y, grid_x}`, SSD, RT-DETR, Faster R-CNN their own) |
| `target_class` | the class whose score is explained |
| `track_id` | YORU's `tracking_id`, from an imported CSV |
| `origin` | `adapter` or `csv_import` |
| `note`, `created` | |

## config.json &mdash; what was asked

| Key | Meaning |
|---|---|
| `request` | the analysis request: `method`, `method_config`, `verify_identity`, `use_cache`, `write_previews`. `AnalysisRequest.from_dict(config["request"])` re-creates it. |
| `method_config` | the method's settings. Occlusion: `patch_size`, `stride`, `baseline {kind, value [B,G,R], sigma}`, `region`, `context_scale`, `score {score_type, identity_mode, iou_threshold}`, `batch_size`, `seed`, `include_ambiguous`. Grad-CAM: `layer`, `score_type`, `identity_mode` (always `fixed_candidate`), `precision`, `score_tolerance`. |
| `score_types`, `identity_modes` | the definitions, in words, of the scores and modes the run's model offers |
| `model_id`, `model_options`, `adapter`, `adapter_version`, `events`, `frame_access`, `seed` | |

## manifest.json &mdash; what it ran with, and how it ended

| Key | Meaning |
|---|---|
| `status` | `running` (while it runs, or the process was killed), `completed` (every event has a row), `cancelled`, `failed` (the identity check failed, or the run itself was interrupted) |
| `software` | versions of YORU-Explain, Python, NumPy, OpenCV, PyTorch, torchvision, YORU, ultralytics, ONNX Runtime, DearPyGui, and the git commits of the YORU and YORU-Explain checkouts |
| `hardware` | platform, CUDA / cuDNN versions, GPU names |
| `adapter` | name, version and capabilities: family, candidate kind, identity modes, score types with their definitions, the measured determinism and batch dependence, the gradient probe's verdict, notes and warnings |
| `model` | weights path, SHA-256, the YORU backend, class names, input size, thresholds, channel order, device, precision, and the family's own settings |
| `identity_check` | the adapter against YORU's own detector on the first frame: `status` (`passed`, `failed`, `not_applicable`), the number of detections of each, `max_abs_diff`, `exact`, the frame |
| `inputs[]` | the sources used, each with `verify {status: ok / changed / missing}` |
| `events`, `error_codes` | counts per result status and per error code |

## results.csv &mdash; one row per event

**results.csv is the record of what finished.** An event's files and its `perturbations.csv` rows are written before its `results.csv` row; rows of an event whose result is not `ok` are not to be used.

| Column | Occlusion | Grad-CAM |
|---|---|---|
| identification | `run_id`, `event_id`, `video_id`, `source_path`, `frame_index`, `timestamp_ms`, `frame_sha1`, `detection_id`, `candidate_index`, `track_id`, `behavior_class`, `class_id`, `target_class`, the box and rotated box | same |
| `stored_score`, `reproduction`, `reproduction_iou` | how the stored detection was found again: `same_candidate`, `iou`, `iou_candidate_changed`, `iou_other_model` | same |
| `method`, `method_kind`, `score_type`, `identity_mode`, `baseline` | `occlusion`, `perturbation_effect`, ... | `gradcam`, `attribution`, ..., `fixed_candidate` |
| `original_score` | the target's score on the unchanged frame at batch size 1 | the score in the inference pass |
| `reference_score` | the same at the run's batch size: the reference of every Δ | as original |
| `perturbed_score`, `delta_score`, `max_delta_patch_id` | the patch with the largest Δ | &mdash; |
| `delta_min`, `delta_mean` | over the counted patches | &mdash; |
| `in_box_mean_delta`, `out_box_mean_delta` | the map's mean over defined pixels inside / outside the box | &mdash; |
| `noop_delta` | Δ of the unchanged frame through the batch pipeline (expected exactly 0) | &mdash; |
| `full_region_score`, `full_region_status` | the whole region replaced | &mdash; |
| `n_perturbations`, `n_counted`, `n_ok`, `n_matched`, `n_ambiguous`, `n_class_changed`, `n_unmatched`, `n_disappeared`, `n_non_finite`, `n_error` | patches, and patches per status | &mdash; |
| `n_candidate_dropped` | fixed-candidate: patches after which NMS would no longer keep the candidate | &mdash; |
| `matching_status` | how the target scored on the unchanged frame | `ok` |
| `gradcam_layer`, `gradcam_stride`, `gradient_support`, `gradient_score`, `cam_max`, `cam_in_box_fraction` | &mdash; | the layer and its stride, cells with a non-zero gradient, the gradient-pass score, the CAM maximum, the CAM mass inside the box |
| outcome | `status` (`ok`, `failed`, `cancelled`), `error_code`, `message`, `map_file`, `preview_file`, `cache_key`, `cached_from`, `elapsed_s` | same |

## perturbations.csv &mdash; one row per occluded input

| Column | Meaning |
|---|---|
| `event_id`, `patch_id` | patches are numbered row by row from 0; the controls are `-1` (`noop`) and `n` (`full_region`) |
| `kind` | `patch`, `noop`, `full_region` |
| `x0`, `y0`, `x1`, `y1` | the replaced rectangle |
| `pixel_change` | the mean absolute change of the replaced pixels, 0&ndash;255 |
| `status` | `ok`, `matched`, `ambiguous`, `class_changed`, `unmatched`, `disappeared`, `non_finite`, `error` ([Statuses]({{ '/methods/what-is-measured/' | relative_url }}#statuses)) |
| `perturbed_score`, `delta_score`, `counted` | the score the Δ was taken from, the Δ, and whether the row entered the map; empty when not counted |
| `iou` | re-detection: IoU of the matched detection with the original box; fixed-candidate: IoU of the candidate's moved box |
| `candidate_index`, `candidate_kept`, `candidate_class` | fixed-candidate: whether NMS keeps the candidate, and its current best class |
| `matched_x1` … `matched_angle`, `matched_score`, `matched_class`, `n_overlapping` | re-detection: the matched (or best-overlapping) detection, and how many same-class detections overlapped enough |
| `error_code` | |

## Error codes {#error-codes}

Every failure is reported with one of these codes &mdash; in `results.csv`, in `perturbations.csv` and in the run log &mdash; and never turned into a score.

| Code | Meaning |
|---|---|
| `model_unsupported` | the model, or the requested method or score, is not supported by the adapter |
| `model_load_failed` | the model could not be loaded |
| `gradients_unavailable` | gradients could not be obtained, or were not verified, for this model |
| `score_unavailable` | the requested score cannot be read for this target (e.g. no candidate) |
| `score_mismatch` | a score recomputed on the same input differs from the reference (e.g. the gradient pass from the inference pass) |
| `target_not_reproduced` | the stored detection was not found again on its frame |
| `frame_mismatch` | the decoded frame is not the frame the event was made from |
| `preprocess_mismatch` | the adapter's preprocessing does not reproduce YORU's inference |
| `identity_check_failed` | the adapter's detections differ from YORU's own detector |
| `non_finite` | NaN or infinity where a number was expected |
| `cuda_oom` | out of GPU memory: try a smaller batch size |
| `missing_data` | something the project needs (video, model, event field) is missing |
| `invalid_config` | the settings are not valid |
| `output_failed` | computed, but the files could not be written (disk full, path too long); none are left behind |
| `cancelled` | the run was cancelled before this event |
| `internal_error` | anything else; the traceback is in `logs/run.log` |

## Map files

`maps/<event_id>__occlusion.npz` &mdash; open with `numpy.load(path, allow_pickle=False)`:

| Array | dtype, shape | Meaning |
|---|---|---|
| `delta_map` | float32 H&times;W | the mean Δ of the counted patches covering each pixel; NaN where none |
| `coverage`, `coverage_all` | uint16 H&times;W | counted patches, and all patches, covering each pixel |
| `lost_fraction` | float32 H&times;W | `1 − coverage / coverage_all`; NaN outside the region |
| `patch_id`, `patch_xyxy` | int32 P, P&times;4 | the patches |
| `patch_score`, `patch_delta` | float64 P | the score used for Δ, and Δ; NaN when not counted |
| `patch_counted`, `patch_status`, `patch_pixel_change` | bool, int8, float32 P | per patch |
| `target_box`, `target_obb`, `roi`, `frame_shape` | | the target, the region the patches tile, the frame size |
| `meta_json` | str | the definitions, the coordinate system, the status codes, the reference score, the settings, the target |

`maps/<event_id>__gradcam.npz`: `cam` (float32 H&times;W, the ReLU map in frame pixels), `cam_feature` (float32 h&times;w, the signed CAM on the layer's grid), `target_box`, `target_obb`, `frame_shape`, and `meta_json` with the layer, its stride, the frame-to-input transform, the gradient-pass score and the gradient support.

## Previews and logs

`previews/<event_id>__<method>.png` shows the frame, the map and the overlay, with the colour scale and the run's settings printed under them. They are for viewing; the numbers are in the NPZ and CSV files. `logs/run.log` holds everything logged during the run, tracebacks included.
