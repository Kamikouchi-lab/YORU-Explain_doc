# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) YORU contributors — see LICENSE for details.

"""Screenshots and figures for the site, made with YORU-Explain itself.

Opens YORU-Explain's own window on a demo project -- YORU's test video and the
YOLOv5 fly test model -- goes through the workflow the guides describe, and
saves the window at each step (``dpg.output_frame_buffer``), together with the
preview PNGs of the runs it makes.  Edit CONFIG, then run it with
YORU-Explain's environment::

    cd path/to/YORU-dev/YORU-Explain
    uv run python path/to/YORU-Explain_doc/scripts/make_screenshots.py

The window is open for about a minute.  The demo project, and YORU's settings
and logs for this session (``YORU_HOME``), go to CONFIG["demo"]: a neutral
path, so the screenshots show no user name.  Delete that folder afterwards.
"""

from __future__ import annotations

import csv
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIG = {
    "demo": Path(r"C:\Users\Public\YORU-Explain-demo"),
    "explain_repo": None,           # None: the checkout yoru_explain is imported from
    "video": None,                  # None: YORU's test_data/test_video_fly_copulation.mp4
    "model": None,                  # None: <YORU-Explain>/.cache/models/fly_copulation_yolov5s.pt
    "out": ROOT / "imgs",
    # Frames of YORU's test video: two solo flies, and a copulating pair.
    "solo_frame": 150,
    "copulation_frame": 6450,
}

os.environ["YORU_HOME"] = str(Path(CONFIG["demo"]) / ".yoru")

import cv2  # noqa: E402
import dearpygui.dearpygui as dpg  # noqa: E402
import numpy as np  # noqa: E402

import yoru_explain  # noqa: E402
from yoru_explain import __version__  # noqa: E402

REPO = Path(CONFIG["explain_repo"] or Path(yoru_explain.__file__).resolve().parents[2])
VIDEO = Path(CONFIG["video"] or REPO.parent / "YORU" / "test_data" / "test_video_fly_copulation.mp4")
MODEL = Path(CONFIG["model"] or REPO / ".cache" / "models" / "fly_copulation_yolov5s.pt")
DEMO = Path(CONFIG["demo"])
OUT = Path(CONFIG["out"])
HOT_PINK_BGR = (180, 105, 255)


class Driver:
    def __init__(self, app):
        self.app = app

    def frame(self) -> None:
        from yoru_explain.gui.main_window import run_callbacks

        run_callbacks(self.app, dpg.get_callback_queue())
        self.app.tick()
        dpg.render_dearpygui_frame()

    def pump(self, seconds: float = 0.4) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.frame()

    def wait(self, condition, what: str, timeout: float = 180.0) -> None:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.frame()
            if condition():
                self.pump(0.5)
                return
        raise SystemExit(f"timed out waiting for {what}")

    def shot(self, name: str) -> Path:
        for tag in self.app.popups.showing:
            print("closing a popup before the screenshot:", dpg.get_item_label(tag))
            self.app.popups.close(tag)
        self.pump(0.6)
        path = OUT / f"{name}.png"
        if path.exists():
            path.unlink()
        dpg.output_frame_buffer(file=str(path))
        end = time.monotonic() + 10
        while not path.exists() and time.monotonic() < end:
            self.frame()
        self.pump(0.3)
        print("screenshot", path)
        return path

    def errors(self):
        return [p for p in self.app.popups.shown if p[0] == "error"]


def zoom(view, box, frame_size, margin: float = 2.4) -> None:
    """Show *box* (frame px) enlarged, keeping the plot's aspect ratio."""
    w_px, h_px = dpg.get_item_rect_size(view.tag)
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    half_h = max(y2 - y1, (x2 - x1) * h_px / max(w_px, 1)) * margin / 2
    half_w = half_h * w_px / max(h_px, 1)
    fw, fh = frame_size
    cx = min(max(cx, half_w), fw - half_w) if 2 * half_w < fw else fw / 2
    cy = min(max(cy, half_h), fh - half_h) if 2 * half_h < fh else fh / 2
    dpg.set_axis_limits(view.x_axis, cx - half_w, cx + half_w)
    dpg.set_axis_limits(view.y_axis, cy - half_h, cy + half_h)


def unzoom(view) -> None:
    dpg.set_axis_limits_auto(view.x_axis)
    dpg.set_axis_limits_auto(view.y_axis)
    view.fit()


