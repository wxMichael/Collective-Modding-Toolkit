namespace CMToolkit.Core.Services;

public interface IAppState
{
    bool IsProcessingData { get; set; }
}

public sealed class AppState : IAppState
{
    public bool IsProcessingData { get; set; }
}
