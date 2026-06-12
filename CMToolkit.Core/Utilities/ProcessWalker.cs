using System.Diagnostics;
using System.Runtime.InteropServices;

namespace CMToolkit.Core.Utilities;

public sealed record ProcessSnapshot(int ProcessId, int ParentProcessId, string Name, string? ExecutablePath);

public interface IProcessWalker
{
    IReadOnlyList<ProcessSnapshot> GetParentProcesses(int maxDepth);
}

public sealed class ProcessWalker : IProcessWalker
{
    public IReadOnlyList<ProcessSnapshot> GetParentProcesses(int maxDepth)
    {
        var parents = new List<ProcessSnapshot>();
        var pid = Environment.ProcessId;

        for (var i = 0; i < maxDepth; i++)
        {
            var parentPid = GetParentProcessId(pid);
            if (parentPid <= 0)
            {
                break;
            }

            try
            {
                using var process = Process.GetProcessById(parentPid);
                parents.Add(new ProcessSnapshot(parentPid, GetParentProcessId(parentPid), process.ProcessName + ".exe", GetExecutablePath(process)));
                pid = parentPid;
            }
            catch
            {
                break;
            }
        }

        return parents;
    }

    private static string? GetExecutablePath(Process process)
    {
        try
        {
            return process.MainModule?.FileName;
        }
        catch
        {
            return null;
        }
    }

    private static int GetParentProcessId(int processId)
    {
        if (!OperatingSystem.IsWindows())
        {
            return 0;
        }

        var handle = CreateToolhelp32Snapshot(SnapshotFlags.Process, 0);
        if (handle == IntPtr.Zero || handle == new IntPtr(-1))
        {
            return 0;
        }

        try
        {
            var entry = new ProcessEntry32 { DwSize = (uint)Marshal.SizeOf<ProcessEntry32>() };
            if (!Process32First(handle, ref entry))
            {
                return 0;
            }

            do
            {
                if (entry.Th32ProcessId == processId)
                {
                    return entry.Th32ParentProcessId;
                }
            }
            while (Process32Next(handle, ref entry));

            return 0;
        }
        finally
        {
            CloseHandle(handle);
        }
    }

    [Flags]
    private enum SnapshotFlags : uint
    {
        Process = 0x00000002,
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private struct ProcessEntry32
    {
        public uint DwSize;
        public uint CntUsage;
        public int Th32ProcessId;
        public IntPtr Th32DefaultHeapId;
        public uint Th32ModuleId;
        public uint CntThreads;
        public int Th32ParentProcessId;
        public int PcPriClassBase;
        public uint DwFlags;

        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string SzExeFile;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr CreateToolhelp32Snapshot(SnapshotFlags dwFlags, uint th32ProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool Process32First(IntPtr hSnapshot, ref ProcessEntry32 lppe);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool Process32Next(IntPtr hSnapshot, ref ProcessEntry32 lppe);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr hObject);
}