def make_project():
    from yoru_explain.io.project import Project

    for p in (VIDEO, MODEL):
        if not p.is_file():
            raise SystemExit(f"missing {p}")
    (DEMO / "videos").mkdir(parents=True, exist_ok=True)
    (DEMO / "models").mkdir(parents=True, exist_ok=True)
    video = DEMO / "videos" / VIDEO.name
    model = DEMO / "models" / MODEL.name
    for src, dst in ((VIDEO, video), (MODEL, model)):
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dst)
    root = DEMO / "fly_copulation"
    if root.exists():
        shutil.rmtree(root)
    project = Project.create(root)
    project.add_source(video)
    project.add_model(model, "yoru-yolov5", {"conf_thresh": 0.25, "iou_thresh": 0.45, "rgb_input": None})
    project.save()
    return root


def main(config=CONFIG) -> int:
    from yoru.gui_layout import GuiSession

    from yoru_explain.core.logs import setup_logging
    from yoru_explain.gui.main_window import WINDOW, ExplainApp
    from yoru_explain.io.project import Project

    OUT.mkdir(parents=True, exist_ok=True)
    root = make_project()
    setup_logging()
    app = ExplainApp()
    session = GuiSession("yoru_explain", f"YORU-Explain {__version__}", width=1500, height=920,
                         min_width=1100, min_height=700)
    session.begin()
    dpg.configure_app(manual_callback_management=True)
    runs = {}
    try:
        app.build()
        session.add_layout_menu(extra_builder=app.build_menus)
        session.finish(fill_window=WINDOW, on_resize=app.layout)
        app.session = session
        app.layout()
        d = Driver(app)
        st = app.state
        st.set_project(Project.open(root))
        d.pump(1.0)

        # Project: load the model.  (Not "Check seeking": on this video it
        # reports, correctly, that seeking is inexact, in a popup that would
        # stay over every screenshot.)
        pt = app.project_tab
        pt.models.select_row(0)
        pt.load_model()
        d.wait(lambda: st.adapter is not None and not st.tasks.busy, "the model")
        d.shot("gui_project")

        # Explore: the two solo flies of frame 150 become events ...
        app.show_tab("explore")
        ex = app.explore_tab
        solo = int(config["solo_frame"])
        ex.set_index(solo)
        d.wait(lambda: ex.frame is not None and ex.frame.frame_index == solo and ex.detections
               and ex._det_adapter is st.adapter, f"frame {solo}")
        ex.add_events(all_on_frame=True)
        # ... and the copulating pair of frame 6450, picked by a click on its box.
        cop = int(config["copulation_frame"])
        ex.set_index(cop)
        d.wait(lambda: ex.frame is not None and ex.frame.frame_index == cop and ex.detections
               and ex._det_adapter is st.adapter, f"frame {cop}")
        k = next(i for i, det in enumerate(ex.detections) if det.class_name == "copulation")
        x1, y1, x2, y2 = ex.detections[k].box
        ex._clicked((x1 + x2) / 2, (y1 + y2) / 2)
        d.pump(0.5)
        d.shot("gui_explore_select")
        ex.add_events(all_on_frame=False)
        d.pump(0.5)
        events = list(st.project.events)
        print("events:", [(e["event_id"], e["frame_index"], e["class_name"], e["score"]) for e in events])
        cop_event = next(e["event_id"] for e in events if e["class_name"] == "copulation")

        # Analyze: occlusion with the defaults (hot pink), on every event.
        app.show_tab("analyze")
        an = app.analyze_tab
        an.set_method("occlusion")
        an.run(selected_only=False)
        d.wait(lambda: dpg.get_value("ana_progress") >= 0.45 or not st.tasks.busy, "progress")
        d.shot("gui_analyze_running")
        d.wait(lambda: not st.tasks.busy, "the occlusion run")
        assert an.last_run is not None and an.last_run.status == "completed", dpg.get_value("ana_status")
        runs["occlusion"] = Path(an.last_run.run_dir)
        d.shot("gui_analyze")

        # Grad-CAM on every event.
        an.set_method("gradcam")
        d.pump(0.3)
        d.shot("gui_analyze_gradcam_settings")
        an.run(selected_only=False)
        d.wait(lambda: not st.tasks.busy, "the Grad-CAM run")
        assert an.last_run.status == "completed", dpg.get_value("ana_status")
        runs["gradcam"] = Path(an.last_run.run_dir)

        # The copulation event once more, with a black baseline.
        app.show_tab("explore")
        keys = ex.events.keys
        ex.events.click(keys.index(cop_event))
        d.pump(0.3)
        assert st.selected_events == [cop_event], st.selected_events
        app.show_tab("analyze")
        an.set_method("occlusion")
        dpg.set_value("ana_value", "0,0,0")
        an._value_typed()
        an.run(selected_only=True)
        d.wait(lambda: not st.tasks.busy, "the black-baseline run")
        runs["occlusion_black"] = Path(an.last_run.run_dir)
        dpg.set_value("ana_value", ",".join(str(v) for v in HOT_PINK_BGR))
        an._value_typed()

        # Explore: the results of the copulation event, zoomed on the pair.
        src = st.project.source(st.project.event(cop_event)["source_id"])
        frame_size = (int(src["width"]), int(src["height"]))
        for run_key, name in (("occlusion", "gui_explore_overlay"), ("gradcam", "gui_explore_gradcam")):
            st.showResult.emit(str(runs[run_key]), cop_event)
            d.wait(lambda: ex._result is not None and ex.frame is not None
                   and ex.frame.frame_index == cop, "the result view")
            dpg.set_value("exp_mode", "Overlay")
            ex.redraw()
            d.pump(0.5)
            zoom(ex.view, (x1, y1, x2, y2), frame_size, margin=1.6)
            d.shot(name)
            unzoom(ex.view)

        # Statistics of the occlusion run; Settings.
        app.show_tab("statistics")
        sp = app.statistics_tab
        sp.refresh()
        names = [Path(r).name for r in sp._run_dirs]
        label = sp._run_labels[names.index(runs["occlusion"].name)]
        dpg.set_value("stat_run", label)
        sp.show_run()
        d.shot("gui_statistics")
        app.show_tab("settings")
        app.settings_tab.refresh()
        d.shot("gui_settings")

        if d.errors():
            print("errors shown in the window:", d.errors())
    finally:
        try:
            app.shutdown()
        finally:
            dpg.destroy_context()

    figures(runs, root)
    return 0


