#
# Collective Modding Toolkit
# Copyright (C) 2024, 2025  wxMichael
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.
#


from enums import InstallType

APP_TITLE = "Collective Modding Toolkit"
APP_VERSION = "0.6.3"

MAX_MODULES_FULL = 254
MAX_MODULES_LIGHT = 4096
MAX_ARCHIVES_GNRL = 256
MAX_ARCHIVES_DX10 = 255
MAX_ARCHIVES_GNRL_AE = 1024
MAX_ARCHIVES_DX10_AE = 1023

COLOR_DEFAULT = "#CACACA"
COLOR_GOOD = "green2"
COLOR_BAD = "#AF5A66"
COLOR_INFO = "dodger blue"
COLOR_NEUTRAL_1 = "gray"
COLOR_NEUTRAL_2 = "bisque"
COLOR_WARNING = "orange"
COLOR_NOTE = "#C5C464"
COLOR_INDIE = "#4b92da"

NEXUS_LINK = "https://www.nexusmods.com/fallout4/mods/87907"
DISCORD_INVITE = "https://discord.gg/tktyEyYHZH"
GITHUB_LINK = "https://github.com/wxMichael/Collective-Modding-Toolkit"

PATCHER_FILTER_OG = "Showing all v1\n(Includes Base Game/DLC/CC)"
PATCHER_FILTER_NG = "Showing all v7 & v8\n(Includes Base Game/DLC/CC)"

NG_STARTUP_BA2_CRC = "A5808F5F"

MODULE_VERSION_95 = b"\x33\x33\x73\x3f"
MODULE_VERSION_1 = b"\x00\x00\x80\x3f"

MODULE_VERSION_SUPPORT = {
	"Morrowind": {"1.2", "1.3"},
	"Oblivion": {"0.8", "1.0"},
	"Skyrim LE": {"0.94", "1.70"},
	"Skyrim VR": {"0.94", "1.70"},
	"Skyrim SE": {"0.94", "1.70", "1.71"},
	"Fallout 3": {"0.85", "0.94"},
	"Fallout 4 VR": {"0.95"},
	"Fallout 4": {"0.95", "1.00"},
	"Fallout NV": {"0.94", "1.32", "1.33", "1.34"},
	"Fallout 76": {"68.0", "216.0", "223.0"},
	"Starfield": {"0.96"},
}

_ui_scale = 1.0


def set_ui_scale(factor: float) -> None:
	global _ui_scale  # ruff: ignore[global-statement]
	_ui_scale = max(factor, 1.0)


def scale(pixels: float) -> int:
	return round(pixels * _ui_scale)


WINDOW_WIDTH = 760
WINDOW_HEIGHT = 450

WINDOW_WIDTH_PATCHER = 700
WINDOW_HEIGHT_PATCHER = 600

PADDING_SEPARATOR_ENDS = 10
PADDING_SEPARATOR_SIDES = 10
SEPARATOR_WIDTH = 1

FONT_SMALLER = ("Cascadia Mono", 8)
FONT_SMALL = ("Cascadia Mono", 10)
FONT = ("Cascadia Mono", 12)
FONT_LARGE = ("Cascadia Mono", 20)

RACE_SUBGRAPH_THRESHOLD = 100

