using CMToolkit.Core.Models;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Parsing;

public static class Mo2IniParser
{
    private static readonly HashSet<string> GeneralSettings = new(StringComparer.OrdinalIgnoreCase)
    {
        "gameName",
        "gamePath",
        "selected_profile",
    };

    private static readonly HashSet<string> Settings = new(StringComparer.OrdinalIgnoreCase)
    {
        "base_directory",
        "cache_directory",
        "download_directory",
        "mod_directory",
        "overwrite_directory",
        "profile_local_inis",
        "profile_local_saves",
        "profiles_directory",
        "skip_file_suffixes",
        "skip_directories",
    };

    public static async Task<ModManagerInfo> ParseAsync(string iniPath, CancellationToken cancellationToken = default)
    {
        var values = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["base_directory"] = Path.GetDirectoryName(iniPath) ?? Environment.CurrentDirectory,
            ["cache_directory"] = "%BASE_DIR%/webcache",
            ["download_directory"] = "%BASE_DIR%/downloads",
            ["mod_directory"] = "%BASE_DIR%/mods",
            ["overwrite_directory"] = "%BASE_DIR%/overwrite",
            ["profile_local_inis"] = false,
            ["profile_local_saves"] = false,
            ["profiles_directory"] = "%BASE_DIR%/profiles",
            ["skip_file_suffixes"] = ".mohidden",
            ["skip_directories"] = string.Empty,
        };

        var info = new ModManagerInfo
        {
            Name = "Mod Organizer",
            ExePath = string.Empty,
            IniPath = iniPath,
        };

        string? section = null;
        foreach (var rawLine in await File.ReadAllLinesAsync(iniPath, cancellationToken))
        {
            var line = rawLine.Trim();
            if (line.Length == 0)
            {
                continue;
            }

            if (line.StartsWith('['))
            {
                section = line;
                continue;
            }

            var separator = line.IndexOf('=');
            if (separator < 0 || section is null)
            {
                continue;
            }

            var setting = line[..separator];
            var value = UnwrapByteArray(line[(separator + 1)..]);

            if (IsSection(section, "customExecutables"))
            {
                CaptureExecutable(info, setting, value);
                continue;
            }

            string? canonicalKey = null;
            if (IsSection(section, "General"))
            {
                canonicalKey = GetCanonicalKey(GeneralSettings, setting);
            }
            else if (IsSection(section, "Settings"))
            {
                canonicalKey = GetCanonicalKey(Settings, setting);
            }

            if (canonicalKey is not null)
            {
                values[canonicalKey] = canonicalKey is "profile_local_inis" or "profile_local_saves"
                    ? bool.TryParse(value, out var parsed) && parsed
                    : value;
            }
        }

        var gameName = values.TryGetValue("gameName", out var rawGameName) ? rawGameName as string : "Fallout 4";
        if (gameName != "Fallout 4")
        {
            throw new InvalidDataException($"Only Fallout 4 is supported. gameName is '{gameName}' in INI: {iniPath}");
        }

        if (!values.TryGetValue("selected_profile", out var selectedProfile) || selectedProfile is not string profile)
        {
            throw new InvalidDataException("Profile is not set in ModOrganizer.ini.");
        }

        ResolvePaths(values);

        info.GamePath = values.TryGetValue("gamePath", out var gamePath) ? gamePath as string : null;
        info.SelectedProfile = profile;
        info.StagePath = (string)values["mod_directory"]!;
        info.OverwritePath = (string)values["overwrite_directory"]!;
        info.ProfilesPath = (string)values["profiles_directory"]!;
        info.SkipFileSuffixes = ParseCsv((string)values["skip_file_suffixes"]!)
            .Select(value => value.ToLowerInvariant())
            .ToArray();
        info.SkipDirectories = ParseCsv((string)values["skip_directories"]!)
            .Select(value => value.ToLowerInvariant())
            .Where(value => value.Length > 0)
            .ToArray();

        foreach (var pair in values)
        {
            info.SettingsDump[pair.Key] = pair.Value;
        }

        return info;
    }

    private static bool IsSection(string? section, string name) =>
        string.Equals(section, $"[{name}]", StringComparison.OrdinalIgnoreCase);

    private static string? GetCanonicalKey(IEnumerable<string> knownKeys, string key)
    {
        foreach (var known in knownKeys)
        {
            if (known.Equals(key, StringComparison.OrdinalIgnoreCase))
            {
                return known;
            }
        }

        return null;
    }

    private static string UnwrapByteArray(string value) =>
        value.StartsWith("@ByteArray(", StringComparison.Ordinal) && value.EndsWith(')')
            ? value[11..^1]
            : value;

    private static void ResolvePaths(Dictionary<string, object?> values)
    {
        var baseDirectory = (string)values["base_directory"]!;

        foreach (var key in values.Keys.ToArray())
        {
            if (key == "base_directory" || !key.EndsWith("directory", StringComparison.Ordinal) && !key.EndsWith("Path", StringComparison.Ordinal))
            {
                continue;
            }

            if (values[key] is not string path)
            {
                continue;
            }

            values[key] = path.Contains("%BASE_DIR%", StringComparison.OrdinalIgnoreCase)
                ? Path.Combine(baseDirectory, path.Replace("%BASE_DIR%", string.Empty, StringComparison.OrdinalIgnoreCase).TrimStart('/', '\\'))
                : path;
        }
    }

    private static IReadOnlyList<string> ParseCsv(string value)
    {
        var values = new List<string>();
        var current = new List<char>();
        var escaped = false;

        foreach (var ch in value)
        {
            if (escaped)
            {
                current.Add(ch);
                escaped = false;
                continue;
            }

            if (ch == '\\')
            {
                escaped = true;
                continue;
            }

            if (ch == ',')
            {
                values.Add(new string(current.ToArray()).Trim());
                current.Clear();
                continue;
            }

            current.Add(ch);
        }

        values.Add(new string(current.ToArray()).Trim());
        return values;
    }

    private static void CaptureExecutable(ModManagerInfo info, string setting, string value)
    {
        if (!setting.EndsWith("binary", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        var fileName = Path.GetFileName(value);
        if (fileName.Equals("xedit.exe", StringComparison.OrdinalIgnoreCase) ||
            fileName.Equals("fo4edit.exe", StringComparison.OrdinalIgnoreCase))
        {
            AddExecutable(info, "xEdit", value);
            var bsarchPath = Path.Combine(Path.GetDirectoryName(value) ?? string.Empty, "BSArch.exe");
            if (PathHelper.FileExists(bsarchPath))
            {
                AddExecutable(info, "BSArch", bsarchPath);
            }
        }
        else if (fileName.Equals("bsarch.exe", StringComparison.OrdinalIgnoreCase))
        {
            AddExecutable(info, "BSArch", value);
        }
    }

    private static void AddExecutable(ModManagerInfo info, string key, string path)
    {
        if (!PathHelper.FileExists(path))
        {
            return;
        }

        if (!info.Executables.TryGetValue(key, out var paths))
        {
            paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            info.Executables[key] = paths;
        }

        paths.Add(path);
    }
}
