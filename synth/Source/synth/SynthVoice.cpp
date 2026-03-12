#include "SynthVoice.h"
#include "../oscillators/SineOscillator.h"

//==============================================================================
SynthVoice::SynthVoice()
{
    // Default to sine wave — swapped at runtime by the waveform selector.
    oscillator = std::make_unique<SineOscillator>();
}

//==============================================================================
void SynthVoice::prepare (double sr)
{
    sampleRate = sr;
    adsr.setSampleRate (sr);
    if (oscillator)
        oscillator->prepare (sr);
}

//==============================================================================
void SynthVoice::noteOn (int midiNoteNumber, float vel, const ADSRParameters& params)
{
    midiNote  = midiNoteNumber;
    velocity  = vel;
    active    = true;
    inRelease = false;

    // Convert MIDI note to frequency using equal temperament
    const double freq = 440.0 * std::pow (2.0, (midiNoteNumber - 69) / 12.0);

    if (oscillator)
    {
        oscillator->reset();
        oscillator->setFrequency (freq);
    }

    adsrParams.attack  = params.attack;
    adsrParams.decay   = params.decay;
    adsrParams.sustain = params.sustain;
    adsrParams.release = params.release;
    adsr.setParameters (adsrParams);
    adsr.noteOn();
}

void SynthVoice::noteOff()
{
    inRelease = true;
    adsr.noteOff();
}

void SynthVoice::kill()
{
    adsr.reset();
    active    = false;
    inRelease = false;
}

//==============================================================================
void SynthVoice::setOscillator (std::unique_ptr<OscillatorBase> newOscillator)
{
    oscillator = std::move (newOscillator);
    if (oscillator && sampleRate > 0.0)
        oscillator->prepare (sampleRate);
}

//==============================================================================
float SynthVoice::renderSample()
{
    if (! active || ! oscillator)
        return 0.0f;

    const float oscSample      = oscillator->getNextSample();
    const float envelopeGain   = adsr.getNextSample();
    const float sample         = oscSample * envelopeGain * velocity;

    // Mark voice free once the envelope has fully decayed after release.
    if (inRelease && ! adsr.isActive())
        active = false;

    return sample;
}

//==============================================================================
void SynthVoice::setADSRParameters (const ADSRParameters& params)
{
    adsrParams.attack  = params.attack;
    adsrParams.decay   = params.decay;
    adsrParams.sustain = params.sustain;
    adsrParams.release = params.release;
    adsr.setParameters (adsrParams);
}
