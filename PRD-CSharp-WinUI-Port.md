# PRD — Collective Modding Toolkit: C# / WinUI 3 Port

| | |
|---|---|
| **Product** | Collective Modding Toolkit (CMT) |
| **Source version** | Python 0.6.1 (Tkinter + sv_ttk "Sun Valley" dark theme) |
| **Target** | C# / .NET 10 / WinUI 3 (Windows App SDK) |
| **Author** | wxMichael |
| **Status** | Draft |
| **Date** | 2026-06-12 |

---

## 1. Background & Purpose

CMT is a desktop toolkit for troubleshooting and optimizing Fallout 4 mod setups, built for the Collective Modding Discord community. The current implementation is Python 3.14 + Tkinter, distributed as a PyInstaller exe and launched through a mod manager (MO2 or Vortex).

This PRD defines the requirements for a full port to C# with WinUI 3. The port replaces the Python runtime, PyInstaller packaging, and Tkinter UI stack with native .NET and Windows App SDK while **preserving the existing UI layout, information architecture, and workflows as closely as possible**.

### Why port

- Eliminate PyInstaller cold-start time, false antivirus positives, and the MO2-VFS crash ("do not install as a mod" caveat).
- Native dark titlebar, DPI scaling, and font rendering without Win32 workarounds (`DwmSetWindowAttribute`, private GDI font loading).
- Single self-contained exe/folder with no Python runtime; faster file I/O for scans (parallelizable in .NET).
- The existing sv_ttk theme is a Fluent/Windows 11 imitation; WinUI 3 *is* Fluent, so visual continuity is achievable with native controls.

### Goals

1. Feature parity with Python v0.6.1 (every tab, modal, scan check, and setting enumerated in this document).
2. UI fidelity: same tab order, same groupings, same labels, same semantic colors, same fixed-size compact window feel.
3. Settings compatibility: read/write the existing `settings.json` schema unchanged, so users can swap exes in place.
4. Equal or better performance for the Data-folder scan and Overview refresh.

### Non-Goals

- New features (INI editor, DDS scanner, conflict detection — all WIP/unimplemented in 0.6.1) are out of scope except where noted as stubs.
- Linux/Steam Deck support.
- Localization beyond what exists today (English UI; `Language` enum used only for BA2 suffix detection).
- Microsoft Store distribution.

---

## 2. Target Platform & Technology

| Concern | Requirement |
|---|---|
| UI framework | WinUI 3, Windows App SDK (latest stable), `dotnet new winui` template baseline |
| Runtime | .NET 10, `net10.0-windows10.0.xxxx` TFM |
| Packaging | **Unpackaged**, self-contained, single output folder. Users add `CMToolkit.exe` to MO2/Vortex executables; MSIX is incompatible with this workflow. Windows App SDK deployed self-contained (`WindowsAppSDKSelfContained=true`) so no runtime install is required. |
| Architecture | x64 only (matches Fallout 4 and current distribution) |
| Min OS | Windows 10 1809+ (Windows App SDK floor); primary target Windows 10/11 |
| Pattern | MVVM (CommunityToolkit.Mvvm). Code-behind acceptable for thin view glue. |
| License | GPL-2.0-or-later (carried over; all dependencies must be compatible) |

### Dependency mapping (Python → .NET)

