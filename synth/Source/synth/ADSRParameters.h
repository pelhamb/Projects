#pragma once

//==============================================================================
// Plain struct for passing ADSR values from the processor to voices.
// Keeps the interface between layers clean.
struct ADSRParameters
{
    float attack  { 0.01f };   // seconds
    float decay   { 0.1f };    // seconds
    float sustain { 0.8f };    // 0.0 – 1.0
    float release { 0.3f };    // seconds
};
