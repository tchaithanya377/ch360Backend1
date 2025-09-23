param(
  [string]$SchemaPath = "$PSScriptRoot/../schema.yml",
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$OperationsFile = "$PSScriptRoot/../operations.txt",
  [int]$MaxExamples = 5,
  [int]$Workers = 1,
  [int]$MaxOpsPerRun = 20,
  [string]$AuthToken = ""
)

$ErrorActionPreference = "Stop"

function Resolve-PathStrict([string]$p) {
  $full = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $p))
  if (-not (Test-Path $full)) { 
    throw "Path not found: $full" 
  }
  return $full
}

function Get-OperationEntries {
  if (-not (Test-Path $OperationsFile)) { 
    return $null 
  }
  
  $lines = Get-Content $OperationsFile -ErrorAction SilentlyContinue
  if (-not $lines) { 
    return $null 
  }
  
  $entries = @()
  foreach ($line in $lines) {
    if ($line -match '^(.+?)\s+->\s+([A-Z]+)\s+(.+)$') {
      $opId = $matches[1].Trim()
      $method = $matches[2].Trim().ToUpperInvariant()
      $path = $matches[3].Trim()
      
      if ($opId -and ($opId -ne "[NO operationId]")) {
        $entry = [PSCustomObject]@{
          Id = $opId
          Method = $method
          Path = $path
        }
        $entries += $entry
      }
    }
  }
  
  return $entries | Sort-Object Id -Unique
}

# Main execution
try {
  $schema = Resolve-PathStrict $SchemaPath
  Write-Host "Using schema: $schema"
} catch { 
  Write-Error "Schema path error: $_"
  exit 2 
}

# Generate operations file if missing
if (-not (Test-Path $OperationsFile)) {
  Write-Host "operations.txt not found. Generating (filtered)..."
  $listScript = Join-Path $PSScriptRoot "list_operation_ids.py"
  & python $listScript --out $OperationsFile
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate operations file"
    exit 3
  }
}

# Get operation entries
$entries = Get-OperationEntries
if (-not $entries -or $entries.Count -eq 0) {
  Write-Host "No operations found in $OperationsFile. Regenerating with --all..."
  $listScript = Join-Path $PSScriptRoot "list_operation_ids.py"
  & python $listScript --all --out $OperationsFile
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to regenerate operations file"
    exit 4
  }
  
  $entries = Get-OperationEntries
  if (-not $entries -or $entries.Count -eq 0) {
    Write-Error "No operations found after regeneration. Please check your schema."
    exit 5
  }
}

Write-Host "Found $($entries.Count) operations to test"

# Activate local venv if available
$venvPath = Join-Path $PSScriptRoot "../.venv/Scripts/Activate.ps1"
if (Test-Path $venvPath) {
  Write-Host "Activating virtual environment..."
  & $venvPath
}

# Check if schemathesis is available
$schemathesisCmd = Get-Command schemathesis -ErrorAction SilentlyContinue
if ($schemathesisCmd) {
  $exe = "schemathesis"
  $runCmd = "run"
  } else {
    $exe = "python"
    $runCmd = "-m", "schemathesis.cli", "run"
  }

Write-Host "Using command: $exe $runCmd"

# Run in batches to avoid Windows command-line length limits
$total = $entries.Count
$batches = [Math]::Ceiling($total / [double]$MaxOpsPerRun)
$successCount = 0
$failCount = 0

for ($i = 0; $i -lt $batches; $i++) {
  $start = $i * $MaxOpsPerRun
  $end = [Math]::Min($start + $MaxOpsPerRun, $total)
  $batchEntries = $entries[$start..($end-1)]
  
  Write-Host "Batch $($i+1)/$batches: testing $($batchEntries.Count) operations..."
  
  # Build include-path regex from selected paths
  $escapedPaths = @()
  foreach ($entry in $batchEntries) {
    $escapedPath = [Regex]::Escape($entry.Path)
    # Make the regex more flexible - allow optional trailing slash
    if ($escapedPath.EndsWith('/')) {
      $escapedPath = $escapedPath.Substring(0, $escapedPath.Length - 1) + '/?'
    } else {
      $escapedPath = $escapedPath + '/?'
    }
    $escapedPaths += "^$escapedPath$"
  }
  $pathRegex = $escapedPaths -join "|"
  
  # Build command arguments
  $args = @()
  if ($exe -eq "python") {
    $args += $runCmd
  } else {
    $args += $runCmd
  }
  $args += @(
    "--max-examples", $MaxExamples.ToString(),
    "--workers", $Workers.ToString(),
    "--include-path", $pathRegex,
    "--url", $BaseUrl,
    $schema
  )
  
  Write-Host "Running: $exe $($args -join ' ')"
  
  # Execute the command
  if ($AuthToken -and $AuthToken.Trim().Length -gt 0) {
    # Rebuild args to include header in correct KEY:VALUE format
    $args = @()
    if ($exe -eq "python") { $args += $runCmd } else { $args += $runCmd }
    $args += @(
      "--max-examples", $MaxExamples.ToString(),
      "--workers", $Workers.ToString(),
      "--include-path", $pathRegex,
      "--header", "Authorization: Bearer $AuthToken",
      "--url", $BaseUrl,
      $schema
    )
    Write-Host "Running (auth): $exe $($args -join ' ')"
    & $exe $args
  } else {
    & $exe $args
  }
  
  if ($LASTEXITCODE -eq 0) {
    $successCount++
    Write-Host "Batch $($i+1) completed successfully"
  } else {
    $failCount++
    Write-Warning "Batch $($i+1) failed with exit code $LASTEXITCODE"
  }
}

Write-Host "Schemathesis run completed: $successCount successful batches, $failCount failed batches"

if ($failCount -gt 0) {
  exit 1
} else {
  exit 0
}