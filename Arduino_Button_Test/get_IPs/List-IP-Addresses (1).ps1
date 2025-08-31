
# Show all IPv4 and IPv6 addresses on all adapters in Windows 11
Get-NetIPAddress |
  Select-Object InterfaceAlias, AddressFamily, IPAddress |
  Format-Table -AutoSize

# Keep the window open so user can read output when double-clicked
Write-Host "`nPress any key to exit..."
$x = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
