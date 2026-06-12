using CMToolkit.Core.Enums;
using CMToolkit.Core.Services;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Tests;

public class FixtureCensusTests
{
    [Theory]
    [InlineData("og", InstallType.OG, 1, 1, 1, 0)]
    [InlineData("ng", InstallType.NG, 0, 2, 0, 1)]
    public async Task OverviewCensusService_MatchesSyntheticInstallFixture(
        string fixtureName,
        InstallType expectedInstallType,
        int expectedOldGenArchives,
        int expectedNextGenArchives,
        int expectedFullModules,
        int expectedLightModules)
    {
        using var fixture = await SyntheticInstallFixture.CreateAsync(fixtureName);
        var service = new OverviewCensusService(
            new FixturePeVersionReader(fixture.BinaryVersions),
            new FixturePathService(fixture.Root, fixture.LocalApplicationData));

        var result = await service.RefreshAsync(fixture.Session);

        Assert.Equal(expectedInstallType, fixture.Session.InstallType);
        Assert.Equal(expectedOldGenArchives, result.Archives.OldGenArchives.Count);
        Assert.Equal(expectedNextGenArchives, result.Archives.NextGenArchives.Count);
        Assert.Equal(expectedFullModules, result.Modules.FullCount);
        Assert.Equal(expectedLightModules, result.Modules.LightCount);
    }

    private sealed class FixturePeVersionReader(IReadOnlyDictionary<string, string> versions) : IPeVersionReader
    {
        public string? GetVersion(string filePath) =>
            versions.GetValueOrDefault(Path.GetFileName(filePath));
    }

    private sealed class FixturePathService(string currentDirectory, string localApplicationData) : IPathService
    {
        public string CurrentDirectory { get; } = currentDirectory;

        public string LocalApplicationData { get; } = localApplicationData;

        public string Documents { get; } = currentDirectory;

        public bool FileExists(string path) => File.Exists(path);

        public bool DirectoryExists(string path) => Directory.Exists(path);
    }
}
