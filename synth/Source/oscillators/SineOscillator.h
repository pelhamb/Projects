#pragma once

#include "OscillatorBase.h"
#include <JuceHeader.h>

//==============================================================================
// Sine wave oscillator.  y = sin(2π * phase)
class SineOscillator : public OscillatorBase
{
public:
    void prepare (double sampleRate) override
    {
        currentSampleRate = sampleRate;
        updatePhaseIncrement (currentFrequency, sampleRate);
    }

    void setFrequency (double frequencyHz) override
    {
        currentFrequency = frequencyHz;
        if (currentSampleRate > 0.0)
            updatePhaseIncrement (frequencyHz, currentSampleRate);
    }

    float getNextSample() override
    {
        const float sample = std::sin (static_cast<float> (phase * 2.0 * juce::MathConstants<double>::pi));
        advancePhase();
        return sample;
    }

    void reset() override
    {
        phase = 0.0;
    }

private:
    double currentFrequency  { 440.0 };
    double currentSampleRate { 0.0 };
};
