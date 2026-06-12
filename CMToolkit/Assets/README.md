# CMToolkit Assets

Bundled files copied to the build output via `CopyToOutputDirectory`.

## Included in repo

- `download-source.txt` — default update channel seed (`github` or `nexus`)
- `fonts/CascadiaMono.ttf` — copied from the system when available during scaffold
- `fonts/CascadiaMono.ttf-LICENSE` — font license

## Copy from Python release bundle

These PNG assets are not tracked in git. Copy from a [cm-toolkit.zip release](https://github.com/wxMichael/Collective-Modding-Toolkit/releases/latest/download/cm-toolkit.zip) into `images/`:

- `icon-32.png`, `icon-256.png`
- `logo-nexusmods.png`, `logo-discord.png`, `logo-github.png`

Convert `icon-32.png` to `icon-32.ico` for the application icon when ready.

## xdelta3.exe

Place `xdelta3.exe` in `tools/` before building the Downgrader (M4). The file is gitignored (`*.exe`) but must be present in the published output folder for delta patching.
