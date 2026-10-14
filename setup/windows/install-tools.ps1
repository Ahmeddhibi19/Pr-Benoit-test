# Portable toolchain for Windows, no administrator rights needed.
# Installs JDK 11.0.8, Maven 3.6.3, gh, uv and a Python 3.11 virtual environment into -Dest.
param(
    [string]$Dest = "C:\w\tools"
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$tools = @(
    @{ Name = "jdk";   Dir = "jdk-11.0.8+10"
       Url  = "https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.8%2B10/OpenJDK11U-jdk_x64_windows_hotspot_11.0.8_10.zip"
       Algo = "SHA256"; Hash = "473e552748b23bd95ad097249e97f5d923d8dde3b956a9487ab17c860a6baa48" },
    @{ Name = "maven"; Dir = "apache-maven-3.6.3"
       Url  = "https://archive.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.zip"
       Algo = "SHA512"; Hash = "1c095ed556eda06c6d82fdf52200bc4f3437a1bab42387e801d6f4c56e833fb82b16e8bf0aab95c9708de7bfb55ec27f653a7cf0f491acebc541af234eded94d" },
    @{ Name = "gh";    Dir = "gh"
       Url  = "https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_windows_amd64.zip"
       Algo = "SHA256"; HashUrl = "https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_checksums.txt" },
    @{ Name = "uv";    Dir = "uv"
       Url  = "https://github.com/astral-sh/uv/releases/download/0.13.1/uv-x86_64-pc-windows-msvc.zip"
       Algo = "SHA256"; HashUrl = "https://github.com/astral-sh/uv/releases/download/0.13.1/uv-x86_64-pc-windows-msvc.zip.sha256" }
)

# Native tools write progress to stderr; only their exit code decides failure.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments)
    $ErrorActionPreference = "Continue"
    & $Exe @Arguments 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$downloads = Join-Path $Dest "_downloads"
New-Item -ItemType Directory -Force -Path $downloads | Out-Null

foreach ($t in $tools) {
    $target = Join-Path $Dest $t.Dir
    if (Test-Path $target) { Write-Host "$($t.Name): already installed in $target"; continue }

    $file = Join-Path $downloads ([IO.Path]::GetFileName(([Uri]$t.Url).AbsolutePath))
    if (-not (Test-Path $file)) {
        # curl.exe ships with Windows 10 and can resume interrupted downloads.
        Invoke-Native "curl.exe" @("-fL", "--retry", "5", "--retry-all-errors", "-C", "-", "-s", "-S", "-o", "$file.part", $t.Url)
        Move-Item "$file.part" $file
    }

    $expected = $t.Hash
    if (-not $expected) {
        $sums = (Invoke-WebRequest -Uri $t.HashUrl -UseBasicParsing).Content
        if ($sums -is [byte[]]) { $sums = [Text.Encoding]::ASCII.GetString($sums) }
        $line = ($sums -split "`n") | Where-Object { $_ -match [regex]::Escape([IO.Path]::GetFileName($file)) } | Select-Object -First 1
        if (-not $line) { $line = ($sums -split "`n")[0] }
        $expected = ($line.Trim() -split "\s+")[0]
    }
    $actual = (Get-FileHash -Algorithm $t.Algo -Path $file).Hash
    if ($actual -ne $expected.ToUpper()) {
        Remove-Item $file
        throw "$($t.Name): checksum mismatch ($actual vs $expected), download removed"
    }
    Write-Host "$($t.Name): checksum ok"

    if ($t.Dir -in @("gh", "uv")) {
        Expand-Archive -Path $file -DestinationPath $target
    } else {
        Expand-Archive -Path $file -DestinationPath $Dest
    }
}

$uv = Join-Path $Dest "uv\uv.exe"
$venv = Join-Path $Dest "py311"
$python = Join-Path $venv "Scripts\python.exe"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Dest "python"
Invoke-Native $uv @("python", "install", "3.11", "--no-bin")
if (-not (Test-Path $venv)) { Invoke-Native $uv @("venv", $venv, "--python", "3.11") }
Invoke-Native $uv @("pip", "install", "--python", $python, "pandas==1.5.3", "numpy==1.26.4", "matplotlib==3.8.4")

Invoke-Native (Join-Path $Dest "jdk-11.0.8+10\bin\java.exe") @("-version")
Invoke-Native $python @("-c", "import sys, pandas, numpy, matplotlib; print(sys.version.split()[0], pandas.__version__, numpy.__version__, matplotlib.__version__)")
