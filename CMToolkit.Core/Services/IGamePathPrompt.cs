namespace CMToolkit.Core.Services;

public interface IGamePathPrompt
{
    Task<bool> ConfirmManualSelectionAsync(CancellationToken cancellationToken = default);

    Task<string?> PickFallout4ExeAsync(CancellationToken cancellationToken = default);
}

public sealed class NullGamePathPrompt : IGamePathPrompt
{
    public Task<bool> ConfirmManualSelectionAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult(false);

    public Task<string?> PickFallout4ExeAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult<string?>(null);
}
