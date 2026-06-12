namespace CMToolkit.Core.Utilities;

public interface IPathService
{
    string CurrentDirectory { get; }

    string LocalApplicationData { get; }

    string Documents { get; }

    bool FileExists(string path);

    bool DirectoryExists(string path);
}

public sealed class PathService : IPathService
{
    public string CurrentDirectory => Environment.CurrentDirectory;

    public string LocalApplicationData =>
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);

    public string Documents =>
        Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);

    public bool FileExists(string path) => PathHelper.FileExists(path);

    public bool DirectoryExists(string path) => PathHelper.DirectoryExists(path);
}

public static class PathHelper
{
    public static bool FileExists(string path)
    {
        try
        {
            return File.Exists(path);
        }
        catch
        {
            return false;
        }
    }

    public static bool DirectoryExists(string path)
    {
        try
        {
            return Directory.Exists(path);
        }
        catch
        {
            return false;
        }
    }

    public static bool IsFallout4Directory(string path) =>
        DirectoryExists(path) && FileExists(Path.Combine(path, "Fallout4.exe"));
}
