#pragma once

#include <JuceHeader.h>
#include "ADSRParameters.h"
#include "../oscillators/OscillatorBase.h"
#include <memory>

//==============================================================================
// One polyphonic voice: oscillator + ADSR envelope.
// The VoiceManager owns a pool of these.
class SynthVoice
{
public:
    SynthVoice();

    //==========================================================================
    // Called by VoiceManager when the host sample rate is set.
    void prepare (double sampleRate);

    //==========================================================================
    // Trigger / release
    void noteOn  (int midiNoteNumber, float velocity, const ADSRParameters& adsrParams);
    void noteOff ();

    // Kill instantly (ALL_NOTES_OFF panic).
    void kill();

    //==========================================================================
    // Swap the oscillator waveform (e.g. when the user changes the selector).
    // Thread-safety: call this from the audio thread only (processBlock context).
    void setOscillator (std::unique_ptr<OscillatorBase> newOscillator);

    //==========================================================================
    // Render one sample.  Returns 0 if the voice is inactive.
    float renderSample();

    //==========================================================================
    // State queries
    bool isActive()        const { return active; }
    int  getMidiNote()     const { return midiNote; }
    bool isInReleasePhase() const { return inRelease; }

    //==========================================================================
    // Update ADSR parameters mid-voice (applied on next note-on, not retroactively).
    void setADSRParameters (const ADSRParameters& params);

private:
    std::unique_ptr<OscillatorBase> oscillator;
    juce::ADSR                      adsr;
    juce::ADSR::Parameters          adsrParams;

    float  velocity  { 0.0f };
    int    midiNote  { -1 };
    bool   active    { false };
    bool   inRelease { false };

    double sampleRate { 44100.0 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SynthVoice)
};
