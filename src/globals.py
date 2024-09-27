from helpers import BaseGameFile, InstallType

APP_TITLE = "Collective Modding Toolkit"
APP_VERSION = 0.1

MAX_MODULES_FULL = 254
MAX_MODULES_LIGHT = 4096
MAX_ARCHIVES_GNRL = 255
MAX_ARCHIVES_DX10 = None
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

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 450

WINDOW_WIDTH_PATCHER = 700
WINDOW_HEIGHT_PATCHER = 600

PADDING_SEPARATOR_ENDS = 10
PADDING_SEPARATOR_SIDES = 10
SEPARATOR_WIDTH = 1

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
	"Fallout4.esm",
	"Fallout4_VR.esm",
	"DLCRobot.esm",
	"DLCworkshop01.esm",
	"DLCworkshop02.esm",
	"DLCworkshop03.esm",
	"DLCCoast.esm",
	"DLCNukaWorld.esm",
	"DLCUltraHighResolution.esm",
)

ABOUT_ARCHIVES = """Bethesda Archive (BA2) Formats & Versions

There are 2 types and 3 versions for Fallout 4 BA2 files:
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
