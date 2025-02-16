import io
from enum import IntEnum, IntFlag
from pathlib import Path

from enums import Magic
from utils import read_uint

DDS_HEADER_SIZE = 124


# Direct Draw Pixel Format
class DDPF(IntFlag):
    ALPHAPIXELS = 0x1
    ALPHA = 0x2
    FOURCC = 0x4
    PALETTEINDEXED8 = 0x20
    RGB = 0x40
    LUMINANCE = 0x20000


# dxgiformat.h
class DXGIFormat(IntEnum):
    UNKNOWN = 0
    R32G32B32A32_TYPELESS = 1
    R32G32B32A32_FLOAT = 2
    R32G32B32A32_UINT = 3
    R32G32B32A32_SINT = 4
    R32G32B32_TYPELESS = 5
    R32G32B32_FLOAT = 6
    R32G32B32_UINT = 7
    R32G32B32_SINT = 8
    R16G16B16A16_TYPELESS = 9
    R16G16B16A16_FLOAT = 10
    R16G16B16A16_UNORM = 11
    R16G16B16A16_UINT = 12
    R16G16B16A16_SNORM = 13
    R16G16B16A16_SINT = 14
    R32G32_TYPELESS = 15
    R32G32_FLOAT = 16
    R32G32_UINT = 17
    R32G32_SINT = 18
    R32G8X24_TYPELESS = 19
    D32_FLOAT_S8X24_UINT = 20
    R32_FLOAT_X8X24_TYPELESS = 21
    X32_TYPELESS_G8X24_UINT = 22
    R10G10B10A2_TYPELESS = 23
    R10G10B10A2_UNORM = 24
    R10G10B10A2_UINT = 25
    R11G11B10_FLOAT = 26
    R8G8B8A8_TYPELESS = 27
    R8G8B8A8_UNORM = 28
    R8G8B8A8_UNORM_SRGB = 29
    R8G8B8A8_UINT = 30
    R8G8B8A8_SNORM = 31
    R8G8B8A8_SINT = 32
    R16G16_TYPELESS = 33
    R16G16_FLOAT = 34
    R16G16_UNORM = 35
    R16G16_UINT = 36
    R16G16_SNORM = 37
    R16G16_SINT = 38
    R32_TYPELESS = 39
    D32_FLOAT = 40
    R32_FLOAT = 41
    R32_UINT = 42
    R32_SINT = 43
    R24G8_TYPELESS = 44
    D24_UNORM_S8_UINT = 45
    R24_UNORM_X8_TYPELESS = 46
    X24_TYPELESS_G8_UINT = 47
    R8G8_TYPELESS = 48
    R8G8_UNORM = 49
    R8G8_UINT = 50
    R8G8_SNORM = 51
    R8G8_SINT = 52
    R16_TYPELESS = 53
    R16_FLOAT = 54
    D16_UNORM = 55
    R16_UNORM = 56
    R16_UINT = 57
    R16_SNORM = 58
    R16_SINT = 59
    R8_TYPELESS = 60
    R8_UNORM = 61
    R8_UINT = 62
    R8_SNORM = 63
    R8_SINT = 64
    A8_UNORM = 65
    R1_UNORM = 66
    R9G9B9E5_SHAREDEXP = 67
    R8G8_B8G8_UNORM = 68
    G8R8_G8B8_UNORM = 69
    BC1_TYPELESS = 70
    BC1_UNORM = 71
    BC1_UNORM_SRGB = 72
    BC2_TYPELESS = 73
    BC2_UNORM = 74
    BC2_UNORM_SRGB = 75
    BC3_TYPELESS = 76
    BC3_UNORM = 77
    BC3_UNORM_SRGB = 78
    BC4_TYPELESS = 79
    BC4_UNORM = 80
    BC4_SNORM = 81
    BC5_TYPELESS = 82
    BC5_UNORM = 83
    BC5_SNORM = 84
    B5G6R5_UNORM = 85
    B5G5R5A1_UNORM = 86
    B8G8R8A8_UNORM = 87
    B8G8R8X8_UNORM = 88
    R10G10B10_XR_BIAS_A2_UNORM = 89
    B8G8R8A8_TYPELESS = 90
    B8G8R8A8_UNORM_SRGB = 91
    B8G8R8X8_TYPELESS = 92
    B8G8R8X8_UNORM_SRGB = 93
    BC6H_TYPELESS = 94
    BC6H_UF16 = 95
    BC6H_SF16 = 96
    BC7_TYPELESS = 97
    BC7_UNORM = 98
    BC7_UNORM_SRGB = 99
    AYUV = 100
    Y410 = 101
    Y416 = 102
    NV12 = 103
    P010 = 104
    P016 = 105
    OPAQUE_420 = 106
    YUY2 = 107
    Y210 = 108
    Y216 = 109
    NV11 = 110
    AI44 = 111
    IA44 = 112
    P8 = 113
    A8P8 = 114
    B4G4R4A4_UNORM = 115
    P208 = 130
    V208 = 131
    V408 = 132
    SAMPLER_FEEDBACK_MIN_MIP_OPAQUE = 189
    SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE = 190


