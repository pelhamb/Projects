# build.ps1 - Synthphia milestone build script
#
# ┌─────────────────────────────────────────────────────────────────────┐
# │  HOW TO BUILD                                                       │
# │                                                                     │
# │  1. Open PowerShell and cd into this folder:                        │
# │       cd C:\Users\pberg\VSCoding\synth                              │
# │                                                                     │
# │  2. Run the build for whichever milestone you want:                 │
# │       .\build.ps1 -Milestone 2                                      │
# │       .\build.ps1 -Milestone 3   ← just change the number          │
# │                                                                     │
# │  3. The compiled VST3 lands in:                                     │
# │       releases\milestone-N\Synthphia N.vst3                        │
# │                                                                     │
# │  4. To install in Ableton, copy that entire .vst3 folder to:       │
# │       C:\Program Files\Common Files\VST3\                          │
# │     Then in Ableton: Preferences → Plug-ins → Rescan               │
# │                                                                     │
# │  NOTE: If you change the milestone number, delete the build\        │
# │  folder first so CMake picks up the new product name cleanly.      │
# │       Remove-Item -Recurse -Force build                             │
# └─────────────────────────────────────────────────────────────────────┘
#
# Prerequisites (one-time, per machine):
#   - Visual Studio with "Desktop development with C++" workload
#   - JUCE submodule: run once after cloning → git submodule update --init

param(
    [Parameter(Mandatory=$true)]
    [int]$Milestone
)

Set-Location $PSScriptRoot

# ── Locate Visual Studio via vswhere ─────────────────────────────────────────
$vsWhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vsWhere)) {
    Write-Host "ERROR: vswhere.exe not found. Is Visual Studio installed?" -ForegroundColor Red
    exit 1
}

$vsPath    = & $vsWhere -latest -property installationPath
$vsMajor   = [int](& $vsWhere -latest -property catalog_productMajorVersion 2>$null)
if (-not $vsMajor) {
    # Fallback: parse from installationPath (e.g. \18\)
    if ($vsPath -match '\\(\d+)\\') { $vsMajor = [int]$Matches[1] }
}

# Map VS major version → CMake generator year string
$generatorYear = switch ($vsMajor) {
    18      { "2026" }
    17      { "2022" }
    16      { "2019" }
    15      { "2017" }
    default { Write-Host "ERROR: Unknown VS major version $vsMajor" -ForegroundColor Red; exit 1 }
}
$generator = "Visual Studio $vsMajor $generatorYear"

# ── Locate CMake ──────────────────────────────────────────────────────────────
# Priority: 1) bundled with VS (always matches the installed VS version)
#           2) bundled in this repo (fallback for machines without VS cmake)
#           3) system PATH
$candidates = @(
    (Join-Path $vsPath "Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"),
    (Join-Path $PSScriptRoot "tools\cmake\bin\cmake.exe")
)
$cmake = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $cmake) {
    $systemCmake = Get-Command cmake -ErrorAction SilentlyContinue
    if ($systemCmake) { $cmake = $systemCmake.Source }
}
if (-not $cmake) {
    Write-Host "ERROR: cmake not found. Install VS 'Desktop development with C++' workload." -ForegroundColor Red
    exit 1
}

$artifactSrc = "build\MySynth_artefacts\Release\VST3\Synthphia${Milestone}.vst3"
$releaseDir  = "releases\milestone-$Milestone"
$tag         = "milestone-$Milestone"

Write-Host ""
Write-Host "=== Synthphia - Building Milestone $Milestone ===" -ForegroundColor Cyan
Write-Host "    VS $vsMajor ($generatorYear)  |  cmake: $cmake" -ForegroundColor DarkGray
Write-Host ""

# ── Configure ─────────────────────────────────────────────────────────────────
Write-Host "Configuring..." -ForegroundColor Yellow
& $cmake -B build -G $generator -A x64 "-DMILESTONE=$Milestone"
if ($LASTEXITCODE -ne 0) { Write-Host "Configure failed." -ForegroundColor Red; exit 1 }

# ── Build ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Building..." -ForegroundColor Yellow
& $cmake --build build --config Release --parallel
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed." -ForegroundColor Red; exit 1 }

# ── Archive artifact ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Archiving artifact to $releaseDir ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Copy-Item -Recurse -Force $artifactSrc $releaseDir
Write-Host "Saved: $releaseDir\Synthphia${Milestone}.vst3" -ForegroundColor Green

# ── Git tag ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Tagging git commit as '$tag' ..." -ForegroundColor Yellow
git tag $tag 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tag '$tag' already exists - skipping." -ForegroundColor DarkYellow
} else {
    Write-Host "Tagged: $tag" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Done! Milestone $Milestone build complete ===" -ForegroundColor Cyan
Write-Host ""
