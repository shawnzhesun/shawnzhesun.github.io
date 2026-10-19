# Shawn’s Studio

An immersive guitar studio for `shawnzhesun.github.io`, drawn like an anime/comic panel: bold ink outlines, cel shading, an orange sunset key light against deep indigo shadows. A front-facing perspective camera, a small draggable camera arc, and the studio is the entire page.

## Preview

```sh
npm run dev
```

Open **http://127.0.0.1:4173**. Plain HTML, CSS, and JavaScript; no runtime framework, backend, CDN, or visitor-side Blender installation.

- Drag horizontally to rotate the camera through **±6°**. The default camera faces the monitoring position directly.
- The whole room height always fits the viewport (no vertical scrolling). Narrow screens pan sideways; screens wider than 16:9 show the full room over a blurred backdrop.
- Hover an object to see its outline (there are no markers); click or tap it to open its panel. Hit areas follow the visible objects at every camera angle. Invisible hotspot buttons remain for keyboard users.
- The **Tide of Echo** poster opens the band panel (Journal on Spotify). Each of the three album sleeves on the wall (Modern Times, Echo of Tide, Journal) is its own object with its own panel and Spotify link; the menu also has a records overview.
- The black name badge hanging from the desk opens Shawn’s LinkedIn.
- The site has no audio.
- The TV shows a live, non-interactive terminal "command center" (`studio/js/terminal.js`), pinned onto the rendered screen with a per-frame homography (`screen` corners in `scene.json`). The render bakes a matching still frame underneath. Reduced motion draws it once.
- The rack panel describes the signal chain (Neve 1073, 1176, LA-2A, bus compressor); the pedalboard panel lists Keeley compressor, Precision Drive, OCD, Strymon delay and reverb.
- The TV panel offers three color treatments for the room. These are image treatments, not alternate rendered lighting setups.
- Small controls inside the room open object navigation, center the camera, and enter fullscreen. Left/right arrow keys move the camera; **Home** centers it. Tab reaches every object, including objects outside the current phone crop.
- Native dialogs contain keyboard focus and support Escape. Direct URL fragments, reduced motion, missing-asset fallback, and a no-JavaScript introduction are supported.

## Camera architecture

This is a **25-view Blender render sequence**, not a live mesh renderer or a CSS tilt effect. Each view is rendered at a real perspective camera position along a 12° arc, in 0.5° increments. Each has a matching object-ID mask and camera-projected hotspot coordinates.

The first frame loads by itself. Lower-resolution neighboring views load in the background (unless data saving is requested). Dragging selects the nearest rendered angle; when movement stops, the selected view upgrades to its full-resolution image. Only a few full-resolution images are kept decoded. Image, mask, and hotspot coordinates switch together, with stale asynchronous loads discarded.

The camera is intentionally bounded: this provides a small look-around interaction, not unrestricted walking or a 360° orbit. Expanding the camera range requires additional renders.

## Guitar geometry and placement

The guitar is modeled after Shawn’s Suhr S-style: offset double-cutaway body with a flame maple top in a charcoal burst (`guitar-top.png`, mapped with generated coordinates), white pearloid HSS pickguard (procedural swirl), two single coils and a bridge humbucker, two knobs and a five-way switch, a two-point bridge, roasted maple neck and headstock, rosewood board with 22 equal-tempered frets, and six inline tuners. Straight-sided parts (neck, fingerboard) use vector Bézier handles so they keep their taper instead of ballooning into an oval. This is original stylized geometry, not a manufacturer CAD model.

The instrument leans backward 7° in a three-foot floor stand. Geometric checks verify floor clearance, no amp/desk intersection, and an estimated center of mass inside the tripod footprint. These are static placement checks, not a rigid-body simulation.

## Comic look

- Cycles materials mix Principled with a little Toon BSDF (30% by default) for a crisp light/shadow terminator while keeping material detail.
- Freestyle draws ink outlines (silhouettes, borders, creases); tiny details are kept in an `Inkless` collection so they don’t turn into noise. `--ink` sets the line width in pixels at 1920 wide (default 2).
- `scripts/pack.py` grades every frame (saturation and contrast) and adds a faint screentone in the deepest shadows.

