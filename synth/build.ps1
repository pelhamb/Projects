# build.ps1 - Synthphia milestone build script
#
# Usage:
#   .\build.ps1 -Milestone 1
#
# What it does:
#   1. Configures and compiles the VST3 via CMake
#   2. Copies the .vst3 artifact to releases\milestone-N\
#   3. Creates a git tag milestone-N
#
# Prerequisites:
#   - CMake at C:\Program Files\CMake\bin\cmake.exe
#   - JUCE submodule already cloned (git submodule add ...)
#   - Visual Studio 2019/2022 Build Tools installed

param(
    [Parameter(Mandatory=$true)]
    [int]$Milestone
)

$cmake = "C:\Program Files\CMake\bin\cmake.exe"
$artifactSrc = "build\MySynth_artefacts\Release\VST3\Synthphia1.vst3"
$releaseDir  = "releases\milestone-$Milestone"
$tag         = "milestone-$Milestone"

Write-Host ""
Write-Host "=== Synthphia - Building Milestone $Milestone ===" -ForegroundColor Cyan
Write-Host ""

# --- Configure ---------------------------------------------------------------
Write-Host "Configuring..." -ForegroundColor Yellow
& $cmake -B build
if ($LASTEXITCODE -ne 0) { Write-Host "Configure failed." -ForegroundColor Red; exit 1 }

# --- Build -------------------------------------------------------------------
Write-Host ""
Write-Host "Building..." -ForegroundColor Yellow
& $cmake --build build --config Release
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed." -ForegroundColor Red; exit 1 }

# --- Archive artifact --------------------------------------------------------
Write-Host ""
Write-Host "Archiving artifact to $releaseDir ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Copy-Item -Recurse -Force $artifactSrc $releaseDir
Write-Host "Saved: $releaseDir\MySynth.vst3" -ForegroundColor Green

# --- Git tag -----------------------------------------------------------------
Write-Host ""
Write-Host "Tagging git commit as '$tag' ..." -ForegroundColor Yellow
git tag $tag
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tag already exists or git error - skipping tag." -ForegroundColor DarkYellow
} else {
    Write-Host "Tagged: $tag" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Done! Milestone $Milestone build complete ===" -ForegroundColor Cyan
Write-Host ""
