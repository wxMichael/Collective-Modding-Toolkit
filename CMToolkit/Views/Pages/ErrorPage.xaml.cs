namespace CMToolkit.Views.Pages;

public sealed partial class ErrorPage : Page
{
    public ErrorPage(string message)
    {
        Message = message;
        InitializeComponent();
    }

    public string Message { get; }
}
