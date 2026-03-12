#pragma once

#include "OscillatorBase.h"
#include <cmath>

//==============================================================================
// Triangle wave oscillator.  y = 1 - 4 * |phase - 0.5|
// Lower aliasing risk than square/saw (derivative discontinuity only).
class TriangleOscillator : public OscillatorBase
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
        const float sample = 1.0f - 4.0f * std::abs (static_cast<float> (phase) - 0.5f);
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
