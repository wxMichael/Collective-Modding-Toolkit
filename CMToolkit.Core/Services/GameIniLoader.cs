using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;
using CMToolkit.Core.Parsing;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Services;

public sealed class GameIniLoader(IPathService pathService)
{
    private readonly IPathService _pathService = pathService;

    public async Task<GameIniData> LoadAsync(CancellationToken cancellationToken = default)
    {
        var docsPath = Path.Combine(_pathService.Documents, "My Games", "Fallout4");
        var gameSettings = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);
        var gamePrefs = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);

        foreach (var fileName in new[] { "Fallout4.ini", "Fallout4Prefs.ini", "Fallout4Custom.ini" })
        {
            var path = Path.Combine(docsPath, fileName);
            if (!_pathService.FileExists(path))
            {
                continue;
            }

            var parsed = await IniReader.ReadAsync(path, cancellationToken);
            MergeInto(fileName == "Fallout4Prefs.ini" ? gamePrefs : gameSettings, parsed);
        }

        var languageCode = gameSettings.TryGetValue("general", out var general) &&
                           general.TryGetValue("slanguage", out var language)
            ? language.ToLowerInvariant()
            : "en";

        var parsedLanguage = ParseLanguage(languageCode);
        var ba2Suffixes = languageCode == "en"
            ? new[] { "main", "textures", "voices_en" }
            : ["main", "textures", "voices_en", $"voices_{languageCode}"];

        return new GameIniData
        {
            GameSettings = gameSettings,
            GamePrefs = gamePrefs,
            Language = parsedLanguage,
            Ba2Suffixes = ba2Suffixes,
        };
    }

    private static void MergeInto(
        Dictionary<string, Dictionary<string, string>> target,
        Dictionary<string, Dictionary<string, string>> source)
    {
        foreach (var (section, values) in source)
        {
            if (!target.TryGetValue(section, out var targetSection))
            {
                targetSection = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                target[section] = targetSection;
            }

            foreach (var (key, value) in values)
            {
                targetSection[key] = value;
            }
        }
    }

    private static Language ParseLanguage(string languageCode) => languageCode switch
    {
        "cn" => Language.Chinese,
        "de" => Language.German,
        "es" => Language.Spanish,
        "esmx" => Language.SpanishLatinAmerica,
        "fr" => Language.French,
        "it" => Language.Italian,
        "ja" => Language.Japanese,
        "pl" => Language.Polish,
        "ptbr" => Language.BrazilianPortuguese,
        _ => Language.English,
    };
}
