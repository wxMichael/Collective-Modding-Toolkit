using System.Diagnostics;

namespace CMToolkit.Core.Utilities;

public interface IPeVersionReader
{
    string? GetVersion(string filePath);
}

public sealed class PeVersionReader : IPeVersionReader
{
    public string? GetVersion(string filePath)
    {
        try
        {
            var info = FileVersionInfo.GetVersionInfo(filePath);
            if (info is { FileMajorPart: 0, FileMinorPart: 0, FileBuildPart: 0, FilePrivatePart: 0 })
            {
                return null;
            }

            return $"{info.FileMajorPart}.{info.FileMinorPart}.{info.FileBuildPart}.{info.FilePrivatePart}";
        }
        catch
        {
            return null;
        }
    }
}
