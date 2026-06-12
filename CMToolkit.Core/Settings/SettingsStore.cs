using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;

namespace CMToolkit.Core.Settings;

public sealed class SettingsStore
{
    private static readonly string[] ValidLogLevels = ["DEBUG", "INFO", "WARNING", "ERROR"];
    private static readonly string[] ValidUpdateSources = ["nexus", "github", "both", "none"];

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        IndentCharacter = '\t',
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private readonly ILogger<SettingsStore> _logger;
    private readonly string _settingsPath;
    private readonly string? _downloadSourcePath;

    public AppSettings Current { get; private set; } = CreateDefaults("nexus");

    public SettingsStore(ILogger<SettingsStore> logger, string? settingsPath = null, string? downloadSourcePath = null)
    {
        _logger = logger;
        _settingsPath = settingsPath ?? Path.Combine(Environment.CurrentDirectory, "settings.json");
        _downloadSourcePath = downloadSourcePath;
        Load();
    }

    public void Load()
    {
        Current = CreateDefaults(ReadDefaultUpdateSource());

        if (!File.Exists(_settingsPath))
        {
            _logger.LogInformation("Settings : {File} not found; using defaults.", Path.GetFileName(_settingsPath));
            Save();
            return;
        }

        var resave = false;
        try
        {
            var json = File.ReadAllText(_settingsPath);
            using var document = JsonDocument.Parse(json);
            if (document.RootElement.ValueKind != JsonValueKind.Object)
            {
                throw new InvalidDataException("Settings file is not a JSON object.");
            }

            var raw = new Dictionary<string, JsonElement>();
            foreach (var property in document.RootElement.EnumerateObject())
            {
                raw[property.Name] = property.Value;
            }

            var defaults = CreateDefaults(ReadDefaultUpdateSource());
            var merged = new Dictionary<string, object?>();

            foreach (var key in GetKnownKeys())
            {
                if (!raw.ContainsKey(key))
                {
                    _logger.LogInformation("Settings : Adding new setting to JSON: {Key}", key);
                    resave = true;
                    merged[key] = GetDefaultValue(defaults, key);
                    continue;
                }

                if (TryParseSetting(key, raw[key], defaults, out var value))
                {
                    merged[key] = value;
                }
                else
                {
                    _logger.LogError("Settings : '{Key}' has invalid value; reset to default.", key);
                    merged[key] = GetDefaultValue(defaults, key);
                    resave = true;
                }
            }

            foreach (var key in raw.Keys)
            {
                if (!GetKnownKeys().Contains(key))
                {
                    _logger.LogError("Settings : Unknown setting '{Key}' will be removed.", key);
                    resave = true;
                }
            }

            Current = FromDictionary(merged);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Settings : Failed to load {File}. Settings will be reset.", Path.GetFileName(_settingsPath));
            Current = CreateDefaults(ReadDefaultUpdateSource());
            resave = true;
        }

        if (resave)
        {
            Save();
        }
    }

    public void Save()
    {
        _logger.LogDebug("Settings : Saving {File}", Path.GetFileName(_settingsPath));
        try
        {
            var json = JsonSerializer.Serialize(ToDictionary(Current), JsonOptions);
            File.WriteAllText(_settingsPath, json + Environment.NewLine);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Settings : Failed to save {File}", Path.GetFileName(_settingsPath));
        }
    }

