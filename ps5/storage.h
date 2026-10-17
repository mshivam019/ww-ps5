// SPDX-License-Identifier: MPL-2.0
#pragma once
#include <filesystem>
#include <string>
namespace ps5_storage {
struct Paths {
    std::filesystem::path app, persistent, previous, download;
};
struct Result {
    std::filesystem::path game, user, states, save;
    std::string error;
    unsigned images = 0;
};
// Copy and verify personal data before relying on its persistent copy.
// Originals are retained. An interrupted copy can be resumed on next launch.
Result prepare(const Paths& paths);
bool valid_title_id(const std::string& id);
std::string title_id(const std::filesystem::path& param);
}
