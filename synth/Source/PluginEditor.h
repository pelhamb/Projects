#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"

//==============================================================================
// Small component that draws a live ADSR envelope shape with four dots
// connected by lines.  It reads the current slider values each paint() call.
class ADSRVisualizer : public juce::Component,
                       public juce::Timer
{
public:
    ADSRVisualizer (juce::Slider& a, juce::Slider& d,
                    juce::Slider& s, juce::Slider& r)
        : attackSlider (a), decaySlider (d),
          sustainSlider (s), releaseSlider (r)
    {
        startTimerHz (30);   // repaint at 30 fps so dots track sliders smoothly
    }

    void timerCallback() override { repaint(); }

    void paint (juce::Graphics& g) override;

private:
    juce::Slider &attackSlider, &decaySlider, &sustainSlider, &releaseSlider;
};

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
    // ADSR visualizer graph
    ADSRVisualizer adsrVisualizer { attackSlider, decaySlider,
                                    sustainSlider, releaseSlider };

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
