# code originally written by perchik71
# TODO: Fix all the names

import ctypes
import logging
import typing
from enum import IntFlag

if typing.TYPE_CHECKING:
	from pathlib import Path

	from helpers import DLLInfo


logger = logging.getLogger(__name__)


def MAKE_EXE_VERSION_EX(major: int, minor: int, build: int, sub: int):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
	result = ((major & 0xFF) << 24) | ((minor & 0xFF) << 16) | ((build & 0xFFF) << 4) | (sub & 0xF)
	return ctypes.c_uint32(result).value


def MAKE_EXE_VERSION(major: int, minor: int, build: int):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
	return MAKE_EXE_VERSION_EX(major, minor, build, 0)


def GET_EXE_VERSION_MAJOR(a):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function, missing-type-function-argument]
	val = ctypes.c_uint32(a).value
	return (val & 0xFF000000) >> 24


def GET_EXE_VERSION_MINOR(a):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function, missing-type-function-argument]
	val = ctypes.c_uint32(a).value
	return (val & 0x00FF0000) >> 16


def GET_EXE_VERSION_BUILD(a):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function, missing-type-function-argument]
	val = ctypes.c_uint32(a).value
	return (val & 0x0000FFF0) >> 4


def GET_EXE_VERSION_SUB(a):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function, missing-type-function-argument]
	val = ctypes.c_uint32(a).value
	return (val & 0x0000000F) >> 0


DONT_RESOLVE_DLL_REFERENCES = 0x00000001

