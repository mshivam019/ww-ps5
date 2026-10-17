// SPDX-License-Identifier: MPL-2.0
// Identify special rendering passes by their program, wherever the game loads it.
#pragma once
#include <bit>
#include <cstdint>
#include <cstring>

namespace gfx {
// Same program hash as Cemu, independent of the regional load address.
inline uint64_t regional_program_hash(const void* bytes, uint32_t size) {
    uint64_t a = 0, b = 0;
    for (uint32_t i = 0; i < size / 4; ++i) {
        uint32_t word;
        std::memcpy(&word, static_cast<const uint8_t*>(bytes) + i * 4, 4);
        a = std::rotl(a + word, 3); b = std::rotr(b ^ word, 7);
    }
    return a + b;
}
enum class ProgramKind { Other, DepthDownsample, OcclusionPixel, OcclusionVertex };
inline ProgramKind program_kind(const void* bytes, uint32_t size, bool vertex) {
    if (!bytes) return ProgramKind::Other;
    if (vertex && size == 384 && regional_program_hash(bytes, size) == 0xd279c909832a6f45ull)
        return ProgramKind::OcclusionVertex;
    if (!vertex && size == 416 && regional_program_hash(bytes, size) == 0xf49059587d7d9669ull)
        return ProgramKind::DepthDownsample;
    if (!vertex && size == 1584 && regional_program_hash(bytes, size) == 0xc2cae30e906b6255ull)
        return ProgramKind::OcclusionPixel;
    return ProgramKind::Other;
}
} // namespace gfx
