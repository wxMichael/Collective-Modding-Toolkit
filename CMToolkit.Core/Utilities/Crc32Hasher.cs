using System.IO.Hashing;

namespace CMToolkit.Core.Utilities;

public static class Crc32Hasher
{
    public static async Task<string> ComputeAsync(
        string filePath,
        int chunkSize = 65536,
        int? maxChunks = null,
        bool skipBa2Header = false,
        CancellationToken cancellationToken = default)
    {
        await using var stream = File.OpenRead(filePath);
        if (skipBa2Header)
        {
            stream.Seek(12, SeekOrigin.Begin);
        }

        var crc = new Crc32();
        var buffer = new byte[chunkSize];
        var chunks = 0;

        while (true)
        {
            var read = await stream.ReadAsync(buffer.AsMemory(0, buffer.Length), cancellationToken);
            if (read == 0)
            {
                break;
            }

            crc.Append(buffer.AsSpan(0, read));

            if (maxChunks is not null && ++chunks >= maxChunks.Value)
            {
                break;
            }
        }

        return crc.GetCurrentHashAsUInt32().ToString("X8");
    }
}
