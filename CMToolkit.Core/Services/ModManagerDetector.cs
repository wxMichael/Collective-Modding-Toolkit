using CMToolkit.Core.Models;
using CMToolkit.Core.Parsing;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Services;

public sealed class ModManagerDetector(
    IProcessWalker processWalker,
    IPeVersionReader versionReader,
    IRegistryReader registryReader,
    IPathService pathService) : IModManagerDetector
{
    private readonly IProcessWalker _processWalker = processWalker;
    private readonly IPeVersionReader _versionReader = versionReader;
    private readonly IRegistryReader _registryReader = registryReader;
    private readonly IPathService _pathService = pathService;

    public async Task<ModManagerDetectionResult> DetectAsync(CancellationToken cancellationToken = default)
    {
        foreach (var process in _processWalker.GetParentProcesses(8))
        {
            var name = NormalizeProcessName(process.Name);
            if (name is not ("ModOrganizer.exe" or "Vortex.exe"))
            {
                continue;
            }

            var displayName = name == "ModOrganizer.exe" ? "Mod Organizer" : "Vortex";
            var exePath = process.ExecutablePath ?? string.Empty;
            var modManager = new ModManagerInfo
            {
                Name = displayName,
                ExePath = exePath,
                Version = NormalizeVersion(_versionReader.GetVersion(exePath)),
            };

            if (displayName == "Mod Organizer")
            {
                await PopulateMo2SettingsAsync(modManager, cancellationToken);
            }

            return new ModManagerDetectionResult
            {
                Found = true,
                Name = modManager.Name,
                Version = modManager.Version,
                Profile = modManager.SelectedProfile,
                ModManager = modManager,
            };
        }

        return new ModManagerDetectionResult { Found = false };
    }

    private async Task PopulateMo2SettingsAsync(ModManagerInfo modManager, CancellationToken cancellationToken)
    {
        var exeDir = Path.GetDirectoryName(modManager.ExePath) ?? _pathService.CurrentDirectory;
        var portableIniPath = Path.Combine(exeDir, "ModOrganizer.ini");
        var portableTxtPath = Path.Combine(exeDir, "portable.txt");
        var portableIniExists = _pathService.FileExists(portableIniPath);

        if (_pathService.FileExists(portableTxtPath))
        {
            if (!portableIniExists)
            {
                throw new FileNotFoundException("portable.txt found but no ModOrganizer.ini found in MO2 install path", portableIniPath);
            }

            CopyMo2Settings(modManager, await Mo2IniParser.ParseAsync(portableIniPath, cancellationToken));
            modManager.Portable = true;
            modManager.PortableTextPath = portableTxtPath;
            return;
        }

        var currentInstance = _registryReader.GetValue(
            RegistryRoot.CurrentUser,
            @"Software\Mod Organizer Team\Mod Organizer",
            "CurrentInstance");

        if (!string.IsNullOrWhiteSpace(currentInstance))
        {
            var appDataIniPath = Path.Combine(_pathService.LocalApplicationData, "ModOrganizer", currentInstance, "ModOrganizer.ini");
            if (_pathService.FileExists(appDataIniPath))
            {
                CopyMo2Settings(modManager, await Mo2IniParser.ParseAsync(appDataIniPath, cancellationToken));
            }
        }

        if (modManager.GamePath is not null)
        {
            return;
        }

        if (!portableIniExists)
        {
            throw new FileNotFoundException("Unable to find ModOrganizer.ini. Please report this along with your MO2 instance details.", portableIniPath);
        }

        CopyMo2Settings(modManager, await Mo2IniParser.ParseAsync(portableIniPath, cancellationToken));
    }

    private static void CopyMo2Settings(ModManagerInfo target, ModManagerInfo source)
    {
        target.IniPath = source.IniPath;
        target.GamePath = source.GamePath;
        target.StagePath = source.StagePath;
        target.OverwritePath = source.OverwritePath;
        target.ProfilesPath = source.ProfilesPath;
        target.SelectedProfile = source.SelectedProfile;
        target.SkipFileSuffixes = source.SkipFileSuffixes;
        target.SkipDirectories = source.SkipDirectories;

        foreach (var (key, values) in source.Executables)
        {
            target.Executables[key] = values;
        }

        foreach (var (key, value) in source.SettingsDump)
        {
            target.SettingsDump[key] = value;
        }
    }

    private static string NormalizeProcessName(string processName) =>
        processName.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)
            ? processName
            : processName + ".exe";

    private static string NormalizeVersion(string? version)
    {
        if (string.IsNullOrWhiteSpace(version))
        {
            return "0.0.0";
        }

        var parts = version.Split('.', StringSplitOptions.RemoveEmptyEntries);
        return string.Join('.', parts.Take(3));
    }
}
