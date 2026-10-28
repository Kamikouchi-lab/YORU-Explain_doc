---
title: Occlusion sensitivity
order: 2
description: Replace one region of the frame at a time with a baseline and record how the detection's score changes. The result is a perturbation effect, mapped.
---

## Definition

For a rectangle *R* of the frame *x*, replaced by a baseline *b*:

```text
Δ(R) = s_ref − s(x with R replaced by b)
```

- **s_ref** is the detection's score on the unchanged frame, evaluated at the run's batch size. At batch size 1 (the default) it is the confidence YORU reports.
- **Patches** of `patch_size` tile the region with `stride`; the last row and column are aligned to the region's edge so that every pixel is covered.
- **The map** gives each pixel the mean Δ of the counted patches covering it, and NaN where no counted patch covers it. A patch is counted when its score exists (`ok`, `matched`; `ambiguous` only on request).
- **Signs are kept.** Δ &gt; 0: hiding *R* lowers the score. Δ &lt; 0: hiding *R* raises it.

<figure>
  <img src="{{ '/imgs/fig_occlusion_patch.png' | relative_url }}" alt="The region around a copulating pair, and the same region with one hot-pink patch">
  <figcaption><strong>One patch of a run.</strong> Left: the region the patches tile &mdash; the copulation detection's box (yellow) enlarged three times, clipped to the frame. Right: the patch whose replacement lowered the score the most, filled with the default hot pink. The detection's score fell from 0.8959 to 0.8412: Δ = 0.055. The run replaced 528 such patches, one at a time.</figcaption>
</figure>

## Controls

Every target is also run through two controls:

| Control | What it is | Expected |
|---|---|---|
| `noop` | the unchanged frame, through the same batch pipeline | Δ exactly 0 &mdash; checks the pipeline on every target |
| `full_region` | the whole region replaced by the baseline | the score with everything around the detection hidden |

In the run above, `noop` gave Δ = 0.0, and replacing the whole region lowered the copulation score from 0.896 to 1.3 &times; 10<sup>&minus;8</sup>.

## Baselines {#baselines}

| Baseline | An occluded patch becomes |
|---|---|
| `constant` (default) | one B,G,R colour: <span class="swatch" style="background:#ff69b4"></span>hot pink `#FF69B4` (180,105,255) by default; <span class="swatch" style="background:#000"></span>black (0,0,0); <span class="swatch" style="background:#727272"></span>YOLOv5's letterbox grey (114,114,114); or any colour |
| `image_mean` | the frame's mean colour |
| `patch_mean` | the patch's own mean colour: removes texture, keeps colour |
| `blur` | the same patch of a Gaussian-blurred frame (sigma): removes detail, keeps colour |
| `noise` | uniform random colours, seeded per patch |

Each patch's real pixel change is recorded (`pixel_change`): a patch that changes no pixel cannot have an effect.

<div class="callout warning" markdown="1">
<p class="callout-title">The effect depends on the baseline</p>

Occlusion edits the frame into something the model never saw. Black over a bright arena is extreme. The default hot pink is strongly red &mdash; and a fly's eyes are red &mdash; so a pink patch may add eye-like evidence as well as hide what it covers. The size of the effect also depends on the patch size and the stride. Compare settings before drawing conclusions.
</div>

The same copulation event with the default hot pink and with black, all other settings equal:

<figure>
  <img src="{{ '/imgs/preview_occlusion_ev-0003.png' | relative_url }}" alt="Occlusion map with the hot-pink baseline">
  <figcaption><span class="swatch" style="background:#ff69b4"></span><strong>Hot pink</strong> (default) &mdash; colour scale &plusmn;0.039</figcaption>
</figure>

<figure>
  <img src="{{ '/imgs/preview_occlusion_black_ev-0003.png' | relative_url }}" alt="Occlusion map with the black baseline">
  <figcaption><span class="swatch" style="background:#000"></span><strong>Black</strong> &mdash; colour scale &plusmn;0.28, seven times wider</figcaption>
</figure>

| Baseline | Largest Δ | Mean Δ in the box | Mean Δ outside | Patches where NMS dropped the candidate |
|---|---|---|---|---|
| hot pink | 0.055 | 0.0066 | &minus;0.0003 | 0 of 528 |
| black | 0.523 | 0.029 | 0.0019 | 2 of 528 |

The largest drop with pink patches is about a tenth of the largest drop with black ones, although the largest effects sit in the same place. A figure should name its baseline; a claim should show more than one.

## Batch size {#batch-size}

A detector's scores depend slightly on how many frames are processed together, because different GPU and CPU kernels are used: up to 2.4 &times; 10<sup>&minus;3</sup> between batch sizes 1 and 4 on CUDA with fp16 autocast, 2 &times; 10<sup>&minus;6</sup> on the CPU. YORU-Explain therefore takes the reference score at the run's batch size, which keeps the `noop` control at exactly 0. Still, per-patch changes at batch size 8 differ from those at batch size 1 by up to 2.7 &times; 10<sup>&minus;3</sup> on the fly model, so effects smaller than that are not resolved at batch sizes above 1. **Batch size 1 is exact.**

Every batch is padded to the same size. A CUDA out-of-memory error fails the event with `cuda_oom`; the batch size is never changed silently during a run.

## Fixed-candidate and re-detection in occlusion

- **Fixed-candidate**: every patch has a score. The run also counts the patches after which NMS would no longer keep the candidate (*candidate dropped*) and records how far the candidate's box moved.
- **Re-detection**: a patch after which the detection is not found again (`disappeared`, `class_changed`, `unmatched`, `ambiguous`) has no score and is not counted. Pixels covered only by such patches are NaN in the map, and `lost_fraction` in the map file shows where that happened.

Definitions of each column: [Output files]({{ '/reference/output-files/' | relative_url }}).