| Python | Purpose | .NET replacement |
|---|---|---|
| `pywin32` (`GetFileVersionInfo`) | PE version detection | `FileVersionInfo.GetVersionInfo` |
| `psutil` | Parent-process walk, RAM | `Process`/`NtQueryInformationProcess` or Toolhelp32 P/Invoke for parent PIDs; `GlobalMemoryStatusEx` or WMI for RAM |
| `winreg` usage | Steam/GOG/MO2 registry, CPU/GPU info | `Microsoft.Win32.Registry` |
| `pyxdelta` | Apply `.xdelta` delta patches | Bundle `xdelta3.exe` (already in repo, GPL-compatible) invoked as a child process (decided, §12.3) |
| `requests` | Update checks, patch downloads | `HttpClient` |
| `chardet` | Encoding detection for INI/text reads | `UTF.Unknown` NuGet (port of chardet) or `StreamReader` with BOM detection + cp1252 fallback |
| `zlib.crc32` | File CRC32 identification | `System.IO.Hashing.Crc32` |
| `tkinter-tooltip` | Tooltips | `ToolTipService` (built-in) |
| `sv_ttk` | Dark Fluent-style theme | Native WinUI Fluent dark theme |
| `ctypes WinDLL` load | F4SE DLL export inspection | **Static PE export-table parsing** (`PeNet` NuGet or hand-rolled reader). Do **not** load third-party DLLs into the process — same results, no code execution risk. |
| `packaging.Version` | Version comparison | `System.Version` / NuGet `SemVer` where needed |
| `configparser` | MO2 `ModOrganizer.ini` | `ini-parser` NuGet or minimal in-house INI reader (must tolerate MO2's `@ByteArray(...)` values) |

---

## 3. UI Fidelity Principles

These rules apply to every screen and override generic WinUI defaults where they conflict:

1. **Window:** Fixed-size main window, non-resizable, non-maximizable, centered on launch. The Python app is 760×450 logical px; treat this as a **reference proportion, not a hard requirement** — WinUI control metrics (touch-friendly padding, type ramp) differ from ttk, so size the window to whatever compact footprint fits the same content density and layout. Finalize dimensions during the M2 visual review. Use `AppWindow`/`OverlappedPresenter` with `IsResizable=false`, `IsMaximizable=false`.
2. **Theme:** Dark theme **forced** (`RequestedTheme=Dark`), matching the dark-only Python app. Mica/backdrop optional; if used it must not lighten the content area noticeably. Light theme support is explicitly out of scope for v1 (deviation from WinUI defaults, by design).
3. **Tabs:** Top-aligned tab strip with the exact order and labels: **Overview, F4SE, Scanner, Tools, Settings, About**. Implement with `NavigationView` in Top mode or `SelectorBar` + `Frame`. Tabs are not closable/reorderable (do not use `TabView`).
4. **Typography:** Ship and use **Cascadia Mono** for content text as today (bundled asset, `FontFamily` resource). Four sizes mirroring `FONT_SMALLER/SMALL/NORMAL/LARGE` (8/10/12/20 pt equivalents, adjusted for WinUI's px-based type ramp).
5. **Semantic colors (carry over exactly):** good = green (`#00EE00`-family), bad = red (`firebrick`), info = dodger blue, warning = orange, neutral/disabled = gray. Define as theme resources, not hard-coded per control.
6. **Accent buttons:** Primary actions ("Scan Game", "Patch All") use `AccentButtonStyle`.
7. **Tooltips:** Every tooltip string from the Python app is preserved verbatim via `ToolTipService`.
8. **Lazy tabs:** Tab content loads on first selection (matching `CMCTabFrame.load()`), with a loading placeholder and red error text on load failure.
9. **Keyboard:** `Esc` closes the window/modals; `Space` additionally closes About/Tree dialogs.
10. **Iconography (decided, §12.4):** Segoe Fluent Icons glyphs replace the UI-chrome PNGs 1:1 (refresh, info, warning, check, update) with identical meaning and placement; existing PNG assets are retained for brand logos (Nexus Mods, Discord, GitHub) and the app icon (icon-32/256).

---

## 4. Application Shell

### 4.1 Window & startup

- Title: `Collective Modding Toolkit v{version}`.
- Startup sequence (port of `main.py`):
  1. Initialize logging to `cm-toolkit.log` in CWD.
  2. Load `settings.json` from CWD (schema §9); reset to defaults on parse failure and rewrite.
  3. Detect game and mod manager (§4.2, §4.3) before showing the main window content.
  4. Apply dark theme; show window centered.
- A global unhandled-exception handler shows an **"An Error Occurred"** dialog with scrollable, copyable exception text (port of the `StdErr` redirect window) and logs it.
- Window close is **blocked while a destructive operation is running** (downgrade patching, archive patching) — port of the `processing_data` guard. The close button is ignored or prompts "operation in progress".

### 4.2 Game detection (port of `game_info.py`)

Resolution order, identical to Python:

1. If launched under a detected mod manager, use MO2's `gamePath` from `ModOrganizer.ini`.
2. CWD, if it contains `Fallout4.exe`.
3. Registry: `HKLM\SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4 → Installed Path`, then GOG `HKLM\SOFTWARE\WOW6432Node\GOG.com\Games\1998527297 → path`.
4. Manual: Yes/No dialog **"Fallout 4 Not Found"** → file picker for `Fallout4.exe`.
5. On failure: error dialog **"Game not found"**, then exit.

Also ports: INI loading from `Documents\My Games\Fallout4\` (`Fallout4.ini`, `Fallout4Prefs.ini`, `Fallout4Custom.ini`), language-aware BA2 suffix handling, and install-type classification (§10).

### 4.3 Mod manager detection (port of `mod_manager_info.py`, `utils.find_mod_manager`)

- Walk up to **8 parent processes**; detect `ModOrganizer.exe` → "Mod Organizer", `Vortex.exe` → "Vortex"; read manager version from PE file version (3 components).
- **MO2:** locate `ModOrganizer.ini` (portable beside exe → `%LOCALAPPDATA%\ModOrganizer\{CurrentInstance}` → portable fallback). Parse `[General]` (gameName, gamePath, selected_profile), `[Settings]` (mod/overwrite/profiles directories with `%BASE_DIR%` substitution, `skip_file_suffixes` default `.mohidden`, `skip_directories`), `[customExecutables]` (xEdit/BSArch discovery).
- **Vortex:** name/version only (no path integration), with the partial-support warning icon as today.
- The Win11 24H2 MO2-VFS workaround (`is_file` open-probe) must be re-evaluated: reproduce only if the .NET file APIs exhibit the same VFS misreporting; otherwise drop it and document the finding.

### 4.4 Update banner (port of `check_for_updates`)

- Channel from `update_source` setting: `nexus` | `github` | `both` | `none`.
- GitHub: `GET https://api.github.com/repos/wxMichael/Collective-Modding-Toolkit/releases/latest` (update to the new C# repo URL at release). Nexus: scrape mod-page meta version.
- When a newer version exists, show a banner row above the tab strip: "An update is available:" + hyperlink(s) `v{X} (NexusMods)` / `v{X} (GitHub)` with tooltips "Open Nexus Mods" / "Open GitHub". Use `InfoBar` (Success severity, non-closable) styled to approximate the current pale-green banner.
- Update check runs **async** (improvement: Python blocks startup on this).

---

## 5. Tabs — Functional & UI Requirements

Tab order: **Overview → F4SE → Scanner → Tools → Settings → About**.

### 5.1 Overview

Dashboard replicating the three-column layout.

**Header block** (right-aligned gray label column + value column):
- `Mod Manager:` — `{name} v{version} [Profile: {profile}]`, or red **"Not Found"** with explanatory tooltip. MO2: info icon opens **"Detected Mod Manager Settings"** dialog (key/value dump of parsed INI). Warning icon when MO2 ≤ 2.5.2 on Win11 24H2, and for Vortex partial support.
- `Game Path:` — clickable; opens the folder in Explorer.
- `Version:` — install-type string in green (per §10 classification).
- `PC Specs:` — two lines: OS name/build + RAM; CPU + GPU/VRAM (registry + memory APIs, port of `PCInfo`).
- **Refresh** icon button (tooltip "Refresh") re-runs all Overview collection.

**Three group boxes side by side** (use `Grid` + titled group styling approximating `Labelframe`):

1. **"Binaries (EXE/DLL/BIN)"** — one row per tracked binary with install-type label colored good/bad/neutral; hover tooltip shows the full version string. `Address Library:` Installed / Not Found. Button **"Downgrade Manager…"** opens the Downgrader (§6.1).
2. **"Archives (BA2)"** — General / Texture / Total counts against limits **256 / 255 / 511**, Unreadable count, v1 and v7/v8 counts. Counts at/over limit render red; near-limit (≥95%) orange. Button **"Archive Patcher…"** opens the patcher (§6.2).
3. **"Modules (ESM/ESL/ESP)"** — Full / Light / Total against **254 / 4096 / 4350**, Unreadable, HEDR v1.00 / v0.95 / v???? counts; info icon opens a **TreeWindow**-style dialog listing modules with invalid HEDR versions.

**Behavioral requirements:**
- Refresh produces the `overview_problems` collection consumed by the Scanner's "Overview Issues" option (full issue list in §7.2).
- Warning dialogs when `Fallout4.ccc` or `plugins.txt` are missing, with the same message text.

### 5.2 F4SE

- Load gate: requires `Data\F4SE\Plugins`; otherwise show the existing error text (including the "launch via your mod manager" hint).
- **Left:** results grid with columns **DLL | OG | NG | AE | Your Game** (proportions matching 240/60/60/60/80). Use `ListView` with a grid header or CommunityToolkit `DataGrid` (decide in design review; ListView preferred per stock-control policy).
- Cell symbols preserved: ✔ supported, ✗ not supported, ? not an F4SE DLL, ⚠ consult mod page / ambiguous NG-vs-AE.
- **Right:** "F4SE DLLs" title + read-only rich text block with the existing legend/explanation (`ABOUT_F4SE_DLLS`), including colored symbols.
- DLL analysis (port of `parse_dll`, reimplemented as **static PE parsing** per §2): detect `F4SEPlugin_Load`/`F4SEPlugin_Preload` exports (is-F4SE), `F4SEPlugin_Query` (OG), `F4SEPlugin_Version` data (`compatibleVersions[16]`) for NG (`0x010A3D40`/`0x010A3D80`) and AE (`> 0x010B0890`). Skip `msdia*.dll`. "Your Game" column maps the detected install type.
- Improvement over Python: add a refresh on tab re-entry or a Refresh button (Python has none; cheap win, keep UI minimal).

### 5.3 Scanner

Replicates the three-surface arrangement. **Decided (§12.1):** Python uses two undecorated floating `Toplevel` windows docked outside the fixed main window (SidePane right, ResultDetailsPane below); the port **integrates both panes into the main window** on this tab — Scan Settings pane on the right within the tab, Result Details pane docked at the bottom (e.g. an `Expander` or persistent panel populated on selection). The single global window size accommodates this layout (§12.2). Floating secondary `AppWindow`s were rejected as fragile (z-order, move-sync, multi-monitor).

**Scan settings pane** ("Scan Settings" group, 7 checkboxes + accent **"Scan Game"** button):

| Setting key | Label |
|---|---|
| `scanner_OverviewIssues` | Overview Issues |
| `scanner_Errors` | Errors |
| `scanner_WrongFormat` | Wrong File Formats |
| `scanner_LoosePrevis` | Loose Previs |
| `scanner_JunkFiles` | Junk Files |
| `scanner_ProblemOverrides` | Problem Overrides |
| `scanner_RaceSubgraphs` | Race Subgraphs |

All default to checked. Tooltips preserved. (Bug-fix over Python: initialize checkboxes **from** persisted settings, not always-true.)

**Results area:**
- "Collapse All" / "Expand All" buttons.
- Info label: `{N} Results ~ Select an item for details`.
- `TreeView` grouped by problem type; when MO2 staging is available, show a **mod** column attributing each file to its source mod (built from `modlist.txt` + overwrite).
- `ProgressBar` + transient label `Scanning… {i}/{n}: {folder}` during scans.

**Details pane** (populated on selection):
- `Mod:` (MO2 only), `Problem:` (path; click opens containing folder), `Summary:`, `Solution:`.
- Buttons: **Copy Details** (clipboard; button text flips to "Copied!" for 3 s), **File List** (TreeWindow dialog for list-backed results, e.g. race subgraphs), **Auto-Fix** (visible only when a fix is registered for the problem type — registry is **empty** in 0.6.1; port the mechanism, ship no fixes).

**Scan engine (port of `scan_data_files` + `scan_settings.py`):**
- Runs on a background thread/Task; results stream to the UI (replace queue-polling with `IProgress<T>`/Dispatcher).
- Scans `Data\` top-level whitelist folders: `f4se, materials, meshes, music, textures, scripts, sound, vis`; always ignores `bodyslide, fo4edit, robco_patcher, source` + MO2 `skip_directories` + `skip_file_suffixes`.
- Check semantics identical to Python (§7.1).
- Before scanning, re-run the Overview refresh so "Overview Issues" is current.

### 5.4 Tools

Three titled columns of launcher buttons, identical content:

| Toolkit Utilities | Other CM Authors' Tools | Other Useful Tools |
|---|---|---|
| Downgrade Manager | Bethini Pie | xEdit / FO4Edit |
| Archive Patcher | CLASSIC Crash Log Scanner | Creation Kit Platform Extended (CKPE) |
| | Vault-Tec Enhanced FaceGen System (VEFS) | Cathedral Assets Optimizer (CAO) |
| | PJM's Precombine/Previs Patching Scripts | BA2 Merging Automation Tool (BMAT) |
| | DDS Texture Scanner | IceStorm's Texture Tools |
| | | CapFrameX |

- First column opens the in-app modals; the rest open URLs in the default browser. Info icons + tooltips preserved.

### 5.5 Settings

- **Update Channel** radio group (writes `update_source` immediately on change):
  - "All: GitHub & Nexus Mods" → `both`
  - "Early: GitHub" → `github`
  - "Stable: Nexus Mods" → `nexus`
  - "Never: Don't Check" → `none`
- **Log Level** radio group: Debug / Info / Error → `log_level`.
- Immediate persistence to `settings.json`, no Save button (matches Python).

### 5.6 About

- Two-line large title "Collective" / "Modding Toolkit", 256px app icon, version line, "Created by wxMichael for the Collective Modding Community", `#cm-toolkit on Discord`.
- Three link blocks (logo + separator + buttons): Nexus Mods, Discord, GitHub — each with **Open Link/Invite** and **Copy Link/Invite** (copy buttons show "Copied!" for 3 s).

---

## 6. Modal Tools

Both are modal windows (WinUI: secondary `Window` with owner-modal behavior, or full-window `ContentDialog`-style overlay — secondary window preferred to honor existing fixed sizes). Quoted dimensions are the Python sizes and, as with the main window (§3.1), are reference proportions — size to fit WinUI control metrics. `Esc` closes unless an operation is running; closing is blocked while patching.

### 6.1 Downgrade Manager (port of `downgrader.py`)

- Title **"Downgrader"**, ~600×334, non-resizable.
- Detects current versions by **CRC32** of 6 files:
  - Game: `Fallout4.exe`, `Fallout4Launcher.exe`, `steam_api64.dll`
  - Creation Kit: `CreationKit.exe`, `Tools\Archive2\Archive2.exe`, `Tools\Archive2\Archive2Interop.dll`
- UI: "Current Game" / "Current CK" status frames; **Desired Version** radios (Old-Gen / Next-Gen); checkboxes **Keep Backups** (`downgrader_keep_backups`) and **Delete Patches** (`downgrader_delete_deltas`); **Patch All** (accent); **About** (help dialog); embedded log view with the existing emoji/color conventions (💭 info, ✅ good, ❌ bad); progress bar.
- Patch flow per file: download `{OG-to-NG-|NG-to-OG-}{filename}.xdelta` from the GitHub `delta-patches` release (async with progress), apply xdelta decode against the source file, write backup `{stem}_{upgrade|downgrade}Backup{ext}` (Simple Downgrader-compatible) when keeping backups, delete `.xdelta` files if requested.
- Skip rules: Anniversary (AE) files, Obsolete, Not Found, already at desired version.
- Refreshes Overview on completion.

### 6.2 Archive Patcher (port of `patcher/`)

- Title **"Archive Patcher"**, ~700×600, non-resizable.
- **Desired Version** radios: `v1 (OG)` / `v8 (NG)`. Patching writes the single version byte at offset 4 of the BA2 header (v1→v8 accepts 0x01 writes 0x08; →v1 accepts 0x07/0x08 writes 0x01).
- Filter label toggling "Showing all v7 & v8…" / "Showing all v1…"; live **Name Filter** text box; candidate list from the Overview archive census; **Patch All**; **About** help dialog; log + progress as in the Downgrader.
- Runs patching off the UI thread (improvement; Python blocks the UI), still guarding window close. Refreshes Overview on completion.

### 6.3 Shared dialog components

- **AboutWindow** equivalent: text + Close, used for downgrader help, archive-format help, auto-fix results, MO2 settings dump.
- **TreeWindow** equivalent: header text + sortable two-column list (count + name) + Close, used for invalid-HEDR modules and race-subgraph file lists.
- **Error window**: "An Error Occurred" with scrollable selectable text.

---

## 7. Scanner Checks & Overview Issues (parity contract)

### 7.1 Scanner checks

| Check | Behavior (must match Python exactly) |
|---|---|
| Wrong File Formats | Per-subfolder extension whitelist in `Data\`; flag misplaced `.dll`s; flag invalid BA2 archive names (not matching plugin + valid suffix) |
| Loose Previs | Flag contents of `Data\Vis\` and `Data\Meshes\Precombined\` |
| Junk Files | `desktop.ini`, `thumbs.db`, `.ds_store`, `*.tmp`, `*.bak`; entire `Data\fomod\` folder |
| Problem Overrides | Loose `AnimTextData` folders; overrides of the 28 known F4SE `.pex` scripts in `Data\Scripts\` (CRC pairs for OG/AE) |
| Race Subgraphs | Count `SADD` records across enabled plugins; warn when total > 100, with per-plugin file list |
| Errors | Checkbox exists and persists but has no scan logic in 0.6.1 — port as-is (stub) |
| Overview Issues | Injects §7.2 list |

Problem/solution taxonomy (`ProblemType`, `SolutionType`) ports 1:1, including solution text and any "linked solution" URLs.

### 7.2 Overview-detected issues

No mod manager; unknown `Fallout4.exe` version; missing Address Library; missing `Fallout4 - Startup.ba2`; missing Data folder / `Fallout4.ccc` / `plugins.txt`; wrong-version or missing binaries (CK, Archive2, `f4se_steam_loader` exemptions preserved); invalid/unreadable archives and modules; invalid HEDR versions; missing NVFlex BA2 when `bNVFlexEnable=1`; missing `Fallout4 - TexturesPatch.ba2` on AE; archive/module limit exceeded.

---

## 8. Architecture Requirements

- **Solution layout:** `CMToolkit` (WinUI app: views, view models) + `CMToolkit.Core` (game/MM detection, scanner, patchers, settings, update check — no UI references) to keep logic testable.
- **Async:** All I/O-bound work (scan, downloads, CRC hashing, Overview census) on background Tasks with `IProgress<T>` reporting; UI thread never blocked > 50 ms.
- **State:** Single `AppState` (game info, mod manager info, overview problem list) shared via DI; tabs observe it (port of the `CMChecker` god-object into observable services).
- **Logging:** `Microsoft.Extensions.Logging` file sink to `cm-toolkit.log` in CWD, level from settings.
- **Testing:** Unit tests for `CMToolkit.Core` — install-type classification from CRC/version fixtures, BA2 header read/patch on synthetic files, module HEDR parsing, MO2 INI parsing (incl. `%BASE_DIR%`, `@ByteArray`), scanner rules against a fixture Data tree, settings round-trip. (The Python repo has no test suite; these are net-new.)

---

## 9. Settings & Data Compatibility

`settings.json` in application directory, schema unchanged:

```json
{
  "log_level": "DEBUG" | "INFO" | "WARNING" | "ERROR",
  "update_source": "nexus" | "github" | "both" | "none",
  "scanner_OverviewIssues": true,
  "scanner_Errors": true,
  "scanner_WrongFormat": true,
  "scanner_LoosePrevis": true,
  "scanner_JunkFiles": true,
  "scanner_ProblemOverrides": true,
  "scanner_RaceSubgraphs": true,
  "downgrader_keep_backups": true,
  "downgrader_delete_deltas": true
}
```

- Unknown keys stripped, missing keys defaulted, invalid file → reset + rewrite (same behavior).
- Default `update_source` seeded from bundled `assets/download-source.txt` (`github`/`nexus`) exactly as today.
- Backup file naming must remain Simple-Downgrader-compatible.

---

## 10. Version Matrix (parity contract)

| Fallout4.exe | Classification |
|---|---|
| 1.10.120–162 | Obsolete |
| **1.10.163.0** | **Old-Gen (OG)** |
| 1.10.980 | Obsolete |
| **1.10.984.0** | **Next-Gen (NG)** |
| 1.11.137–191 | Obsolete |
| **1.11.221.0** | **Anniversary (AE)** |

- **Down-Grade (DG):** OG exe + NG `Fallout4 - Startup.ba2` (CRC `A5808F5F`).
- `steam_api64.dll`: Steam OG vs shared NG/AE hashes; GOG OG CRC `BD3AA35F`.
- F4SE loaders: 0.0.6.23 (OG), 0.0.7.2 (NG), 0.0.7.4–7.7 (Obsolete), 0.0.7.8 (AE).
- Creation Kit: 1.10.162.0 (OG), 1.10.943.1 (Obsolete), 1.10.982.3 (NG), 1.11.137.0 (AE). Missing CK/Archive2 renders neutral gray, not red.
- BA2: v1 universal; v7/v8 NG+; patcher normalizes to v8 when upgrading. Limits: GNRL 256, DX10 255. Modules: Full 254, Light 4096, warn at 95%.

All CRC tables, version constants, and F4SE compatible-version magic numbers (`0x010A3D40`, `0x010A3D80`, `0x010B0890`) port verbatim from `globals.py`.

---

## 11. Milestones

| # | Milestone | Contents | Exit criteria |
|---|---|---|---|
| M1 | Core library | Game/MM detection, install-type classification, settings, logging, Overview census (binaries/archives/modules) | Unit tests green against fixtures; CLI smoke harness prints correct census for OG and NG installs |
| M2 | Shell + Overview + Settings + About | Window, theme, tab shell, update banner, three Overview group boxes, Settings/About tabs | Side-by-side visual review vs Python screenshots; settings.json interop verified |
| M3 | F4SE + Scanner | Static PE F4SE analysis, full scan engine, results tree, details pane, MO2 mod attribution | Scan output matches Python output on the same test Data folder (diff = empty) |
| M4 | Downgrader + Archive Patcher | Delta download/apply, backups, BA2 byte patching, logs/progress | Round-trip OG↔NG on a real install; BA2 v1↔v8 round-trip byte-identical except version byte |
| M5 | Release hardening | Crash dialog, close guards, perf pass, icon/asset polish, self-contained publish, MO2/Vortex launch testing (incl. MO2 VFS) | Beta build to #cm-toolkit testers |

---

## 12. Resolved Design Decisions

Formerly open questions; all resolved per the recommended option.

1. **Scanner pane layout** (§5.3): **Decided** — integrate the Scan Settings pane and Result Details pane into the main window on the Scanner tab. No floating docked windows.
2. **Window sizing:** **Decided** — window dimensions are flexible; size to fit WinUI control metrics while keeping the compact fixed-size, non-resizable character (§3.1). One global window size for all tabs, accommodating the integrated Scanner panes; exact dimensions finalized at the M2/M3 visual reviews.
3. **xdelta strategy:** **Decided** — bundle `xdelta3.exe` and invoke it as a child process for delta patch application.
4. **Icon glyphs:** **Decided** — Segoe Fluent Icons glyphs for UI chrome (refresh, info, warning, check, update); existing PNG assets for brand logos (Nexus Mods, Discord, GitHub) and the app icon.
5. **Nexus update check:** **Decided** — keep HTML scraping for v1 parity; Nexus API migration deferred to a post-release enhancement.

---

## 13. Acceptance Criteria (summary)

- All six tabs, both modal tools, and all dialogs present with matching labels, groupings, ordering, colors, and tooltips (verified against Python-version screenshots).
- Identical scan results, install-type classification, and counts on a reference OG install, NG install, and AE install.
- `settings.json` written by Python 0.6.1 loads unmodified; settings written by the port load in Python 0.6.1.
- Launches correctly via MO2 and Vortex as a registered executable; no crash when run inside MO2 VFS (fix or explicitly document if still unsupported).
- Cold start to interactive Overview ≤ 2 s on a SATA-SSD reference machine (Python/PyInstaller baseline is noticeably slower).
- No UI freezes during scan, downgrade, or archive patching.
