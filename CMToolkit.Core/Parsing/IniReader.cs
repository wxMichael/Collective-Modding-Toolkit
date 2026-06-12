namespace CMToolkit.Core.Parsing;

public static class IniReader
{
    public static async Task<Dictionary<string, Dictionary<string, string>>> ReadAsync(
        string filePath,
        CancellationToken cancellationToken = default)
    {
        var result = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);
        var section = "NO-SECTION";

        foreach (var rawLine in await File.ReadAllLinesAsync(filePath, cancellationToken))
        {
            var line = rawLine.Trim();
            if (line.Length == 0 || line.StartsWith(';') || line.StartsWith('#'))
            {
                continue;
            }

            if (line.StartsWith('[') && line.EndsWith(']'))
            {
                section = line[1..^1].ToLowerInvariant();
                result.TryAdd(section, new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase));
                continue;
            }

            var separator = line.IndexOf('=');
            if (separator < 0)
            {
                continue;
            }

            if (!result.TryGetValue(section, out var sectionValues))
            {
                sectionValues = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                result[section] = sectionValues;
            }

            sectionValues[line[..separator].Trim().ToLowerInvariant()] = line[(separator + 1)..].Trim();
        }

        return result;
    }
}