RUNTIME_VERSION_1_1_29 = MAKE_EXE_VERSION(1, 1, 29)  # 0x010101D0    initial version
RUNTIME_VERSION_1_1_30 = MAKE_EXE_VERSION(1, 1, 30)  # 0x010101E0	day1 patch
RUNTIME_VERSION_1_2 = MAKE_EXE_VERSION(1, 2, 33)  # 0x01020210	beta
RUNTIME_VERSION_1_2_37 = MAKE_EXE_VERSION(1, 2, 37)  # 0x01020250	beta
RUNTIME_VERSION_1_3_45 = MAKE_EXE_VERSION(1, 3, 45)  # 0x010302D0	beta
RUNTIME_VERSION_1_3_47 = MAKE_EXE_VERSION(1, 3, 47)  # 0x010302F0	release
RUNTIME_VERSION_1_4_124 = MAKE_EXE_VERSION(1, 4, 124)  # 0x010407C0	beta
RUNTIME_VERSION_1_4_125 = MAKE_EXE_VERSION(1, 4, 125)  # 0x010407D0	beta
RUNTIME_VERSION_1_4_131 = MAKE_EXE_VERSION(1, 4, 131)  # 0x01040830	beta
RUNTIME_VERSION_1_4_132 = MAKE_EXE_VERSION(1, 4, 132)  # 0x01040840	released without a beta version
RUNTIME_VERSION_1_5_141 = MAKE_EXE_VERSION(1, 5, 141)  # 0x010508D0	beta
RUNTIME_VERSION_1_5_147 = MAKE_EXE_VERSION(1, 5, 147)  # 0x01050930	beta
RUNTIME_VERSION_1_5_151 = MAKE_EXE_VERSION(1, 5, 151)  # 0x01050970	beta
RUNTIME_VERSION_1_5_154 = MAKE_EXE_VERSION(1, 5, 154)  # 0x010509A0	beta
RUNTIME_VERSION_1_5_157 = MAKE_EXE_VERSION(1, 5, 157)  # 0x010509D0	beta
RUNTIME_VERSION_1_5_205 = MAKE_EXE_VERSION(1, 5, 205)  # 0x01050CD0	beta
RUNTIME_VERSION_1_5_210 = MAKE_EXE_VERSION(1, 5, 210)  # 0x01050D20	beta
RUNTIME_VERSION_1_5_307 = MAKE_EXE_VERSION(1, 5, 307)  # 0x01051330	release
RUNTIME_VERSION_1_5_412 = MAKE_EXE_VERSION(1, 5, 412)  # 0x010519C0	beta
RUNTIME_VERSION_1_5_414 = MAKE_EXE_VERSION(1, 5, 414)  # 0x010519E0	beta
RUNTIME_VERSION_1_5_416 = MAKE_EXE_VERSION(1, 5, 416)  # 0x01051A00	release
RUNTIME_VERSION_1_6_0 = MAKE_EXE_VERSION(1, 6, 0)  # 0x01060000	beta
RUNTIME_VERSION_1_6_3 = MAKE_EXE_VERSION(1, 6, 3)  # 0x01060030	beta - promoted to release
RUNTIME_VERSION_1_6_9 = MAKE_EXE_VERSION(1, 6, 9)  # 0x01060090	release
RUNTIME_VERSION_1_7_7 = MAKE_EXE_VERSION(1, 7, 7)  # 0x01070070	beta
RUNTIME_VERSION_1_7_9 = MAKE_EXE_VERSION(1, 7, 9)  # 0x01070090	beta - promoted to release
RUNTIME_VERSION_1_7_10 = MAKE_EXE_VERSION(1, 7, 10)  # 0x010700A0	release
RUNTIME_VERSION_1_7_12 = MAKE_EXE_VERSION(1, 7, 12)  # 0x010700C0	release
RUNTIME_VERSION_1_7_15 = MAKE_EXE_VERSION(1, 7, 15)  # 0x010700F0	release
RUNTIME_VERSION_1_7_19 = MAKE_EXE_VERSION(1, 7, 19)  # 0x01070130	release - rolled back
RUNTIME_VERSION_1_7_22 = MAKE_EXE_VERSION(1, 7, 22)  # 0x01070160	release - bugfix for 1.7.19
RUNTIME_VERSION_1_8_7 = MAKE_EXE_VERSION(1, 8, 7)  # 0x01080070	release
RUNTIME_VERSION_1_9_4 = MAKE_EXE_VERSION(1, 9, 4)  # 0x01090040	release
RUNTIME_VERSION_1_10_20 = MAKE_EXE_VERSION(1, 10, 20)  # 0x010A0140	beta/release
RUNTIME_VERSION_1_10_26 = MAKE_EXE_VERSION(1, 10, 26)  # 0x010A01A0	creation club update 2
RUNTIME_VERSION_1_10_40 = MAKE_EXE_VERSION(1, 10, 40)  # 0x010A0280	creation club update 3
RUNTIME_VERSION_1_10_50 = MAKE_EXE_VERSION(1, 10, 50)  # 0x010A0320	creation club update 4
RUNTIME_VERSION_1_10_64 = MAKE_EXE_VERSION(1, 10, 64)  # 0x010A0400	creation club update 5
RUNTIME_VERSION_1_10_75 = MAKE_EXE_VERSION(1, 10, 75)  # 0x010A04B0	creation club update 6
RUNTIME_VERSION_1_10_82 = MAKE_EXE_VERSION(1, 10, 82)  # 0x010A0520	creation club update 7
RUNTIME_VERSION_1_10_89 = MAKE_EXE_VERSION(1, 10, 89)  # 0x010A0590	creation club update 8
RUNTIME_VERSION_1_10_98 = MAKE_EXE_VERSION(1, 10, 98)  # 0x010A0620	creation club update 9
RUNTIME_VERSION_1_10_106 = MAKE_EXE_VERSION(1, 10, 106)  # 0x010A06A0	creation club update 10
RUNTIME_VERSION_1_10_111 = MAKE_EXE_VERSION(1, 10, 111)  # 0x010A06F0	creation club update 11
RUNTIME_VERSION_1_10_114 = MAKE_EXE_VERSION(1, 10, 114)  # 0x010A0720	creation club update 12
RUNTIME_VERSION_1_10_120 = MAKE_EXE_VERSION(1, 10, 120)  # 0x010A0780	creation club update 13
RUNTIME_VERSION_1_10_130 = MAKE_EXE_VERSION(1, 10, 130)  # 0x010A0820	creation club update 14
RUNTIME_VERSION_1_10_138 = MAKE_EXE_VERSION(1, 10, 138)  # 0x010A08A0	creation club update 15
RUNTIME_VERSION_1_10_162 = MAKE_EXE_VERSION(1, 10, 162)  # 0x010A0A20	creation club update 16
RUNTIME_VERSION_1_10_163 = MAKE_EXE_VERSION(1, 10, 163)  # 0x010A0A30	creation club update 17
RUNTIME_VERSION_1_10_980 = MAKE_EXE_VERSION(1, 10, 980)  # 0x010A3D40	'next generation' update
RUNTIME_VERSION_1_10_984 = MAKE_EXE_VERSION(1, 10, 984)  # 0x010A3D80	hotfix
RUNTIME_VERSION_1_11_137 = MAKE_EXE_VERSION(1, 11, 137)  # 0x010B0890	'anniversary edition' update
RUNTIME_VERSION_1_11_159 = MAKE_EXE_VERSION(1, 11, 159)  # 0x010B09F0	hotfix
RUNTIME_VERSION_1_11_169 = MAKE_EXE_VERSION(1, 11, 169)  # 0x010B0A90	hotfix
RUNTIME_VERSION_1_11_191 = MAKE_EXE_VERSION(1, 11, 191)  # 0x010B0BF0	hotfix
RUNTIME_VERSION_1_11_221 = MAKE_EXE_VERSION(1, 11, 221)  # 0x010B0DD0
RUNTIME_VERSION_1_11_240 = MAKE_EXE_VERSION(1, 11, 240)  # 0x010B0F00	creation club

