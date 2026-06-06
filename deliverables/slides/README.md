# Vent Squad — presentation deck (HTML)

`Vent_Squad_Slides.html` is a self-contained [reveal.js](https://revealjs.com)
deck. It loads reveal.js from a CDN, so there is **no build step** — just open it
in a browser. The figures are pulled from `../../figures/`, so run
`python -m src.build_all` once first (from the repo root) to make sure every figure
exists.

## Present it
1. Open `Vent_Squad_Slides.html` in Chrome/Edge/Firefox (double-click, or
   `open Vent_Squad_Slides.html` on macOS).
2. Arrow keys / space to advance; `F` for fullscreen; **`S` for speaker notes**
   (each slide has presenter notes for the video narration).

## Export to PDF (for the `Team_VentSquad_PPT_V1` deliverable)
1. In the browser, add `?print-pdf` to the file URL, e.g.
   `…/Vent_Squad_Slides.html?print-pdf`, and reload.
2. **Print** (Ctrl/Cmd-P) → **Destination: Save as PDF** → **Layout: Landscape**,
   **Margins: None**, and tick **Background graphics**.
3. Save as `Team_VentSquad_PPT_V1.pdf`.

## If you need an editable PowerPoint instead
- The fastest route to `.pptx` is to take the exported PDF (or the slide content in
  `../Vent_Squad_Deck.md`) into PowerPoint / Google Slides / Canva and apply a
  template. The numbers and speaker notes here are final; only the SPE membership
  numbers on slide 1 remain to add.

## Slide ↔ figure map
| Slide | Figure |
|-------|--------|
| 4 Why BLT-01 | `ntg_vs_thermogis.png` |
| 5 Method | `md_vs_tvd.png` |
| 6 Resource | `mc_mwth_blt.png` |
| 7 Design A | `design_a_schematic.png` |
| 9 Economics | `lcoe_tornado.png` |

All numbers match the technical report and are produced by `src/`
(`python -m src.build_all`).
