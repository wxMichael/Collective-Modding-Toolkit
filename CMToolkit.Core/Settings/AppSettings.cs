namespace CMToolkit.Core.Settings;

public sealed class AppSettings
{
    public string LogLevel { get; set; } = "INFO";

    public string UpdateSource { get; set; } = "nexus";

    public bool ScannerOverviewIssues { get; set; } = true;

    public bool ScannerErrors { get; set; } = true;

    public bool ScannerWrongFormat { get; set; } = true;

    public bool ScannerLoosePrevis { get; set; } = true;

    public bool ScannerJunkFiles { get; set; } = true;

    public bool ScannerProblemOverrides { get; set; } = true;

    public bool ScannerRaceSubgraphs { get; set; } = true;

    public bool DowngraderKeepBackups { get; set; } = true;

    public bool DowngraderDeleteDeltas { get; set; } = true;
}
