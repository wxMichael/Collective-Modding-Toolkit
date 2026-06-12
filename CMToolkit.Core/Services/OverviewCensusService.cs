using CMToolkit.Core.Constants;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Services;

public sealed class OverviewCensusService(IPeVersionReader versionReader, IPathService pathService)
{
    private readonly IPeVersionReader _versionReader = versionReader;
    private readonly IPathService _pathService = pathService;

    public async Task<OverviewCensusResult> RefreshAsync(
        GameSession session,
        CancellationToken cancellationToken = default)
    {
        var result = new OverviewCensusResult();

        if (session.ModManager is null)
        {
            result.Problems.Add(new OverviewProblem(
                ProblemType.NoModManager,
                "No Mod Manager",
                "No Mod Manager Detected",
                Solution: "Launch this app with your mod manager."));
        }

        await GatherBinariesAsync(session, result, cancellationToken);
        await GatherModulesAsync(session, result, cancellationToken);
        await GatherArchivesAsync(session, result, cancellationToken);

        AddLimitProblems(result);
        return result;
    }

    private async Task GatherBinariesAsync(
        GameSession session,
        OverviewCensusResult result,
        CancellationToken cancellationToken)
    {
        foreach (var tableEntry in VersionTables.BaseFiles)
        {
            var relativeFileName = tableEntry.Key;
            var fileName = Path.GetFileName(relativeFileName);
            var path = Path.Combine(session.GamePath, relativeFileName);
            var info = await GetBinaryInfoAsync(fileName, relativeFileName, path, session.InstallType, cancellationToken);
            result.Binaries[fileName] = info;

            if (fileName.Equals("Fallout4.exe", StringComparison.OrdinalIgnoreCase))
            {
                session.InstallType = info.InstallType;
                if (session.InstallType == InstallType.Unknown)
                {
                    result.Problems.Add(new OverviewProblem(
                        ProblemType.UnknownGameVersion,
                        "Unknown Game Version",
                        $"{info.Version ?? info.Hash} is an unknown version.",
                        Path: path,
                        RelativePath: fileName,
                        Solution: "Either update the game/verify files in Steam, or report this issue."));
                }

                DetectAddressLibrary(session, result, info.Version);
                await DetectDowngradedGameAsync(session, result, cancellationToken);
            }
            else
            {
                AddBinaryProblemIfNeeded(session, result, info, fileName, path);
            }
        }
    }

    private async Task<BinaryFileInfo> GetBinaryInfoAsync(
        string fileName,
        string tableKey,
        string path,
        InstallType currentInstallType,
        CancellationToken cancellationToken)
    {
        if (!_pathService.FileExists(path))
        {
            return new BinaryFileInfo(fileName, null, null, null, InstallType.NotFound);
        }

        var version = _versionReader.GetVersion(path);
        var hash = await Crc32Hasher.ComputeAsync(path, cancellationToken: cancellationToken);
        var installType = version is not null
            ? VersionTables.Classify(tableKey, version)
            : InstallType.Unknown;

        if (installType == InstallType.Unknown)
        {
            installType = VersionTables.Classify(tableKey, hash);
        }

        if (installType == InstallType.NGAE && currentInstallType is InstallType.NG or InstallType.AE)
        {
            installType = currentInstallType;
        }

        return new BinaryFileInfo(fileName, path, version ?? hash, hash, installType);
    }

    private static void DetectAddressLibrary(GameSession session, OverviewCensusResult result, string? falloutVersion)
    {
        if (session.DataPath is null || falloutVersion is null)
        {
            return;
        }

        var relativePath = Path.Combine("F4SE", "Plugins", $"version-{falloutVersion.Replace('.', '-')}.bin");
        var addressLibraryPath = Path.Combine(session.DataPath, relativePath);
        if (File.Exists(addressLibraryPath))
        {
            result.AddressLibraryPath = addressLibraryPath;
        }
        else
        {
            result.Problems.Add(new OverviewProblem(
                ProblemType.FileNotFound,
                "Address Library",
                "Address Library is a requirement for many F4SE mods and playing downgraded, and likely needs to be installed.",
                Path: addressLibraryPath,
                RelativePath: relativePath,
                Solution: "Download the mod here:",
                ExtraData: ["https://www.nexusmods.com/fallout4/mods/47327"]));
        }
    }

