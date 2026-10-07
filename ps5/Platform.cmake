# Native PS5 compile bring-up. No host Vulkan loader is linked.
set(PS5_VULKAN_HEADERS "" CACHE PATH "Directory containing vulkan/vulkan.h")
if(NOT EXISTS "${PS5_VULKAN_HEADERS}/vulkan/vulkan.h")
  message(FATAL_ERROR "Set PS5_VULKAN_HEADERS to the pinned RADV release include directory")
endif()
set(Vulkan_INCLUDE_DIR "${PS5_VULKAN_HEADERS}" CACHE PATH "" FORCE)
# FindVulkan requires a library even though this runtime only consumes its headers.
# The SDL-host link path does not link Vulkan::Vulkan; native linking supplies RADV.
set(Vulkan_LIBRARY "${PS5_PAYLOAD_SDK}/target/lib/libc.a" CACHE FILEPATH "" FORCE)
set(WWHD_BUNDLED_DEPS ON CACHE BOOL "" FORCE)
