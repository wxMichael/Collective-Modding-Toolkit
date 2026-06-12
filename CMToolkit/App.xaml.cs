using CMToolkit.Core.Constants;
using CMToolkit.Core.Logging;
using CMToolkit.Core.Services;
using CMToolkit.Core.Settings;
using CMToolkit.Core.Utilities;
using CMToolkit.Services;
using CMToolkit.ViewModels;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace CMToolkit;

public partial class App : Application
{
    private Window? _window;
    private ServiceProvider? _services;

    public App()
    {
        InitializeComponent();
        UnhandledException += OnUnhandledException;
    }

    public static ServiceProvider Services =>
        ((App)Current)._services ?? throw new InvalidOperationException("Services not initialized.");

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _services = ConfigureServices();
        var logger = _services.GetRequiredService<ILogger<App>>();
        var startMessage = $"Starting {AppInfo.Title} v{AppInfo.Version}";
        logger.LogInformation(new string('-', startMessage.Length));
        logger.LogInformation("{Message}", startMessage);
        logger.LogInformation("{Timestamp}", DateTime.Now.ToString("yyyy-MM-dd HH:mm"));

        _window = _services.GetRequiredService<MainWindow>();
        _window.Activate();
    }

    private static ServiceProvider ConfigureServices()
    {
        var bootstrapLogger = NullLogger<SettingsStore>.Instance;
        var settingsStore = new SettingsStore(bootstrapLogger);

        var services = new ServiceCollection();
        services.AddSingleton(settingsStore);

        services.AddLogging(builder =>
        {
            builder.AddCmtFileLogging();
            builder.SetMinimumLevel(CmtLoggingExtensions.ToCmtLogLevel(settingsStore.Current.LogLevel));
        });

        services.AddSingleton<IAppState, AppState>();
        services.AddSingleton<IPathService, PathService>();
        services.AddSingleton<IRegistryReader, RegistryReader>();
        services.AddSingleton<IProcessWalker, ProcessWalker>();
        services.AddSingleton<IPeVersionReader, PeVersionReader>();
        services.AddSingleton<IGamePathPrompt, NullGamePathPrompt>();
        services.AddSingleton<GameIniLoader>();
        services.AddSingleton<IModManagerDetector, ModManagerDetector>();
        services.AddSingleton<IGameDetector, GameDetector>();
        services.AddSingleton<OverviewCensusService>();
        services.AddSingleton<NavigationService>();
        services.AddSingleton<MainViewModel>();
        services.AddSingleton<MainWindow>();

        return services.BuildServiceProvider();
    }

    private void OnUnhandledException(object sender, Microsoft.UI.Xaml.UnhandledExceptionEventArgs e)
    {
        if (_services?.GetService<ILogger<App>>() is ILogger logger)
        {
            logger.LogError(e.Exception, "Unhandled application exception.");
        }

        e.Handled = true;
    }
}
