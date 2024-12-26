# Changelog

## [0.4.0] - 2024-12-26

### Added

- #### Overview

  - PC Specs now displayed, along with a warning about issues with MO2's VFS if Windows 11 24H2 is detected.
  - Update checking for Nexus Mods.

- #### Scanner

  - Race Subgraphs option. Counts the total number of Subgraph Addititve Race subrecords (RACE \ SADD).
  Thanks Zzyxzz for suggesting this and providing the details!
  - Junk file extensions: `.bak` and `.tmp`.  
  Thanks Alundra for all the suggestions! More on the rest later.
  - Solution text for Invalid Module versions.

- #### Tools

  - Button for BA2 Merging Automation Tool (BMAT).
  - Channel names for CM Authors' tools.

### Changed

- #### Scanner

  - Improved results display with collapsible groups by type, a count, and a note to click for details.
  - Better detection and description for F4SE script overrides, as there are some mods that intentionally provide these.  
  Thanks Argon for the feedback!
  - Mod files and Data will only be scanned if selected options require it.

### Fixed

  - Potential crash reading INI files if a setting was not within any [section].

## [0.3.2] - 2024-12-20

### Fixed

- #### Overview

  - Files with missing version numbers should now show as Unknown instead of erroring.

- #### Scanner

  - Ensure paths read from MO2 settings are converted to Path types.  
  Should fix `TypeError: unsupported operand type(s) for /: 'str' and 'str'`.

## [0.3.1] - 2024-12-20

### Changed

- Zip file now has the app in a subfolder named `Tools/CM-Toolkit/` to aid Collections.

- #### Overview

  - Refreshing won't show errors again for `Fallout4.ccc` and `plugins.txt` if missing.

### Fixed

- #### Scanner

  - Some MO2-specific code was being run when using Vortex.

## [0.3] - 2024-12-19

### Added

- Pressing Space will close About windows.

- #### Overview

  - Count for modules with unknown HEDR versions.
  - Note on Vortex support if detected. Overview should be accurate but Scanner can't yet identify the source mod for issues.

- #### Scanner

  - Issues from Overview will be reported in the Scanner.
  - Detect BA2s that won't be loaded due to invalid file names.
  - Detect loose file overrides of F4SE's `*.pex` files.

- #### Tools

  - Button for PJM's Precombine/Previs Patching Scripts.

  - #### Archive Patcher

    - File name filter to patch only specific archives.

  - #### Downgrader

    - Options to delete backups and delta patches after the patch process.

### Fixed

- Issues caused by Windows 11 24H2 have been worked around.  
It seems 24H2 made some of Python's file-related functions stop working inside MO2's virtual filesystem.
- Having a Documents folder in a non-default location works now.
- UnicodeDecode error with non-English characters in INI files.
- Wrong link for Cathedral Assets Optimizer

### Changed

- #### Overview

  - Counts will now turn orange when within 5% of a limit.

- #### F4SE

  - Whitelisted `ClockWidget.dll` for OG+NG support.

- #### Scanner

  - Reworked how scanning is done to speed it up by only doing checks on Data instead of all staged mods.  
  As a result, if two mods have identical problem files only the conflict winners are reported.
  - Whitelisted `*.cdf` files for `Data/Sound/`
  - Primary text color is now a light gray instead of white to be easier on the eyes.  
  Colors will likely be configurable in a later update.
  - Scanning disabled when all options are disabled.

## [0.2.1] - 2024-12-01

### Added

- #### Tools

  - Buttons linking to tools made by other authors.

### Fixed

- BA2s listed in Fallout4.ini were not being counted properly.  
On a clean game install the count is now 19 higher.
- The error window was failing to open when the app encountered a problem.
- Mod manager detection details window was failing to open for Vortex users.
- Text formatting was merging lines in the mod manager detection details window.

## [0.2] - 2024-11-29

### Changed

- GUI accent color is now green instead of blue.
- No longer has all files compressed into a single exe. Anti-virus tends to flag single-exe Python apps as malware, and Nexus Mods quarantines such apps regularly. Planned features will likely require additional files, so the change from a single file was inevitable.

- #### Overview

  - Counts for modules and archives now account for enabled plugins and validity of archive filenames.
  - `*.esl` files without the ESL header flag are now counted as Light as the engine forces the flag at runtime.
  - Binaries are now labeled with install type, and show version or hash on hover.
  - Renamed *Invalid* module/archive counts to *Unreadable* and moved them to the top section.
  - Corrected General BA2 limit to 256 and set Texture limit tentatively to the same.  
  I intend to do my own testing at some point for the functional limit of texture archives.
  - HEDR v0.95 count is now a neutral color as they're only a concern if Form IDs are out of range.  
  A later update may attempt to detect these.

- #### F4SE

  - Non-whitelisted DLLs detected as OG+NG will have a ⚠️ as some only support both enough to tell users if they have the wrong DLL.
  - Filtered out Microsoft Visual C++ DLLs such as `msdia140.dll` from Buffout 4 NG.

- #### Tools

  - #### Downgrader

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

[0.4.0]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.4.0
[0.3.2]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.3.2
[0.3.1]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.3.1
[0.3]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.3
[0.2.1]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.2.1
[0.2]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.2
[0.1]: https://github.com/wxMichael/Collective-Modding-Toolkit/releases/tag/0.1