## Edit content

| Change | File |
| --- | --- |
| Band copy, gear descriptions, Spotify and LinkedIn links | `studio/js/content.js` |
| Minimal scene document | `index.html` |
| Immersive view and modal styling | `studio/css/studio.css` |
| Dragging, frame loading, hit testing, panels | `studio/js/app.js` |
| Cover framing, bounded pan and angle selection | `studio/js/geometry.js` |
| Room, guitar, camera arc, lighting | `blender/studio.py` |
| Rug and amp cloth generation | `scripts/textures.py` |
| Window view crop, baked terminal frame, wave poster, badge, album sleeves, guitar top | `scripts/comic_art.py` |
| Live terminal on the TV | `studio/js/terminal.js` |
| Signal chain and pedalboard copy | `studio/js/content.js` |
| Supplied artwork (album covers, band logo, portrait, window view) | `blender/source/` |

The poster combines the band logo (extracted from the Journal cover, since the supplied logo file is 150 px) with the breaking wave from the Echo of Tide artwork.

## Rebuild

Requires Blender 5.x, Python 3.10+, and `uv`. Verified locally with Blender 5.2.2 on macOS. The runner detects Blender in `/Applications`; elsewhere put `blender` on PATH or set `BLENDER_BIN`.

```sh
npm run textures
npm run render -- --width 1920 --samples 56 --views 25
```

For a fast single-angle art-direction preview:

```sh
npm run render -- --width 1920 --samples 16 --views 1 --no-masks
```

`--no-masks` skips the mask pass and packing will fail, so use it only for looking at `build/views/00.png`. Camera framing flags: `--lens`, `--cam-z`, `--target-z`, `--radius`. A one-view build intentionally has no camera rotation. Restore a 25-view build before publishing the interactive version. View count must be a positive odd number.

The pipeline creates:

- `build/studio.blend`: editable central-camera scene, saved before material substitution for masks.
- `build/views/`: full PNG renders and masks, kept outside Git.
- `build/guitar-placement.json`: support-footprint check.
- `studio/assets/views/`: desktop/mobile WebP frames and lossless masks.
- `studio/assets/scene.json`: frame manifest, camera angles, and hotspot positions.
- `studio/assets/studio.webp`: the default frame, also used for the page preview.
- `studio/assets/poster.webp`: band-panel artwork.

The scene manifest is published only after every frame has been packed. Commit the generated `studio/assets/` files alongside scene updates. Blender does not run on the web server.

Room artwork is generated locally; album covers, the band logo and the portrait are Shawn’s and live in `blender/source/`. Style and guitar reference photos are kept out of the repository. The render-plus-hotspot concept was inspired by EdwinjJ1’s `personal-website/002`; this version uses its own scene and frontend.

## Verify

```sh
npm test
```

Dependency-free tests cover coordinate transforms, edge-safe touch tolerance, height-fit sizing, bounded panning, and camera frame selection.

The optional browser test uses Playwright and an isolated temporary profile. Run the preview server first:

```sh
npm install --no-save playwright
npx playwright install chromium
node scripts/check-browser.mjs
```

Or set `PLAYWRIGHT_MODULE` to an installed Playwright ESM entry point and `CHROME_BIN` to a Chrome executable. `STUDIO_URL` overrides the preview URL.

The browser checks cover: absence of surrounding page UI; a front-facing default; left/right rotation and rapid reversal; a rotated poster’s actual pixel hit area; aligned hotspot positions; mouse and touch drag without accidental clicks; phone panning; keyboard access; modal focus; Spotify and LinkedIn destinations; no audio controls; mood controls; deep links; and fallback behavior. Screenshots are written to `build/qa/`.

To inspect the rendered model’s geometry:

```sh
blender --background build/studio.blend --python-exit-code 1 --python scripts/check_model.py
```

This writes `build/model-check.json` and fails on floor, amp, or desk intersections; unexpected proportions; incorrect string/fret counts; or an invalid stand footprint.

## GitHub Pages

The root `index.html` and `studio/` directory are the complete static website. Publish those through the repository’s GitHub Pages configuration. The scripts do not commit, push, or deploy anything.

