# CM clips for animated workouts

These 321 MP4s match the verified Drive IDs in `../cmfit-catalog.json`.
The original H.264/yuv420p clips are preserved, including the complete body
and apparatus. No body parts are animated or cropped independently here.

The GIF generator uses the selected library's visual theme, names, and current
student prescriptions. Synonyms and abbreviations can match automatically;
qualified variants are suggestions requiring an explicit choice. Bi-sets are
expanded in the GIF draft without editing the original combined workout line.

Confirmed selections are remembered separately for CM and GymFaster in the
local `treinoGifChoicesV1` preference. A device video is used only in the current
session. When a source comes from another library, its identity stays visible.

Generation fetches complete clips and processes one decoder at a time. Small
indexed frames are cached in the GIF worker to limit mobile memory use.
