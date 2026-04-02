#include "PluginEditor.h"

//==============================================================================
// ADSRVisualizer implementation
//==============================================================================
void ADSRVisualizer::paint (juce::Graphics& g)
{
    const auto bounds = getLocalBounds().toFloat().reduced (4.0f);
    const float w = bounds.getWidth();
    const float h = bounds.getHeight();
    const float x0 = bounds.getX();
    const float y0 = bounds.getY();

    // Dark sub-panel background
    g.setColour (juce::Colour (0xff181825));
    g.fillRoundedRectangle (bounds, 4.0f);

    // Faint grid line at sustain level
    g.setColour (juce::Colour (0xff313244));
    g.drawHorizontalLine (static_cast<int> (y0 + h), x0, x0 + w);

    // Read current parameter values
    const float attack  = (float) attackSlider.getValue();   // 0.001 – 5.0 s
    const float decay   = (float) decaySlider.getValue();    // 0.001 – 5.0 s
    const float sustain = (float) sustainSlider.getValue();  // 0.0 – 1.0
    const float release = (float) releaseSlider.getValue();  // 0.001 – 10.0 s

    // Normalise time segments so they always fill the width nicely.
    // Give sustain a fixed visual hold width (20 % of the graph).
    const float sustainHold = 0.20f;
    const float timeTotal = attack + decay + release;
    const float timeFactor = (timeTotal > 0.0f) ? (1.0f - sustainHold) / timeTotal : 1.0f;

    const float normA = attack  * timeFactor;
    const float normD = decay   * timeFactor;
    const float normR = release * timeFactor;

    // Five key points:
    //   P0 = start (0, 0 amplitude)
    //   P1 = end of attack (attack, 1.0)
    //   P2 = end of decay  (attack+decay, sustain)
    //   P3 = end of sustain hold (attack+decay+hold, sustain)
    //   P4 = end of release (1.0, 0)
    auto toScreen = [&](float nx, float ny) -> juce::Point<float>
    {
        return { x0 + nx * w, y0 + (1.0f - ny) * h };
    };

    const auto p0 = toScreen (0.0f, 0.0f);
    const auto p1 = toScreen (normA, 1.0f);
    const auto p2 = toScreen (normA + normD, sustain);
    const auto p3 = toScreen (normA + normD + sustainHold, sustain);
    const auto p4 = toScreen (normA + normD + sustainHold + normR, 0.0f);

    // Draw envelope line
    juce::Path envelope;
    envelope.startNewSubPath (p0);
    envelope.lineTo (p1);
    envelope.lineTo (p2);
    envelope.lineTo (p3);
    envelope.lineTo (p4);

    g.setColour (juce::Colour (0xff89b4fa));
    g.strokePath (envelope, juce::PathStrokeType (2.0f));

    // Draw dots at the four ADSR control points (p1–p4)
    const float dotRadius = 4.0f;
    g.setColour (juce::Colour (0xffcba6f7));   // purple accent for dots
    for (auto& pt : { p1, p2, p3, p4 })
        g.fillEllipse (pt.x - dotRadius, pt.y - dotRadius,
                       dotRadius * 2.0f, dotRadius * 2.0f);
}

//==============================================================================
// Editor implementation
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
    // ADSR visualizer
    addAndMakeVisible (adsrVisualizer);

    //==========================================================================
    // Master gain & tuning (rotary)
    setupSlider (masterGainKnob, masterGainLabel, "Volume");
    setupSlider (tuningKnob,     tuningLabel,     "Tuning");

    masterGainAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::MasterGain, masterGainKnob);
    tuningAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        apvts, ParamID::Tuning, tuningKnob);

    //==========================================================================
    setSize (520, 380);
}

MySynthAudioProcessorEditor::~MySynthAudioProcessorEditor() {}

//==============================================================================
void MySynthAudioProcessorEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1e1e2e));   // dark background

    g.setColour (juce::Colour (0xff89b4fa));  // accent blue
    g.setFont (juce::Font (16.0f, juce::Font::bold));
    g.drawFittedText ("Synthphia - Milestone 4", getLocalBounds().removeFromTop (28),
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
    // ADSR visualizer graph (below the sliders)
    const int graphH = 80;
    const int graphW = 4 * sliderSpacing;                 // same width as the 4 sliders
    const int graphY = topOffset + labelH + 4 + sliderH + labelH + 8;
    adsrVisualizer.setBounds (adsrStartX, graphY, graphW, graphH);

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
