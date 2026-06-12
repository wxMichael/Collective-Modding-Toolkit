using CMToolkit.Core.Constants;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;

namespace CMToolkit.Core.Utilities;

public static class ModuleHeaderParser
{
    public static ModuleHeader Parse(ReadOnlySpan<byte> header)
    {
        if (header.Length < 34 || !header[..4].SequenceEqual("TES4"u8))
        {
            return new ModuleHeader(ModuleHedrVersion.Unknown, null, false, true, "Module is either corrupt or not in TES4 format.");
        }

        if (!header.Slice(24, 4).SequenceEqual("HEDR"u8))
        {
            return new ModuleHeader(ModuleHedrVersion.Unknown, null, false, true, "Module HEDR field was not found.");
        }

        var hedrBytes = header.Slice(30, 4);
        var hedrVersion = ModuleHedrVersion.Unknown;
        float? unknownHedrValue = null;

        if (hedrBytes.SequenceEqual(VersionTables.ModuleVersion95))
        {
            hedrVersion = ModuleHedrVersion.Version095;
        }
        else if (hedrBytes.SequenceEqual(VersionTables.ModuleVersion1))
        {
            hedrVersion = ModuleHedrVersion.Version100;
        }
        else
        {
            unknownHedrValue = MathF.Round(BitConverter.ToSingle(hedrBytes), 2);
        }

        var flags = BitConverter.ToUInt32(header.Slice(8, 4));
        return new ModuleHeader(hedrVersion, unknownHedrValue, (flags & (uint)ModuleFlag.Light) != 0, false);
    }
}
