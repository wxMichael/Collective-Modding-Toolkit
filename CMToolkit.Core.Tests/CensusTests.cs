using System.Text;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;
using CMToolkit.Core.Services;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Tests;

public class CensusTests
{
    [Fact]
    public async Task OverviewCensusService_ClassifiesBinariesArchivesAndModules()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var gameDir = Path.Combine(root, "Fallout 4");
        var dataDir = Path.Combine(gameDir, "Data");
        var appData = Path.Combine(root, "AppData");
        Directory.CreateDirectory(dataDir);
        Directory.CreateDirectory(Path.Combine(dataDir, "F4SE", "Plugins"));
        Directory.CreateDirectory(Path.Combine(appData, "Fallout4"));

        await File.WriteAllTextAsync(Path.Combine(gameDir, "Fallout4.exe"), string.Empty);
        await File.WriteAllBytesAsync(Path.Combine(dataDir, "Fallout4 - Misc.ba2"), MakeBa2(1, "GNRL"));
        await File.WriteAllBytesAsync(Path.Combine(dataDir, "Fallout4 - Textures1.ba2"), MakeBa2(8, "DX10"));
        await File.WriteAllBytesAsync(Path.Combine(dataDir, "Fallout4.esm"), MakeModule(light: false, hedr100: true));
        await File.WriteAllBytesAsync(Path.Combine(dataDir, "TestLight.esl"), MakeModule(light: true, hedr100: false));
        await File.WriteAllTextAsync(Path.Combine(gameDir, "Fallout4.ccc"), string.Empty);
        await File.WriteAllTextAsync(Path.Combine(appData, "Fallout4", "plugins.txt"), "*TestLight.esl");
        await File.WriteAllTextAsync(Path.Combine(dataDir, "F4SE", "Plugins", "version-1-10-163-0.bin"), string.Empty);

        try
        {
            var session = new GameSession
            {
                GamePath = gameDir,
                DataPath = dataDir,
                IniData = new GameIniData
                {
                    GameSettings = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase)
                    {
                        ["archive"] = new(StringComparer.OrdinalIgnoreCase)
                        {
                            ["sresourcearchivelist"] = "Fallout4 - Misc.ba2,Fallout4 - Textures1.ba2",
                        },
                    },
                },
            };

            var service = new OverviewCensusService(
                new FakePeVersionReader(file => Path.GetFileName(file) == "Fallout4.exe" ? "1.10.163.0" : null),
                new FakePathService(root, appData));

            var result = await service.RefreshAsync(session);

            Assert.Equal(InstallType.OG, session.InstallType);
            Assert.Equal(InstallType.OG, result.Binaries["Fallout4.exe"].InstallType);
            Assert.NotNull(result.AddressLibraryPath);
            Assert.Equal(1, result.Archives.GeneralCount);
            Assert.Equal(1, result.Archives.TextureCount);
            Assert.Single(result.Archives.OldGenArchives);
            Assert.Single(result.Archives.NextGenArchives);
            Assert.Equal(1, result.Modules.FullCount);
            Assert.Equal(1, result.Modules.LightCount);
            Assert.Equal(1, result.Modules.HedrVersion100Count);
            Assert.Single(result.Modules.HedrVersion095Modules);
            Assert.DoesNotContain(result.Problems, problem => problem.Title == "Unknown Game Version");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static byte[] MakeBa2(byte version, string format) =>
        [.. Encoding.ASCII.GetBytes("BTDX"), version, 0, 0, 0, .. Encoding.ASCII.GetBytes(format)];

    private static byte[] MakeModule(bool light, bool hedr100)
    {
        var bytes = new byte[34];
        Encoding.ASCII.GetBytes("TES4").CopyTo(bytes, 0);
        BitConverter.GetBytes(light ? (uint)ModuleFlag.Light : 0).CopyTo(bytes, 8);
        Encoding.ASCII.GetBytes("HEDR").CopyTo(bytes, 24);
        (hedr100 ? [0x00, 0x00, 0x80, 0x3f] : new byte[] { 0x33, 0x33, 0x73, 0x3f }).CopyTo(bytes, 30);
        return bytes;
    }

    private sealed class FakePeVersionReader(Func<string, string?> getVersion) : IPeVersionReader
    {
        public string? GetVersion(string filePath) => getVersion(filePath);
    }

    private sealed class FakePathService(string currentDirectory, string localApplicationData) : IPathService
    {
        public string CurrentDirectory { get; } = currentDirectory;

        public string LocalApplicationData { get; } = localApplicationData;

        public string Documents { get; } = currentDirectory;

        public bool FileExists(string path) => File.Exists(path);

        public bool DirectoryExists(string path) => Directory.Exists(path);
    }
}
