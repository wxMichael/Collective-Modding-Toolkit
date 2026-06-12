using Microsoft.Win32;

namespace CMToolkit.Core.Utilities;

public enum RegistryRoot
{
    CurrentUser,
    LocalMachine,
}

public interface IRegistryReader
{
    string? GetValue(RegistryRoot root, string subkey, string valueName);
}

public sealed class RegistryReader : IRegistryReader
{
    public string? GetValue(RegistryRoot root, string subkey, string valueName)
    {
        if (!OperatingSystem.IsWindows())
        {
            return null;
        }

        try
        {
            var hive = root == RegistryRoot.CurrentUser
                ? RegistryHive.CurrentUser
                : RegistryHive.LocalMachine;
            using var baseKey = RegistryKey.OpenBaseKey(hive, RegistryView.Default);
            using var key = baseKey.OpenSubKey(subkey);
            return key?.GetValue(valueName) as string;
        }
        catch
        {
            return null;
        }
    }
}