BASE_FILES: dict[str, dict[str, InstallType]] = {
	"Fallout4.exe": {
		"1.10.120.0": InstallType.Obsolete,
		"1.10.130.0": InstallType.Obsolete,
		"1.10.138.0": InstallType.Obsolete,
		"1.10.162.0": InstallType.Obsolete,
		"1.10.163.0": InstallType.OG,
		"1.10.980.0": InstallType.Obsolete,
		"1.10.984.0": InstallType.NG,
		"1.11.137.0": InstallType.Obsolete,
		"1.11.159.0": InstallType.Obsolete,
		"1.11.169.0": InstallType.Obsolete,
		"1.11.191.0": InstallType.Obsolete,
		"1.11.221.0": InstallType.Obsolete,
		"1.11.240.0": InstallType.AE2,  # if we ever get another update, mark as Obsolete2 to keep the 1024 BA2 changes
	},
	"Fallout4Launcher.exe": {
		"02445570": InstallType.OG,  # 1.10.120 to 1.10.163
		"F6A06FF5": InstallType.NG,  # 1.10.980 to 1.10.984
		"0E696744": InstallType.Obsolete,  # 1.11.137
		"D15C6A49": InstallType.Obsolete,  # 1.11.159
		"8C52BE93": InstallType.Obsolete,  # 1.11.169a
		"591009C9": InstallType.Obsolete,  # 1.11.169b
		"720BB9C3": InstallType.Obsolete,  # 1.11.191
		"CA61EDD7": InstallType.Obsolete,  # 1.11.221
		"57D1C794": InstallType.AE2,  # 1.11.240
	},
	"steam_api64.dll": {
		"2.89.45.4": InstallType.OG,  # 1.10.120 to 1.10.163
		"7.40.51.27": InstallType.NGAE,  # 1.10.980 to 1.11.240
		"BD3AA35F": InstallType.OG,  # GOG
	},
	"f4se_loader.exe": {
		"0.0.6.23": InstallType.OG,
		"0.0.7.2": InstallType.NG,
		"0.0.7.4": InstallType.Obsolete,
		"0.0.7.5": InstallType.Obsolete,
		"0.0.7.6": InstallType.Obsolete,
		"0.0.7.7": InstallType.Obsolete,
		"0.0.7.8": InstallType.Obsolete,
		"0.0.7.9": InstallType.AE2,
	},
	"f4se_steam_loader.dll": {
		"0.0.6.23": InstallType.OG,
	},
	"CreationKit.exe": {
		"1.10.162.0": InstallType.OG,
		"1.10.943.1": InstallType.Obsolete,
		"1.10.982.3": InstallType.NG,
		"1.11.137.0": InstallType.Obsolete,
		"1.11.240.0": InstallType.Obsolete,
		"1.11.246.0": InstallType.AE2,
	},
	"Tools\\Archive2\\Archive2.exe": {
		"4CDFC7B5": InstallType.OG,
		"71A5240B": InstallType.NG,
		"C867674F": InstallType.Obsolete,
		"9A059211": InstallType.Obsolete,
		"B2EEF34A": InstallType.AE2,
	},
}

GAME_MASTERS = (
	"fallout4.esm",
	"fallout4_vr.esm",
	"dlcrobot.esm",
	"dlcworkshop01.esm",
	"dlcworkshop02.esm",
	"dlcworkshop03.esm",
	"dlccoast.esm",
	"dlcnukaworld.esm",
	"dlcultrahighresolution.esm",
)

ARCHIVE_NAME_WHITELIST = (
	"creationkit - shaders.ba2",
	"creationkit - textures.ba2",
	"fallout4 - animations.ba2",
	"fallout4 - interface.ba2",
	"fallout4 - materials.ba2",
	"fallout4 - meshes.ba2",
	"fallout4 - meshesextra.ba2",
	"fallout4 - misc.ba2",
	"fallout4 - nvflex.ba2",
	"fallout4 - shaders.ba2",
	"fallout4 - sounds.ba2",
	"fallout4 - startup.ba2",
	"fallout4 - textures1.ba2",
	"fallout4 - textures2.ba2",
	"fallout4 - textures3.ba2",
	"fallout4 - textures4.ba2",
	"fallout4 - textures5.ba2",
	"fallout4 - textures6.ba2",
	"fallout4 - textures7.ba2",
	"fallout4 - textures8.ba2",
	"fallout4 - textures9.ba2",
	"fallout4 - texturespatch.ba2",
	"fallout4 - voices.ba2",
	"dlcultrahighresolution - textures01.ba2",
	"dlcultrahighresolution - textures02.ba2",
	"dlcultrahighresolution - textures03.ba2",
	"dlcultrahighresolution - textures04.ba2",
	"dlcultrahighresolution - textures05.ba2",
	"dlcultrahighresolution - textures06.ba2",
	"dlcultrahighresolution - textures07.ba2",
	"dlcultrahighresolution - textures08.ba2",
	"dlcultrahighresolution - textures09.ba2",
	"dlcultrahighresolution - textures10.ba2",
	"dlcultrahighresolution - textures11.ba2",
	"dlcultrahighresolution - textures12.ba2",
	"dlcultrahighresolution - textures13.ba2",
	"dlcultrahighresolution - textures14.ba2",
	"dlcultrahighresolution - textures15.ba2",
	"dlcultrahighresolution - textures16.ba2",
)

