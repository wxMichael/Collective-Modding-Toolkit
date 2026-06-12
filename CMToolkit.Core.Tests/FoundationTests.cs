using System.Text;
using CMToolkit.Core.Constants;
using CMToolkit.Core.Enums;
using CMToolkit.Core.Models;
using CMToolkit.Core.Utilities;

namespace CMToolkit.Core.Tests;

public class FoundationTests
{
    [Fact]
    public void VersionTables_ClassifyKnownFallout4Versions()
    {
        Assert.Equal(InstallType.OG, VersionTables.Classify("Fallout4.exe", "1.10.163.0"));
        Assert.Equal(InstallType.NG, VersionTables.Classify("Fallout4.exe", "1.10.984.0"));
        Assert.Equal(InstallType.AE, VersionTables.Classify("Fallout4.exe", "1.11.191.0"));
        Assert.Equal(InstallType.Obsolete, VersionTables.Classify("Fallout4.exe", "1.10.980.0"));
        Assert.Equal(InstallType.Unknown, VersionTables.Classify("Fallout4.exe", "9.9.9.9"));
    }

    [Fact]
    public async Task Crc32Hasher_ComputesUppercaseChecksumAndCanSkipBa2Header()
    {
        var tempFile = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}.bin");
        await File.WriteAllBytesAsync(tempFile, Encoding.ASCII.GetBytes("123456789"));

        try
        {
            Assert.Equal("CBF43926", await Crc32Hasher.ComputeAsync(tempFile));
        }
        finally
        {
            File.Delete(tempFile);
        }

        var ba2File = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}.ba2");
        await File.WriteAllBytesAsync(
            ba2File,
            [.. Encoding.ASCII.GetBytes("BTDX"), 1, 0, 0, 0, .. Encoding.ASCII.GetBytes("GNRL123456789")]);

        try
        {
            Assert.Equal("CBF43926", await Crc32Hasher.ComputeAsync(ba2File, skipBa2Header: true));
        }
        finally
        {
            File.Delete(ba2File);
        }
    }

    [Fact]
    public void Ba2HeaderParser_ReadsFormatAndVersion()
    {
        byte[] header = [.. Encoding.ASCII.GetBytes("BTDX"), 8, 0, 0, 0, .. Encoding.ASCII.GetBytes("DX10")];

        var result = Ba2HeaderParser.Parse(header);

        Assert.Equal(ArchiveVersion.NG, result.Version);
        Assert.Equal(ArchiveFormat.DX10, result.Format);
        Assert.False(result.IsUnreadable);
    }

    [Fact]
    public void ModuleHeaderParser_ReadsHedrAndLightFlag()
    {
        var header = new byte[34];
        Encoding.ASCII.GetBytes("TES4").CopyTo(header, 0);
        BitConverter.GetBytes((uint)ModuleFlag.Light).CopyTo(header, 8);
        Encoding.ASCII.GetBytes("HEDR").CopyTo(header, 24);
        VersionTables.ModuleVersion95.CopyTo(header, 30);

        var result = ModuleHeaderParser.Parse(header);

        Assert.Equal(ModuleHedrVersion.Version095, result.HedrVersion);
        Assert.True(result.IsLight);
    }

    [Fact]
    public void PathHelper_RecognizesFallout4Directory()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempDir);

        try
        {
            Assert.False(PathHelper.IsFallout4Directory(tempDir));
            File.WriteAllText(Path.Combine(tempDir, "Fallout4.exe"), string.Empty);
            Assert.True(PathHelper.IsFallout4Directory(tempDir));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
