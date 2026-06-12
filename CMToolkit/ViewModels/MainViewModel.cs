using CMToolkit.Core.Constants;
using CMToolkit.Services;
using CommunityToolkit.Mvvm.Input;

namespace CMToolkit.ViewModels;

public partial class MainViewModel : BaseViewModel
{
    private readonly NavigationService _navigationService;

    public MainViewModel(NavigationService navigationService)
    {
        _navigationService = navigationService;
        Title = AppInfo.WindowTitle;
        UpdateBannerVisible = false;
    }

    public string WindowTitle => AppInfo.WindowTitle;

    [ObservableProperty]
    public partial bool UpdateBannerVisible { get; set; }

    [ObservableProperty]
    public partial string UpdateBannerMessage { get; set; } = "An update is available:";

    [RelayCommand]
    private async Task SelectTabAsync(ShellTab tab) => await _navigationService.NavigateAsync(tab);
}
