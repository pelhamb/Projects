#include "PluginProcessor.h"
#include "PluginEditor.h"

//==============================================================================
MySynthAudioProcessor::MySynthAudioProcessor()
    : AudioProcessor (BusesProperties()
                          .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "Parameters", createParameterLayout())
{
}

MySynthAudioProcessor::~MySynthAudioProcessor() {}

//==============================================================================
juce::AudioProcessorValueTreeState::ParameterLayout
MySynthAudioProcessor::createParameterLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;

    // Waveform selector: 0=Sine, 1=Square, 2=Saw, 3=Triangle
    layout.add (std::make_unique<juce::AudioParameterInt> (
        ParamID::Waveform, "Waveform", 0, 3, 0));

    // ADSR — all in seconds
    layout.add (std::make_unique<juce::AudioParameterFloat> (
        ParamID::Attack,  "Attack",
        juce::NormalisableRange<float> (0.001f, 5.0f, 0.001f, 0.5f), 0.01f));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        ParamID::Decay,   "Decay",
        juce::NormalisableRange<float> (0.001f, 5.0f, 0.001f, 0.5f), 0.1f));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        ParamID::Sustain, "Sustain",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.001f), 0.8f));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        ParamID::Release, "Release",
        juce::NormalisableRange<float> (0.001f, 10.0f, 0.001f, 0.5f), 0.3f));

    // Master gain
    layout.add (std::make_unique<juce::AudioParameterFloat> (
        ParamID::MasterGain, "Master Gain",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.001f), 0.7f));

    // Coarse tuning ±24 semitones
    layout.add (std::make_unique<juce::AudioParameterFloat> (
        ParamID::Tuning, "Tuning",
        juce::NormalisableRange<float> (-24.0f, 24.0f, 0.01f), 0.0f));

    return layout;
}

//==============================================================================
void MySynthAudioProcessor::prepareToPlay (double /*sampleRate*/, int /*samplesPerBlock*/)
{
    // Milestone 1: no audio engine to prepare yet.
    // Milestone 2 will initialise the VoiceManager here.
}

void MySynthAudioProcessor::releaseResources()
{
    // Nothing to release for milestone 1.
}

bool MySynthAudioProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    // Only stereo (or mono) output; no audio input needed for a synth.
    if (layouts.getMainOutputChannelSet() != juce::AudioChannelSet::stereo() &&
        layouts.getMainOutputChannelSet() != juce::AudioChannelSet::mono())
        return false;

    // No audio input for an instrument
    if (! layouts.getMainInputChannelSet().isDisabled())
        return false;

    return true;
}

//==============================================================================
void MySynthAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                          juce::MidiBuffer& /*midiMessages*/)
{
    juce::ScopedNoDenormals noDenormals;

    // Milestone 1: output silence.
    // Milestone 2 will hand the buffer + midiMessages to the VoiceManager.
    buffer.clear();
}

//==============================================================================
juce::AudioProcessorEditor* MySynthAudioProcessor::createEditor()
{
    return new MySynthAudioProcessorEditor (*this);
}

//==============================================================================
void MySynthAudioProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    // Serialise the APVTS to XML so Ableton can save/restore plugin state.
    auto state = apvts.copyState();
    std::unique_ptr<juce::XmlElement> xml (state.createXml());
    copyXmlToBinary (*xml, destData);
}

void MySynthAudioProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    std::unique_ptr<juce::XmlElement> xmlState (getXmlFromBinary (data, sizeInBytes));
    if (xmlState != nullptr && xmlState->hasTagName (apvts.state.getType()))
        apvts.replaceState (juce::ValueTree::fromXml (*xmlState));
}

//==============================================================================
// DAW-facing factory function
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new MySynthAudioProcessor();
}
