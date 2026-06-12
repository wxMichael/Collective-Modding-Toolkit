using CMToolkit.Core.Models;

namespace CMToolkit.Core.Services;

public sealed class ModManagerDetectionResult
{
    public bool Found { get; init; }

    public string? Name { get; init; }

    public string? Version { get; init; }

    public string? Profile { get; init; }

    public ModManagerInfo? ModManager { get; init; }
}

public interface IModManagerDetector
{
    Task<ModManagerDetectionResult> DetectAsync(CancellationToken cancellationToken = default);
}
