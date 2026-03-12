# Modular Synthesizer VST Plugin — Architecture & Guiding Documentation

> **Purpose:** This document establishes the structural blueprint, layering conventions, and design philosophy for a JUCE-based, MIDI-driven synthesizer plugin. It is intended to guide implementation in Claude Code or any C++ development environment. The goal is a plugin that is legible, extensible, and capable of being loaded as an Instrument in Ableton Live 10+.

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Plugin Format & DAW Compatibility](#plugin-format--daw-compatibility)
3. [System Architecture Overview](#system-architecture-overview)
4. [Layer Breakdown](#layer-breakdown)
   - [Layer 1: Plugin Host Interface](#layer-1-plugin-host-interface)
   - [Layer 2: MIDI Processing](#layer-2-midi-processing)
   - [Layer 3: Voice Manager](#layer-3-voice-manager)
   - [Layer 4: Oscillator Module (Modular Core)](#layer-4-oscillator-module-modular-core)
   - [Layer 5: Signal Chain (Envelope + Mixing)](#layer-5-signal-chain-envelope--mixing)
   - [Layer 6: Audio Output Buffer](#layer-6-audio-output-buffer)
   - [Layer 7: UI Layer](#layer-7-ui-layer)
5. [Oscillator Modularity Design](#oscillator-modularity-design)
6. [Voice Architecture](#voice-architecture)
7. [Parameter System](#parameter-system)
8. [Directory Structure](#directory-structure)
9. [Build System](#build-system)
10. [Waveform Reference (Initial 4)](#waveform-reference-initial-4)
11. [Glossary](#glossary)
12. [Implementation Priorities & Roadmap](#implementation-priorities--roadmap)

---

## Technology Stack

| Concern             | Technology                       | Rationale                                                                 |
|---------------------|----------------------------------|---------------------------------------------------------------------------|
| Language            | C++17                            | Industry standard for DSP; JUCE requires it                              |
| Framework           | JUCE 7.x                         | Abstracts VST2/VST3/AU formats; handles MIDI, threading, UI              |
| Plugin Format       | VST3 (primary), VST2 (fallback)  | VST3 is the current standard; VST2 for older Ableton instances           |
| Build System        | CMake 3.22+                      | Works seamlessly with JUCE's CMakeLists integration                      |
| UI Toolkit          | JUCE Component (built-in)        | Native to JUCE; renders consistently across platforms                    |
| DSP Math            | `<cmath>`, JUCE DSP module       | Oscillator math is straightforward; JUCE DSP handles filters etc.        |

---

## Plugin Format & DAW Compatibility

**Target:** Ableton Live 10.0.2 and above.

Ableton Live 10 introduced full VST3 support (previously VST2-only). Both formats will be compiled from the same source.

- **VST2:** `.dll` (Windows), `.vst` (macOS) — placed in `C:/Program Files/VSTPlugins/` or `/Library/Audio/Plug-Ins/VST/`
- **VST3:** `.vst3` bundle — placed in the OS-defined VST3 directory (JUCE handles bundle construction)
- **AU (optional):** `.component` — macOS only, for Logic Pro compatibility

JUCE's `AudioProcessor` base class satisfies all three format contracts simultaneously. The plugin advertises itself as a **MIDI instrument** (not an effect), meaning Ableton will load it on an Instrument Track and route MIDI into it automatically.

**Key flag in JUCE plugin descriptor:**
```
IS_SYNTH = true
NEEDS_MIDI_INPUT = true
NEEDS_MIDI_OUTPUT = false
```

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        DAW (Ableton Live)                   │
│                                                             │
│  MIDI Track ──► [MIDI Input] ──► Plugin ──► [Audio Output] │
└──────────────────────────┬──────────────────────────────────┘
                           │ VST3 / VST2 host call
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               Layer 1: Plugin Host Interface                │
│           (AudioProcessor subclass — JUCE core)             │
└───────────────────────┬─────────────────────────────────────┘
                        │
              ┌─────────▼──────────┐
              │ Layer 2: MIDI      │
              │ Processing         │
              │ (MidiBuffer parse) │
              └─────────┬──────────┘
                        │ NoteOn / NoteOff / Pitch Bend etc.
              ┌─────────▼──────────┐
              │ Layer 3: Voice     │
              │ Manager            │
              │ (polyphony pool)   │
              └──┬──────┬──────┬───┘
                 │      │      │  (up to N concurrent voices)
          ┌──────▼─┐ ┌──▼───┐ ┌▼─────┐
          │ Voice 0│ │Voice1│ │Voice2│  ...
          │        │ │      │ │      │
          │ Osc ◄──┼─┤ Osc ◄┼─┤ Osc  │  Layer 4: Oscillator Module
          │ ADSR   │ │ ADSR │ │ ADSR │  Layer 5: Envelope
          └────┬───┘ └──┬───┘ └──┬───┘
               │         │        │
              ┌▼─────────▼────────▼────┐
              │  Layer 6: Mixer /       │
              │  Output Buffer          │
              └────────────┬────────────┘
                           │ float[] stereo buffer
                    ┌──────▼──────┐
                    │  Ableton    │
                    │  Audio In   │
                    └─────────────┘

              ┌─────────────────────┐
              │  Layer 7: UI        │  (runs on message thread)
              │  (knobs, waveform   │
              │   selector, ADSR)   │
              └─────────────────────┘
```

---

## Layer Breakdown

### Layer 1: Plugin Host Interface

**File:** `src/PluginProcessor.h / .cpp`

This is the JUCE-mandated entry point. It subclasses `juce::AudioProcessor` and is the object the DAW instantiates.

**Responsibilities:**
- Declare plugin metadata (name, channel layout, MIDI needs)
- Implement `prepareToPlay(sampleRate, blockSize)` — called when DAW initializes audio
- Implement `processBlock(AudioBuffer<float>&, MidiBuffer&)` — called every audio frame
- Expose `AudioProcessorValueTreeState` (APVTS) for parameter management and preset saving

**Key design constraint:** `processBlock` runs on the **audio thread** — no memory allocation, no UI calls, no mutex locks allowed here. Everything must be prepared in advance.

---

### Layer 2: MIDI Processing

**File:** `src/MidiProcessor.h / .cpp` (or inline in PluginProcessor)

JUCE delivers MIDI events packed into a `MidiBuffer` alongside each audio block. The MIDI processor iterates this buffer and dispatches events to the Voice Manager.

**Events to handle (minimum viable):**
- `NOTE_ON` (note number + velocity) → trigger voice
- `NOTE_OFF` (note number) → release voice
- `PITCH_WHEEL` → modulate all active voices' pitch
- `ALL_NOTES_OFF` (MIDI CC 123) → panic kill all voices
- `MODULATION_WHEEL` (MIDI CC 1) → route to LFO or other modulation target (future)

**MIDI to frequency conversion:**
```
frequency = 440.0 * pow(2.0, (noteNumber - 69) / 12.0)
```
This is the standard equal-temperament formula; 69 is MIDI note A4 (440 Hz).

---

### Layer 3: Voice Manager

**File:** `src/VoiceManager.h / .cpp`

The Voice Manager maintains a fixed pool of `SynthVoice` objects (e.g., 16 voices for polyphony). When a NOTE_ON arrives, it finds a free voice or steals the oldest one.

**Key behaviors:**
- **Voice allocation:** scan pool for inactive voice; assign note + frequency
- **Voice stealing:** if all voices are active, steal the voice with the lowest priority (typically the oldest or the quietest)
- **Voice release:** on NOTE_OFF, tell the voice to begin its ADSR release phase; do not mark it free until the envelope reaches zero
- **Render loop:** each audio block, iterate all active voices and sum their output into the master buffer

**Polyphony constant:**
```cpp
static constexpr int MAX_VOICES = 16;
```
This is adjustable. 16 is a reasonable default; Serum uses up to 16 unison voices per note on top of polyphony.

---

### Layer 4: Oscillator Module (Modular Core)

**Files:** `src/oscillators/OscillatorBase.h`, `src/oscillators/SineOscillator.h`, etc.

This is the centerpiece of the plugin's modularity. Every waveform is implemented as a subclass of a common abstract base. Swapping waveforms requires only changing which subclass is instantiated — no other code needs to change.

#### Abstract Interface

```cpp
class OscillatorBase {
public:
    virtual ~OscillatorBase() = default;

    // Called once when sample rate is known
    virtual void prepare(double sampleRate) = 0;

    // Set the frequency in Hz
    virtual void setFrequency(double frequencyHz) = 0;

    // Render one sample; advance internal phase
    virtual float getNextSample() = 0;

    // Reset phase (e.g., on voice trigger)
    virtual void reset() = 0;
};
```

Each concrete oscillator owns its own **phase accumulator** (a value from 0.0 to 1.0 that wraps around each cycle). The phase increment per sample is:

```
phaseIncrement = frequency / sampleRate
```

This is self-contained — no shared state between oscillators.

---

### Layer 5: Signal Chain (Envelope + Mixing)

**File:** `src/SynthVoice.h / .cpp`

Each `SynthVoice` contains one `OscillatorBase*` and one `ADSREnvelope`. The voice's output is the oscillator sample multiplied by the current envelope amplitude.

#### ADSR Envelope

The ADSR (Attack, Decay, Sustain, Release) envelope is the fundamental amplitude shaping tool in subtractive synthesis:

- **Attack:** time (ms) for amplitude to rise from 0 → 1 after NOTE_ON
- **Decay:** time (ms) to fall from 1 → Sustain level
- **Sustain:** level (0.0–1.0) held while key is depressed
- **Release:** time (ms) to fall from Sustain → 0 after NOTE_OFF

JUCE provides `juce::ADSR` out of the box. Use it as the default implementation.

**Per-sample voice render:**
```cpp
float VoiceManager::renderSample() {
    float oscillatorSample = oscillator->getNextSample();
    float envelopeGain    = adsr.getNextSample();
    return oscillatorSample * envelopeGain * velocity;
}
```

---

### Layer 6: Audio Output Buffer

**Responsibility:** handled inside `PluginProcessor::processBlock`.

All active voices are summed into the DAW's provided `AudioBuffer<float>`. Apply a master gain to prevent clipping from voice summation:

```cpp
masterGain = 1.0f / std::sqrt((float)MAX_VOICES);
```

This is the standard RMS-normalized approach to polyphonic summation.

---

### Layer 7: UI Layer

**Files:** `src/PluginEditor.h / .cpp`

The UI runs on the **message thread**, entirely separate from the audio thread. JUCE's `AudioProcessorValueTreeState` (APVTS) bridges the two threads safely via atomic parameter values.

**Initial UI components:**
- Waveform selector (dropdown or toggle buttons: Sine / Square / Saw / Triangle)
- ADSR sliders (4 sliders with labels)
- Master volume knob
- Oscillator tuning knob (semitone offset)

**APVTS attachment pattern:**
Each UI component is "attached" to a named parameter in the APVTS. When the user moves a knob, the APVTS atomically updates the value the audio thread reads. This is the thread-safe communication mechanism.

---

## Oscillator Modularity Design

The plugin uses the **Strategy Pattern** to achieve oscillator modularity. The `SynthVoice` holds a `std::unique_ptr<OscillatorBase>` and calls through the interface. Swapping waveforms at runtime is as simple as:

```cpp
voice.setOscillator(std::make_unique<SawtoothOscillator>());
```

#### Initial Four Waveforms

| Waveform  | Class Name           | Mathematical Form                        |
|-----------|----------------------|------------------------------------------|
| Sine      | `SineOscillator`     | `sin(2π * phase)`                        |
| Square    | `SquareOscillator`   | `phase < 0.5 ? 1.0 : -1.0`              |
| Sawtooth  | `SawtoothOscillator` | `2.0 * phase - 1.0`                      |
| Triangle  | `TriangleOscillator` | `1.0 - 4.0 * abs(phase - 0.5)`          |

**Anti-aliasing note:** Square, sawtooth, and triangle waveforms generated naïvely (as above) produce **aliasing artifacts** at higher frequencies because their abrupt discontinuities produce harmonics above the Nyquist limit. For production quality, consider implementing **PolyBLEP** (Polynomial Band-Limited Step) correction on those three. This is a well-documented technique and a recommended next milestone after the initial 4 waveforms work correctly.

---

## Voice Architecture

```
SynthVoice
├── OscillatorBase*         (polymorphic — swappable)
├── juce::ADSR              (envelope)
├── float currentFrequency
├── float velocity          (0.0 – 1.0, from MIDI velocity)
├── int midiNoteNumber      (for NOTE_OFF matching)
└── bool isActive
```

The Voice Manager pool:
```
VoiceManager
└── SynthVoice voices[MAX_VOICES]
```

---

## Parameter System

All automatable parameters live in the `AudioProcessorValueTreeState` (APVTS). This is JUCE's thread-safe, serializable parameter container. It also enables Ableton to automate any parameter via its automation lanes.

**Initial parameter set:**

| Parameter ID       | Type   | Range         | Default | Description                       |
|--------------------|--------|---------------|---------|-----------------------------------|
| `waveform`         | Int    | 0–3           | 0       | 0=Sine, 1=Square, 2=Saw, 3=Tri    |
| `attack`           | Float  | 0.001–5.0 s   | 0.01    | ADSR attack time                  |
| `decay`            | Float  | 0.001–5.0 s   | 0.1     | ADSR decay time                   |
| `sustain`          | Float  | 0.0–1.0       | 0.8     | ADSR sustain level                |
| `release`          | Float  | 0.001–10.0 s  | 0.3     | ADSR release time                 |
| `masterGain`       | Float  | 0.0–1.0       | 0.7     | Master output volume              |
| `tuning`           | Float  | -24–+24 semi  | 0.0     | Semitone offset (coarse tune)     |

Parameters are declared in `PluginProcessor.cpp` and referenced by ID string everywhere else.

---

## Directory Structure

```
MySynth/
├── CMakeLists.txt              # JUCE CMake configuration
├── README.md
├── ARCHITECTURE.md             # This document
│
├── Source/
│   ├── PluginProcessor.h       # AudioProcessor subclass (audio thread)
│   ├── PluginProcessor.cpp
│   ├── PluginEditor.h          # AudioProcessorEditor subclass (UI thread)
│   ├── PluginEditor.cpp
│   │
│   ├── synth/
│   │   ├── VoiceManager.h      # Polyphony / voice pool
│   │   ├── VoiceManager.cpp
│   │   ├── SynthVoice.h        # Individual voice (oscillator + envelope)
│   │   ├── SynthVoice.cpp
│   │   └── ADSRParameters.h    # Struct for passing ADSR values cleanly
│   │
│   └── oscillators/
│       ├── OscillatorBase.h    # Abstract interface (pure virtual)
│       ├── SineOscillator.h    # Concrete: sine wave
│       ├── SquareOscillator.h  # Concrete: square wave
│       ├── SawtoothOscillator.h
│       └── TriangleOscillator.h
│
├── JUCE/                       # JUCE submodule (git submodule add)
│
└── Builds/
    ├── MacOSX/
    └── VisualStudio2022/
```

---

## Build System

**CMakeLists.txt essentials:**

```cmake
cmake_minimum_required(VERSION 3.22)
project(MySynth VERSION 0.1.0)

add_subdirectory(JUCE)

juce_add_plugin(MySynth
    PLUGIN_MANUFACTURER_CODE MYCO
    PLUGIN_CODE MSYN
    FORMATS VST3 VST AU          # Compile all three
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    PRODUCT_NAME "MySynth"
)

target_sources(MySynth PRIVATE
    Source/PluginProcessor.cpp
    Source/PluginEditor.cpp
    Source/synth/VoiceManager.cpp
    Source/synth/SynthVoice.cpp
)

target_compile_features(MySynth PUBLIC cxx_std_17)

target_link_libraries(MySynth PRIVATE
    juce::juce_audio_utils
    juce::juce_dsp
    juce::juce_gui_basics
)
```

**Build steps:**
```bash
git submodule add https://github.com/juce-framework/JUCE.git
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

The compiled `.vst3` will appear in `build/MySynth_artefacts/VST3/`.

---

## Waveform Reference (Initial 4)

### Sine Wave
- **Timbre:** Pure, smooth, single harmonic
- **Use:** Sub-bass, clean leads, pad layers
- **Formula:** `y = sin(2π * phase)`

### Square Wave
- **Timbre:** Hollow, buzzy — contains only odd harmonics (1st, 3rd, 5th...)
- **Use:** Classic chiptune, clarinets, bass stabs
- **Formula:** `y = phase < 0.5 ? 1.0f : -1.0f`
- **Aliasing risk:** High — implement PolyBLEP for production use

### Sawtooth Wave
- **Timbre:** Bright, rich — contains all harmonics (1st, 2nd, 3rd...)
- **Use:** Strings, brass emulation, aggressive leads
- **Formula:** `y = 2.0f * phase - 1.0f`
- **Aliasing risk:** High — PolyBLEP strongly recommended

### Triangle Wave
- **Timbre:** Softer than square, flute-like — odd harmonics only but attenuated
- **Use:** Flute, whistle, soft leads
- **Formula:** `y = 1.0f - 4.0f * std::abs(phase - 0.5f)`
- **Aliasing risk:** Low — discontinuity is in the derivative, not the signal itself

---

## Glossary

| Term         | Meaning                                                                         |
|--------------|---------------------------------------------------------------------------------|
| JUCE         | C++ framework for audio applications and plugins                                |
| VST          | Virtual Studio Technology — Steinberg's plugin format standard                  |
| VST3         | Third-generation VST; supports better parameter handling and side-chaining      |
| AU           | Audio Unit — Apple's native plugin format                                       |
| APVTS        | AudioProcessorValueTreeState — JUCE's thread-safe parameter system              |
| ADSR         | Attack, Decay, Sustain, Release — standard amplitude envelope shape             |
| Phase        | A 0.0→1.0 value representing position within one waveform cycle                 |
| Aliasing     | Distortion artifact when signal harmonics exceed the Nyquist frequency           |
| PolyBLEP     | Polynomial Band-Limited Step — technique to reduce aliasing in naive oscillators |
| Polyphony    | The ability to play multiple notes simultaneously                                |
| Voice        | One instance of an oscillator + envelope, corresponding to one active note      |
| Voice Steal  | Reassigning a playing voice to a new note when the polyphony limit is reached   |
| Sample Rate  | Number of audio samples per second (typically 44100 or 48000 Hz in Ableton)    |
| Audio Thread | High-priority OS thread where `processBlock` executes; no allocations allowed   |

---

## Implementation Priorities & Roadmap

### Milestone 1 — Structural Shell (No Audio)
- [ ] JUCE CMake project compiles and loads in Ableton as a blank instrument
- [ ] APVTS declared with all parameters
- [ ] UI opens without crashing

### Milestone 2 — Sine Voice (Single Note)
- [ ] `OscillatorBase` abstract class implemented
- [ ] `SineOscillator` implemented
- [ ] Single `SynthVoice` renders a sine wave on MIDI NOTE_ON
- [ ] ADSR envelope shapes the amplitude
- [ ] Audio output is correct (no clipping, no silence)

### Milestone 3 — Polyphony
- [ ] `VoiceManager` pool implemented (16 voices)
- [ ] Voice allocation and release working
- [ ] Voice stealing on polyphony overflow

### Milestone 4 — Remaining Waveforms
- [ ] `SquareOscillator`, `SawtoothOscillator`, `TriangleOscillator` implemented
- [ ] Waveform selector in UI updates oscillator type across all voices in real time

### Milestone 5 — Quality Pass
- [ ] PolyBLEP anti-aliasing on Square and Sawtooth
- [ ] Pitch bend wheel modulation
- [ ] Tuning parameter working
- [ ] Preset save/load via APVTS XML serialization

### Milestone 6 — Polish (Serum parity concepts)
- [ ] Multiple oscillators per voice (Osc A + Osc B mix)
- [ ] Unison (multiple detuned oscillators per note)
- [ ] Filter module (JUCE DSP ladder filter)
- [ ] LFO routable to pitch, filter cutoff, or amplitude
```
