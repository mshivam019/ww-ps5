// Standalone host-side tests; no game files, player settings or guest code needed.
#include "mods/manager.h"
#include "mods/mods.h"
#include "mods/climb.h"
#include "overlay/hostui.h"
#include <cassert>
#include <cstdlib>
#include <map>
#include <string>

namespace {
bool state[6]{};
float speed = 1, sensitivity = .15f;
std::map<std::string,std::string> preferences;
int reads = 0, writes = 0;
void env(const char* key, const char* value) {
#ifdef _WIN32
    _putenv_s(key, value ? value : "");
#else
    if (value) setenv(key,value,1); else unsetenv(key);
#endif
}
}
namespace mods {
bool direct_camera() { return state[0]; } void set_direct_camera(bool b) { state[0]=b; }
bool mouse_camera() { return state[1]; } void set_mouse_camera(bool b) { state[1]=b; }
bool first_person_wheel() { return state[2]; } void set_first_person_wheel(bool b) { state[2]=b; }
bool climb_enabled() { return state[3]; } void set_climb_enabled(bool b) { state[3]=b; }
bool quick_doors() { return state[4]; } void set_quick_doors(bool b) { state[4]=b; }
bool fast_scenes() { return state[5]; } void set_fast_scenes(bool b) { state[5]=b; }
float camera_speed() { return speed; }
void set_camera_speed(float f) { speed=f; }
float mouse_sensitivity() { return sensitivity; }
void set_mouse_sensitivity(float f) { sensitivity=f; }
}
namespace hostui {
bool get(const char* k, std::string& value) {
    ++reads; auto it=preferences.find(k);
    if(it==preferences.end()) return false;
    value=it->second;return true;
}
void set(const char* k, const std::string& value) { ++writes;preferences[k]=value; }
}
#include "mods/packages.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <chrono>
namespace {
mods::packages::View view(const std::string& id) {for(auto v:mods::packages::list())if(v.id==id)return v;return {};}
// Second process on the same storage: a confirmed native package loads after a restart without asking.
int restart_check(const char* storage) {
    using namespace mods::packages;
    env("WWHD_NO_HOST_INPUT","1");env("WWHD_MOD_MANAGER_DIR",storage);env("WWHD_TEST_TRUST_NATIVE_MODS",nullptr);
    initialize();std::string error;
    assert(view("fixture").enabled && view("fixture").native_confirmed && unconfirmed_native("fixture").empty());
    frame(1);assert(view("fixture").active && view("fixture").status=="changed");
    assert(enable("fixture",false,error));frame(2);assert(!view("fixture").active);
    return 0;
}
}
int main(int argc, char** argv) {
    namespace fs=std::filesystem;
    using namespace mods::packages;
    if(argc == 3 && std::string(argv[1]) == "--restart") return restart_check(argv[2]);
    assert(argc == 3 || argc == 4);
    env("WWHD_TEST_TRUST_NATIVE_MODS",nullptr);
    auto root=fs::path(argv[1])/std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    assert(!fs::exists(root));
    fs::create_directories(root);
    env("WWHD_NO_HOST_INPUT","1");
    env("WWHD_MOD_MANAGER_DIR",(root/"storage").string().c_str());
    initialize();
    std::string error;
    auto package=[&](const char* id, const char* extra, const char* setting="wall-climb") {
        auto path=root/id;fs::create_directories(path);
        std::ofstream(path/"manifest.json") << "{\"format_version\":1,\"id\":\"" << id
          << "\",\"name\":\"" << id << "\",\"version\":\"1.0.0\",\"game_id\":\"wwhd-usa\","
          << "\"kind\":\"settings\",\"settings\":{\"" << setting << "\":true}" << extra << "}";
        return path.string();
    };
    assert(install(package("climb-preset",""),error));
    assert(list().size()==1 && list()[0].id=="climb-preset");
    assert(list()[0].native_confirmed && unconfirmed_native("climb-preset").empty()); // settings presets never ask
    assert(enable("climb-preset",true,error));frame(1);assert(state[3] && list()[0].active);
    assert(!remove("climb-preset",error));
    assert(enable("climb-preset",false,error));frame(2);assert(!state[3]);
    assert(create_profile("Adventure",error));
    assert(enable("climb-preset",true,error));frame(20);assert(state[3]);
    assert(select_profile("Adventure",error));frame(21);assert(!state[3]);
    assert(current_profile()=="Adventure");assert(!delete_profile("Adventure",error));
    assert(select_profile("Default",error));assert(delete_profile("Adventure",error));
    assert(install(package("missing-dep",",\"dependencies\":[{\"id\":\"absent\"}]"),error));
    assert(!enable("missing-dep",true,error));
    assert(remove("missing-dep",error));
    assert(install(package("cycle-a",",\"dependencies\":[{\"id\":\"cycle-b\"}]"),error));
    assert(install(package("cycle-b",",\"dependencies\":[{\"id\":\"cycle-a\"}]","quick-doors"),error));
    assert(!enable("cycle-a",true,error));assert(error.find("cycle")!=std::string::npos);
    assert(remove("cycle-a",error));assert(remove("cycle-b",error));
    assert(install(package("conflicting",",\"conflicts\":[\"climb-preset\"]","quick-doors"),error));
    assert(!enable("conflicting",true,error));assert(remove("conflicting",error));
    assert(install(package("typed",R"(,"options":[{"id":"toggle","name":"Toggle","type":"bool","default":false},{"id":"rate","name":"Rate","type":"number","min":1,"max":10,"default":2},{"id":"mode","name":"Mode","type":"enum","choices":["a","b"],"default":"a"}])","quick-doors"),error));
    assert(configure("typed","toggle",true,error));assert(!configure("typed","toggle",1,error));
    assert(configure("typed","rate",5,error));assert(!configure("typed","rate",11,error));
    assert(configure("typed","mode","b",error));assert(!configure("typed","mode","c",error));
    assert(install((root/"typed").string(),error));assert(remove("typed",error));
    auto bad=root/"bad.wwhdmod";std::ofstream(bad)<<"not a package";assert(!install(bad.string(),error));
    auto native=root/"native";fs::create_directories(native);
    fs::copy_file(argv[2],native/"fixture.dylib");
    std::ofstream(native/"manifest.json") << "{\"format_version\":1,\"id\":\"fixture\",\"name\":\"Fixture\",\"version\":\"1.0.0\",\"game_id\":\"wwhd-usa\",\"kind\":\"native\",\"abi_version\":1,\"binaries\":{\""
      << platform_key() << "\":\"fixture.dylib\"},\"options\":[{\"id\":\"label\",\"name\":\"Label\",\"type\":\"string\",\"default\":\"initial\"}]}";
    assert(install(native.string(),error));
    auto find=[] {return view("fixture");};
    auto storage=root/"storage";
    auto trusted=[&] {std::ifstream f(storage/"profiles.json");std::string text{std::istreambuf_iterator<char>(f),{}};
        auto value=mods::json::parse(text);return value.get("native_trust").get("fixture").string();};
    // Unconfirmed native code: enable() refuses and nothing loads until the player confirms.
    assert(!find().native_confirmed);
    auto pending=unconfirmed_native("fixture");assert(pending.size()==1 && pending[0].first=="fixture" && pending[0].second=="Fixture");
    assert(!enable("fixture",true,error));assert(error.find("native code")!=std::string::npos);
    frame(3);assert(!find().active && !find().enabled);
    // A settings preset that requires the native package names it in the confirmation.
    assert(install(package("needs-native",",\"dependencies\":[{\"id\":\"fixture\"}]","fast-scenes"),error));
    pending=unconfirmed_native("needs-native");assert(pending.size()==1 && pending[0].first=="fixture");
    assert(!enable("needs-native",true,error));assert(remove("needs-native",error));
    // Test aid: pre-confirmed only in isolated test runs, and never written to profiles.json.
    env("WWHD_TEST_TRUST_NATIVE_MODS","other,fixture");assert(find().native_confirmed && unconfirmed_native("fixture").empty());
    env("WWHD_TEST_TRUST_NATIVE_MODS",nullptr);assert(!find().native_confirmed && trusted().empty());
    assert(confirm_native("fixture",error));assert(trusted().size()==64);
    assert(find().native_confirmed && unconfirmed_native("fixture").empty());
    assert(!confirm_native("climb-preset",error));
    assert(enable("fixture",true,error));frame(6);
    assert(find().active && find().status=="initial");
    assert(configure("fixture","label","changed",error));frame(4);assert(find().status=="changed");
    assert(!configure("fixture","label",42,error));
    assert(enable("fixture",false,error));frame(5);assert(!find().active);
    // Confirmed: a new process loads it from the saved profile without asking again.
    assert(enable("fixture",true,error));frame(7);assert(find().active);
    std::string restart="\""+std::string(argv[0])+"\" --restart \""+storage.string()+"\"";
#ifdef _WIN32
    restart="\""+restart+"\"";  // cmd.exe /c drops the outer quotes of a line that starts with one
#endif
    assert(std::system(restart.c_str())==0);
    // That process disabled it; this one keeps its own view until told, so follow the saved state.
    assert(enable("fixture",false,error));frame(8);assert(!find().active);
    // A changed library under the same ID asks again, including when a profile switch would load it.
    assert(create_profile("Native",error));assert(select_profile("Native",error));
    assert(enable("fixture",true,error));frame(9);assert(find().active);
    assert(select_profile("Default",error));frame(10);assert(!find().active);
    auto before=trusted();
    std::ofstream(native/"fixture.dylib",std::ios::binary|std::ios::app) << "changed build";
    assert(install(native.string(),error));assert(!find().native_confirmed && trusted()==before);
    assert(select_profile("Native",error));frame(11);
    assert(!find().active && !find().enabled && find().reason.find("native code you have not confirmed")!=std::string::npos);
    assert(unconfirmed_native("fixture").size()==1 && !enable("fixture",true,error));
    assert(confirm_native("fixture",error));assert(trusted()!=before);
    assert(enable("fixture",true,error));frame(12);assert(find().active && find().reason.empty());
    assert(enable("fixture",false,error));frame(13);assert(select_profile("Default",error));assert(delete_profile("Native",error));
    // Removing forgets the confirmation; reinstalling asks again.
    assert(remove("fixture",error));assert(trusted().empty());
    assert(install(native.string(),error));assert(!find().native_confirmed);
    assert(remove("fixture",error));assert(enable("climb-preset",false,error));frame(30);assert(remove("climb-preset",error));
    assert(list().empty());
    if(argc == 4) {
        assert(install(argv[3],error));
        auto id=list().at(0).id;
        if(list()[0].kind=="native") {assert(!enable(id,true,error));assert(confirm_native(id,error));}
        assert(enable(id,true,error));frame(40);assert(list()[0].active);
        assert(configure(id,"label","ZIP works",error));frame(41);
        assert(list()[0].status.starts_with("ZIP works"));
        assert(enable(id,false,error));frame(42);assert(remove(id,error));
    }
    std::cout << "Package install, settings, profiles, dependencies, native load/config/unload passed\n";
}
