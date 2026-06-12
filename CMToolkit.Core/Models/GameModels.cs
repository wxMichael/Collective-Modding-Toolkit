using CMToolkit.Core.Enums;

namespace CMToolkit.Core.Models;

public sealed class GameIniData
{
    public Dictionary<string, Dictionary<string, string>> GameSettings { get; init; } =
        new(StringComparer.OrdinalIgnoreCase);

    public Dictionary<string, Dictionary<string, string>> GamePrefs { get; init; } =
        new(StringComparer.OrdinalIgnoreCase);

    public Language Language { get; init; } = Language.English;

    public IReadOnlyList<string> Ba2Suffixes { get; init; } = ["main", "textures", "voices_en"];
}

public sealed class GameSession
{
    public required string GamePath { get; init; }

    public string? DataPath { get; init; }

    public string? F4sePath { get; init; }

    public InstallType InstallType { get; set; } = InstallType.Unknown;

    public ModManagerInfo? ModManager { get; init; }

    public GameIniData IniData { get; init; } = new();
}
