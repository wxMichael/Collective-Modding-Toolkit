using CMToolkit.Core.Parsing;

namespace CMToolkit.Core.Tests;

public class ParsingTests
{
    [Fact]
    public async Task IniReader_ParsesSectionsAndLowercasesKeys()
    {
        var file = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}.ini");
        await File.WriteAllTextAsync(
            file,
            """
            [Archive]
            sResourceArchiveList=Fallout4 - Misc.ba2
            [General]
            sLanguage=en
            """);

        try
        {
            var parsed = await IniReader.ReadAsync(file);

            Assert.Equal("Fallout4 - Misc.ba2", parsed["archive"]["sresourcearchivelist"]);
            Assert.Equal("en", parsed["general"]["slanguage"]);
        }
        finally
        {
            File.Delete(file);
        }
    }

    [Fact]
    public async Task Mo2IniParser_ParsesSectionsAndKeysCaseInsensitively()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var baseDir = Path.Combine(root, "base");
        var gameDir = Path.Combine(root, "Fallout 4");
        Directory.CreateDirectory(baseDir);
        Directory.CreateDirectory(gameDir);

        var iniPath = Path.Combine(root, "ModOrganizer.ini");
        await File.WriteAllTextAsync(
            iniPath,
            $$"""
            [general]
            GameName=Fallout 4
            GAMEPATH={{gameDir}}
            Selected_Profile=@ByteArray(CaseProfile)

            [settings]
            BASE_DIRECTORY={{baseDir}}
            Mod_Directory=%BASE_DIR%/mods
            """);

        try
        {
            var parsed = await Mo2IniParser.ParseAsync(iniPath);

            Assert.Equal(gameDir, parsed.GamePath);
            Assert.Equal("CaseProfile", parsed.SelectedProfile);
            Assert.Equal(Path.Combine(baseDir, "mods"), parsed.StagePath);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public async Task Mo2IniParser_ResolvesBaseDirByteArraySkipsAndExecutables()
    {
        var root = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        var baseDir = Path.Combine(root, "base");
        var gameDir = Path.Combine(root, "Fallout 4");
        var toolsDir = Path.Combine(root, "tools");
        Directory.CreateDirectory(baseDir);
        Directory.CreateDirectory(gameDir);
        Directory.CreateDirectory(toolsDir);
        await File.WriteAllTextAsync(Path.Combine(toolsDir, "FO4Edit.exe"), string.Empty);
        await File.WriteAllTextAsync(Path.Combine(toolsDir, "BSArch.exe"), string.Empty);

        var iniPath = Path.Combine(root, "ModOrganizer.ini");
        await File.WriteAllTextAsync(
            iniPath,
            $$"""
            [General]
            gameName=Fallout 4
            gamePath={{gameDir}}
            selected_profile=@ByteArray(Default)

            [Settings]
            base_directory={{baseDir}}
            mod_directory=%BASE_DIR%/mods
            overwrite_directory=%BASE_DIR%/overwrite
            profiles_directory=%BASE_DIR%/profiles
            skip_file_suffixes=.mohidden,.bak
            skip_directories=cache, overwrite

            [customExecutables]
            1\binary={{Path.Combine(toolsDir, "FO4Edit.exe")}}
            """);

        try
        {
            var parsed = await Mo2IniParser.ParseAsync(iniPath);

            Assert.Equal(gameDir, parsed.GamePath);
            Assert.Equal("Default", parsed.SelectedProfile);
            Assert.Equal(Path.Combine(baseDir, "mods"), parsed.StagePath);
            Assert.Equal(Path.Combine(baseDir, "overwrite"), parsed.OverwritePath);
            Assert.Equal(Path.Combine(baseDir, "profiles"), parsed.ProfilesPath);
            Assert.Equal([".mohidden", ".bak"], parsed.SkipFileSuffixes);
            Assert.Equal(["cache", "overwrite"], parsed.SkipDirectories);
            Assert.Contains(parsed.Executables["xEdit"], path => path.EndsWith("FO4Edit.exe", StringComparison.OrdinalIgnoreCase));
            Assert.Contains(parsed.Executables["BSArch"], path => path.EndsWith("BSArch.exe", StringComparison.OrdinalIgnoreCase));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