RUNTIME_VERSION_MAMMONTH_SHIT_LATEST = RUNTIME_VERSION_1_10_162
RUNTIME_VERSION_OG_LATEST = RUNTIME_VERSION_1_10_163
RUNTIME_VERSION_NG_LATEST = RUNTIME_VERSION_1_10_984
RUNTIME_VERSION_AE_LATEST = RUNTIME_VERSION_1_11_240


class VersionSupport(IntFlag):
	kVersionSupportOG = (1,)
	kVersionSupportNG = (2,)
	kVersionSupportAE = (4,)


class F4SEPluginVersion(IntFlag):
	kVersion = 1


class F4SEPluginAddressIndependence(IntFlag):
	# set this if you exclusively use signature matching to find your addresses and have NO HARDCODED ADDRESSES
	# the F4SE code does not use signature matching, so calling functions in the F4SE headers is not safe with this flag
	kAddressIndependence_Signatures = 1  # 0b001
	# set this if you are using a 1.10.980+ version of the Address Library
	kAddressIndependence_AddressLibrary_1_10_980 = 2  # 0b010
	# set this if you are using a 1.11.137+ version of the Address Library
	kAddressIndependence_AddressLibrary_1_11_137 = 4  # 0b100


class F4SEPluginStructureIndependence(IntFlag):
	# set this if your plugin doesn't use any game structures
	kStructureIndependence_NoStructs = 1  # 0b001
	# works with the structure layout in 1.10.980+
	kStructureIndependence_1_10_980Layout = 2  # 0b010
	# works with the structure layout in 1.11.137+
	kStructureIndependence_1_11_137Layout = 4  # 0b100


ArrayCompatibleVersion = ctypes.c_uint32 * 16


def F4SEPlugin_IsAE(version: ctypes.c_uint32):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
	return version >= RUNTIME_VERSION_1_11_137


def F4SEPlugin_IsNG(version: ctypes.c_uint32):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
	return (version >= RUNTIME_VERSION_1_10_980) and (version <= RUNTIME_VERSION_1_10_984)


def F4SEPlugin_IsOG(version: ctypes.c_uint32):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
	return version == RUNTIME_VERSION_OG_LATEST


