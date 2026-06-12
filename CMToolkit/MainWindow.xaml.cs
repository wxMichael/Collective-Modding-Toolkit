using CMToolkit.Services;
using CMToolkit.ViewModels;
using Microsoft.UI.Windowing;

namespace CMToolkit;

public sealed partial class MainWindow : Window
{
    private readonly NavigationService _navigationService;
    private bool _isNavigating;

    public MainWindow(MainViewModel viewModel, NavigationService navigationService)
    {
        ViewModel = viewModel;
        _navigationService = navigationService;
        InitializeComponent();

        _navigationService.ContentFrame = ContentFrame;
        ConfigureWindow();
        ShellNavigation.SelectedItem = ShellNavigation.MenuItems[0];
        _ = _navigationService.NavigateAsync(ShellTab.Overview);
    }

    public MainViewModel ViewModel { get; }

    private void ConfigureWindow()
    {
        ExtendsContentIntoTitleBar = false;
        SystemBackdrop = null;

        if (AppWindow.Presenter is OverlappedPresenter presenter)
        {
            presenter.IsResizable = false;
            presenter.IsMaximizable = false;
            presenter.SetBorderAndTitleBar(true, true);
        }

        AppWindow.Resize(new Windows.Graphics.SizeInt32(900, 560));
        CenterOnScreen();
    }

    private void CenterOnScreen()
    {
        var displayArea = DisplayArea.GetFromWindowId(AppWindow.Id, DisplayAreaFallback.Primary);
        if (displayArea is null)
        {
            return;
        }

        var workArea = displayArea.WorkArea;
        var size = AppWindow.Size;
        AppWindow.Move(new Windows.Graphics.PointInt32(
            workArea.X + ((workArea.Width - size.Width) / 2),
            workArea.Y + ((workArea.Height - size.Height) / 2)));
    }

    private async void ShellNavigation_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (_isNavigating || args.SelectedItem is not NavigationViewItem item || item.Tag is not string tag)
        {
            return;
        }

        if (!TryParseTab(tag, out var tab))
        {
            return;
        }

        _isNavigating = true;
        try
        {
            await _navigationService.NavigateAsync(tab);
        }
        finally
        {
            _isNavigating = false;
        }
    }

    private static bool TryParseTab(string tag, out ShellTab tab)
    {
        tab = tag switch
        {
            "Overview" => ShellTab.Overview,
            "F4SE" => ShellTab.F4se,
            "Scanner" => ShellTab.Scanner,
            "Tools" => ShellTab.Tools,
            "Settings" => ShellTab.Settings,
            "About" => ShellTab.About,
            _ => default,
        };

        return tag is "Overview" or "F4SE" or "Scanner" or "Tools" or "Settings" or "About";
    }
}
