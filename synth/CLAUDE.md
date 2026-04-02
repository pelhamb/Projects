# Claude Code — Project Notes

## Build Process

- **Pelham (the user) will always run the build command.** Do NOT run `build.ps1` or cmake builds yourself. Make your code changes, then tell Pelham which milestone to build and let him handle it.
- The build script is `.\build.ps1 -Milestone N` — Pelham runs this from the main repo in PowerShell.
- Work directly on the main branch unless Pelham asks otherwise. Avoid worktrees — they caused path issues with the VST3 plugin output in the past.

## Plugin Install Path

- Pelham's custom Ableton plugins folder: `C:\Users\pberg\Desktop\Ableton Files\plugins\VstPlugins\`
- Plugins are organized under a company subfolder: `Valhalla\SynthphiaN.vst3`
- Do NOT copy VST3 artifacts to `C:\Program Files\Common Files\VST3\` — that's not where Pelham's Ableton scans.

## Version Naming

- Each milestone builds as **SynthphiaN** (e.g., Synthphia2 for milestone 2).
- All user-facing text must use `JucePlugin_Name` macro, never hardcode a version string.
- See SYNTH_ARCHITECTURE.md "Version Naming Convention" section for the full checklist.
