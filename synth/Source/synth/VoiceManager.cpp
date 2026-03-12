#include "VoiceManager.h"
#include "../oscillators/SineOscillator.h"
#include "../oscillators/SquareOscillator.h"
#include "../oscillators/SawtoothOscillator.h"
#include "../oscillators/TriangleOscillator.h"

//==============================================================================
VoiceManager::VoiceManager() {}

//==============================================================================
void VoiceManager::prepare (double sampleRate)
{
    for (auto& v : voices)
        v.prepare (sampleRate);
}

//==============================================================================
void VoiceManager::processBlock (juce::AudioBuffer<float>& buffer,
                                 juce::MidiBuffer&         midiMessages,
                                 const ADSRParameters&     adsrParams,
                                 float                     masterGain)
{
    const int numSamples = buffer.getNumSamples();
    buffer.clear();

    // ---- Process MIDI events ------------------------------------------------
    for (const auto metadata : midiMessages)
    {
        const auto msg = metadata.getMessage();

        if (msg.isNoteOn())
        {
            const float vel = static_cast<float> (msg.getVelocity()) / 127.0f;
            handleNoteOn (msg.getNoteNumber(), vel, adsrParams);
        }
        else if (msg.isNoteOff())
        {
            handleNoteOff (msg.getNoteNumber());
        }
        else if (msg.isAllNotesOff() || msg.isAllSoundOff())
        {
            allNotesOff();
        }
    }

    // ---- Render all active voices -------------------------------------------
    // RMS-normalised master gain to prevent clipping from summation.
    const float normGain = masterGain / std::sqrt (static_cast<float> (MAX_VOICES));
    const int numChannels = buffer.getNumChannels();

    for (int sample = 0; sample < numSamples; ++sample)
    {
        float mixed = 0.0f;

        for (auto& voice : voices)
            mixed += voice.renderSample();

        mixed *= normGain;

        for (int ch = 0; ch < numChannels; ++ch)
            buffer.addSample (ch, sample, mixed);
    }
}

//==============================================================================
void VoiceManager::handleNoteOn (int midiNote, float velocity,
                                  const ADSRParameters& params)
{
    // Re-trigger a voice already playing this note (legato / retriggering).
    for (auto& v : voices)
    {
        if (v.isActive() && v.getMidiNote() == midiNote)
        {
            v.noteOn (midiNote, velocity, params);
            return;
        }
    }

    voices[findAvailableVoice()].noteOn (midiNote, velocity, params);
}

void VoiceManager::handleNoteOff (int midiNote)
{
    for (auto& v : voices)
    {
        if (v.isActive() && v.getMidiNote() == midiNote && ! v.isInReleasePhase())
        {
            v.noteOff();
            return;
        }
    }
}

void VoiceManager::allNotesOff()
{
    for (auto& v : voices)
        v.kill();
}

//==============================================================================
int VoiceManager::findAvailableVoice() const
{
    // Prefer a truly inactive voice.
    for (int i = 0; i < MAX_VOICES; ++i)
        if (! voices[i].isActive())
            return i;

    // All voices active — steal voice 0 (simple round-robin placeholder).
    // A more sophisticated implementation would steal the oldest or quietest.
    return 0;
}

//==============================================================================
void VoiceManager::setWaveform (int waveformIndex)
{
    for (auto& voice : voices)
    {
        std::unique_ptr<OscillatorBase> osc;

        switch (waveformIndex)
        {
            case 0:  osc = std::make_unique<SineOscillator>();     break;
            case 1:  osc = std::make_unique<SquareOscillator>();   break;
            case 2:  osc = std::make_unique<SawtoothOscillator>(); break;
            case 3:  osc = std::make_unique<TriangleOscillator>(); break;
            default: osc = std::make_unique<SineOscillator>();     break;
        }

        voice.setOscillator (std::move (osc));
    }
}
