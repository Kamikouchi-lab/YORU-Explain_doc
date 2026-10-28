---
title: Grad-CAM
order: 3
description: A gradient-weighted feature map of the detection's score — an attribution, offered only for models whose gradient path was verified.
---

## Definition

For the candidate's score *s* and the feature map *A* of a layer (channels *c*, cells *i, j*):

```text
α_c      = mean over i, j of  ∂s / ∂A_c(i, j)
CAM      = Σ_c  α_c · A_c
Grad-CAM = max(CAM, 0)
```

The map file keeps both: `cam_feature`, the signed CAM on the layer's grid, and `cam`, the ReLU upsampled bilinearly (cell *(i, j)* centred on input pixel *((j+½)·stride, (i+½)·stride)*, where *stride* is the layer's stride in input pixels), cropped by the input padding and resized to the frame.

<figure>
  <img src="{{ '/imgs/preview_gradcam_ev-0003.png' | relative_url }}" alt="Grad-CAM of a copulation detection">
  <figcaption><strong>Grad-CAM of the copulation detection</strong> (YOLOv5, default layer <code>model.23</code>, stride 32). Left to right: the frame, the map, the map over the frame. 99.9% of the map's mass lies in the box.</figcaption>
</figure>

## Which layer

By default, the feature map the candidate's score is computed from:

| Family | Default layer |
|---|---|
| YOLOv5 | the input of the `Detect` head at the candidate's own level (`model.17`, `model.20` or `model.23` for v5s-sized models) |
| YOLOv8, YOLO11, YOLOv5u, YOLOv10 | the head's input at the candidate's level (YOLOv10: through the one-to-one branch that produced the score) |
| RT-DETR | the decoder input at the level of the query's encoder token |
| Faster / Mask R-CNN | the FPN level the proposal is pooled from |
| SSD | the backbone level of the default box |
| ONNX, black box | none: no gradients |

Other layers whose maps tile the input can be chosen in *Analyze*. On one frame a query or a proposal is a well-defined candidate, so Grad-CAM is offered for RT-DETR and Faster R-CNN although fixed-candidate occlusion is not.

## When a map is made

A map is produced only if

1. the gradient probe passed when the model was loaded;
2. the target has its candidate;
3. the score in the gradient pass equals the inference score (within `score_tolerance`, 10<sup>&minus;4</sup>; the measured difference is 0);
4. the gradient is finite and not zero everywhere;
5. the map is finite.

Otherwise the result is `failed`, with an error code and no map.

## The model is never changed

Grad-CAM never puts a model in training mode and never changes its weights; the gradients are taken with respect to activations, from a copy of the input. After every Grad-CAM test the weights (state-dict SHA-256), the evaluation mode of every module and the detections were unchanged, and no parameter had a gradient.

## Where the gradient reaches {#gradient-support}

`gradient_support` in `results.csv` is the number of cells of the layer where the score's gradient is not zero. It decides what the map can show.

YOLOv5's `Detect` head is a 1&times;1 convolution, so at its input the gradient is non-zero at **exactly one cell**. The map then shows where the channels *that cell* relies on are active anywhere in the frame &mdash; on another fly of the same class as much as on the target:

<figure>
  <img src="{{ '/imgs/preview_gradcam_ev-0001.png' | relative_url }}" alt="Grad-CAM of one of two solo flies, bright on both">
  <figcaption><strong>One of two solo flies</strong> (frame 150, layer <code>model.20</code>, gradient at 1 cell). The map is as bright on the other fly as on the detected one: 50% of its mass lies in the box. The same happens for the second fly. This is what the method measures here, not a failure.</figcaption>
</figure>

Other heads spread the gradient over more cells (measured on the test models):

| Model | Default layer (stride) | Cells with gradient |
|---|---|---|
| YOLOv5 | `model.23` (32) | 1 |
| YOLOv5, earlier layers | `model.17`, `model.9` | 49&ndash;361 |
| YOLOv8n, YOLO11n, YOLOv5u, YOLOv10n (and seg, pose) | head input (32) | 25 |
| YOLO11n-OBB | `model.16` (8) | 15 |
| RT-DETR-L | `model.27` (32) | 342 |
| Faster R-CNN | `backbone.fpn.2` (16) | 280 |
| Mask R-CNN | `backbone.fpn.2` (16) | 252 |
| SSD300 | `backbone.2` (32) | 9 |

## Grad-CAM and occlusion are different measurements

Grad-CAM is an **attribution**: a statement about the gradient of the score at one layer. Occlusion is a **perturbation effect**: what happens to the score when the image is edited. They need not agree, and neither is the other's ground truth. Sanity checks of Grad-CAM (weight randomisation) and per-event comparisons with occlusion are planned ([Roadmap]({{ '/devnotes/roadmap/' | relative_url }})).
