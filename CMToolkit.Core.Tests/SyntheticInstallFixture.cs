using System.Text;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;

namespace CMToolkit.Core.Tests;

public sealed class SyntheticInstallFixture : IDisposable
{
    private SyntheticInstallFixture(
        string root,
        string localApplicationData,
        GameSession session,
        IReadOnlyDictionary<string, string> binaryVersions)
    {
        Root = root;
        LocalApplicationData = localApplicationData;
        Session = session;
        BinaryVersions = binaryVersions;
    }

    public string Root { get; }

    public string LocalApplicationData { get; }

    public GameSession Session { get; }

    public IReadOnlyDictionary<string, string> BinaryVersions { get; }

    public static async Task<SyntheticInstallFixture> CreateAsync(string fixtureName)
    {
        var root = Path.Combine(Path.GetTempPath(), $"cmtoolkit-{fixtureName}-{Guid.NewGuid():N}");
        var gamePath = Path.Combine(root, "Fallout 4");
        var dataPath = Path.Combine(gamePath, "Data");
        var localAppData = Path.Combine(root, "LocalAppData");
        Directory.CreateDirectory(dataPath);
        Directory.CreateDirectory(Path.Combine(localAppData, "Fallout4"));

        var versions = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var archiveSettings = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        await File.WriteAllTextAsync(Path.Combine(gamePath, "Fallout4.exe"), string.Empty);
        await File.WriteAllTextAsync(Path.Combine(gamePath, "Fallout4.ccc"), string.Empty);
        await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Startup.ba2"), MakeBa2(1, "GNRL"));

        if (fixtureName == "og")
        {
            versions["Fallout4.exe"] = "1.10.163.0";
            await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4.esm"), MakeModule(light: false, hedr100: true));
            await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Misc.ba2"), MakeBa2(1, "GNRL"));
            await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Textures1.ba2"), MakeBa2(8, "DX10"));
            archiveSettings["sresourcearchivelist"] = "Fallout4 - Misc.ba2,Fallout4 - Textures1.ba2";
        }
        else if (fixtureName == "ng")
        {
            versions["Fallout4.exe"] = "1.10.984.0";
            await File.WriteAllBytesAsync(Path.Combine(dataPath, "TestLight.esl"), MakeModule(light: true, hedr100: false));
            await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Misc.ba2"), MakeBa2(8, "GNRL"));
            await File.WriteAllBytesAsync(Path.Combine(dataPath, "Fallout4 - Textures1.ba2"), MakeBa2(8, "DX10"));
            await File.WriteAllTextAsync(Path.Combine(localAppData, "Fallout4", "plugins.txt"), "*TestLight.esl");
            archiveSettings["sresourcearchivelist"] = "Fallout4 - Misc.ba2,Fallout4 - Textures1.ba2";
        }
        else
        {
            throw new ArgumentOutOfRangeException(nameof(fixtureName), fixtureName, "Unknown synthetic fixture.");
        }

        var session = new GameSession
        {
            GamePath = gamePath,
            DataPath = dataPath,
            IniData = new GameIniData
            {
                GameSettings = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase)
                {
                    ["archive"] = archiveSettings,
                },
            },
        };

        return new SyntheticInstallFixture(root, localAppData, session, versions);
    }

    public void Dispose()
    {
        if (Directory.Exists(Root))
        {
            Directory.Delete(Root, recursive: true);
        }
    }

    private static byte[] MakeBa2(byte version, string format) =>
        [.. Encoding.ASCII.GetBytes("BTDX"), version, 0, 0, 0, .. Encoding.ASCII.GetBytes(format), .. Encoding.ASCII.GetBytes("fixture")];

    private static byte[] MakeModule(bool light, bool hedr100)
    {
        var bytes = new byte[34];
        Encoding.ASCII.GetBytes("TES4").CopyTo(bytes, 0);
        BitConverter.GetBytes(light ? (uint)ModuleFlag.Light : 0).CopyTo(bytes, 8);
        Encoding.ASCII.GetBytes("HEDR").CopyTo(bytes, 24);
        (hedr100 ? [0x00, 0x00, 0x80, 0x3f] : new byte[] { 0x33, 0x33, 0x73, 0x3f }).CopyTo(bytes, 30);
        return bytes;
    }
}
