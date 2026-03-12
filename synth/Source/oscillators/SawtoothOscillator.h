#pragma once

#include "OscillatorBase.h"

//==============================================================================
// Sawtooth wave oscillator.  y = 2 * phase - 1
// Note: naive implementation — aliasing at high frequencies.
// PolyBLEP correction is planned for Milestone 5.
class SawtoothOscillator : public OscillatorBase
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
        const float sample = static_cast<float> (2.0 * phase - 1.0);
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
