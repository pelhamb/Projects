#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"

//==============================================================================
class MySynthAudioProcessorEditor : public juce::AudioProcessorEditor
{
public:
    explicit MySynthAudioProcessorEditor (MySynthAudioProcessor&);
    ~MySynthAudioProcessorEditor() override;

    //==========================================================================
    void paint (juce::Graphics&) override;
    void resized() override;

private:
    MySynthAudioProcessor& audioProcessor;

    //==========================================================================
    // Waveform selector
    juce::Label         waveformLabel;
    juce::ComboBox      waveformSelector;
    std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> waveformAttachment;

    //==========================================================================
    // ADSR sliders
    juce::Slider attackSlider,  decaySlider,  sustainSlider,  releaseSlider;
    juce::Label  attackLabel,   decayLabel,   sustainLabel,   releaseLabel;

    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attackAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> decayAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> sustainAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> releaseAttachment;

    //==========================================================================
    // Master gain & tuning
    juce::Slider masterGainKnob, tuningKnob;
    juce::Label  masterGainLabel, tuningLabel;

    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> masterGainAttachment;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> tuningAttachment;

    //==========================================================================
    void setupSlider (juce::Slider& slider, juce::Label& label,
                      const juce::String& labelText,
                      juce::Slider::SliderStyle style = juce::Slider::RotaryVerticalDrag);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MySynthAudioProcessorEditor)
};
