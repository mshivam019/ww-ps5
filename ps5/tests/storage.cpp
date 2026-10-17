// SPDX-License-Identifier: MPL-2.0
#include "storage.h"
#include <cassert>
#include <fstream>
#include <iostream>
namespace fs = std::filesystem;
void put(const fs::path& p, const std::string& data) {
    fs::create_directories(p.parent_path()); std::ofstream(p) << data;
}
std::string read(const fs::path& p) {
    std::ifstream in(p); return {std::istreambuf_iterator<char>(in), {}};
}
void game(const fs::path& root) {
    put(root / "game/game.wwhd", "test module fixture");
    put(root / "game/code/cking.rpx", "test executable fixture");
    put(root / "game/content/data", "content");
    put(root / "game/meta/meta.xml", "meta");
}
int main(int argc, char** argv) {
    assert(argc == 2);
    const fs::path root = argv[1];
    ps5_storage::Paths p{root / "app", root / "data", root / "previous", root / "download"};
    game(p.app); put(p.app / "disc.ISO", "own disc image");
    put(p.app / "user/settings.ini", "language=3\n");
    put(p.app / "user/save/slot", "obsolete bundled save");
    put(p.download / "user/save/slot", "old save"); put(p.app / "user/states/1", "state");
    // Resume a previously interrupted import.
    put(p.persistent / "game.importing/content/data", "content");
    auto r = ps5_storage::prepare(p);
    assert(r.error.empty() && r.images == 1);
    assert(read(r.game / "content/data") == "content");
    assert(read(r.save / "slot") == "old save");
    assert(fs::exists(p.app / "disc.ISO"));
    put(r.save / "slot", "newer save");
    put(p.previous / "disc.ISO", "different disc image");
    // Simulate the store replacing the complete installed title.
    fs::remove_all(p.app); fs::create_directories(p.app);
    r = ps5_storage::prepare(p);
    assert(r.error.empty());
    assert(read(r.game / "code/cking.rpx") == "test executable fixture");
    assert(read(r.save / "slot") == "newer save");
    assert(read(r.states / "1") == "state");
    assert(read(r.user / "settings.ini") == "language=3\n");
    assert(read(p.persistent / "images/disc.ISO") == "own disc image");
    assert(read(p.persistent / "images/disc-1.ISO") == "different disc image");
    // A conflicting interrupted copy must retain both inputs.
    ps5_storage::Paths conflict{root / "other-app", root / "other-data", root / "absent", {}};
    game(conflict.app); put(conflict.persistent / "game.importing/content/data", "conflict");
    assert(!ps5_storage::prepare(conflict).error.empty());
    assert(read(conflict.app / "game/content/data") == "content");
    assert(read(conflict.persistent / "game.importing/content/data") == "conflict");
    // No writes through an interrupted destination symlink.
    ps5_storage::Paths links{root / "linked-app", root / "linked-data", root / "absent", {}};
    game(links.app); fs::create_directories(root / "outside");
    fs::create_directories(links.persistent);
    fs::create_directory_symlink(root / "outside", links.persistent / "game.importing");
    assert(!ps5_storage::prepare(links).error.empty());
    assert(fs::is_empty(root / "outside"));
    put(root / "param.json", "{\"titleId\":\"PPSA99649\"}");
    assert(ps5_storage::title_id(root / "param.json") == "PPSA99649");
    assert(!ps5_storage::valid_title_id("../../app"));
    std::cout << "Storage import, update, resume, conflicts and symlinks: PASS\n";
}
