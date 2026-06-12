using System.Text;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;

namespace CMToolkit.Core.Utilities;

public static class Ba2HeaderParser
{
    public static Ba2Header Parse(ReadOnlySpan<byte> header)
    {
        if (header.Length < 12 || !header[..4].SequenceEqual("BTDX"u8))
        {
            return new Ba2Header(null, ArchiveFormat.Unknown, true, "Archive is either corrupt or not in Bethesda Archive 2 format.");
        }

        ArchiveVersion? version = header[4] switch
        {
            1 => ArchiveVersion.OG,
            7 => ArchiveVersion.NG7,
            8 => ArchiveVersion.NG,
            _ => null,
        };

        if (version is null)
        {
            return new Ba2Header(null, ArchiveFormat.Unknown, true, $"Archive version ({header[4]}) is not valid for Fallout 4.");
        }

        var formatBytes = header[8..12];
        var format = formatBytes.SequenceEqual("GNRL"u8)
            ? ArchiveFormat.GNRL
            : formatBytes.SequenceEqual("DX10"u8)
                ? ArchiveFormat.DX10
                : ArchiveFormat.Unknown;

        if (format == ArchiveFormat.Unknown)
        {
            return new Ba2Header(version, format, true, $"Archive format ({Encoding.ASCII.GetString(formatBytes)}) is not valid for Fallout 4.");
        }

        return new Ba2Header(version, format, false);
    }
}
