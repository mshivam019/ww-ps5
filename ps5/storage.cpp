// SPDX-License-Identifier: MPL-2.0
#include "storage.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <fstream>
#include <stdexcept>
namespace ps5_storage {
namespace fs = std::filesystem;
namespace {
void safe_directories(const fs::path& directory) {
    fs::path current;
    for (const auto& component : directory) {
        current /= component;
        if (fs::is_symlink(current)) throw std::runtime_error("Import path contains a symbolic link");
        if (fs::exists(current) && !fs::is_directory(current))
            throw std::runtime_error("Import path contains a non-directory");
    }
    fs::create_directories(directory);
}
bool same(const fs::path& left, const fs::path& right) {
    if (fs::is_symlink(left) || fs::is_symlink(right) ||
        !fs::is_regular_file(left) || !fs::is_regular_file(right)) return false;
    if (fs::file_size(left) != fs::file_size(right)) return false;
    std::ifstream a(left, std::ios::binary), b(right, std::ios::binary);
    if (!a || !b) return false;
    std::array<char, 65536> x{}, y{};
    while (a && b) {
        a.read(x.data(), x.size()); b.read(y.data(), y.size());
        if (a.gcount() != b.gcount() ||
            !std::equal(x.begin(), x.begin() + a.gcount(), y.begin())) return false;
    }
    return !a.bad() && !b.bad();
}
void verified_copy(const fs::path& source, const fs::path& destination) {
    if (fs::is_symlink(source) || !fs::is_regular_file(source))
        throw std::runtime_error("Personal data contains a non-regular file");
    if (fs::exists(destination)) {
        if (fs::is_symlink(destination) || !fs::is_regular_file(destination) ||
            !same(source, destination))
            throw std::runtime_error("A different persistent file already exists: " + destination.string());
        return;
    }
    safe_directories(destination.parent_path());
    const fs::path temporary = destination.string() + ".importing";
    if (fs::is_symlink(temporary) || (fs::exists(temporary) && !fs::is_regular_file(temporary)))
        throw std::runtime_error("Unsafe interrupted import path");
    fs::copy_file(source, temporary, fs::copy_options::overwrite_existing);
    if (!same(source, temporary)) throw std::runtime_error("Personal data verification failed");
    fs::rename(temporary, destination);
}
bool game_ready(const fs::path& game) {
    // Monolithic builds also use this migration; they have no separate module.
    return !fs::is_symlink(game) && fs::is_regular_file(game / "code/cking.rpx") &&
           fs::is_directory(game / "content") && fs::is_directory(game / "meta");
}
void copy_game(const fs::path& source, const fs::path& destination) {
    const fs::path temporary = destination.string() + ".importing";
    safe_directories(temporary);
    for (const auto& entry : fs::recursive_directory_iterator(source)) {
        if (entry.is_symlink()) throw std::runtime_error("Game folder contains a symbolic link");
        const auto relative = entry.path().lexically_relative(source);
        if (entry.is_directory()) safe_directories(temporary / relative);
        else verified_copy(entry.path(), temporary / relative);
    }
    // Refuse to merge an interrupted import from a different game package.
    for (const auto& entry : fs::recursive_directory_iterator(temporary)) {
        const auto original = source / entry.path().lexically_relative(temporary);
        if (entry.is_symlink() || !fs::exists(original))
            throw std::runtime_error("Interrupted game import differs from this package");
    }
    if (!game_ready(temporary)) throw std::runtime_error("Incomplete persistent game copy");
    fs::rename(temporary, destination);
}
bool image(const fs::path& path) {
    auto ext = path.extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(),
        [](unsigned char c) { return char(std::tolower(c)); });
    return ext == ".iso" || ext == ".wua" || ext == ".wud" || ext == ".wux";
}
void preserve_images(const fs::path& source, const fs::path& destination, unsigned& count) {
    if (!fs::is_directory(source)) return;
    for (const auto& entry : fs::directory_iterator(source)) {
        if (!image(entry.path())) continue;
        if (entry.is_symlink()) throw std::runtime_error("Disc image is a symbolic link");
        if (!entry.is_regular_file()) continue;
        auto target = destination / entry.path().filename();
        unsigned suffix = 1;
        while (fs::exists(target) && !same(entry.path(), target))
            target = destination / (entry.path().stem().string() + "-" +
                std::to_string(suffix++) + entry.path().extension().string());
        verified_copy(entry.path(), target);
        ++count;
    }
}
void import_user(const fs::path& source, const fs::path& destination) {
    if (!fs::is_directory(source)) return;
    if (fs::is_symlink(source)) throw std::runtime_error("User folder is a symbolic link");
    for (const auto& entry : fs::recursive_directory_iterator(source)) {
        if (entry.is_symlink()) throw std::runtime_error("User folder contains a symbolic link");
        if (!entry.is_regular_file()) continue;
        const auto target = destination / entry.path().lexically_relative(source);
        if (!fs::exists(target)) verified_copy(entry.path(), target);
    }
}
}
bool valid_title_id(const std::string& id) {
    return id.size() == 9 &&
        std::all_of(id.begin(), id.begin()+4, [](char c) { return c >= 'A' && c <= 'Z'; }) &&
        std::all_of(id.begin()+4, id.end(), [](char c) { return c >= '0' && c <= '9'; });
}
std::string title_id(const fs::path& param) {
    std::ifstream input(param);
    std::string json;
    char c;
    while (json.size() < 16384 && input.get(c)) json += c;
    const auto key = json.find("\"titleId\"");
    if (key != std::string::npos) {
        const auto colon = json.find(':', key+9);
        const auto start = colon == std::string::npos ? colon : json.find('"', colon+1);
        if (start != std::string::npos) {
            const auto end = json.find('"', start+1);
            const auto id = json.substr(start+1, end-start-1);
            if (valid_title_id(id)) return id;
        }
    }
    throw std::runtime_error("Cannot read this app's title ID");
}
Result prepare(const Paths& paths) {
    Result result;
    result.game = paths.persistent / "game";
    result.user = paths.persistent / "user";
    result.states = result.user / "states";
    result.save = result.user / "save";
    try {
        safe_directories(paths.persistent);
        safe_directories(result.user);
        preserve_images(paths.app, paths.persistent / "images", result.images);
        preserve_images(paths.previous, paths.persistent / "images", result.images);
        if (!game_ready(result.game)) {
            if (fs::exists(result.game))
                throw std::runtime_error("Persistent game folder is incomplete; repair it with the matching setup");
            if (game_ready(paths.app / "game")) copy_game(paths.app / "game", result.game);
            else if (game_ready(paths.previous / "game")) copy_game(paths.previous / "game", result.game);
        }
        // /download0 and /app0 need not expose the same writable user folder.
        if (!paths.download.empty()) import_user(paths.download / "user", result.user);
        import_user(paths.app / "user", result.user);
        import_user(paths.previous / "user", result.user);
        safe_directories(result.states);
        safe_directories(result.save);
    } catch (const std::exception& ex) {
        result.error = std::string("Could not protect game data before updates: ") + ex.what() +
            ". Original files were retained. Check access and free space in " + paths.persistent.string();
    }
    return result;
}
}
