#pragma once

//==============================================================================
// Abstract base for all oscillator types.
// Concrete subclasses own their own phase accumulator and implement these four
// methods — no other code needs to change when swapping waveforms.
class OscillatorBase
{
public:
    virtual ~OscillatorBase() = default;

    // Called once when the host sample rate is known (or changes).
    virtual void prepare (double sampleRate) = 0;

    // Set the output frequency in Hz.
    virtual void setFrequency (double frequencyHz) = 0;

    // Render one sample and advance the internal phase accumulator.
    virtual float getNextSample() = 0;

    // Reset the phase to 0 (call on voice trigger for phase-coherent output).
    virtual void reset() = 0;

protected:
    // Shared helper: phase increment per sample.
    // Subclasses may use this directly.
    double phaseIncrement { 0.0 };
    double phase          { 0.0 };    // 0.0 – 1.0

    void updatePhaseIncrement (double frequencyHz, double sampleRate)
    {
        phaseIncrement = frequencyHz / sampleRate;
    }

    // Advance phase and wrap into [0, 1).
    void advancePhase()
    {
        phase += phaseIncrement;
        if (phase >= 1.0) phase -= 1.0;
    }
};
