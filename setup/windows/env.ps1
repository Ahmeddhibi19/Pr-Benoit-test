# Session environment for the portable toolchain. Usage: . .\setup\windows\env.ps1 -Tools C:\w\tools
param(
    [string]$Tools = "C:\w\tools"
)
$env:JAVA_HOME = Join-Path $Tools "jdk-11.0.8+10"
$env:MAVEN_HOME = Join-Path $Tools "apache-maven-3.6.3"
$env:MAVEN_OPTS = "-Xmx2g"
$env:JAVA_TOOL_OPTIONS = "-Dfile.encoding=UTF-8"
$paths = @(
    (Join-Path $env:JAVA_HOME "bin"),
    (Join-Path $env:MAVEN_HOME "bin"),
    (Join-Path $Tools "gh\bin"),
    (Join-Path $Tools "uv"),
    (Join-Path $Tools "py311\Scripts")
)
$env:Path = ($paths -join ";") + ";" + $env:Path
