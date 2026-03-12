#pragma once

#include "OscillatorBase.h"

//==============================================================================
// Square wave oscillator.  y = phase < 0.5 ? 1 : -1
// Note: naive implementation — aliasing at high frequencies.
// PolyBLEP correction is planned for Milestone 5.
class SquareOscillator : public OscillatorBase
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
        const float sample = (phase < 0.5) ? 1.0f : -1.0f;
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