    private static async Task DetectDowngradedGameAsync(
        GameSession session,
        OverviewCensusResult result,
        CancellationToken cancellationToken)
    {
        if (session.DataPath is null || session.InstallType != InstallType.OG)
        {
            return;
        }

        var startupBa2 = Path.Combine(session.DataPath, "Fallout4 - Startup.ba2");
        if (!File.Exists(startupBa2))
        {
            result.Problems.Add(new OverviewProblem(
                ProblemType.FileNotFound,
                "Fallout4 - Startup.ba2",
                "This is a base game file, and is used by CM Toolkit to differentiate between Old-Gen and Down-Grade.",
                Path: startupBa2,
                RelativePath: "Fallout4 - Startup.ba2",
                Solution: "Verify files with Steam or reinstall the game."));
            return;
        }

        var crc = await Crc32Hasher.ComputeAsync(startupBa2, skipBa2Header: true, cancellationToken: cancellationToken);
        if (crc == VersionTables.NextGenStartupBa2Crc)
        {
            session.InstallType = InstallType.DG;
        }
    }

    private static void AddBinaryProblemIfNeeded(
        GameSession session,
        OverviewCensusResult result,
        BinaryFileInfo info,
        string fileName,
        string path)
    {
        if (info.InstallType == session.InstallType ||
            info.InstallType == InstallType.OG && session.InstallType == InstallType.DG)
        {
            return;
        }

        if (info.InstallType == InstallType.NotFound)
        {
            if (fileName is "CreationKit.exe" or "Archive2.exe" ||
                session.InstallType is InstallType.NG or InstallType.AE && fileName == "f4se_steam_loader.dll")
            {
                return;
            }

            result.Problems.Add(new OverviewProblem(
                ProblemType.FileNotFound,
                fileName,
                "This file is missing from your game installation.",
                Path: path,
                RelativePath: fileName));
            return;
        }

        result.Problems.Add(new OverviewProblem(
            ProblemType.WrongVersion,
            fileName,
            "The version of this binary does not match your installed game version.",
            Path: path,
            RelativePath: fileName));
    }

    private async Task GatherModulesAsync(
        GameSession session,
        OverviewCensusResult result,
        CancellationToken cancellationToken)
    {
        if (session.DataPath is null)
        {
            result.Problems.Add(new OverviewProblem(
                ProblemType.FileNotFound,
                "Data",
                "The Data folder was not found in your game install path.",
                Solution: "Verify files with Steam or reinstall the game."));
            return;
        }

        var enabled = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var master in VersionTables.GameMasters)
        {
            var path = Path.Combine(session.DataPath, master);
            if (_pathService.FileExists(path))
            {
                enabled.Add(path);
            }
        }

        var cccPath = Path.Combine(session.GamePath, "Fallout4.ccc");
        if (_pathService.FileExists(cccPath))
        {
            foreach (var line in await File.ReadAllLinesAsync(cccPath, cancellationToken))
            {
                var path = Path.Combine(session.DataPath, line.Trim());
                if (_pathService.FileExists(path))
                {
                    enabled.Add(path);
                }
            }
        }
        else
        {
            result.Problems.Add(new OverviewProblem(
                ProblemType.FileNotFound,
                "Fallout4.ccc",
                "The CC list file was not found in your game install path. This is used to detect which CC modules/archives may be enabled.",
                Path: cccPath,
                RelativePath: "Fallout4.ccc",
                Solution: "Verify files with Steam or reinstall the game."));
        }

