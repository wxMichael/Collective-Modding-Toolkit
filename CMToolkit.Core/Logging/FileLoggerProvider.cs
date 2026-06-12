using Microsoft.Extensions.Logging;

namespace CMToolkit.Core.Logging;

public sealed class FileLoggerProvider : ILoggerProvider
{
    private readonly string _logPath;
    private readonly object _lock = new();

    public FileLoggerProvider(string? logPath = null)
    {
        _logPath = logPath ?? Path.Combine(Environment.CurrentDirectory, "cm-toolkit.log");
    }

    public ILogger CreateLogger(string categoryName) => new FileLogger(categoryName, _logPath, _lock);

    public void Dispose()
    {
    }

    private sealed class FileLogger(string categoryName, string logPath, object sync) : ILogger
    {
        private readonly string _categoryName = categoryName;
        public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;

        public bool IsEnabled(LogLevel logLevel) => logLevel != LogLevel.None;

        public void Log<TState>(
            LogLevel logLevel,
            EventId eventId,
            TState state,
            Exception? exception,
            Func<TState, Exception?, string> formatter)
        {
            if (!IsEnabled(logLevel))
            {
                return;
            }

            var message = formatter(state, exception);
            var line = $"{logLevel.ToString().ToUpperInvariant()} : {message}";
            if (exception is not null)
            {
                line += Environment.NewLine + exception;
            }

            lock (sync)
            {
                File.AppendAllText(logPath, line + Environment.NewLine);
            }
        }
    }
}

public static class CmtLoggingExtensions
{
    public static ILoggingBuilder AddCmtFileLogging(this ILoggingBuilder builder, string? logPath = null)
    {
        builder.AddProvider(new FileLoggerProvider(logPath));
        return builder;
    }

    public static LogLevel ToCmtLogLevel(string? setting) => setting?.ToUpperInvariant() switch
    {
        "DEBUG" => LogLevel.Debug,
        "INFO" => LogLevel.Information,
        "WARNING" => LogLevel.Warning,
        "ERROR" => LogLevel.Error,
        _ => LogLevel.Information,
    };
}
