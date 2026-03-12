#include "PluginEditor.h"

//==============================================================================
MySynthAudioProcessorEditor::MySynthAudioProcessorEditor (MySynthAudioProcessor& p)
    : AudioProcessorEditor (&p), audioProcessor (p)
{
    auto& apvts = audioProcessor.getAPVTS();

    //==========================================================================
    // Waveform selector
    waveformLabel.setText ("Waveform", juce::dontSendNotification);
    waveformLabel.setJustificationType (juce::Justification::centred);
    addAndMakeVisible (waveformLabel);

    waveformSelector.addItem ("Sine",     1);
    waveformSelector.addItem ("Square",   2);
    waveformSelector.addItem ("Sawtooth", 3);
    waveformSelector.addItem ("Triangle", 4);
    addAndMakeVisible (waveformSelector);
    waveformAttachment = std::make_unique<juce::AudioProcessorValueTreeState::ComboBoxAttachment> (
        apvts, ParamID::Waveform, waveformSelector);

    //==========================================================================
    // ADSR sliders (vertical)
    setupSlider (attackSlider,  attackLabel,  "Attack",  juce::Slider::LinearVertical);
    setupSlider (decaySlider,   decayLabel,   "Decay",   juce::Slider::LinearVertical);
    setupSlider (sustainSlider, sustainLabel, "Sustain", juce::Slider::LinearVertical);
    setupSlider (releaseSlider, releaseLabel, "Release", juce::Slider::LinearVertical);

    attackAttachment  = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::Attack,  attackSlider);
    decayAttachment   = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::Decay,   decaySlider);
    sustainAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::Sustain, sustainSlider);
    releaseAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::Release, releaseSlider);

    //==========================================================================
    // Master gain & tuning (rotary)
    setupSlider (masterGainKnob, masterGainLabel, "Volume");
    setupSlider (tuningKnob,     tuningLabel,     "Tuning");

    masterGainAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::MasterGain, masterGainKnob);
    tuningAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::Tuning, tuningKnob);

    //==========================================================================
    setSize (520, 300);
}

MySynthAudioProcessorEditor::~MySynthAudioProcessorEditor() {}

//==============================================================================
void MySynthAudioProcessorEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1e1e2e));   // dark background

    g.setColour (juce::Colour (0xff89b4fa));  // accent blue
    g.setFont (juce::Font (16.0f, juce::Font::bold));
    g.drawFittedText ("Synthphia1", getLocalBounds().removeFromTop (28),
                      juce::Justification::centred, 1);

    // Section labels
    g.setColour (juce::Colour (0xffa6adc8).withAlpha (0.6f));
    g.setFont (11.0f);
    g.drawText ("OSCILLATOR", juce::Rectangle<int> (10, 30, 120, 16),
                juce::Justification::left);
    g.drawText ("ENVELOPE",   juce::Rectangle<int> (160, 30, 200, 16),
                juce::Justification::left);
    g.drawText ("OUTPUT",     juce::Rectangle<int> (390, 30, 120, 16),
                juce::Justification::left);
}

void MySynthAudioProcessorEditor::resized()
{
    const int margin     = 10;
    const int labelH     = 18;
    const int knobSize   = 70;
    const int sliderW    = 40;
    const int sliderH    = 160;
    const int topOffset  = 50;

    //--------------------------------------------------------------------------
    // Waveform selector (left column)
    waveformLabel.setBounds    (margin, topOffset, 140, labelH);
    waveformSelector.setBounds (margin, topOffset + labelH + 2, 140, 28);

    //--------------------------------------------------------------------------
    // ADSR sliders (centre block)
    const int adsrStartX = 160;
    const int sliderSpacing = sliderW + 10;

    auto placeAdsr = [&](juce::Slider& s, juce::Label& l, int col)
    {
        int x = adsrStartX + col * sliderSpacing;
        s.setBounds (x, topOffset + labelH + 4, sliderW, sliderH);
        l.setBounds (x, topOffset + labelH + 4 + sliderH + 2, sliderW, labelH);
    };

    placeAdsr (attackSlider,  attackLabel,  0);
    placeAdsr (decaySlider,   decayLabel,   1);
    placeAdsr (sustainSlider, sustainLabel, 2);
    placeAdsr (releaseSlider, releaseLabel, 3);

    //--------------------------------------------------------------------------
    // Master gain + tuning knobs (right column)
    const int rightX = 390;
    masterGainKnob.setBounds  (rightX, topOffset + labelH + 4,  knobSize, knobSize);
    masterGainLabel.setBounds (rightX, topOffset + labelH + 4 + knobSize + 2, knobSize, labelH);

    tuningKnob.setBounds  (rightX, topOffset + labelH + knobSize + 36, knobSize, knobSize);
    tuningLabel.setBounds (rightX, topOffset + labelH + knobSize * 2 + 38, knobSize, labelH);
}

//==============================================================================
void MySynthAudioProcessorEditor::setupSlider (juce::Slider& slider, juce::Label& label,
                                               const juce::String& labelText,
                                               juce::Slider::SliderStyle style)
{
    slider.setSliderStyle (style);
    slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, 60, 16);
    slider.setColour (juce::Slider::thumbColourId,       juce::Colour (0xff89b4fa));
    slider.setColour (juce::Slider::trackColourId,       juce::Colour (0xff45475a));
    slider.setColour (juce::Slider::rotarySliderOutlineColourId, juce::Colour (0xff45475a));
    slider.setColour (juce::Slider::rotarySliderFillColourId,   juce::Colour (0xff89b4fa));
    slider.setColour (juce::Slider::textBoxTextColourId, juce::Colour (0xffcdd6f4));
    slider.setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
    addAndMakeVisible (slider);

    label.setText (labelText, juce::dontSendNotification);
    label.setJustificationType (juce::Justification::centred);
    label.setColour (juce::Label::textColourId, juce::Colour (0xffa6adc8));
    label.setFont (juce::Font (11.0f));
    addAndMakeVisible (label);
}
