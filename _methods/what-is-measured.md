---
title: What is measured
order: 1
description: "“How does this detection’s score depend on the frame?” needs three definitions before it is a measurement: which score, which detection, and how that detection is followed when the frame changes."
---

## The score

By default the explained score is `confidence`: in every model family, the number YORU reports for the detection, computed the way that family computes it. On the unchanged frame it equals YORU's reported confidence **bit for bit**.

| YORU backend | Models | Candidate | `confidence` is | Identity modes | Grad-CAM |
|---|---|---|---|---|---|
| `yolov5` | YOLOv5 (YORU v1) | anchor slot | &sigma;(objectness) &times; &sigma;(class logit) | fixed, re-detection | yes |
| `ultralytics` | YOLOv8, YOLO11, YOLOv5u, YOLOv10; OBB, seg, pose | anchor point | &sigma;(class logit) | fixed, re-detection | yes |
| `rtdetr` | RT-DETR | decoder query | &sigma;(class logit) | re-detection | yes |
| `torchvision` | Faster / Mask R-CNN | region proposal | softmax over classes + background | re-detection | yes |
| `torchvision` | SSD300 | default box | softmax over classes + background | fixed, re-detection | yes |
| `onnx` | ONNX exports of YOLOv5 / YOLOv8 / YOLO11 | output row | as exported | fixed, re-detection | no |
| any | anything YORU loads, as a black box | &mdash; | YORU's reported conf | re-detection | no |

Other scores can be explained where the family has them:

| Score | Definition |
|---|---|
| `obj_x_cls` | &sigma;(objectness) &times; &sigma;(class logit) &mdash; the confidence YOLOv5 reports |
| `cls_prob` | &sigma;(class logit) &mdash; the confidence YOLOv8 / YOLO11 / RT-DETR report; for YOLOv5, the class probability given an object |
| `obj_prob` | &sigma;(objectness) &mdash; the class-agnostic object probability (YOLOv5) |
| `cls_softmax` | softmax over the classes and the background &mdash; the confidence of torchvision's Faster R-CNN, Mask R-CNN and SSD |
| `cls_logit` | the class logit, before the sigmoid or softmax |
| `obj_logit` | the objectness logit, before the sigmoid (YOLOv5) |

Each run writes the definitions of the scores its model offers into `config.json`, and `results.csv` names the one used.

## The candidate

Before NMS, a detector scores thousands of **candidates** &mdash; anchor slots, anchor points, queries, proposals, default boxes &mdash; and NMS keeps a few of them as detections. YORU-Explain recovers, for every detection, the candidate it came from, exactly: for YOLOv5 the one candidate whose box equals the NMS output bit for bit; for the ultralytics models the indices NMS itself returns; for SSD, Faster R-CNN and ONNX the exact equality of box and score. An event stores that candidate and where it sits (for YOLOv5: level, stride, anchor and grid cell).

Reading the candidate on the unchanged frame gives the detection's reported confidence bit for bit. That is what makes "the score of *this* detection" well defined.

## Following the detection on a changed frame {#identity-modes}

Occlusion changes the frame, so the detection has to be found again on every changed frame. There are two ways, and they answer different questions.

<div class="flow">
  <div class="flow-row">
    <p class="flow-title">Fixed-candidate</p>
    <div class="flow-steps">
      <div class="flow-step">Frame with a region replaced</div>
      <div class="flow-step">Forward pass: every candidate is scored</div>
      <div class="flow-step key">Read <b>the same candidate</b> <i>k</i> and class <i>c</i></div>
      <div class="flow-step end">Its score &mdash; always defined; plus: would NMS still keep it? how far did its box move?</div>
    </div>
  </div>
  <div class="flow-row">
    <p class="flow-title">Re-detection</p>
    <div class="flow-steps">
      <div class="flow-step">Frame with a region replaced</div>
      <div class="flow-step">The detector end to end, NMS and threshold included</div>
      <div class="flow-step key">Find <b>exactly one</b> detection of class <i>c</i> with IoU &ge; 0.5 to the original box</div>
      <div class="flow-step end">Its confidence &mdash; or a status and <b>no score</b></div>
    </div>
  </div>
</div>

**Fixed-candidate** (default where offered) asks *how does this candidate's score change?* The same candidate is read on every changed frame, so its score always exists. The run also records whether NMS would still keep it (`candidate_kept`), the IoU of its moved box with the original, and its current best class. This mode needs a candidate that is a fixed slot &mdash; an anchor slot, anchor point, default box or output row. RT-DETR's queries and Faster R-CNN's proposals are chosen anew for every input, so "the same candidate" on a changed frame is not defined; those models refuse this mode before a run starts and are followed by re-detection.

**Re-detection** asks *does the detector still report this box, and with what confidence?* The detector runs as in YORU, and its output is matched to the original detection: same class, IoU &ge; 0.5 (rotated boxes of OBB models by the exact IoU of the two rotated rectangles). When there is no unique match, the patch gets a status instead of a score.

The two modes give different numbers. On YORU's test video, wherever NMS dropped the fixed candidate, re-detection matched a *different* candidate, and the per-patch changes of the two modes differed by up to 0.20.

## Statuses {#statuses}

| Status | Mode | Scored? | Meaning |
|---|---|---|---|
| `ok` | fixed-candidate | yes | the candidate's score was read |
| `matched` | re-detection | yes | exactly one same-class detection with IoU &ge; the threshold |
| `ambiguous` | re-detection | only if asked | two or more such detections |
| `class_changed` | re-detection | no | only detections of another class overlap enough |
| `unmatched` | re-detection | no | something overlaps the box, but below the threshold |
| `disappeared` | re-detection | no | nothing overlaps the box |
| `non_finite` | both | no | NaN or infinity |
| `error` | both | no | see the error code |

<div class="callout" markdown="1">
<p class="callout-title">A lost detection has no score &mdash; never 0</p>

A detection that vanished may have been suppressed under a neighbour, or may sit just below the threshold: its score is unknown, not 0. Lost, ambiguous and failed targets are written as empty cells (NaN in maps) with their status and error code, so nothing missing can be averaged in as a zero.
</div>

## Never "the best box of the class"

The best box of the class anywhere in the frame is never used as the target. With two flies of one class it would follow whichever is stronger: in a test with two same-class squares, hiding one lowered its own score by up to 0.49, while "the best box of the class" reported no change at all.

## The same detections as YORU {#identity-check}

Each adapter runs its family exactly as YORU's backend does, calling the family's own functions &mdash; YORU's bundled YOLOv5 code, ultralytics' NMS and box scaling, torchvision's model pieces &mdash; rather than copies of them. Every run then checks this (unless the check is unticked on the *Analyze* tab): on its first frame it loads YORU's own detector, compares every box, confidence and class (and rotated box), and **stops if they differ**. The result is written to the run's manifest as the *identity check*. For every test model, on the CPU and on CUDA, the two were equal bit for bit ([Validation]({{ '/reference/validation/' | relative_url }})).

A black-box model *is* YORU's detector, so its check is `not_applicable`.
