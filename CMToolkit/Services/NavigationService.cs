namespace CMToolkit.Services;

public enum ShellTab
{
    Overview,
    F4se,
    Scanner,
    Tools,
    Settings,
    About,
}

public sealed class NavigationService
{
    private readonly Dictionary<ShellTab, Type> _pageTypes = new()
    {
        [ShellTab.Overview] = typeof(Views.Pages.OverviewPage),
        [ShellTab.F4se] = typeof(Views.Pages.F4sePage),
        [ShellTab.Scanner] = typeof(Views.Pages.ScannerPage),
        [ShellTab.Tools] = typeof(Views.Pages.ToolsPage),
        [ShellTab.Settings] = typeof(Views.Pages.SettingsPage),
        [ShellTab.About] = typeof(Views.Pages.AboutPage),
    };

    private readonly HashSet<ShellTab> _loadedTabs = [];

    public Frame? ContentFrame { get; set; }

    public bool IsLoaded(ShellTab tab) => _loadedTabs.Contains(tab);

    public async Task NavigateAsync(ShellTab tab)
    {
        if (ContentFrame is null)
        {
            return;
        }

        if (!_loadedTabs.Contains(tab))
        {
            ContentFrame.Content = new Views.Pages.LoadingPage();
            await Task.Yield();

            try
            {
                ContentFrame.Navigate(_pageTypes[tab]);
                _loadedTabs.Add(tab);
            }
            catch (Exception ex)
            {
                ContentFrame.Content = new Views.Pages.ErrorPage(ex.Message);
            }

            return;
        }

        ContentFrame.Navigate(_pageTypes[tab]);
    }
}
