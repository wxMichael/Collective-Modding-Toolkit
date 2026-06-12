using System.Text;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;
using CMToolkit.Core.Services;
using CMToolkit.Core.Settings;
using CMToolkit.Core.Utilities;
using Microsoft.Extensions.Logging.Abstractions;

return await SmokeProgram.RunAsync(args);

internal static class SmokeProgram
{
    public static async Task<int> RunAsync(string[] args)
    {
        _ = new SettingsStore(NullLogger<SettingsStore>.Instance);

        if (args.Length != 2 || args[0] is not ("--fixture" or "--real"))
        {
            PrintUsage();
            return 2;
        }

        try
        {
            using var fixture = args[0] == "--fixture"
                ? await SmokeFixture.CreateAsync(args[1])
                : null;

            var session = fixture?.Session ?? await CreateRealSessionAsync(args[1]);
            if (session is null)
            {
                await Console.Error.WriteLineAsync($"Game path not found or invalid: {args[1]}");
                return 1;
            }

            IPeVersionReader versionReader = fixture is not null
                ? new FixturePeVersionReader(fixture.BinaryVersions)
                : new PeVersionReader();
            IPathService pathService = fixture is not null
                ? new FixturePathService(fixture.Root, fixture.LocalApplicationData)
                : new PathService();

            var result = await new OverviewCensusService(versionReader, pathService).RefreshAsync(session);
            PrintSummary(session, result);
            return 0;
        }
        catch (Exception ex)
        {
            await Console.Error.WriteLineAsync(ex.Message);
            return 1;
        }
    }

    private static async Task<GameSession?> CreateRealSessionAsync(string gamePath)
    {
        if (File.Exists(gamePath))
        {
            gamePath = Path.GetDirectoryName(gamePath) ?? gamePath;
        }

        if (!PathHelper.IsFallout4Directory(gamePath))
        {
            return null;
        }

        var pathService = new PathService();
        var dataPath = Path.Combine(gamePath, "Data");
        return new GameSession
        {
            GamePath = gamePath,
            DataPath = Directory.Exists(dataPath) ? dataPath : null,
            F4sePath = Directory.Exists(Path.Combine(dataPath, "F4SE", "Plugins"))
                ? Path.Combine(dataPath, "F4SE", "Plugins")
                : null,
            IniData = await new GameIniLoader(pathService).LoadAsync(),
        };
    }

    private static void PrintSummary(GameSession session, OverviewCensusResult result)
    {
        Console.WriteLine($"Game Path: {session.GamePath}");
        Console.WriteLine($"Install Type: {session.InstallType.ToDisplayString()}");
        Console.WriteLine();
        Console.WriteLine("Binaries:");
        foreach (var binary in result.Binaries.Values)
        {
            Console.WriteLine($"  {binary.Name}: {binary.InstallType.ToDisplayString()} ({binary.Version ?? "Not Found"})");
        }

        Console.WriteLine();
        Console.WriteLine("Archives:");
        Console.WriteLine($"  General: {result.Archives.GeneralCount}");
        Console.WriteLine($"  Texture: {result.Archives.TextureCount}");
        Console.WriteLine($"  Total: {result.Archives.GeneralCount + result.Archives.TextureCount}");
        Console.WriteLine($"  v1: {result.Archives.OldGenArchives.Count}");
        Console.WriteLine($"  v7/v8: {result.Archives.NextGenArchives.Count}");
        Console.WriteLine($"  Unreadable: {result.Archives.UnreadableArchives.Count}");

        Console.WriteLine();
        Console.WriteLine("Modules:");
        Console.WriteLine($"  Full: {result.Modules.FullCount}");
        Console.WriteLine($"  Light: {result.Modules.LightCount}");
        Console.WriteLine($"  Total: {result.Modules.FullCount + result.Modules.LightCount}");
        Console.WriteLine($"  HEDR v1.00: {result.Modules.HedrVersion100Count}");
        Console.WriteLine($"  HEDR v0.95: {result.Modules.HedrVersion095Modules.Count}");
        Console.WriteLine($"  HEDR v????: {result.Modules.UnknownHedrModules.Count}");
        Console.WriteLine($"  Unreadable: {result.Modules.UnreadableModules.Count}");

        Console.WriteLine();
        Console.WriteLine($"Problems: {result.Problems.Count}");
    }

    private static void PrintUsage()
    {
        Console.WriteLine("Usage:");
        Console.WriteLine("  CMToolkit.Smoke --fixture og");
        Console.WriteLine("  CMToolkit.Smoke --fixture ng");
        Console.WriteLine("  CMToolkit.Smoke --real \"D:\\Steam\\steamapps\\common\\Fallout 4\"");
    }
}

