cmake_minimum_required(VERSION 3.22)
project(MySynth VERSION 0.1.0)

# JUCE must be cloned as a submodule:
#   git submodule add https://github.com/juce-framework/JUCE.git
add_subdirectory(JUCE)

juce_add_plugin(MySynth
    COMPANY_NAME "Valhalla"
    PLUGIN_MANUFACTURER_CODE Vlhl
    PLUGIN_CODE Sp01
    FORMATS VST3 AU
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    PRODUCT_NAME "Synthphia1"
)

target_sources(MySynth PRIVATE
    Source/PluginProcessor.cpp
    Source/PluginEditor.cpp
    Source/synth/VoiceManager.cpp
    Source/synth/SynthVoice.cpp
)

target_compile_features(MySynth PUBLIC cxx_std_17)

target_compile_definitions(MySynth PUBLIC
    JUCE_VST3_CAN_REPLACE_VST2=0
)

target_link_libraries(MySynth PRIVATE
    juce::juce_audio_utils
    juce::juce_dsp
    juce::juce_gui_basics
    juce::juce_gui_extra
)

# Silence JUCE's recommendation to use their recommended flags
juce_generate_juce_header(MySynth)
