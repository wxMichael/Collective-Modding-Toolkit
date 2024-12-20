from typing import NotRequired, TypedDict

from enums import InstallType

APP_TITLE = "Collective Modding Toolkit"
APP_VERSION = "0.3.1"

MAX_MODULES_FULL = 254
MAX_MODULES_LIGHT = 4096
MAX_ARCHIVES_GNRL = 256
MAX_ARCHIVES_DX10 = 256

COLOR_DEFAULT = "#CACACA"
COLOR_GOOD = "green2"
COLOR_BAD = "firebrick1"
COLOR_INFO = "dodger blue"
COLOR_NEUTRAL_1 = "gray"
COLOR_NEUTRAL_2 = "bisque"
COLOR_WARNING = "orange"

NEXUS_LINK = "https://www.nexusmods.com/fallout4/mods/87907"
DISCORD_INVITE = "https://discord.gg/pF9U5FmD6w"
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


class BaseGameFile(TypedDict):
	OnlyOG: NotRequired[bool]
	UseHash: NotRequired[bool]
	Versions: dict[str, InstallType]


BASE_FILES: dict[str, BaseGameFile] = {
	"Fallout4.exe": {
		"Versions": {
			"1.10.163.0": InstallType.OG,
			"1.10.980.0": InstallType.NG,
			"1.10.984.0": InstallType.NG,
		},
	},
	"Fallout4Launcher.exe": {
		"UseHash": True,
		"Versions": {
			"02445570": InstallType.OG,
			"F6A06FF5": InstallType.NG,
		},
	},
	"steam_api64.dll": {
		"Versions": {
			"2.89.45.4": InstallType.OG,
			"7.40.51.27": InstallType.NG,
		},
	},
	"f4se_loader.exe": {
		"Versions": {
			"0.0.6.23": InstallType.OG,
			"0.0.7.2": InstallType.NG,
		},
	},
	"f4se_steam_loader.dll": {
		"OnlyOG": True,
		"Versions": {
			"0.0.6.23": InstallType.OG,
		},
	},
	"CreationKit.exe": {
		"Versions": {
			"1.10.162.0": InstallType.OG,
			"1.10.982.3": InstallType.NG,
		},
	},
	"Tools\\Archive2\\Archive2.exe": {
		"Versions": {
			"1.1.0.4": InstallType.OG,
			"1.1.0.5": InstallType.NG,
		},
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

• v1: FO4 v1.10.163 and earlier
• v7/8: FO4 v1.10.980 and later

It's suspected there are format differences between versions for XBox/PS, but for PC the only difference is the number itself.
v7/8 are identical so this tool only patches to v1 & v8.

Why Patch Versions?

Patching is only needed if you use tools that require it.
Most tools check the version to ensure compatiblity but v7/8 didn't exist when these tools were made, so they assume it's a different format and show errors.
Because they're actually identical, you can just patch the version number in the file header so the tools will allow reading them."""

ABOUT_DOWNGRADING_TITLE = "About Downgrading Fallout 4 & Creation Kit"
ABOUT_DOWNGRADING = """This downgrader makes use of delta patches which are downloaded as-needed from the CMT GitHub page.
Patches range in size from 23KB to 63MB.

Backups are created prior to patching, and will be used instead of patches if present.
Simple Downgrader's backups will also be used.
Backup naming:
Fallout4_downgradeBackup.exe
Fallout4_upgradeBackup.exe

Both Creation Kit and the game require steam_api64.dll to match their version, so they must be patched together (for now)."""

ABOUT_F4SE_DLLS = """This checks all DLLs in
Data/F4SE/Plugins/ for
version-specific code to
determine OG/NG support.

\N{HEAVY CHECK MARK} Version is supported

\N{CROSS MARK} Version not supported

\N{BLACK QUESTION MARK ORNAMENT} Not an F4SE DLL.
May still be loaded by
other DLLs.

\N{WARNING SIGN} Consult mod page to
verify version support if
you see this icon.
Some DLLs detected as OG+NG
only actually support both
enough to tell users if
they have the wrong DLL."""

TOOLTIP_NO_MOD_MANAGER = "Your mod manager must launch the app to be detected."
TOOLTIP_GAME_PATH = "Click to open folder"
TOOLTIP_LOCATION = "Click to open location"
TOOLTIP_REFRESH = "Refresh"

TOOLTIP_ADDRESS_LIBRARY_MISSING = "Address Library is required for many F4SE mods."

TOOLTIP_BA2_FORMATS = """General/GNRL/Main: Used for all non-texture files.
Hard limit of 256, after which the game will crash at the main menu.

Texture/DX10: Used only for textures.
No hard limit, but functional limit is 256, after which the game fails
to use correct textures."""
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
TOOLTIP_HEDR_UNKNOWN = """These modules have an unknown header version.
Fallout 4 OG & NG support only v0.95 and v1.00."""

TOOLTIP_SCAN_OVERVIEW = "Report issues from Overview"
TOOLTIP_SCAN_FORMATS = "Check file types against a whitelist per Data folder.\ne.g. MP3 instead of XWM/WAV in Data/Sound/."
TOOLTIP_SCAN_PREVIS = "Report loose Data/Vis/ and Data/Meshes/Precombined/ folders."
TOOLTIP_SCAN_JUNK = """Report junk files such as desktop.ini, Thumbs.db,
and leftover fomod folders."""
TOOLTIP_SCAN_BAD_OVERRIDES = """Detect overrides that typically cause issues
such as outdated F4SE script files or loose AnimTextData folders."""

TOOLTIP_SCAN_DDS = "Check dimensions and formats of DDS files for issues."
TOOLTIP_SCAN_BA2 = "Scan inside BA2 archives.\nNote: Checks may be limited for compressed archives."
TOOLTIP_SCAN_CONFLICTS = "Detect conflicting mods and mod settings."
TOOLTIP_SCAN_SUGGEST = "Make suggestions for changes to your mod setup."

TOOLTIP_SAVE_MODE = """Settings are saved to a JSON file by default.
If this is disabled or the JSON file is deleted, default
settings will be used and update checks will be disabled."""
TOOLTIP_UPDATE_MODE = """GitHub will always have the latest release.
Nexus Mods releases may be delayed due to
their review process or to await more testing."""

TOOLTIP_DOWNGRADER_BACKUPS = """Backups are created prior to patching, and will be used instead of patches if present.
Simple Downgrader's backups will also be used.

Backups allow quicker switching between versions.
Uncheck this to delete backups after patching."""
TOOLTIP_DOWNGRADER_DELTAS = """Delta patches are downloaded as-needed and used to patch from one version to another.
If backups are present, they will be used instead.

These xdelta files are only needed during the patching process.
Check this to delete xdeltas after patching."""

F4SE_CRC = {
	"actor.pex": ("C250936E", "AE6222BE"),
	"actorbase.pex": ("0681E1F5", "FB9BCDAB"),
	"armor.pex": ("C145D146", "3F9E535A"),
	"armoraddon.pex": ("B0D1B057", "4F62262C"),
	"cell.pex": ("0CB47BBE", "29F5583B"),
	"component.pex": ("EE3B04A6", "CF50DEA9"),
	"constructibleobject.pex": ("9CDD93BE", "55489CE6"),
	"defaultobject.pex": ("9DF10D4B", "D173AE18"),
	"encounterzone.pex": ("4EC6CE1F", "A70D8729"),
	"equipslot.pex": ("3ECC3CA5", "73A59F70"),
	"f4se.pex": ("6EEEE7D9", "13E2A430"),
	"favoritesmanager.pex": ("AC1694B2", "4933B1C6"),
	"form.pex": ("57919410", "06E8A822"),
	"game.pex": ("2B0602CC", "BCF2E430"),
	"headpart.pex": ("8DC03678", "F6E4A814"),
	"input.pex": ("92399489", "D5FC1734"),
	"instancedata.pex": ("73F0FBBC", "C1F7FA69"),
	"location.pex": ("D35726C4", "F2E89378"),
	"matswap.pex": ("49F6C1D2", "CC2D9B50"),
	"math.pex": ("8D97F9D2", "35F956BD"),
	"miscobject.pex": ("A6DE1C41", "C4EA2902"),
	"objectmod.pex": ("9161CD93", "97601F72"),
	"objectreference.pex": ("AD399939", "64FC714E"),
	"perk.pex": ("F7D88CCC", "D596624D"),
	"scriptobject.pex": ("E3AF8EC9", "68F24E0F"),
	"ui.pex": ("00286C67", "749CC3DA"),
	"utility.pex": ("5FDFAB76", "9B902650"),
	"watertype.pex": ("6543E221", "946E310A"),
	"weapon.pex": ("E1E3A63C", "BCA3FD37"),
}