class F4SEPluginVersionData(ctypes.Structure):
	_fields_ = [
		# set to kVersion
		("dataVersion", ctypes.c_uint32),
		# version number of your plugin
		("pluginVersion", ctypes.c_uint32),
		# null-terminated ASCII plugin name
		("name", ctypes.c_char * 256),
		# null-terminated ASCII plugin author name (can be empty)
		("author", ctypes.c_char * 256),
		# bitfield. describe how you find your addresses using the kAddressIndependence_ enums
		("addressIndependence", ctypes.c_uint32),
		# bitfield. describe how you handle structure layout using the kStructureIndependence_ enums
		("structureIndependence", ctypes.c_uint32),
		# zero-terminated list of RUNTIME_VERSION_ defines your plugin is compatible with
		("compatibleVersions", ArrayCompatibleVersion),
		# minimum version of the script extender required, compared against PACKED_F4SE_VERSION
		# you probably should just set this to 0 unless you know what you are doing
		("seVersionRequired", ctypes.c_uint32),
		# bitfield. set to 0
		("reservedNonBreaking", ctypes.c_uint32),
		# bitfield. set to 0
		("reservedBreaking", ctypes.c_uint32),
		# set to 0
		("reserved", ctypes.c_uint8 * 512),
	]

	def HasSupportAddressLibraryAE(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(
			F4SEPluginAddressIndependence(self.addressIndependence)
			& F4SEPluginAddressIndependence.kAddressIndependence_AddressLibrary_1_11_137,
		)

	def HasSupportAddressLibraryNG(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(
			F4SEPluginAddressIndependence(self.addressIndependence)
			& F4SEPluginAddressIndependence.kAddressIndependence_AddressLibrary_1_10_980,
		)

	def HasSupportSignatureScanning(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(
			F4SEPluginAddressIndependence(self.addressIndependence)
			& F4SEPluginAddressIndependence.kAddressIndependence_Signatures,
		)

	def HasSupportStructureIndependenceAE(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(
			F4SEPluginStructureIndependence(self.structureIndependence)
			& F4SEPluginStructureIndependence.kStructureIndependence_1_11_137Layout,
		)

	def HasSupportStructureIndependenceNG(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(
			F4SEPluginStructureIndependence(self.structureIndependence)
			& F4SEPluginStructureIndependence.kStructureIndependence_1_10_980Layout,
		)

	def HasSupportNoStructureIndependence(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(
			F4SEPluginStructureIndependence(self.structureIndependence)
			& F4SEPluginStructureIndependence.kStructureIndependence_NoStructs,
		)

	def HasCompatibleCurrentVersion(self, version: ctypes.c_uint32):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		return bool(version in self.compatibleVersions)

	def DeterminateSupportVersion(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		if (self.dataVersion != F4SEPluginVersion.kVersion) or (self.name[0] == b"\x00"):
			return 0

		result = 0
		if self.HasSupportAddressLibraryAE() and self.HasSupportStructureIndependenceAE():
			result |= VersionSupport.kVersionSupportAE
		if self.HasSupportAddressLibraryNG() and self.HasSupportStructureIndependenceNG():
			result |= VersionSupport.kVersionSupportNG

		return result

	def IsSupportVersion(self, version: ctypes.c_uint32) -> bool:  # ruff: ignore[invalid-function-name]
		if (self.dataVersion != F4SEPluginVersion.kVersion) or (self.name[0] == b"\x00"):
			return False

		# TODO: check for 'known bad' versions of plugins

		hasAddressIndependence = False  # ruff: ignore[non-lowercase-variable-in-function]
		hasStructureIndependence = False  # ruff: ignore[non-lowercase-variable-in-function]

		if F4SEPlugin_IsAE(version):
			hasAddressIndependence = self.HasSupportAddressLibraryAE() or self.HasSupportSignatureScanning()  # ruff: ignore[non-lowercase-variable-in-function]
			hasStructureIndependence = self.HasSupportStructureIndependenceAE() or self.HasSupportNoStructureIndependence()  # ruff: ignore[non-lowercase-variable-in-function]
			# print("AE ", hasAddressIndependence, hasStructureIndependence)
		elif F4SEPlugin_IsNG(version):
			hasAddressIndependence = self.HasSupportAddressLibraryNG() or self.HasSupportSignatureScanning()  # ruff: ignore[non-lowercase-variable-in-function]
			hasStructureIndependence = self.HasSupportStructureIndependenceNG() or self.HasSupportNoStructureIndependence()  # ruff: ignore[non-lowercase-variable-in-function]
			# print("NG", hasAddressIndependence, hasStructureIndependence)

		hasVersionIndependent = hasAddressIndependence and hasStructureIndependence  # ruff: ignore[non-lowercase-variable-in-function]

		# currently anything in the "breaking change" field means that compatibility has been broken by an update
		if self.reservedBreaking > 0:
			hasVersionIndependent = False  # ruff: ignore[non-lowercase-variable-in-function]

		# check al exist lol

		# simple version list
		return not (not hasVersionIndependent and not self.HasCompatibleCurrentVersion(version))

	def IsSupportVersionNG(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		# evildarkarchon: fixed more pythonic
		return any(self.IsSupportVersion(n) for n in (RUNTIME_VERSION_1_10_980, RUNTIME_VERSION_1_10_984))

	def IsSupportVersionAE(self):  # ruff: ignore[invalid-function-name, missing-return-type-undocumented-public-function]
		# evildarkarchon: fixed more pythonic
		return any(
			self.IsSupportVersion(n)
			for n in (
				RUNTIME_VERSION_1_11_137,
				RUNTIME_VERSION_1_11_159,
				RUNTIME_VERSION_1_11_169,
				RUNTIME_VERSION_1_11_191,
				RUNTIME_VERSION_1_11_221,
				RUNTIME_VERSION_1_11_240,
			)
		)


## version requirement for this def is cursed as fuck
# def parse_dll(file_path: Path, version: ctypes.c_uint32) -> DLLInfo:
def parse_dll(file_path: Path, version: ctypes.c_uint32) -> DLLInfo:
	dll = ctypes.WinDLL(str(file_path), winmode=DONT_RESOLVE_DLL_REFERENCES)
	dll_info: DLLInfo = {
		"IsF4SE": hasattr(dll, "F4SEPlugin_Load") or hasattr(dll, "F4SEPlugin_Preload"),
		"SupportsOG": hasattr(dll, "F4SEPlugin_Query"),
		"SupportsNGAE": hasattr(dll, "F4SEPlugin_Version"),
		"SupportsNG": None,
		"SupportsAE": None,
		"AddrIndependentNG": None,
		"AddrIndependentAE": None,
		"StructIndependentNG": None,
		"StructIndependentAE": None,
		"SupportsCurrent": None,
	}

	if dll_info["SupportsNGAE"]:
		# Get info about plugin from dll
		v = ctypes.cast(
			dll.F4SEPlugin_Version,
			ctypes.POINTER(F4SEPluginVersionData),
		).contents

		logger.debug("name: %s", v.name)
		logger.debug("addressIndependence: %s", v.addressIndependence)
		logger.debug("structureIndependence: %s", v.structureIndependence)

		# checks NG supports
		dll_info["AddrIndependentNG"] = v.HasSupportAddressLibraryNG() or v.HasSupportSignatureScanning()
		dll_info["StructIndependentNG"] = v.HasSupportStructureIndependenceNG() or v.HasSupportNoStructureIndependence()

		if dll_info["AddrIndependentNG"] and dll_info["StructIndependentNG"]:
			# If it uses Address Library or signatures
			dll_info["SupportsNG"] = True
		else:
			# Check known NG versions
			dll_info["SupportsNG"] = v.IsSupportVersionNG()

		dll_info["AddrIndependentAE"] = v.HasSupportAddressLibraryAE() or v.HasSupportSignatureScanning()
		dll_info["StructIndependentAE"] = v.HasSupportStructureIndependenceAE() or v.HasSupportNoStructureIndependence()

		if dll_info["AddrIndependentAE"] and dll_info["StructIndependentAE"]:
			# If it uses Address Library or signatures
			dll_info["SupportsAE"] = True
		else:
			# Check known NG versions
			dll_info["SupportsAE"] = v.IsSupportVersionAE()

		logger.debug("SupportsNG: %s", dll_info["SupportsNG"])
		logger.debug("SupportsAE: %s", dll_info["SupportsAE"])

		# this section of the code is cursed
		dll_info["SupportsCurrent"] = v.IsSupportVersion(version)
		logger.debug("SupportsCurrent: %s", dll_info["SupportsCurrent"])
	return dll_info


# Output debug info plugin from dll
# Sets P71_DEBUG_F4SE_LIBRARY as 0 - disabled | 1 - enabled
# if P71_DEBUG_F4SE_LIBRARY:

# 	def PrintDebug(file_path: Path, version: ctypes.c_uint32):
# 		test = PluginDllInfo(file_path, version)
# 		print("file_path: ", "".rjust(19), file_path)
# 		print(f"IsF4SE: {test.IsF4SE:>25}")
# 		print(f"SupportsOG: {test.SupportsOG:>21}")
# 		print(f"SupportsNGAE: {test.SupportsNGAE:>19}")
# 		print(f"SupportsNG: {test.SupportsNG:>21}")
# 		print(f"SupportsAE: {test.SupportsAE:>21}")
# 		print(f"AddrIndependentNG: {test.AddrIndependentNG:>14}")
# 		print(f"StructIndependentNG: {test.StructIndependentNG:>12}")
# 		print(f"AddrIndependentAE: {test.AddrIndependentAE:>14}")
# 		print(f"StructIndependentAE: {test.StructIndependentAE:>12}")
# 		print(f"SupportsCurrent: {test.SupportsCurrent:>16}")

# 	PrintDebug("G:/SteamLibrary/steamapps/common/Fallout 4/Data/f4se/plugins/HighFPSPhysicsFix.dll", RUNTIME_VERSION_1_11_221)
