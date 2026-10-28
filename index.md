---
layout: default
title: Home
description: >-
  YORU-Explain measures which parts of a video frame the score of one YORU
  detection depends on: occlusion sensitivity and verified Grad-CAM, for
  every YORU detection backend.
---

<div class="hero">
  <img class="hero-logo only-dark" src="{{ '/logos/YORU-Explain_logo_dark.png' | relative_url }}" alt="YORU-Explain">
  <img class="hero-logo only-light" src="{{ '/logos/YORU-Explain_logo_light.png' | relative_url }}" alt="YORU-Explain">
  <p class="lead">Which parts of the frame does the detector's score for <em>this</em> detection depend on, and by how much?</p>
  <div class="button-row">
    <a class="button primary" href="{{ '/guides/install/' | relative_url }}">Get started</a>
    <a class="button" href="{{ '/methods/what-is-measured/' | relative_url }}">How it works</a>
    <a class="button blue" href="{{ site.github.repo }}">GitHub</a>
  </div>
</div>

<figure>
  <img src="{{ '/imgs/preview_occlusion_ev-0003.png' | relative_url }}" alt="Occlusion sensitivity of a copulation detection: the frame, the map of score changes, and the map over the frame">
  <figcaption><strong>One detection, explained.</strong> A YOLOv5 model detects copulation (score 0.896) in a frame of YORU's test video. Square patches of 32 pixels, every 16 pixels around the pair, were replaced by hot pink one at a time, and the change in the detection's score is mapped: red where hiding the patch lowers the score, blue where it raises it. Left to right: the frame, the map, the map over the frame &mdash; the preview YORU-Explain writes for every result.</figcaption>
</figure>

## YORU-Explain

