#pragma once

#include <JuceHeader.h>

//==============================================================================
// Parameter IDs — single source of truth, used by both processor and editor
namespace ParamID
{
    inline constexpr const char* Waveform   = "waveform";
    inline constexpr const char* Attack     = "attack";
    inline constexpr const char* Decay      = "decay";
    inline constexpr const char* Sustain    = "sustain";
    inline constexpr const char* Release    = "release";
    inline constexpr const char* MasterGain = "masterGain";
    inline constexpr const char* Tuning     = "tuning";
}

//==============================================================================
class MySynthAudioProcessor : public juce::AudioProcessor
{
public:
    MySynthAudioProcessor();
    ~MySynthAudioProcessor() override;

    //==========================================================================
    // AudioProcessor interface
    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;

    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;

    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    //==========================================================================
    // Editor
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    //==========================================================================
    // Plugin info
    const juce::String getName() const override { return JucePlugin_Name; }

    bool acceptsMidi() const override  { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    //==========================================================================
    // Programs (presets — stub for now)
    int getNumPrograms() override                                   { return 1; }
    int getCurrentProgram() override                                { return 0; }
    void setCurrentProgram (int) override                           {}
    const juce::String getProgramName (int) override                { return {}; }
    void changeProgramName (int, const juce::String&) override      {}

    //==========================================================================
    // State persistence
    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    //==========================================================================
    // Thread-safe parameter access
    juce::AudioProcessorValueTreeState& getAPVTS() { return apvts; }

private:
    //==========================================================================
    // APVTS factory — called once in the constructor initialiser list
    static juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();

    juce::AudioProcessorValueTreeState apvts;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MySynthAudioProcessor)
};
