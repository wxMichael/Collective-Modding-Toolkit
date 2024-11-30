# Changelog

## [0.2] - 2024-01-27

### Changed

- GUI accent color is now green instead of blue.
- No longer has all files compressed into a single exe. Anti-virus tends to flag single-exe Python apps as malware, and Nexus Mods quarantines such apps regularly. Planned features will likely require additional files, so the change from a single file was inevitable.

#### Overview

- Counts for modules and archives now account for enabled plugins and validity of archive filenames.
- `*.esl` files without the ESL header flag are now counted as Light as the engine forces the flag at runtime.
- Binaries are now labeled with install type, and show version or hash on hover.
- Renamed *Invalid* module/archive counts to *Unreadable* and moved them to the top section.
- Corrected General BA2 limit to 256 and set Texture limit tentatively to the same.  
I intend to do my own testing at some point for the functional limit of texture archives.
- HEDR v0.95 count is now a neutral color as they're only a concern if Form IDs are out of range.  
A later update may attempt to detect these.

#### F4SE

- Non-whitelisted DLLs detected as OG+NG will have a ⚠️ as some only support both enough to tell users if they have the wrong DLL.
- Filtered out Microsoft Visual C++ DLLs such as `msdia140.dll` from Buffout 4 NG

#### Downgrader

- Merged Game and CK downgrade options since they both require `steam_api64.dll` to match.  
Supporting version mixing is on the roadmap.


### Added

- The Scanner tab! The WIP Errors/Conflicts/Suggestions tabs were merged into one.  
It currently only supports `Data/` and MO2's mods folder with basic checks like wrong file formats.
- Tooltips for various elements on the Overview tab with related info.
- Detection of MO2 settings for profiles, instances, and game/mod/INI paths.
- Tool buttons in the Tools tab, with teasers for tentatively-planned tools.
- Count of HEDR v1.00 now listed for consistency.
- Pressing Escape will close the focused window.
- F4SE and Downgrader "about" text and dark-themed the About windows.

## [0.1] - 2024-09-27

_Initial release._

[0.2]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.2
[0.1]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.1
