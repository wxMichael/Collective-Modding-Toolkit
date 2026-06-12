using CMToolkit.Core.Models;
using CMToolkit.Core.Services;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Tests;

public class DetectionTests
{
    [Fact]
    public async Task ModManagerDetector_DetectsPortableModOrganizerAndParsesProfile()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var gameDir = Path.Combine(root, "Fallout 4");
        var mo2Dir = Path.Combine(root, "MO2");
        Directory.CreateDirectory(gameDir);
        Directory.CreateDirectory(mo2Dir);
        var mo2Exe = Path.Combine(mo2Dir, "ModOrganizer.exe");
        await File.WriteAllTextAsync(mo2Exe, string.Empty);
        await File.WriteAllTextAsync(Path.Combine(mo2Dir, "portable.txt"), string.Empty);
        await File.WriteAllTextAsync(
            Path.Combine(mo2Dir, "ModOrganizer.ini"),
            $$"""
            [General]
            gameName=Fallout 4
            gamePath={{gameDir}}
            selected_profile=Collective
            """);

        try
        {
            var detector = new ModManagerDetector(
                new FakeProcessWalker([new ProcessSnapshot(10, 0, "ModOrganizer.exe", mo2Exe)]),
                new FakePeVersionReader("2.5.2.0"),
                new FakeRegistryReader(),
                new PathService());

            var result = await detector.DetectAsync();

            Assert.True(result.Found);
            Assert.Equal("Mod Organizer", result.Name);
            Assert.Equal("2.5.2", result.Version);
            Assert.Equal("Collective", result.Profile);
            Assert.True(result.ModManager!.Portable);
            Assert.Equal(gameDir, result.ModManager.GamePath);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task ModManagerDetector_FallsBackToExeDirIniWithoutMarkingPortable()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var gameDir = Path.Combine(root, "Fallout 4");
        var mo2Dir = Path.Combine(root, "MO2");
        Directory.CreateDirectory(gameDir);
        Directory.CreateDirectory(mo2Dir);
        var mo2Exe = Path.Combine(mo2Dir, "ModOrganizer.exe");
        await File.WriteAllTextAsync(mo2Exe, string.Empty);
        await File.WriteAllTextAsync(
            Path.Combine(mo2Dir, "ModOrganizer.ini"),
            $$"""
            [General]
            gameName=Fallout 4
            gamePath={{gameDir}}
            selected_profile=Collective
            """);

        try
        {
            var detector = new ModManagerDetector(
                new FakeProcessWalker([new ProcessSnapshot(10, 0, "ModOrganizer.exe", mo2Exe)]),
                new FakePeVersionReader("2.5.2.0"),
                new FakeRegistryReader(),
                new PathService());

            var result = await detector.DetectAsync();

            Assert.True(result.Found);
            Assert.False(result.ModManager!.Portable);
            Assert.Equal(gameDir, result.ModManager.GamePath);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task GameDetector_NormalizesExePathToInstallDirectory()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var gameDir = Path.Combine(root, "Fallout 4");
        Directory.CreateDirectory(Path.Combine(gameDir, "Data"));
        var falloutExe = Path.Combine(gameDir, "Fallout4.exe");
        await File.WriteAllTextAsync(falloutExe, string.Empty);

        try
        {
            var detector = new GameDetector(
                new FakeModManagerDetector(new ModManagerDetectionResult { Found = false }),
                new FakeRegistryReader(),
                new FakePathService(currentDirectory: root, documents: root),
                new FakeGamePathPrompt(falloutExe),
                new GameIniLoader(new FakePathService(currentDirectory: root, documents: root)));

            var result = await detector.DetectAsync();

            Assert.True(result.Found);
            Assert.Equal(gameDir, result.GamePath);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task GameDetector_UsesModOrganizerGamePathBeforeCurrentDirectory()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var gameDir = Path.Combine(root, "Fallout 4");
        Directory.CreateDirectory(Path.Combine(gameDir, "Data"));
        await File.WriteAllTextAsync(Path.Combine(gameDir, "Fallout4.exe"), string.Empty);

        try
        {
            var modManager = new ModManagerInfo
            {
                Name = "Mod Organizer",
                ExePath = Path.Combine(root, "MO2", "ModOrganizer.exe"),
                GamePath = gameDir,
                SelectedProfile = "Collective",
            };

            var detector = new GameDetector(
                new FakeModManagerDetector(new ModManagerDetectionResult { Found = true, ModManager = modManager }),
                new FakeRegistryReader(),
                new FakePathService(currentDirectory: root, documents: root),
                new NullGamePathPrompt(),
                new GameIniLoader(new FakePathService(currentDirectory: root, documents: root)));

            var result = await detector.DetectAsync();

            Assert.True(result.Found);
            Assert.Equal(gameDir, result.GamePath);
            Assert.Equal(Path.Combine(gameDir, "Data"), result.Session!.DataPath);
            Assert.Equal(modManager, result.Session.ModManager);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task GameIniLoader_DerivesLocalizedBa2SuffixesFromLanguage()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var iniDir = Path.Combine(root, "My Games", "Fallout4");
        Directory.CreateDirectory(iniDir);
        await File.WriteAllTextAsync(Path.Combine(iniDir, "Fallout4.ini"), "[General]\nsLanguage=de");

        try
        {
            var loader = new GameIniLoader(new FakePathService(currentDirectory: root, documents: root));

            var data = await loader.LoadAsync();

            Assert.Equal(["main", "textures", "voices_en", "voices_de"], data.Ba2Suffixes);
            Assert.Equal("de", data.GameSettings["general"]["slanguage"]);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private sealed class FakeProcessWalker(IReadOnlyList<ProcessSnapshot> processes) : IProcessWalker
    {
        public IReadOnlyList<ProcessSnapshot> GetParentProcesses(int maxDepth) => processes.Take(maxDepth).ToArray();
    }

    private sealed class FakePeVersionReader(string? version) : IPeVersionReader
    {
        public string? GetVersion(string filePath) => version;
    }

    private sealed class FakeRegistryReader : IRegistryReader
    {
        public Dictionary<(RegistryRoot Root, string Subkey, string ValueName), string> Values { get; } = [];

        public string? GetValue(RegistryRoot root, string subkey, string valueName) =>
            Values.TryGetValue((root, subkey, valueName), out var value) ? value : null;
    }

    private sealed class FakeModManagerDetector(ModManagerDetectionResult result) : IModManagerDetector
    {
        public Task<ModManagerDetectionResult> DetectAsync(CancellationToken cancellationToken = default) => Task.FromResult(result);
    }

    private sealed class FakeGamePathPrompt(string pickedExePath) : IGamePathPrompt
    {
        public Task<bool> ConfirmManualSelectionAsync(CancellationToken cancellationToken = default) =>
            Task.FromResult(true);

        public Task<string?> PickFallout4ExeAsync(CancellationToken cancellationToken = default) =>
            Task.FromResult<string?>(pickedExePath);
    }

    private sealed class FakePathService(string currentDirectory, string documents) : IPathService
    {
        public string CurrentDirectory { get; } = currentDirectory;

        public string LocalApplicationData { get; } = currentDirectory;

        public string Documents { get; } = documents;

        public bool FileExists(string path) => File.Exists(path);

        public bool DirectoryExists(string path) => Directory.Exists(path);
    }
}
