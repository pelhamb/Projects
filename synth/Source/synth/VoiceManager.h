#pragma once

#include <JuceHeader.h>
#include "SynthVoice.h"
#include "ADSRParameters.h"
#include <array>

//==============================================================================
// Manages a fixed pool of SynthVoice objects.
// Handles voice allocation, stealing, and per-block rendering.
class VoiceManager
{
public:
    static constexpr int MAX_VOICES = 16;

    VoiceManager();

    //==========================================================================
    // Called from PluginProcessor::prepareToPlay
    void prepare (double sampleRate);

    //==========================================================================
    // Called from processBlock — iterates the MidiBuffer and renders audio.
    void processBlock (juce::AudioBuffer<float>& buffer,
                       juce::MidiBuffer&         midiMessages,
                       const ADSRParameters&     adsrParams,
                       float                     masterGain);

    //==========================================================================
    // Swap all voice oscillators to a new waveform type.
    // waveformIndex: 0=Sine, 1=Square, 2=Saw, 3=Triangle
    void setWaveform (int waveformIndex);

    //==========================================================================
    // Kill all active voices immediately (MIDI panic).
    void allNotesOff();

private:
    std::array<SynthVoice, MAX_VOICES> voices;

    void handleNoteOn  (int midiNote, float velocity, const ADSRParameters& params);
    void handleNoteOff (int midiNote);

    // Returns the index of a free voice, or the voice to steal if all are active.
    int findAvailableVoice() const;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (VoiceManager)
};
