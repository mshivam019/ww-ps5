#pragma once
#include <vulkan/vulkan.h>
namespace ps5ww {
PFN_vkGetInstanceProcAddr instance_proc();
VkSurfaceKHR display_surface(VkInstance instance, uint32_t& width, uint32_t& height);
}
