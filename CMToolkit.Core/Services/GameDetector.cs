using CMToolkit.Core.Models;
using CMToolkit.Core.Utilities;
namespace CMToolkit.Core.Services;

public sealed class GameDetector(
    IModManagerDetector modManagerDetector,
    IRegistryReader registryReader,
    IPathService pathService,
    IGamePathPrompt gamePathPrompt,
    GameIniLoader iniLoader) : IGameDetector
{
    private readonly IModManagerDetector _modManagerDetector = modManagerDetector;
    private readonly IRegistryReader _registryReader = registryReader;
    private readonly IPathService _pathService = pathService;
    private readonly IGamePathPrompt _gamePathPrompt = gamePathPrompt;
    private readonly GameIniLoader _iniLoader = iniLoader;

    public async Task<GameDetectionResult> DetectAsync(CancellationToken cancellationToken = default)
    {
        var modManager = (await _modManagerDetector.DetectAsync(cancellationToken)).ModManager;

        var gamePath = modManager?.Name == "Mod Organizer" && !string.IsNullOrWhiteSpace(modManager.GamePath)
            ? modManager.GamePath
            : null;

        gamePath ??= PathHelper.IsFallout4Directory(_pathService.CurrentDirectory)
            ? _pathService.CurrentDirectory
            : null;

        var registryPath = GetRegistryGamePath();
        gamePath ??= registryPath;

        if (string.IsNullOrWhiteSpace(gamePath) &&
            await _gamePathPrompt.ConfirmManualSelectionAsync(cancellationToken))
        {
            gamePath = await _gamePathPrompt.PickFallout4ExeAsync(cancellationToken);
        }

        if (string.IsNullOrWhiteSpace(gamePath))
        {
            return new GameDetectionResult { Found = false, Error = "A Fallout 4 installation could not be found." };
        }

        if (_pathService.FileExists(gamePath))
        {
            gamePath = Path.GetDirectoryName(gamePath) ?? string.Empty;
        }

        if (string.IsNullOrWhiteSpace(gamePath) || !_pathService.FileExists(Path.Combine(gamePath, "Fallout4.exe")))
        {
            var error = registryPath is not null
                ? $"A Fallout 4 installation could not be found. The path set in your registry is: {registryPath}"
                : "A Fallout 4 installation could not be found.";
            return new GameDetectionResult { Found = false, Error = error };
        }

        var dataPath = Path.Combine(gamePath, "Data");
        var f4sePath = Path.Combine(dataPath, "F4SE", "Plugins");
        var iniData = await _iniLoader.LoadAsync(cancellationToken);
        var session = new GameSession
        {
            GamePath = gamePath,
            DataPath = _pathService.DirectoryExists(dataPath) ? dataPath : null,
            F4sePath = _pathService.DirectoryExists(f4sePath) ? f4sePath : null,
            ModManager = modManager,
            IniData = iniData,
        };

        return new GameDetectionResult
        {
            Found = true,
            GamePath = gamePath,
            Session = session,
        };
    }

    private string? GetRegistryGamePath() =>
        _registryReader.GetValue(
            RegistryRoot.LocalMachine,
            @"SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4",
            "Installed Path")
        ?? _registryReader.GetValue(
            RegistryRoot.LocalMachine,
            @"SOFTWARE\WOW6432Node\GOG.com\Games\1998527297",
            "path");
}
