from enum import Enum, IntEnum, IntFlag, StrEnum


class Tool(tuple[str, ...], Enum):
	xEdit = ("xedit.exe", "fo4edit.exe")  # noqa: N815
	BSArch = ("bsarch.exe",)
	ComplexSorter = ("complex sorter (32bit).bat", "complex sorter.bat")


class CSIDL(IntEnum):
	Desktop = 0
	Documents = 5
	AppData = 26
	AppDataLocal = 28


class InstallType(StrEnum):
	OG = "Old-Gen"
	DG = "Down-Grade"
	NG = "Next-Gen"
	Unknown = "Unknown"
	NotFound = "Not Found"


class Magic(bytes, Enum):
	BTDX = b"BTDX"
	GNRL = b"GNRL"
	DX10 = b"DX10"
	TES4 = b"TES4"
	HEDR = b"HEDR"
	DDS = b"DDS "


class Tab(StrEnum):
	Overview = "Overview"
	F4SE = "F4SE"
	Scanner = "Scanner"
	Tools = "Tools"
	About = "About"


class LogType(StrEnum):
	Info = "info"
	Good = "good"
	Bad = "bad"


class ArchiveVersion(IntEnum):
	OG = 1
	NG7 = 7
	NG = 8


class ModuleFlag(IntFlag):
	Light = 0x0200


class ProblemType(StrEnum):
	JunkFile = "Junk File"
	UnexpectedFormat = "Unexpected Format"
	MisplacedDLL = "Misplaced DLL"
	LoosePrevis = "Loose Previs"
	AnimTextDataFolder = "Loose AnimTextData"
	InvalidArchive = "Invalid Archive"
	InvalidModule = "Invalid Module"
	InvalidArchiveName = "Invalid Archive Name"
	F4SEOverride = "F4SE Script Override"
	FileNotFound = "File Not Found"
	WrongVersion = "Wrong Version"
	ComplexSorter = "Complex Sorter Error"


class SolutionType(StrEnum):
	ArchiveOrDeleteFile = "These files should either be archived or deleted."
	ArchiveOrDeleteFolder = "These folders should either be archived or deleted."
	DeleteFile = "This file should be deleted."
	# DeleteFolder = "This folder should be deleted."
	ConvertDeleteOrIgnoreFile = "This file may need to be converted and relevant files updated for the new name.\nOtherwise it can likely be deleted or ignored."
	DeleteOrIgnoreFile = "It can either be deleted or ignored."
	DeleteOrIgnoreFolder = "It can either be deleted or ignored."
	RenameArchive = "Archives must be named the same as a plugin with an added suffix or added to an INI."
	DownloadMod = "Download the mod here:"
	VerifyFiles = (
		"Verify files with Steam or reinstall the game.\nIf you downgraded the game you will need to do so again afterward."
	)
	UnknownFormat = "If this file type is expected here, please report it."
	ComplexSorterFix = "IF you are using xEdit v4.1.5g+, all references to 'Addon Index' in this file should be updated to 'Parent Combination Index'."


class Language(StrEnum):
	Chinese = "cn"
	German = "de"
	English = "en"
	Spanish = "es"
	SpanishLatinAmerica = "esmx"
	French = "fr"
	Italian = "it"
	Japanese = "ja"
	Polish = "pl"
	BrazilianPortuguese = "ptbr"
	Russian = "ru"
