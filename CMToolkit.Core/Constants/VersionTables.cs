using CMToolkit.Core.Enums;

namespace CMToolkit.Core.Constants;

public static class VersionTables
{
    public const int MaxArchivesGeneral = 256;
    public const int MaxArchivesTexture = 255;
    public const int MaxModulesFull = 254;
    public const int MaxModulesLight = 4096;
    public const string NextGenStartupBa2Crc = "A5808F5F";

    public static readonly byte[] ModuleVersion95 = [0x33, 0x33, 0x73, 0x3f];
    public static readonly byte[] ModuleVersion1 = [0x00, 0x00, 0x80, 0x3f];

    public static readonly IReadOnlyList<string> GameMasters =
    [
        "fallout4.esm",
        "fallout4_vr.esm",
        "dlcrobot.esm",
        "dlcworkshop01.esm",
        "dlcworkshop02.esm",
        "dlcworkshop03.esm",
        "dlccoast.esm",
        "dlcnukaworld.esm",
        "dlcultrahighresolution.esm",
    ];

    public static readonly IReadOnlyDictionary<string, IReadOnlyDictionary<string, InstallType>> BaseFiles =
        new Dictionary<string, IReadOnlyDictionary<string, InstallType>>(StringComparer.OrdinalIgnoreCase)
        {
            ["Fallout4.exe"] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["1.10.120.0"] = InstallType.Obsolete,
                ["1.10.130.0"] = InstallType.Obsolete,
                ["1.10.138.0"] = InstallType.Obsolete,
                ["1.10.162.0"] = InstallType.Obsolete,
                ["1.10.163.0"] = InstallType.OG,
                ["1.10.980.0"] = InstallType.Obsolete,
                ["1.10.984.0"] = InstallType.NG,
                ["1.11.137.0"] = InstallType.Obsolete,
                ["1.11.159.0"] = InstallType.Obsolete,
                ["1.11.169.0"] = InstallType.Obsolete,
                ["1.11.191.0"] = InstallType.AE,
            },
            ["Fallout4Launcher.exe"] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["02445570"] = InstallType.OG,
                ["F6A06FF5"] = InstallType.NG,
                ["0E696744"] = InstallType.Obsolete,
                ["D15C6A49"] = InstallType.Obsolete,
                ["8C52BE93"] = InstallType.Obsolete,
                ["591009C9"] = InstallType.Obsolete,
                ["720BB9C3"] = InstallType.AE,
            },
            ["steam_api64.dll"] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["2.89.45.4"] = InstallType.OG,
                ["7.40.51.27"] = InstallType.NGAE,
                ["BD3AA35F"] = InstallType.OG,
            },
            ["f4se_loader.exe"] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["0.0.6.23"] = InstallType.OG,
                ["0.0.7.2"] = InstallType.NG,
                ["0.0.7.4"] = InstallType.Obsolete,
                ["0.0.7.5"] = InstallType.Obsolete,
                ["0.0.7.6"] = InstallType.Obsolete,
                ["0.0.7.7"] = InstallType.AE,
            },
            ["f4se_steam_loader.dll"] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["0.0.6.23"] = InstallType.OG,
            },
            ["CreationKit.exe"] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["1.10.162.0"] = InstallType.OG,
                ["1.10.943.1"] = InstallType.Obsolete,
                ["1.10.982.3"] = InstallType.NG,
                ["1.11.137.0"] = InstallType.AE,
            },
            [Path.Combine("Tools", "Archive2", "Archive2.exe")] = new Dictionary<string, InstallType>(StringComparer.OrdinalIgnoreCase)
            {
                ["4CDFC7B5"] = InstallType.OG,
                ["71A5240B"] = InstallType.NG,
                ["C867674F"] = InstallType.AE,
            },
        };

    public static InstallType Classify(string fileName, string versionOrCrc)
    {
        if (!BaseFiles.TryGetValue(fileName, out var values))
        {
            return InstallType.Unknown;
        }

        return values.GetValueOrDefault(versionOrCrc, InstallType.Unknown);
    }
}
