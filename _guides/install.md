---
title: Install
order: 1
description: YORU-Explain lives next to a YORU checkout and is installed with uv, as YORU-Tracker is.
---

## What you need

- **Windows 11.** It is the platform YORU-Explain is developed and verified on; other platforms are untested.
- **[uv](https://docs.astral.sh/uv/)**, which installs Python 3.10 and every package from the lock file. No conda environment is needed.
- **git**, to clone YORU and YORU-Explain.
- **A YORU checkout** of version {{ site.yoru_requirement }} or later that has YORU's YOLOv5 backend (`yoru/libs/yolov5`). YORU-Explain runs YORU's own code in process, so it needs YORU itself, not only its models.
- **Optionally an NVIDIA GPU.** PyTorch is installed as its CUDA 12.8 build; RTX 50-series cards need it. Without a GPU everything runs on the CPU.

## 1. Put YORU and YORU-Explain side by side

```text
YORU-dev/
├── YORU/            # https://github.com/Kamikouchi-lab/YORU (2.0.0b3 or later, with yoru/libs/yolov5)
└── YORU-Explain/    # https://github.com/Kamikouchi-lab/YORU-Explain
```

```bash
mkdir YORU-dev
cd YORU-dev
git clone https://github.com/Kamikouchi-lab/YORU.git
git clone https://github.com/Kamikouchi-lab/YORU-Explain.git
```

Then choose the YORU version. YORU's `yoru-tracker-lite` branch carries the external API that YORU's sister applications build on, together with the YOLOv5 backend, and it is the YORU that YORU-Explain's automatic tests run against:

```bash
git -C YORU checkout yoru-tracker-lite
```

<div class="callout info" markdown="1">
<p class="callout-title">Already using YORU-Tracker?</p>

Use the same `YORU-dev/YORU` checkout. YORU-Tracker and YORU-Explain both install YORU from `../YORU`, each into its own `.venv`.
</div>

## 2. Create the environment

```bash
cd YORU-Explain
uv sync
```

`uv sync` creates `YORU-Explain/.venv` with Python 3.10, YORU installed in editable mode from `../YORU`, and the CUDA 12.8 builds of `torch` and `torchvision` on Windows and Linux. The versions come from `uv.lock`, so every installation gets the same ones.

## 3. Start the application

```bash
uv run python -m yoru_explain
```

`uv run yoru-explain` does the same. The window opens on the *Project* tab; the [next page]({{ '/guides/project/' | relative_url }}) starts from there.

<div class="callout warning" markdown="1">
<p class="callout-title">Use <code>uv run</code>, not a bare <code>python</code></p>

On a Windows machine where `python` is the Microsoft Store stub, a bare `python -m yoru_explain` does not start the environment's Python. `uv run ...` (or `.venv\Scripts\python.exe`) always does.
</div>

There is no command line to learn: every setting is made in the window, or in Python ([Python API]({{ '/guides/python-api/' | relative_url }})).

## Without a sibling checkout

The built package depends on `yoru>=2.0.0b3,<3`, never on a local path. In an environment of your own, install YORU first, then YORU-Explain from its folder:

```bash
pip install "yoru @ git+https://github.com/Kamikouchi-lab/YORU"
pip install .
```

Install a PyTorch build that matches your CUDA version yourself in that case; `uv sync` does it for you.

## Check the installation

1. `uv run python -m yoru_explain` opens a window titled *YORU-Explain {{ site.version | remove: "v" }}* with five tabs.
2. The *Settings* tab lists the versions of YORU-Explain, YORU, PyTorch and the other packages, the GPU, and the adapters available for each YORU backend.
3. On the *Project* tab, **Add synthetic test model** and **Load selected model** load a small detector with known answers; it needs no weights and shows that the analysis runs ([Project]({{ '/guides/project/' | relative_url }})).

## Logs

YORU-Explain writes its log next to YORU's: `~/.yoru/logs/yoru_explain.log` (on Windows `C:\Users\<you>\.yoru\logs\`). The `YORU_HOME` environment variable moves both. Every analysis run also writes its own `logs/run.log` in its run folder, with tracebacks. **Help &rarr; Open log folder** opens the folder. Check these first when something fails.

## Updating

```bash
git -C ../YORU pull
git pull
uv sync
```

YORU and YORU-Explain are updated together: `uv sync` re-installs YORU from the checkout beside it.