def _event_rows(run_dir: Path):
    with open(run_dir / "results.csv", encoding="utf-8", newline="") as fh:
        return {r["event_id"]: r for r in csv.DictReader(fh)}


def figures(runs, root: Path) -> None:
    """The run previews, and the occluded frame of the largest drop."""
    from yoru_explain.io.project import Project

    project = Project.open(root)
    cop = next(e for e in project.events if e["class_name"] == "copulation")
    solo = next(e for e in project.events if e["class_name"] == "solo")
    # The pages show the copulating pair and the first solo fly.
    shown = {cop["event_id"], solo["event_id"]}
    for key, run_dir in runs.items():
        for png in sorted((run_dir / "previews").glob("*.png")):
            event_id = png.stem.split("__")[0]
            if event_id not in shown:
                continue
            dst = OUT / f"preview_{key}_{event_id}.png"
            shutil.copy2(png, dst)
            print("preview", dst)

    rows = _event_rows(runs["occlusion"])
    row = rows[cop["event_id"]]
    data = np.load(runs["occlusion"] / "maps" / f"{cop['event_id']}__occlusion.npz", allow_pickle=False)
    roi = [int(v) for v in data["roi"]]
    pid = int(row["max_delta_patch_id"])
    ids = list(int(v) for v in data["patch_id"])
    px0, py0, px1, py1 = (int(v) for v in data["patch_xyxy"][ids.index(pid)])
    with project.open_source(cop["source_id"]) as reader:
        image = reader.read(int(cop["frame_index"]), exact=True).image.copy()
    occluded = image.copy()
    occluded[py0:py1, px0:px1] = HOT_PINK_BGR
    x0, y0, x1, y1 = roi
    panels = []
    for img in (image, occluded):
        crop = img[y0:y1, x0:x1].copy()
        bx = [float(cop[k]) for k in ("x1", "y1", "x2", "y2")]
        cv2.rectangle(crop, (int(round(bx[0] - x0)), int(round(bx[1] - y0))),
                      (int(round(bx[2] - x0)), int(round(bx[3] - y0))), (0, 220, 255), 1, cv2.LINE_AA)
        scale = max(1, int(np.ceil(360 / max(crop.shape[:2]))))
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        panels.append(crop)
    gap = np.full((panels[0].shape[0], 16, 3), 255, np.uint8)
    out = np.hstack([panels[0], gap, panels[1]])
    path = OUT / "fig_occlusion_patch.png"
    cv2.imwrite(str(path), out)
    print("figure", path, "patch", pid, (px0, py0, px1, py1), "delta", row["delta_score"],
          "reference", row["reference_score"], "perturbed", row["perturbed_score"])
    for key in ("occlusion", "occlusion_black"):
        r = _event_rows(runs[key])[cop["event_id"]]
        print(key, {k: r[k] for k in ("original_score", "delta_score", "in_box_mean_delta",
                                         "out_box_mean_delta", "noop_delta", "full_region_score",
                                         "n_perturbations", "n_candidate_dropped")})
    g = _event_rows(runs["gradcam"])
    for eid, r in g.items():
        print("gradcam", eid, {k: r[k] for k in ("status", "gradcam_layer", "gradient_support",
                                                    "cam_in_box_fraction")})


if __name__ == "__main__":
    sys.exit(main())