class D3DFMT(IntEnum):
    UNKNOWN = 0
    R8G8B8 = 20
    A8R8G8B8 = 21
    X8R8G8B8 = 22
    R5G6B5 = 23
    X1R5G5B5 = 24
    A1R5G5B5 = 25
    A4R4G4B4 = 26
    R3G3B2 = 27
    A8 = 28
    A8R3G3B2 = 29
    X4R4G4B4 = 30
    A2B10G10R10 = 31
    A8B8G8R8 = 32
    X8B8G8R8 = 33
    G16R16 = 34
    A2R10G10B10 = 35
    A16B16G16R16 = 36
    A8P8 = 40
    P8 = 41
    L8 = 50
    A8L8 = 51
    A4L4 = 52
    V8U8 = 60
    L6V5U5 = 61
    X8L8V8U8 = 62
    Q8W8V8U8 = 63
    V16U16 = 64
    A2W10V10U10 = 67
    D16_LOCKABLE = 70
    D32 = 71
    D15S1 = 73
    D24S8 = 75
    D24X8 = 77
    D24X4S4 = 79
    D16 = 80
    D32F_LOCKABLE = 82
    D24FS8 = 83
    D32_LOCKABLE = 84
    S8_LOCKABLE = 85
    L16 = 81
    VERTEXDATA = 100
    INDEX16 = 101
    INDEX32 = 102
    Q16W16V16U16 = 110
    R16F = 111
    G16R16F = 112
    A16B16G16R16F = 113
    R32F = 114
    G32R32F = 115
    A32B32G32R32F = 116
    CxV8U8 = 117
    A1 = 118
    UYVY = 1498831189
    R8G8_B8G8 = 1195525970  # RGBG
    YUY2 = 844715353
    G8R8_G8B8 = 1111970375  # GRGB
    DXT1 = 827611204
    DXT2 = 844388420
    DXT3 = 861165636
    DXT4 = 877942852
    DXT5 = 894720068
    DX10 = 808540228
    BC4S = 1395934018
    BC4U = 1429488450
    BC5S = 1395999554
    BC5U = 1429553986
    ATI1 = 826889281
    ATI2 = 843666497
    MULTI2_ARGB8 = 827606349  # MET1


DDS_HEADER_SIZE = 124

