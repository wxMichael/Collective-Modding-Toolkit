using CMToolkit.Core.Enums;

namespace CMToolkit.Core.Models;

public sealed record BinaryFileInfo(
    string Name,
    string? Path,
    string? Version,
    string? Hash,
    InstallType InstallType);

public sealed class ArchiveCensus
{
    public int GeneralCount { get; set; }

    public int TextureCount { get; set; }

    public HashSet<string> OldGenArchives { get; } = new(StringComparer.OrdinalIgnoreCase);

    public HashSet<string> NextGenArchives { get; } = new(StringComparer.OrdinalIgnoreCase);

    public HashSet<string> EnabledArchives { get; } = new(StringComparer.OrdinalIgnoreCase);

    public HashSet<string> UnreadableArchives { get; } = new(StringComparer.OrdinalIgnoreCase);
}

public sealed class ModuleCensus
{
    public int FullCount { get; set; }

    public int LightCount { get; set; }

    public int HedrVersion100Count { get; set; }

    public List<string> EnabledModules { get; } = [];

    public HashSet<string> UnreadableModules { get; } = new(StringComparer.OrdinalIgnoreCase);

    public HashSet<string> HedrVersion095Modules { get; } = new(StringComparer.OrdinalIgnoreCase);

    public Dictionary<string, float> UnknownHedrModules { get; } = new(StringComparer.OrdinalIgnoreCase);
}

public sealed record OverviewProblem(
    ProblemType Type,
    string Title,
    string Summary,
    string? Path = null,
    string? RelativePath = null,
    string? Solution = null,
    string? Mod = null,
    IReadOnlyList<string>? ExtraData = null);

public sealed class OverviewCensusResult
{
    public Dictionary<string, BinaryFileInfo> Binaries { get; } = new(StringComparer.OrdinalIgnoreCase);

    public string? AddressLibraryPath { get; set; }

    public ArchiveCensus Archives { get; } = new();

    public ModuleCensus Modules { get; } = new();

    public List<OverviewProblem> Problems { get; } = [];
}
