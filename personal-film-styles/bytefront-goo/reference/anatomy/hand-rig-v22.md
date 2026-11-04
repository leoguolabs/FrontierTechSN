# Goo v22 hand anatomy and replay

The rejected v20 binding trusted generated prompt labels. They were wrong. The raster cells are mixed: audit the thumb base, visible nails or palm creases, finger direction, and forearm together before assigning a side.

## Frozen cell map

| Cell | Visible surface | Actual source side |
| --- | --- | --- |
| hands-cuffs / relaxed | dorsal, fingers downward | RIGHT +1 |
| hands-cuffs / open | palm, fingers upward/right | LEFT -1 |
| hands-cuffs / point | palm, index upward | LEFT -1 |
| hands-cuffs / grip and writeGrip | thumb/index pinch, palmar oblique | LEFT -1 |
| hands-actions / press | dorsal, index rightward | RIGHT +1 |
| hands-actions / scratch | dorsal, curled fingers upward | RIGHT +1 |
| hands-actions / chin | dorsal fist | RIGHT +1 |
| hands-actions / write | right writing grip with integrated pencil | UNUSED in v21 |

In canonical right-facing Goo, the near screen-right arm is the anatomical LEFT (-1); far screen-left is RIGHT (+1). Rotate each cell so its forearm points along local +X. Reflect local Y once by target side / observed source side. Transform contact markers identically. Mirroring the whole actor swaps the complete pose coherently. A fixed navy clothing patch is retained as identity decoration.

For the two palm-up shrug hands, thumbs must be on the inner side, toward the body. The previous v21 anatomy review documented rejected v20 thumbs pointing outward. Current cells are frozen in assets/goo-v04 and their binding is retained. Relaxed dorsal hands were already correctly attached and were not blindly flipped.

## Contacts and layered props

The painted sprites include the short wrist, ribbed cuff and overlap sleeve. The cuff follows the forearm. Chin and forehead contacts follow the head pivot; the supporting arm meets the opposite elbow. Glasses contact targets the bridge. Identity button finger follows the button contact while the far hand hangs relaxed.

writeGrip uses the LEFT pinch artwork, marker [1316,640] in the original atlas. The pencil is drawn behind the thumb/index, at angle -0.9 rad. A shared grip point is offset from the actual pencil tip; the same tip drives the drawn mark. This avoids reflecting an integrated pencil into an upside-down orientation. The study mark stays inside the paper. The formula close-up forearm enters from below and travels with the wrist.

## Mandatory review when editing

Render both actor directions, relaxed hands, palm-up presentation, both shrug hands, chin/support, forehead, glasses, idea-pointing, writing, manuscript grip/release, and button/switch presses. Inspect the actual pictures and motion around each change; numeric reach and continuity checks cannot establish anatomy or naturalness. Do not start a long render while an obvious anatomy or contact defect remains.

Use the frozen PNGs and package lock for replay. Prompts document origin; regenerating them is not a deterministic reproduction method. Review grids and the shared timeline are the reference for another agent. No published Mid-century assets or site pages are modified.

## V22 supporting-arm correction

The v21 torso silhouette remained exposed outside the far RIGHT supporting sleeve in chin mode. In goo.mjs, chin supporting solveContact now uses effective foreshortened arm lengths [110,150] instead of [105,105]. This moves the elbow outside the hoodie edge while keeping the hand under the other elbow. Front sleeve redraw and hand-side mapping are unchanged. Both actor directions and the chin-to-forehead transition are included in the v22 visual evidence. See review/sleeve-before-after-v22.png.