        var pluginsPath = Path.Combine(_pathService.LocalApplicationData, "Fallout4", "plugins.txt");
        if (_pathService.FileExists(pluginsPath))
        {
            foreach (var line in await File.ReadAllLinesAsync(pluginsPath, cancellationToken))
            {
                if (!line.StartsWith('*'))
                {
                    continue;
                }

                var path = Path.Combine(session.DataPath, line[1..].Trim());
                if (_pathService.FileExists(path))
                {
                    enabled.Add(path);
                }
            }
        }
        else
        {
            result.Problems.Add(new OverviewProblem(
                ProblemType.FileNotFound,
                "plugins.txt",
                "plugins.txt was not found. This is used to detect which modules/archives are enabled.",
                Solution: session.ModManager is null ? "Launch this app with your mod manager." : "N/A"));

            foreach (var modulePath in Directory.EnumerateFiles(session.DataPath)
                         .Where(path => Path.GetExtension(path).Equals(".esp", StringComparison.OrdinalIgnoreCase) ||
                                        Path.GetExtension(path).Equals(".esl", StringComparison.OrdinalIgnoreCase) ||
                                        Path.GetExtension(path).Equals(".esm", StringComparison.OrdinalIgnoreCase)))
            {
                enabled.Add(modulePath);
            }
        }