YORU-Explain is a sister application of [YORU](https://kamikouchi-lab.github.io/YORU_doc/), like [YORU-Tracker](https://github.com/Kamikouchi-lab/YORU-Tracker): its own window, its own command, YORU unchanged. It loads a model of any of YORU's detection backends the way YORU runs it, checks that it detects exactly what YORU detects, lets you pick one detection on a video frame, and measures

- **Occlusion sensitivity** &mdash; the change in that detection's score when a region of the frame is replaced by a baseline (a *perturbation effect*);
- **Grad-CAM** &mdash; a gradient-weighted feature map of that score (an *attribution*), offered only for models whose gradient path was verified.

<div class="callout" markdown="1">
<p class="callout-title">One model's score &mdash; not biology</p>

Both methods are about **one model's score** for one detection. Neither is evidence of what the animal does or which body part matters biologically; a map that does not highlight the wing is a measurement, not a failure. See [Reading the results]({{ '/methods/interpretation/' | relative_url }}).
</div>

## Part of the YORU family

<div class="family">
{% for app in site.data.ecosystem %}
  <div class="family-card{% if app.current %} current{% endif %}" style="--app-accent: {{ app.accent }}">
    <h3>{{ app.name }}{% if app.current %}<span class="badge">this site</span>{% endif %}</h3>
    <p>{{ app.purpose }}</p>
    <code>{{ app.launch }}</code>
    <div class="family-links">{% if app.docs %}<a href="{{ app.docs }}">Documentation</a> &middot; {% endif %}<a href="{{ app.repo }}">GitHub</a></div>
  </div>
{% endfor %}
</div>

The three applications are installed side by side in one folder and look like siblings: each window is YORU's navy DearPyGui theme with its own accent &mdash; YORU blue, YORU-Tracker's teal, YORU-Explain's hot pink. YORU never imports YORU-Explain; YORU-Explain runs YORU's detectors through YORU's own code and checks itself against them.

| | YORU | YORU-Tracker | YORU-Explain |
|---|---|---|---|
| Purpose | detection, closed loop | identity, trajectories | why a detection scores as it does |
| Launch | `python -m yoru` | `python -m yoru_tracker` | `python -m yoru_explain` |
| GUI | DearPyGui | DearPyGui | DearPyGui |
| Accent | <span class="swatch" style="background:#194682"></span>YORU blue | <span class="swatch" style="background:#48c9be"></span>teal | <span class="swatch" style="background:#ff69b4"></span>hot pink |

## Versions

| | Version | Notes |
|---|---|---|
| **YORU-Explain** | {{ site.version }} | First version, in development; no release has been tagged yet |
| **YORU** (needed) | {{ site.yoru_requirement }} or later | A 2.0 version with the YOLOv5 backend (`yoru/libs/yolov5`); see [Install]({{ '/guides/install/' | relative_url }}) |

## Features

<div class="features">
  <div class="feature">
    <h3>Every YORU backend</h3>
    <p>YOLOv5 (YORU v1 models); YOLOv8, YOLO11, YOLOv5u, YOLOv10 with detect, rotated-box OBB, segmentation and pose; RT-DETR; Faster R-CNN, Mask R-CNN, SSD; ONNX exports. Anything else YORU loads runs as a black box.</p>
  </div>
  <div class="feature">
    <h3>Identical to YORU</h3>
    <p>Each model runs exactly as YORU runs it. By default every run first compares the detections with YORU's own detector, bit for bit, and stops if they differ.</p>
  </div>
  <div class="feature">
    <h3>The detection itself</h3>
    <p>The explained score is that of the pre-NMS candidate the detection came from &mdash; never "the best box of the class", which would follow whichever of two flies is stronger.</p>
  </div>
  <div class="feature">
    <h3>No score is never zero</h3>
    <p>A target that disappears, becomes ambiguous or fails gets a named status and no number. Nothing missing is written as 0.</p>
  </div>
  <div class="feature">
    <h3>Reproducible runs</h3>
    <p>Each run folder holds the request, the provenance (versions, GPU, model SHA-256, frame hashes, the identity check) and tables that carry their schema version.</p>
  </div>
  <div class="feature">
    <h3>Window and Python</h3>
    <p>A DearPyGui window like YORU's, which never blocks while a run is going, and a Python API &mdash; the same functions the window calls.</p>
  </div>
</div>

## Quick install

YORU-Explain needs a YORU checkout next to it, as YORU-Tracker does. With [uv](https://docs.astral.sh/uv/):

```bash
mkdir YORU-dev
cd YORU-dev
git clone https://github.com/Kamikouchi-lab/YORU.git
git -C YORU checkout yoru-tracker-lite
git clone https://github.com/Kamikouchi-lab/YORU-Explain.git
cd YORU-Explain
uv sync
uv run python -m yoru_explain
```

`uv sync` creates `.venv` with YORU installed (editable) from `../YORU` and the CUDA 12.8 build of PyTorch on Windows and Linux. The [install guide]({{ '/guides/install/' | relative_url }}) has the details and the route without a sibling checkout.

## Learn about YORU-Explain

- [User guide]({{ '/guides/install/' | relative_url }}) &mdash; install, then the five tabs of the window: Project, Explore, Analyze, Statistics, Settings; and the Python API
- [How it works]({{ '/methods/what-is-measured/' | relative_url }}) &mdash; what exactly is measured, occlusion sensitivity, Grad-CAM, and how to read the results
- [Reference]({{ '/reference/backends/' | relative_url }}) &mdash; supported models, output files, what has been validated
- [Q&amp;A]({{ '/troubleshooting/' | relative_url }}) and [Screenshots]({{ '/screenshots/' | relative_url }})
- [Development notes]({{ '/devnotes/architecture/' | relative_url }}) &mdash; architecture, tests, roadmap

## Requirements

### OS
- Windows 11 (verified). Other platforms are untested.

### Software
- Python 3.10 (uv provides it)
- YORU {{ site.yoru_requirement }} or later with `yoru/libs/yolov5`, checked out next to YORU-Explain

### Hardware
- An NVIDIA GPU is optional: everything also runs on the CPU, more slowly. PyTorch is installed as its CUDA 12.8 build, which RTX 50-series cards need.

### Development environment
- Windows 11, Python 3.10.22, torch 2.11.0+cu128, ultralytics 8.3.222, torchvision 0.26.0, onnxruntime 1.23.2, DearPyGui 1.11.1
- GPU: NVIDIA GeForce RTX 5060 Ti (results also checked on the CPU)

## Reference

- Hayato M. Yamanouchi et al., YORU: Animal behavior detection with object-based approach for real-time closed-loop feedback. *Sci. Adv.* 12, eadw2109 (2026). [DOI:10.1126/sciadv.adw2109](https://www.science.org/doi/10.1126/sciadv.adw2109)
- M. D. Zeiler, R. Fergus, Visualizing and understanding convolutional networks. *ECCV* (2014) &mdash; occlusion sensitivity.
- R. R. Selvaraju et al., Grad-CAM: Visual explanations from deep networks via gradient-based localization. *ICCV* (2017).

## License

AGPL-3.0-or-later. YORU-Explain runs YORU's AGPL code in process, including the bundled YOLOv5, and ultralytics (AGPL-3.0), torchvision (BSD-3-Clause) and ONNX Runtime (MIT), with which YORU runs its other backends. DearPyGui is MIT.
