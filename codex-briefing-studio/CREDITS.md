# Credits and provenance

**Independent film and studio:** LeoGuoLabs, made with Codex.

**Style reference:** LemoLab's *The Ship Decides*, “Engineering Briefing Board”
from [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar).
The reference film is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The reference is retained locally for comparison. The new film changes the
subject, writing, geometry, camera schedule, drawings, audio, and implementation.
It credits LemoLab for the visual reference; no endorsement is implied.

Reference download:
https://github.com/lemomo-ai/lemo-opuscar/releases/download/films/briefing-board.mp4

Reference SHA-256:
`cf09a6db65a100fc877d4e7ffee8113aee642e6056822ad2055a48189f7a80cc`

The reference repository's style and demo descriptions were consulted. Its
rendering engine, scene implementation, and build workflow were not imported.
This project does not create FrontierTechSN application Tasks.

**Notebook photograph:** Jan Kahánek,
[original Unsplash photograph](https://unsplash.com/photos/g3O5ZtRk2E4);
[Wikimedia Commons provenance and CC0 record](https://commons.wikimedia.org/wiki/File:A_notebook.jpg).
The image was published on Unsplash before June 5, 2017, according to that
record. The original source image is preserved. It depicts an illustrative
notebook, not an experimental setting. Two pinned uses appear in the composition.

The final film uses a generative cutout derived from this photograph. Built-in
`image_gen` removed the table and reconstructed the originally cropped notebook
edges. It is not an unaltered photograph. The generated alpha channel is retained;
the renderer adds shadows and magnets. The exact prompt, asset hash, and review
are in [assets/notebook-cutout.json](assets/notebook-cutout.json).

**Typography:** Kalam (Indian Type Foundry) and Archivo (Omnibus-Type), downloaded
from the Google Fonts repository, under the SIL Open Font License. License
texts are retained in `assets/fonts/`.

**Drawings:** Student, teacher, Turkish flag, ruler, magnets, labels, dimension
lines, and board material are authored in this project's renderer. The flag is
a stylized depiction; no flag image was downloaded.

**Audio:** Chatterbox, voice `space-en-f1`, using the configured service. Provider
WAVs and request identities remain in ignored local media. Music and material
foley are synthesized by this project's audio script, without sampled music.

**Research:** See [FACTS.md](FACTS.md).

Generated media, downloaded reference media, source photographs, and private
provider records are excluded from Git. Asset URLs and reproducible source
instructions are retained.
