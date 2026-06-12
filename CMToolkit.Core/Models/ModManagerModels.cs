namespace CMToolkit.Core.Models;

public sealed class ModManagerInfo
{
    public required string Name { get; init; }

    public required string ExePath { get; init; }

    public string Version { get; init; } = "0.0.0";

    public string? IniPath { get; set; }

    public string? PortableTextPath { get; set; }

    public bool Portable { get; set; }

    public string? GamePath { get; set; }

    public string? StagePath { get; set; }

    public string? OverwritePath { get; set; }

    public string? ProfilesPath { get; set; }

    public string? SelectedProfile { get; set; }

    public IReadOnlyList<string> SkipFileSuffixes { get; set; } = [".mohidden"];

    public IReadOnlyList<string> SkipDirectories { get; set; } = [];

    public Dictionary<string, HashSet<string>> Executables { get; } = new(StringComparer.OrdinalIgnoreCase);

    public Dictionary<string, object?> SettingsDump { get; } = new(StringComparer.Ordinal);
}
