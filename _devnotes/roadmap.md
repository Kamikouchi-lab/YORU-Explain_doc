---
title: Roadmap
order: 3
description: What version 0.1 contains, and the concrete work planned after it, in order.
---

## v0.1 &mdash; this version

- An adapter for every YORU detection backend, each identical to YORU's own detector: YOLOv5 (YORU v1 models), ultralytics (YOLOv8 / YOLO11 / YOLOv5u / YOLOv10, with OBB, segmentation and pose), RT-DETR, torchvision (Faster R-CNN, Mask R-CNN, SSD300), ONNX; anything else as a black box.
- Fixed-candidate and re-detection scoring; occlusion sensitivity with controls; verified Grad-CAM.
- The DearPyGui window, like YORU's and YORU-Tracker's (the first window was PyQt5; DearPyGui since 2026-10-17).
- Reproducible run folders with provenance, and 330 tests.

## v0.2 &mdash; validity of the explanations

1. **Deletion and insertion curves** per event: remove (or add back) patches in the order of their occlusion Δ and record the score after each step, with the areas under the curves; random orderings as the null.
2. **Randomised controls**: the score change for random patches of the same total area as the top patches; background-only occlusion; the same analysis on a frame with the target region inpainted.
3. **Sensitivity to the settings**: a grid of baselines &times; patch sizes &times; strides on the same events, reporting the rank correlation and the overlap of the top regions between maps, and flagging events whose top region moves with the setting.
4. **Grad-CAM sanity checks**: cascading weight randomisation of a *copy* of the model (never the loaded one), and Grad-CAM against occlusion per event.
5. **Group analysis with hierarchy**: events carry video, animal and day; summaries are computed per animal or video first and only then across them. Frames are never treated as independent replicates, and the window states the unit used.
6. **Failure statistics**: per run and per class, the share of `disappeared`, `class_changed`, `ambiguous` and dropped-candidate patches, and the noise floor.
7. Resuming an interrupted run in place.

## v0.3 &mdash; regions with names

1. Import masks (label images, polygons) per frame or per track, and a polygon editor in *Explore*.
2. Region occlusion: replace a whole named region &mdash; wing, head, thorax, legs, background &mdash; with each baseline; area-normalised effects and matched-area random controls.
3. Optional external segmentation behind an adapter, with the masks stored and hashed like any input.
4. Association with independently measured morphology or kinematics, when such features are supplied &mdash; reported as association, not cause.

## v0.4 &mdash; YORU-Tracker

1. Read YORU-Tracker's track and detections CSVs; attach track IDs to events; select "all frames of track 7 between t0 and t1" as one set of events.
2. Per-track summaries over time, with frames still not treated as independent.
3. Further identity modes: fixed-candidate mode for RT-DETR (following the encoder token a query was selected from) and Faster R-CNN (following the RPN anchor); YOLO26 end to end once YORU's ultralytics runs it so; rotated occlusion regions for OBB targets.
4. Other methods, such as RISE, with the agreement between methods reported.

## Housekeeping

- Once YORU documents its YOLOv5 entry points, move `adapters/_yoru.py` to the documented names and drop the internal list.
