# Goo v23 arm revision

The anatomical left arm is the near arm on screen right, with GOO_NEAR_HAND=-1. This revision keeps the audited v21 hand cells and v22 opposite-arm support pose.

The old front sleeve excluded a 40-unit circle around the shoulder. That exposed the torso's painted outer line through the near sleeve. Both foreground sleeves are now composited completely over the body and front-collar pass. The far-arm support geometry is unchanged; its old shoulder cutout is removed as well.

Writing no longer uses fixed-length two-bone inverse kinematics. Its old elbow solution folded inward toward the abdomen at the beginning of the stroke. `writingReach()` solves a near-straight shoulder-to-grip reach, with the elbow only six local units outside that axis. A shared grip marker positions the pencil; the hand and cuff rotate with the forearm.

The study desk is lowered 24 stage pixels, the paper is shifted right, and the stroke follows a short upward diagonal. Across all 57 pre-transition frames of the current Chinese study shot, elbow x stays between 160.77 and 169.71, beyond shoulder x=102; bend is 5.73–6.79 degrees; shoulder-to-wrist path length is 151.39–153.13 units. These numerical observations complement the start/middle/end images and motion preview; they do not establish subjective acceptance.

Edit the writing workspace in src/rebuild/scenes.mjs `study()`, and the reach in src/rebuild/goo.mjs `writingReach()`. Do not rotate or mirror a hand independently of its forearm. Preserve GOO_NEAR_HAND and handMarker()/handWorldMarker() contact geometry. Recheck the whole stroke, not only its final held pose.

The v23 Chinese encode predates the accepted straight-arm correction. The partial v23b encode has that correction but predates the final right-shoulder fix. Both are superseded. The corrected master revision is v23c. Do not deliver or package the superseded encodes as the final film.
