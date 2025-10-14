# Behavior Logger UI - PowerShell Build and Run Script

Write-Host "Behavior Logger UI - Build and Run Script" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Accept optional switch to only compile
param(
    [switch]$compileOnly
)

# Set Java environment variables if needed
$env:JAVA_HOME = "C:\Program Files\Java\jdk-16.0.2"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Set MySQL connector JAR path
# Use all jars in lib/ so JFreeChart and other libs are available
$JARS = "lib/*"
# Create class directory if it doesn't exist
# (original script kept only the mysql jar; leave as originally authored)

# Create class directory if it doesn't exist
if (-not (Test-Path "classes")) {
    New-Item -ItemType Directory -Path "classes"
}

Write-Host "Compiling Java files with lib/* on the classpath..." -ForegroundColor Cyan
# Ensure we operate from the script directory so relative paths resolve consistently
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Push-Location $scriptDir
try {
    # Compile all .java files in this directory with the combined classpath (include all jars)
    # PowerShell doesn't expand *.java for external programs; enumerate files and pass them to javac
    $javaFiles = Get-ChildItem -Path $scriptDir -Filter "*.java" | ForEach-Object { $_.FullName }
    if ($javaFiles.Count -eq 0) {
        Write-Host "No Java source files found to compile" -ForegroundColor Yellow
        Write-Host "Error: Compilation failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    & javac -d classes -cp "$JARS" $javaFiles
} finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Compilation failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not $compileOnly) {
    Write-Host "Running application..." -ForegroundColor Cyan
    # Ensure we run from the script directory when launching
    Push-Location $scriptDir
    try {
        java -cp "classes;$JARS" BehaviorLoggerUIMain
    } finally {
        Pop-Location
    }

    Read-Host "Press Enter to exit"
} else {
    Write-Host "Compile-only mode complete." -ForegroundColor Green
}