internal sealed class FixturePeVersionReader(IReadOnlyDictionary<string, string> versions) : IPeVersionReader
{
    public string? GetVersion(string filePath) =>
        versions.GetValueOrDefault(Path.GetFileName(filePath));
}

internal sealed class FixturePathService(string currentDirectory, string localApplicationData) : IPathService
{
    public string CurrentDirectory { get; } = currentDirectory;

    public string LocalApplicationData { get; } = localApplicationData;

    public string Documents { get; } = currentDirectory;

    public bool FileExists(string path) => File.Exists(path);

    public bool DirectoryExists(string path) => Directory.Exists(path);
}

internal sealed class SmokeFixture : IDisposable
{
    private SmokeFixture(string root, string localApplicationData, GameSession session, IReadOnlyDictionary<string, string> binaryVersions)
    {
        Root = root;
        LocalApplicationData = localApplicationData;
        Session = session;
        BinaryVersions = binaryVersions;
    }

    public string Root { get; }

    public string LocalApplicationData { get; }

    public GameSession Session { get; }

    public IReadOnlyDictionary<string, string> BinaryVersions { get; }

    public static async Task<SmokeFixture> CreateAsync(string fixtureName)
    {
        var root = Path.Combine(Path.GetTempPath(), $"cmtoolkit-smoke-{fixtureName}-{Guid.NewGuid():N}");
        var gamePath = Path.Combine(root, "Fallout 4");
        var dataPath = Path.Combine(gamePath, "Data");
        var localAppData = Path.Combine(root, "LocalAppData");
        Directory.CreateDirectory(dataPath);
        Directory.CreateDirectory(Path.Combine(localAppData, "Fallout4"));

        var versions = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var archiveSettings = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["sresourcearchivelist"] = "Fallout4 - Misc.ba2,Fallout4 - Textures1.ba2",
        };

        await File.WriteAllTextAsync(Path.Combine(gamePath, "Fallout4.exe"), string.Empty);
        await File.WriteAllTextAsync(Path.Combine(gamePath, "Fallout4.ccc"), string.Empty);
        await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Startup.ba2"), MakeBa2(1, "GNRL"));

        switch (fixtureName)
        {
            case "og":
                versions["Fallout4.exe"] = "1.10.163.0";
                await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4.esm"), MakeModule(light: false, hedr100: true));
                await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Misc.ba2"), MakeBa2(1, "GNRL"));
                await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Textures1.ba2"), MakeBa2(8, "DX10"));
                break;
            case "ng":
                versions["Fallout4.exe"] = "1.10.984.0";
                await File.WriteAllBytesAsync(Path.Combine(dataPath, "TestLight.esl"), MakeModule(light: true, hedr100: false));
                await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Misc.ba2"), MakeBa2(8, "GNRL"));
                await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Textures1.ba2"), MakeBa2(8, "DX10"));
                await File.WriteAllTextAsync(Path.Combine(localAppData, "Fallout4", "plugins.txt"), "*TestLight.esl");
                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(fixtureName), fixtureName, "Unknown fixture. Expected 'og' or 'ng'.");
        }

        var session = new GameSession
        {
            GamePath = gamePath,
            DataPath = dataPath,
            IniData = new GameIniData
            {
                GameSettings = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase)
                {
                    ["archive"] = archiveSettings,
                },
            },
        };

        return new SmokeFixture(root, localAppData, session, versions);
    }

    public void Dispose()
    {
        if (Directory.Exists(Root))
        {
            Directory.Delete(Root, recursive: true);
        }
    }

    private static byte[] MakeBa2(byte version, string format) =>
        [.. Encoding.ASCII.GetBytes("BTDX"), version, 0, 0, 0, .. Encoding.ASCII.GetBytes(format), .. Encoding.ASCII.GetBytes("fixture")];

    private static byte[] MakeModule(bool light, bool hedr100)
    {
        var bytes = new byte[34];
        Encoding.ASCII.GetBytes("TES4").CopyTo(bytes, 0);
        BitConverter.GetBytes(light ? (uint)ModuleFlag.Light : 0).CopyTo(bytes, 8);
        Encoding.ASCII.GetBytes("HEDR").CopyTo(bytes, 24);
        (hedr100 ? [0x00, 0x00, 0x80, 0x3f] : new byte[] { 0x33, 0x33, 0x73, 0x3f }).CopyTo(bytes, 30);
        return bytes;
    }
}