ABOUT_ARCHIVES_TITLE = "Bethesda Archive (BA2) Formats & Versions"
ABOUT_ARCHIVES = """There are 2 formats and 3 versions for Fallout 4 BA2 files:
• General (GNRL)
• Textures (DX10)

• v1: Required by FO4 v1.10.163 and earlier. Works in all versions.
• v7/8: Only supported in FO4 v1.10.980 and later.

It's suspected there are format differences between versions for XBox/PS, but for PC the only difference is the number itself.
v7/8 are identical so this tool only patches to v1 & v8.

Why Patch Versions?

Patching is only needed if you use tools that require it.
Most tools check the version to ensure compatibility but v7/8 didn't exist when these tools were made, so they assume it's a different format and show errors.
Because they're actually identical, you can just patch the version number in the file header so the tools will allow reading them."""

ABOUT_DOWNGRADING_TITLE = "About Downgrading Fallout 4 & Creation Kit"
ABOUT_DOWNGRADING = """This downgrader makes use of delta patches which are downloaded as-needed from the CMT GitHub page.
Patches range in size from 1KB to 66MB.

Backups are created prior to patching, and will be used instead of patches if present.
Simple Downgrader's backups will also be used.
Backup naming:
Fallout4_downgradeBackup.exe
Fallout4_upgradeBackup.exe

Both Creation Kit and the game require steam_api64.dll to match their version, so they must be patched together (for now)."""

ABOUT_F4SE_DLLS = """This checks all DLLs in
Data/F4SE/Plugins/ for
version-specific code to
determine OG/NG/AE support.

\N{HEAVY CHECK MARK} Version is supported

\N{HEAVY ASTERISK} DLL uses Address Library

\N{BLACK QUESTION MARK ORNAMENT} Not an F4SE DLL.
May still be loaded by
other DLLs.

\N{WARNING SIGN} Consult mod page to
verify version support if
you see this icon.
Some DLLs' version support
cannot be reliably
determined."""

TOOLTIP_NO_MOD_MANAGER = "Your mod manager must launch the app to be detected."
TOOLTIP_GAME_PATH = "Click to open folder"
TOOLTIP_LOCATION = "Click to open location"
TOOLTIP_REFRESH = "Refresh"

TOOLTIP_ADDRESS_LIBRARY_MISSING = "Address Library is required for many F4SE mods."

TOOLTIP_BA2_FORMATS = """General/GNRL/Main: Used for all non-texture files.
Hard limit of 256, after which the game will crash at the main menu.

Texture/DX10: Used only for textures.
No hard limit, but functional limit is 255, after which the game fails
to use correct textures.
1.11.240 has increased this limit to 1024."""
TOOLTIP_UNREADABLE = "Files that could not be read due to permissions, unexpected format, or corruption."
TOOLTIP_BA2_VERSIONS = """v1 works with all FO4 versions.
v7/v8 require either BASS or NG.
Some apps only support v1."""
TOOLTIP_MODULE_TYPES = """Full modules include all non-Light modules.
Light modules are ESL-flagged and/or have the .esl extension.

Light modules give up the capacity to contain more than 4096
new records in exchange for having a higher plugin limit."""
TOOLTIP_HEDR_100 = """Plugin header v1.00 has a larger Form ID range.
Any plugins with IDs below 800 MUST be v1.00.
FO4VR only supports v0.95."""
TOOLTIP_HEDR_95 = """Plugin header v0.95 has a smaller Form ID range.
Any plugins with IDs below 800 MUST be v1.00.
FO4VR only supports v0.95.

In the base game, these 4 modules are v0.95:
• DLCCoast.esm
• DLCworkshop02.esm
• DLCworkshop03.esm
• DLCNukaWorld.esm"""
TOOLTIP_HEDR_UNKNOWN = """These modules have an unsupported header version.
Fallout 4 supports only v0.95 and v1.00.

Files with v0.94 were likey made with FalloutSnip and
should be replaced, recreated, or removed.
Use such mods AT YOUR OWN RISK as they may result
in unknown behavior or issues due to having an invalid
structure or corruption."""

TOOLTIP_SCAN_OVERVIEW = "Report details of issues from Overview"
TOOLTIP_SCAN_ERRORS = """Check for errors in mod configuration or files."""
TOOLTIP_SCAN_FORMATS = "Check file types against a whitelist per Data folder.\ne.g. MP3 instead of XWM/WAV in Data/Sound/."
TOOLTIP_SCAN_PREVIS = "Report loose Data/Vis/ and Data/Meshes/Precombined/ folders."
TOOLTIP_SCAN_JUNK = """Report junk files such as desktop.ini, Thumbs.db,
and leftover fomod folders."""
TOOLTIP_SCAN_BAD_OVERRIDES = """Check for overrides that typically cause issues
such as outdated F4SE script files or loose AnimTextData folders."""
INFO_SCAN_RACE_SUBGRAPHS = """Counts race animation subgraph records (RACE \\ SADD).
Depending on your PC, adding too many of these may result in stutter when loading Cells.
This issue needs more investigation as this may be mere correlation and not causation."""
TOOLTIP_SCAN_RACE_SUBGRAPHS = f"""{INFO_SCAN_RACE_SUBGRAPHS}

Base Game Count: 37
Warning Threshold: {RACE_SUBGRAPH_THRESHOLD}"""