class DDSInfo:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_name = file_path.name

        with file_path.open("rb") as fp:
            if fp.read(4) != Magic.DDS:
                msg = "not a DDS file"
                raise SyntaxError(msg)

            header_size = read_uint(fp)
            if header_size != DDS_HEADER_SIZE:
                msg = f"Unsupported header size {header_size}"
                raise OSError(msg)

            header_bytes = fp.read(DDS_HEADER_SIZE - 4)
            if len(header_bytes) != DDS_HEADER_SIZE - 4:
                msg = f"Incomplete header: {len(header_bytes)} bytes"
                raise OSError(msg)

            header = io.BytesIO(header_bytes)

            # Skip Flags ([1:])
            self._size: tuple[int, int] = read_uint(header, 3)[1:]  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]
            _ = read_uint(header, 3)  # pitch, depth, mipmaps
            _ = read_uint(header, 11)  # reserved

            # Pixel Format
            _, pfflags, fourcc, bitcount = read_uint(header, 4)
            if pfflags & DDPF.RGB:
                # Texture contains uncompressed RGB data
                if pfflags & DDPF.ALPHAPIXELS:
                    self.mode = "RGBA"
                    # mask_count = 4
                else:
                    self.mode = "RGB"
                    # mask_count = 3

                # masks = struct.unpack(f"<{mask_count}I", header.read(mask_count * 4))
                return

            if pfflags & DDPF.LUMINANCE:
                if bitcount == 8:  # noqa: PLR2004
                    self.mode = "L"
                elif bitcount == 16 and pfflags & DDPF.ALPHAPIXELS:  # noqa: PLR2004
                    self.mode = "LA"
                else:
                    msg = f"Unsupported bitcount {bitcount} for {pfflags}"
                    raise OSError(msg)

            elif pfflags & DDPF.PALETTEINDEXED8:
                self.mode = "P"
            elif pfflags & DDPF.FOURCC:
                match fourcc:
                    case D3DFMT.DXT1:
                        self.mode = "RGBA"
                        self.pixel_format = "DXT1"
                    case D3DFMT.DXT3:
                        self.mode = "RGBA"
                        self.pixel_format = "DXT3"
                    case D3DFMT.DXT5:
                        self.mode = "RGBA"
                        self.pixel_format = "DXT5"
                    case D3DFMT.BC4U | D3DFMT.ATI1:
                        self.mode = "L"
                        self.pixel_format = "BC4"
                    case D3DFMT.BC5S:
                        self.mode = "RGB"
                        self.pixel_format = "BC5S"
                    case D3DFMT.BC5U | D3DFMT.ATI2:
                        self.mode = "RGB"
                        self.pixel_format = "BC5"
                    case D3DFMT.DX10:
                        dxgi_format = read_uint(fp)
                        # ignoring flags which pertain to volume textures and cubemaps
                        # fp.read(16)
                        match dxgi_format:
                            case DXGIFormat.BC1_UNORM | DXGIFormat.BC1_TYPELESS:
                                self.mode = "RGBA"
                                self.pixel_format = "BC1"
                            case DXGIFormat.BC4_TYPELESS | DXGIFormat.BC4_UNORM:
                                self.mode = "L"
                                self.pixel_format = "BC4"
                            case DXGIFormat.BC5_TYPELESS | DXGIFormat.BC5_UNORM:
                                self.mode = "RGB"
                                self.pixel_format = "BC5"
                            case DXGIFormat.BC5_SNORM:
                                self.mode = "RGB"
                                self.pixel_format = "BC5S"
                            case DXGIFormat.BC6H_UF16:
                                self.mode = "RGB"
                                self.pixel_format = "BC6H"
                            case DXGIFormat.BC6H_SF16:
                                self.mode = "RGB"
                                self.pixel_format = "BC6HS"
                            case DXGIFormat.BC7_TYPELESS | DXGIFormat.BC7_UNORM | DXGIFormat.BC7_UNORM_SRGB:
                                self.mode = "RGBA"
                                self.pixel_format = "BC7"
                                # if dxgi_format == DXGIFormat.BC7_UNORM_SRGB:
                                # 	self.info["gamma"] = 1 / 2.2
                            case (
                                DXGIFormat.R8G8B8A8_TYPELESS
                                | DXGIFormat.R8G8B8A8_UNORM
                                | DXGIFormat.R8G8B8A8_UNORM_SRGB
                            ):
                                self.mode = "RGBA"
                                # if dxgi_format == DXGIFormat.R8G8B8A8_UNORM_SRGB:
                                # 	self.info["gamma"] = 1 / 2.2
                            case _:
                                msg = f"Unimplemented DXGI format {dxgi_format}"
                                raise NotImplementedError(msg)
                    case _:
                        msg = f"Unimplemented pixel format {fourcc}"
                        raise NotImplementedError(msg)
            else:
                msg = f"Unknown pixel format flags {pfflags}"
                raise NotImplementedError(msg)

    @property
    def width(self) -> int:
        return self._size[0]

    @property
    def height(self) -> int:
        return self._size[1]

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def is_npot(self) -> bool:
        return any(not (n & n - 1 == 0 and n != 0) for n in self._size)
