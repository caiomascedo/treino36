# GymFaster media

The MP4 filenames match the verified Drive IDs in `../gymfaster-catalog.json`.
These same-origin copies allow the browser to draw actual exercise frames into
an animated workout GIF without depending on Drive CORS or a generation API.

Clips retain the source exercise motion. They use H.264, a 480 × 480 white canvas,
and 20 fps. A fixed crop spans the sampled movement, with padding to keep the
body and equipment in frame; the crop does not follow individual body parts.

The workout export uses the student's current section and prescriptions, with
100 synchronized frames over five seconds and an infinite loop. Selecting a
catalog video saves its original Drive link through the existing workout store.
A video supplied from the device is used only in the current GIF session.

The GIF encoder is gifenc 1.0.3, with its MIT license in `../gif-vendor/`.
