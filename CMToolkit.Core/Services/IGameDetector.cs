using CMToolkit.Core.Models;

namespace CMToolkit.Core.Services;

public sealed class GameDetectionResult
{
    public bool Found { get; init; }

    public string? GamePath { get; init; }

    public string? Error { get; init; }

    public GameSession? Session { get; init; }
}

public interface IGameDetector
{
    Task<GameDetectionResult> DetectAsync(CancellationToken cancellationToken = default);
}
