namespace CMToolkit.Core.Enums;

public enum InstallType
{
    Obsolete,
    OG,
    DG,
    NG,
    AE,
    NGAE,
    Unknown,
    NotFound,
}

public enum ArchiveVersion
{
    OG = 1,
    NG7 = 7,
    NG = 8,
}

public enum ArchiveFormat
{
    Unknown,
    GNRL,
    DX10,
}

[Flags]
public enum ModuleFlag : uint
{
    Light = 0x0200,
}

public enum ModuleHedrVersion
{
    Version095,
    Version100,
    Unknown,
}

public enum ProblemType
{
    FileNotFound,
    InvalidArchive,
    InvalidModule,
    WrongVersion,
    NoModManager,
    UnknownGameVersion,
    LimitExceeded,
}

public enum SolutionType
{
    None,
    VerifyFiles,
    DownloadMod,
}

public enum Language
{
    Chinese,
    German,
    English,
    Spanish,
    SpanishLatinAmerica,
    French,
    Italian,
    Japanese,
    Polish,
    BrazilianPortuguese,
}

public static class InstallTypeExtensions
{
    public static string ToDisplayString(this InstallType installType) => installType switch
    {
        InstallType.Obsolete => "Obsolete",
        InstallType.OG => "Old-Gen",
        InstallType.DG => "Down-Grade",
        InstallType.NG => "Next-Gen",
        InstallType.AE => "Anniversary",
        InstallType.NGAE => "Next-Gen & Anniversary",
        InstallType.Unknown => "Unknown",
        InstallType.NotFound => "Not Found",
        _ => installType.ToString(),
    };
}
