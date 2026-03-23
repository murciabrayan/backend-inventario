$envFile = Join-Path $PSScriptRoot ".env"

Get-Content $envFile | ForEach-Object {
  if (-not $_ -or $_.StartsWith("#")) {
    return
  }

  $parts = $_ -split "=", 2
  if ($parts.Length -eq 2) {
    [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
  }
}

$python = 'C:\Program Files\PostgreSQL\17\pgAdmin 4\python\python.exe'
$packages = Join-Path $PSScriptRoot "packages"
$manage = Join-Path $PSScriptRoot "manage.py"
$projectRoot = $PSScriptRoot

& $python -c "import runpy, sys; sys.path.insert(0, r'$packages'); sys.path.insert(0, r'$projectRoot'); sys.argv=['manage.py', 'migrate']; runpy.run_path(r'$manage', run_name='__main__')"
