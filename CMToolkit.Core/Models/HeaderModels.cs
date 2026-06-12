using CMToolkit.Core.Enums;

namespace CMToolkit.Core.Models;

public sealed record Ba2Header(
    ArchiveVersion? Version,
    ArchiveFormat Format,
    bool IsUnreadable,
    string? Error = null);

public sealed record ModuleHeader(
    ModuleHedrVersion HedrVersion,
    float? UnknownHedrValue,
    bool IsLight,
    bool IsUnreadable,
    string? Error = null);
