using CMToolkit.Core.Settings;
using Microsoft.Extensions.Logging;

namespace CMToolkit.Core.Tests;

public class SettingsStoreTests
{
    [Fact]
    public void SaveAndLoad_RoundTripsDefaultSettings()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempDir);

        var settingsPath = Path.Combine(tempDir, "settings.json");
        var downloadSourcePath = Path.Combine(tempDir, "download-source.txt");
        File.WriteAllText(downloadSourcePath, "github");

        var loggerFactory = LoggerFactory.Create(builder => builder.AddDebug());
        var logger = loggerFactory.CreateLogger<SettingsStore>();

        var store = new SettingsStore(logger, settingsPath, downloadSourcePath);
        store.Save();

        var reloaded = new SettingsStore(logger, settingsPath, downloadSourcePath);

        Assert.Equal("github", reloaded.Current.UpdateSource);
        Assert.Equal("INFO", reloaded.Current.LogLevel);
        Assert.True(reloaded.Current.ScannerOverviewIssues);
        Assert.True(reloaded.Current.DowngraderKeepBackups);

        var json = File.ReadAllText(settingsPath);
        Assert.Contains("\"update_source\": \"github\"", json);
        Assert.Contains("\"scanner_OverviewIssues\": true", json);
    }

    [Fact]
    public void Load_ResetsInvalidJsonAndRewritesDefaults()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempDir);

        try
        {
            var settingsPath = Path.Combine(tempDir, "settings.json");
            var downloadSourcePath = Path.Combine(tempDir, "download-source.txt");
            File.WriteAllText(downloadSourcePath, "nexus");
            File.WriteAllText(settingsPath, "{ invalid");

            var loggerFactory = LoggerFactory.Create(builder => builder.AddDebug());
            var store = new SettingsStore(loggerFactory.CreateLogger<SettingsStore>(), settingsPath, downloadSourcePath);

            Assert.Equal("nexus", store.Current.UpdateSource);
            Assert.Equal("INFO", store.Current.LogLevel);
            Assert.Contains("\"update_source\": \"nexus\"", File.ReadAllText(settingsPath));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void Load_StripsUnknownKeysAndDefaultsInvalidValues()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempDir);

        try
        {
            var settingsPath = Path.Combine(tempDir, "settings.json");
            var downloadSourcePath = Path.Combine(tempDir, "download-source.txt");
            File.WriteAllText(downloadSourcePath, "github");
            File.WriteAllText(
                settingsPath,
                """
                {
                  "log_level": "LOUD",
                  "update_source": "both",
                  "scanner_OverviewIssues": false,
                  "unknown": true
                }
                """);

            var loggerFactory = LoggerFactory.Create(builder => builder.AddDebug());
            var store = new SettingsStore(loggerFactory.CreateLogger<SettingsStore>(), settingsPath, downloadSourcePath);
            var json = File.ReadAllText(settingsPath);

            Assert.Equal("INFO", store.Current.LogLevel);
            Assert.Equal("both", store.Current.UpdateSource);
            Assert.False(store.Current.ScannerOverviewIssues);
            Assert.DoesNotContain("unknown", json);
            Assert.Contains("\"log_level\": \"INFO\"", json);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
