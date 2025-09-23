param(
  [string]$SchemaPath = "schema.yml",
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$OperationsFile = "operations.txt",
  [int]$MaxExamples = 5,
  [int]$Workers = 1,
  [string]$AuthToken = ""
)

$ErrorActionPreference = "Stop"

Write-Host "Schemathesis Simple Runner"
Write-Host "Schema: $SchemaPath"
Write-Host "Base URL: $BaseUrl"
Write-Host "Operations: $OperationsFile"

# Check if files exist
if (-not (Test-Path $SchemaPath)) {
  Write-Error "Schema file not found: $SchemaPath"
  exit 1
}

if (-not (Test-Path $OperationsFile)) {
  Write-Host "Generating operations file..."
  python tools\list_operation_ids.py --out $OperationsFile
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate operations file"
    exit 2
  }
}

# Activate venv if available
if (Test-Path ".venv\Scripts\Activate.ps1") {
  Write-Host "Activating virtual environment..."
  . .venv\Scripts\Activate.ps1
}

# Check schemathesis availability
$schemathesisCmd = Get-Command schemathesis -ErrorAction SilentlyContinue
if ($schemathesisCmd) {
  $cmd = "schemathesis"
  $args = @("run")
} else {
  $cmd = "python"
  $args = @("-m", "schemathesis.cli", "run")
}

# Add common arguments
$args += @(
  "--max-examples", $MaxExamples.ToString(),
  "--workers", $Workers.ToString(),
  "--url", $BaseUrl
)

# Add schema file
$args += $SchemaPath

if ($AuthToken -and $AuthToken.Trim().Length -gt 0) {
  $args = @()
  if ($schemathesisCmd) { $args += @("run") } else { $args += @("-m", "schemathesis.cli", "run") }
  $args += @(
    "--max-examples", $MaxExamples.ToString(),
    "--workers", $Workers.ToString(),
    "--header", "Authorization: Bearer $AuthToken",
    "--url", $BaseUrl,
    $SchemaPath
  )
}

Write-Host "Running: $cmd $($args -join ' ')"

# Execute
& $cmd $args

if ($LASTEXITCODE -eq 0) {
  Write-Host "Schemathesis completed successfully"
  exit 0
} else {
  Write-Error "Schemathesis failed with exit code $LASTEXITCODE"
  exit $LASTEXITCODE
}