    private string ReadDefaultUpdateSource()
    {
        var path = _downloadSourcePath;
        if (string.IsNullOrEmpty(path))
        {
            path = Path.Combine(AppContext.BaseDirectory, "Assets", "download-source.txt");
        }

        try
        {
            if (File.Exists(path))
            {
                var source = File.ReadAllText(path).Trim();
                if (source is "nexus" or "github")
                {
                    _logger.LogDebug("Settings : Download source: '{Source}'", source);
                    return source;
                }

                _logger.LogError("Settings : Invalid download source: '{Source}'", source);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Settings : Failed to detect download source.");
        }

        return "nexus";
    }

    private static AppSettings CreateDefaults(string updateSource) => new()
    {
        LogLevel = "INFO",
        UpdateSource = updateSource,
    };

    private static HashSet<string> GetKnownKeys() =>
    [
        "log_level",
        "update_source",
        "scanner_OverviewIssues",
        "scanner_Errors",
        "scanner_WrongFormat",
        "scanner_LoosePrevis",
        "scanner_JunkFiles",
        "scanner_ProblemOverrides",
        "scanner_RaceSubgraphs",
        "downgrader_keep_backups",
        "downgrader_delete_deltas",
    ];

    private static object? GetDefaultValue(AppSettings defaults, string key) => key switch
    {
        "log_level" => defaults.LogLevel,
        "update_source" => defaults.UpdateSource,
        "scanner_OverviewIssues" => defaults.ScannerOverviewIssues,
        "scanner_Errors" => defaults.ScannerErrors,
        "scanner_WrongFormat" => defaults.ScannerWrongFormat,
        "scanner_LoosePrevis" => defaults.ScannerLoosePrevis,
        "scanner_JunkFiles" => defaults.ScannerJunkFiles,
        "scanner_ProblemOverrides" => defaults.ScannerProblemOverrides,
        "scanner_RaceSubgraphs" => defaults.ScannerRaceSubgraphs,
        "downgrader_keep_backups" => defaults.DowngraderKeepBackups,
        "downgrader_delete_deltas" => defaults.DowngraderDeleteDeltas,
        _ => throw new ArgumentOutOfRangeException(nameof(key)),
    };

    private static bool TryParseSetting(string key, JsonElement element, AppSettings defaults, out object? value)
    {
        value = null;
        return key switch
        {
            "log_level" => TryParseString(element, ValidLogLevels, defaults.LogLevel, out value),
            "update_source" => TryParseString(element, ValidUpdateSources, defaults.UpdateSource, out value),
            "scanner_OverviewIssues" or "scanner_Errors" or "scanner_WrongFormat" or "scanner_LoosePrevis"
                or "scanner_JunkFiles" or "scanner_ProblemOverrides" or "scanner_RaceSubgraphs"
                or "downgrader_keep_backups" or "downgrader_delete_deltas"
                => TryParseBool(element, out value),
            _ => false,
        };
    }

    private static bool TryParseString(JsonElement element, string[] allowed, string fallback, out object? value)
    {
        if (element.ValueKind == JsonValueKind.String)
        {
            var text = element.GetString();
            if (text is not null && allowed.Contains(text))
            {
                value = text;
                return true;
            }
        }

        value = fallback;
        return false;
    }

    private static bool TryParseBool(JsonElement element, out object? value)
    {
        if (element.ValueKind is JsonValueKind.True or JsonValueKind.False)
        {
            value = element.GetBoolean();
            return true;
        }

        value = null;
        return false;
    }

    private static AppSettings FromDictionary(Dictionary<string, object?> values) => new()
    {
        LogLevel = (string)(values["log_level"] ?? "INFO"),
        UpdateSource = (string)(values["update_source"] ?? "nexus"),
        ScannerOverviewIssues = (bool)(values["scanner_OverviewIssues"] ?? true),
        ScannerErrors = (bool)(values["scanner_Errors"] ?? true),
        ScannerWrongFormat = (bool)(values["scanner_WrongFormat"] ?? true),
        ScannerLoosePrevis = (bool)(values["scanner_LoosePrevis"] ?? true),
        ScannerJunkFiles = (bool)(values["scanner_JunkFiles"] ?? true),
        ScannerProblemOverrides = (bool)(values["scanner_ProblemOverrides"] ?? true),
        ScannerRaceSubgraphs = (bool)(values["scanner_RaceSubgraphs"] ?? true),
        DowngraderKeepBackups = (bool)(values["downgrader_keep_backups"] ?? true),
        DowngraderDeleteDeltas = (bool)(values["downgrader_delete_deltas"] ?? true),
    };

    public static Dictionary<string, object> ToDictionary(AppSettings settings) => new()
    {
        ["log_level"] = settings.LogLevel,
        ["update_source"] = settings.UpdateSource,
        ["scanner_OverviewIssues"] = settings.ScannerOverviewIssues,
        ["scanner_Errors"] = settings.ScannerErrors,
        ["scanner_WrongFormat"] = settings.ScannerWrongFormat,
        ["scanner_LoosePrevis"] = settings.ScannerLoosePrevis,
        ["scanner_JunkFiles"] = settings.ScannerJunkFiles,
        ["scanner_ProblemOverrides"] = settings.ScannerProblemOverrides,
        ["scanner_RaceSubgraphs"] = settings.ScannerRaceSubgraphs,
        ["downgrader_keep_backups"] = settings.DowngraderKeepBackups,
        ["downgrader_delete_deltas"] = settings.DowngraderDeleteDeltas,
    };
}