        foreach (var modulePath in enabled)
        {
            result.Modules.EnabledModules.Add(modulePath);
            await CountModuleAsync(modulePath, result, cancellationToken);
        }
    }

    private static async Task CountModuleAsync(
        string modulePath,
        OverviewCensusResult result,
        CancellationToken cancellationToken)
    {
        byte[] header;
        try
        {
            header = new byte[34];
            await using var stream = File.OpenRead(modulePath);
            var read = await stream.ReadAsync(header.AsMemory(0, header.Length), cancellationToken);
            if (read < 34)
            {
                result.Modules.UnreadableModules.Add(modulePath);
                result.Problems.Add(new OverviewProblem(ProblemType.InvalidModule, Path.GetFileName(modulePath), "Module is either corrupt or not in TES4 format.", Path: modulePath, RelativePath: Path.GetFileName(modulePath), Mod: "OVERVIEW"));
                return;
            }
        }
        catch
        {
            result.Modules.UnreadableModules.Add(modulePath);
            result.Problems.Add(new OverviewProblem(ProblemType.InvalidModule, Path.GetFileName(modulePath), "Failed to read module due to permissions or the file is missing.", Path: modulePath, RelativePath: Path.GetFileName(modulePath), Mod: "OVERVIEW"));
            return;
        }

        var parsed = ModuleHeaderParser.Parse(header);
        if (parsed.IsUnreadable)
        {
            result.Modules.UnreadableModules.Add(modulePath);
            result.Problems.Add(new OverviewProblem(ProblemType.InvalidModule, Path.GetFileName(modulePath), parsed.Error ?? "Module is invalid.", Path: modulePath, RelativePath: Path.GetFileName(modulePath), Mod: "OVERVIEW"));
            return;
        }

        if (parsed.HedrVersion == ModuleHedrVersion.Version095)
        {
            result.Modules.HedrVersion095Modules.Add(modulePath);
        }
        else if (parsed.HedrVersion == ModuleHedrVersion.Version100)
        {
            result.Modules.HedrVersion100Count++;
        }
        else if (parsed.UnknownHedrValue is float value)
        {
            result.Modules.UnknownHedrModules[modulePath] = value;
            result.Problems.Add(new OverviewProblem(ProblemType.InvalidModule, Path.GetFileName(modulePath), $"Module version ({value}) is not valid for Fallout 4.", Path: modulePath, RelativePath: Path.GetFileName(modulePath), Mod: "OVERVIEW"));
        }

        if (parsed.IsLight || Path.GetExtension(modulePath).Equals(".esl", StringComparison.OrdinalIgnoreCase))
        {
            result.Modules.LightCount++;
        }
        else
        {
            result.Modules.FullCount++;
        }
    }

    private async Task GatherArchivesAsync(
        GameSession session,
        OverviewCensusResult result,
        CancellationToken cancellationToken)
    {
        if (session.DataPath is null)
        {
            return;
        }

        if (!session.IniData.GameSettings.TryGetValue("archive", out var archiveSettings))
        {
            throw new InvalidDataException("Archive section missing from INIs");
        }

        foreach (var key in new[] { "sresourceindexfilelist", "sresourcestartuparchivelist", "sresourcearchivelist", "sresourcearchivelist2" })
        {
            if (!archiveSettings.TryGetValue(key, out var archiveList))
            {
                continue;
            }

            foreach (var archiveName in archiveList.Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries))
            {
                var path = Path.Combine(session.DataPath, archiveName);
                if (_pathService.FileExists(path))
                {
                    result.Archives.EnabledArchives.Add(path);
                }
            }
        }

        foreach (var modulePath in result.Modules.EnabledModules)
        {
            foreach (var suffix in session.IniData.Ba2Suffixes)
            {
                var archivePath = Path.Combine(
                    Path.GetDirectoryName(modulePath) ?? session.DataPath,
                    $"{Path.GetFileNameWithoutExtension(modulePath)} - {suffix}.ba2");
                if (_pathService.FileExists(archivePath))
                {
                    result.Archives.EnabledArchives.Add(archivePath);
                }
            }
        }

        await CountEnabledArchivesAsync(result, cancellationToken);
    }

    private static async Task CountEnabledArchivesAsync(
        OverviewCensusResult result,
        CancellationToken cancellationToken)
    {
        foreach (var archivePath in result.Archives.EnabledArchives)
        {
            byte[] header;
            try
            {
                header = new byte[12];
                await using var stream = File.OpenRead(archivePath);
                var read = await stream.ReadAsync(header.AsMemory(0, header.Length), cancellationToken);
                if (read < 12)
                {
                    result.Archives.UnreadableArchives.Add(archivePath);
                    result.Problems.Add(new OverviewProblem(ProblemType.InvalidArchive, Path.GetFileName(archivePath), "Archive is either corrupt or not in Bethesda Archive 2 format.", Path: archivePath, RelativePath: Path.GetFileName(archivePath), Mod: "OVERVIEW"));
                    continue;
                }
            }
            catch
            {
                result.Archives.UnreadableArchives.Add(archivePath);
                result.Problems.Add(new OverviewProblem(ProblemType.InvalidArchive, Path.GetFileName(archivePath), "Failed to read archive due to permissions or the file is missing.", Path: archivePath, RelativePath: Path.GetFileName(archivePath), Mod: "OVERVIEW"));
                continue;
            }

            var parsed = Ba2HeaderParser.Parse(header);
            if (parsed.IsUnreadable)
            {
                result.Archives.UnreadableArchives.Add(archivePath);
                result.Problems.Add(new OverviewProblem(ProblemType.InvalidArchive, Path.GetFileName(archivePath), parsed.Error ?? "Archive is invalid.", Path: archivePath, RelativePath: Path.GetFileName(archivePath), Mod: "OVERVIEW"));
                continue;
            }

            if (parsed.Format == ArchiveFormat.GNRL)
            {
                result.Archives.GeneralCount++;
            }
            else if (parsed.Format == ArchiveFormat.DX10)
            {
                result.Archives.TextureCount++;
            }

            if (parsed.Version == ArchiveVersion.OG)
            {
                result.Archives.OldGenArchives.Add(archivePath);
            }
            else
            {
                result.Archives.NextGenArchives.Add(archivePath);
            }
        }
    }

    private static void AddLimitProblems(OverviewCensusResult result)
    {
        AddLimitProblem(result, result.Archives.GeneralCount, VersionTables.MaxArchivesGeneral, "General", "Archive");
        AddLimitProblem(result, result.Archives.TextureCount, VersionTables.MaxArchivesTexture, "Texture", "Archive");
        AddLimitProblem(result, result.Modules.FullCount, VersionTables.MaxModulesFull, "Full", "Module");
        AddLimitProblem(result, result.Modules.LightCount, VersionTables.MaxModulesLight, "Light", "Module");
    }

    private static void AddLimitProblem(
        OverviewCensusResult result,
        int count,
        int limit,
        string fileFormat,
        string fileType)
    {
        if (count <= limit)
        {
            return;
        }

        result.Problems.Add(new OverviewProblem(
            ProblemType.LimitExceeded,
            $"{count} {fileFormat} {fileType}s",
            $"You have {count} {fileFormat} {fileType}s enabled. The limit is {limit}.",
            Solution: $"{fileType}s must be reduced to stay below the game limit."));
    }
}