TOOLTIP_SCAN_DDS = "Check dimensions and formats of DDS files for issues."
TOOLTIP_SCAN_BA2 = "Scan inside BA2 archives.\nNote: Checks may be limited for compressed archives."
TOOLTIP_SCAN_CONFLICTS = "Detect conflicting mods and mod settings."
TOOLTIP_SCAN_SUGGEST = "Make suggestions for changes to your mod setup."

TOOLTIP_UPDATE_SOURCE = """GitHub will always have the latest release.
Nexus Mods releases may be delayed to
await more testing."""
TOOLTIP_LOG_LEVEL = """Sets the minimum importance level for messages sent to the log file.
DEBUG: Extra verbose.
INFO: Default.
ERROR: Only log errors."""

TOOLTIP_DOWNGRADER_BACKUPS = """Backups are created prior to patching, and will be used instead of patches if present.
Simple Downgrader's backups will also be used.

Backups allow quicker switching between versions.
Uncheck this to delete backups after patching."""
TOOLTIP_DOWNGRADER_DELTAS = """Delta patches are downloaded as-needed and used to patch from one version to another.
If backups are present, they will be used instead.

These xdelta files are only needed during the patching process.
Check this to delete xdeltas after patching."""

F4SE_CRC = {
	"actor.pex": ("C250936E", "AE6222BE", "72388175"),
	"actorbase.pex": ("0681E1F5", "FB9BCDAB", "8206385D"),
	"armor.pex": ("C145D146", "3F9E535A", "06FC8AB2"),
	"armoraddon.pex": ("B0D1B057", "4F62262C", "8453CB43"),
	"cell.pex": ("0CB47BBE", "29F5583B", "043B5F5A"),
	"component.pex": ("EE3B04A6", "CF50DEA9", "6A1A2D87"),
	"constructibleobject.pex": ("9CDD93BE", "55489CE6", "3C9B9628"),
	"defaultobject.pex": ("9DF10D4B", "D173AE18", "AD23389A"),
	"encounterzone.pex": ("4EC6CE1F", "A70D8729", "6C1C70D5"),
	"equipslot.pex": ("3ECC3CA5", "73A59F70", "33DEE9AF"),
	"f4se.pex": ("6EEEE7D9", "13E2A430", "C3FC9A6E"),
	"favoritesmanager.pex": ("AC1694B2", "4933B1C6", "0D6CA970"),
	"form.pex": ("57919410", "06E8A822", "FF43CA3E"),
	"game.pex": ("2B0602CC", "BCF2E430", "8876EE5C"),
	"headpart.pex": ("8DC03678", "F6E4A814", "8F5714E9"),
	"input.pex": ("92399489", "D5FC1734", "BA2FF626"),
	"instancedata.pex": ("73F0FBBC", "C1F7FA69", "5AB4C774"),
	"location.pex": ("D35726C4", "F2E89378", "427B459D"),
	"math.pex": ("8D97F9D2", "35F956BD", "05DEB0F0"),
	"matswap.pex": ("49F6C1D2", "CC2D9B50", "B6E8FA13"),
	"miscobject.pex": ("A6DE1C41", "C4EA2902", "C672A908"),
	"objectmod.pex": ("9161CD93", "97601F72", "D58CA42E"),
	"objectreference.pex": ("AD399939", "64FC714E", "4F79982B"),
	"perk.pex": ("F7D88CCC", "D596624D", "432D9EB4"),
	"scriptobject.pex": ("E3AF8EC9", "68F24E0F", "41228361"),
	"ui.pex": ("00286C67", "749CC3DA", "BBF99EC3"),
	"utility.pex": ("5FDFAB76", "9B902650", "4FA68A14"),
	"watertype.pex": ("6543E221", "946E310A", "11400876"),
	"weapon.pex": ("E1E3A63C", "BCA3FD37", "996B1034"),
}
