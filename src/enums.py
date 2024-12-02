from enum import Enum, IntEnum, IntFlag, StrEnum, auto


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


class ProblemType(IntEnum):
	JunkFile = auto()
	UnexpectedFormat = auto()
	MisplacedDLL = auto()
	LoosePrevis = auto()
	AnimTextDataFolder = auto()
	InvalidArchiveName = auto()


class SolutionType(Enum):
	ArchiveOrDelete = auto()
	DeleteFile = auto()
	DeleteFolder = auto()
	DeleteOrIgnoreFile = auto()
	RenameArchive = auto()

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
