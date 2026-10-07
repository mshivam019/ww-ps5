// VideoOut presentation through the PS5 RADV VK_KHR_display interface.
// Based on the display contract demonstrated by PS5_VulkanTemplate and
// PS5CEMU-HAR (premohq); no desktop Vulkan loader or window surface is used.
#include "display.h"
#include <algorithm>
#include <cstdio>
#include <stdexcept>
#include <vector>
extern "C" VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL
vk_icdGetInstanceProcAddr(VkInstance, const char*);
namespace ps5ww {
PFN_vkGetInstanceProcAddr instance_proc() { return &vk_icdGetInstanceProcAddr; }
static void check(VkResult result, const char* operation) {
    if (result != VK_SUCCESS)
        throw std::runtime_error(std::string(operation) + ": " + std::to_string(int(result)));
}
VkSurfaceKHR display_surface(VkInstance instance, uint32_t& width, uint32_t& height) {
#define LOAD(name) \
    auto name = reinterpret_cast<PFN_##name>(instance_proc()(instance, #name)); \
    if (!name) throw std::runtime_error("Missing display entry point: " #name)
    LOAD(vkEnumeratePhysicalDevices);
    LOAD(vkGetPhysicalDeviceDisplayPropertiesKHR);
    LOAD(vkGetDisplayModePropertiesKHR);
    LOAD(vkGetPhysicalDeviceDisplayPlanePropertiesKHR);
    LOAD(vkGetDisplayPlaneSupportedDisplaysKHR);
    LOAD(vkGetDisplayPlaneCapabilitiesKHR);
    LOAD(vkCreateDisplayPlaneSurfaceKHR);
#undef LOAD
    uint32_t count = 0;
    check(vkEnumeratePhysicalDevices(instance, &count, nullptr), "Enumerate PS5 GPU");
    if (!count) throw std::runtime_error("RADV reports no PS5 GPU");
    std::vector<VkPhysicalDevice> devices(count);
    check(vkEnumeratePhysicalDevices(instance, &count, devices.data()), "Read PS5 GPUs");
    const auto device = devices.front();
    count = 0;
    check(vkGetPhysicalDeviceDisplayPropertiesKHR(device, &count, nullptr), "Enumerate VideoOut");
    if (!count) throw std::runtime_error("No VideoOut display");
    std::vector<VkDisplayPropertiesKHR> displays(count);
    check(vkGetPhysicalDeviceDisplayPropertiesKHR(device, &count, displays.data()), "Read VideoOut");
    const auto display = displays.front().display;
    count = 0;
    check(vkGetDisplayModePropertiesKHR(device, display, &count, nullptr), "Enumerate display modes");
    std::vector<VkDisplayModePropertiesKHR> modes(count);
    check(vkGetDisplayModePropertiesKHR(device, display, &count, modes.data()), "Read display modes");
    // Start with the same 4K 59.94 Hz output used by the tested Dusklight title.
    const auto mode = std::find_if(modes.begin(), modes.end(), [](const auto& m) {
        return m.parameters.visibleRegion.width == 3840 && m.parameters.visibleRegion.height == 2160 &&
               m.parameters.refreshRate >= 59000 && m.parameters.refreshRate <= 61000;
    });
    if (mode == modes.end()) throw std::runtime_error("VideoOut lacks 3840x2160 at 60 Hz");
    fprintf(stderr, "[display] selected %ux%u at %.3f Hz\n", mode->parameters.visibleRegion.width, mode->parameters.visibleRegion.height, mode->parameters.refreshRate / 1000.0);
    count = 0;
    check(vkGetPhysicalDeviceDisplayPlanePropertiesKHR(device, &count, nullptr), "Enumerate planes");
    std::vector<VkDisplayPlanePropertiesKHR> planes(count);
    check(vkGetPhysicalDeviceDisplayPlanePropertiesKHR(device, &count, planes.data()), "Read planes");
    for (uint32_t index = 0; index < planes.size(); ++index) {
        uint32_t supported = 0;
        check(vkGetDisplayPlaneSupportedDisplaysKHR(device, index, &supported, nullptr), "Enumerate plane displays");
        std::vector<VkDisplayKHR> supported_displays(supported);
        check(vkGetDisplayPlaneSupportedDisplaysKHR(device, index, &supported, supported_displays.data()), "Read plane displays");
        if (std::find(supported_displays.begin(), supported_displays.end(), display) == supported_displays.end()) continue;
        VkDisplayPlaneCapabilitiesKHR caps{};
        check(vkGetDisplayPlaneCapabilitiesKHR(device, mode->displayMode, index, &caps), "Read plane capabilities");
        if (!(caps.supportedAlpha & VK_DISPLAY_PLANE_ALPHA_OPAQUE_BIT_KHR)) continue;
        VkDisplaySurfaceCreateInfoKHR info{VK_STRUCTURE_TYPE_DISPLAY_SURFACE_CREATE_INFO_KHR};
        info.displayMode = mode->displayMode;
        info.planeIndex = index;
        info.planeStackIndex = planes[index].currentStackIndex;
        info.transform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR;
        info.globalAlpha = 1.0f;
        info.alphaMode = VK_DISPLAY_PLANE_ALPHA_OPAQUE_BIT_KHR;
        info.imageExtent = mode->parameters.visibleRegion;
        VkSurfaceKHR surface = VK_NULL_HANDLE;
        check(vkCreateDisplayPlaneSurfaceKHR(instance, &info, nullptr, &surface), "Create VideoOut surface");
        width = info.imageExtent.width;
        height = info.imageExtent.height;
        return surface;
    }
    throw std::runtime_error("No compatible VideoOut plane");
}
}
