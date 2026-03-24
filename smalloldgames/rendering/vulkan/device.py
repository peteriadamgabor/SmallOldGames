from __future__ import annotations

from typing import Any

import glfw
from vulkan import (
    VK_API_VERSION_1_0,
    VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    VK_KHR_SWAPCHAIN_EXTENSION_NAME,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_QUEUE_GRAPHICS_BIT,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SAMPLE_COUNT_2_BIT,
    VK_SAMPLE_COUNT_4_BIT,
    VK_SHARING_MODE_EXCLUSIVE,
    VK_SUCCESS,
    VkApplicationInfo,
    VkBufferCreateInfo,
    VkCommandPoolCreateInfo,
    VkDeviceCreateInfo,
    VkDeviceQueueCreateInfo,
    VkInstanceCreateInfo,
    VkMemoryAllocateInfo,
    VkPhysicalDeviceFeatures,
    ffi,
    vkAllocateMemory,
    vkBindBufferMemory,
    vkCreateBuffer,
    vkCreateCommandPool,
    vkCreateDevice,
    vkCreateInstance,
    vkDestroyBuffer,
    vkDestroyCommandPool,
    vkDestroyDevice,
    vkDestroyInstance,
    vkEnumerateDeviceExtensionProperties,
    vkEnumeratePhysicalDevices,
    vkFreeMemory,
    vkGetBufferMemoryRequirements,
    vkGetDeviceProcAddr,
    vkGetDeviceQueue,
    vkGetInstanceProcAddr,
    vkGetPhysicalDeviceMemoryProperties,
    vkGetPhysicalDeviceProperties,
    vkGetPhysicalDeviceQueueFamilyProperties,
    vkMapMemory,
    vkUnmapMemory,
)

from .constants import MAX_VERTEX_BYTES
from .types import QueueFamilies


def _max_usable_sample_count(properties) -> int:
    """Return the highest MSAA sample count supported, capped at 4x."""
    counts = properties.limits.framebufferColorSampleCounts
    if counts & VK_SAMPLE_COUNT_4_BIT:
        return VK_SAMPLE_COUNT_4_BIT
    if counts & VK_SAMPLE_COUNT_2_BIT:
        return VK_SAMPLE_COUNT_2_BIT
    return VK_SAMPLE_COUNT_1_BIT


def find_memory_type(renderer: Any, type_filter: int, properties: int) -> int:
    memory_properties = vkGetPhysicalDeviceMemoryProperties(renderer.physical_device)
    for index in range(memory_properties.memoryTypeCount):
        memory_type = memory_properties.memoryTypes[index]
        if (type_filter & (1 << index)) and (memory_type.propertyFlags & properties) == properties:
            return index
    raise RuntimeError("No suitable Vulkan memory type found.")


def create_buffer(renderer: Any, size: int, usage: int, memory_properties: int) -> tuple[object, object]:
    buffer_info = VkBufferCreateInfo(
        size=size,
        usage=usage,
        sharingMode=VK_SHARING_MODE_EXCLUSIVE,
    )
    buffer = vkCreateBuffer(renderer.device, buffer_info, None)
    requirements = vkGetBufferMemoryRequirements(renderer.device, buffer)
    memory = vkAllocateMemory(
        renderer.device,
        VkMemoryAllocateInfo(
            allocationSize=requirements.size,
            memoryTypeIndex=find_memory_type(renderer, requirements.memoryTypeBits, memory_properties),
        ),
        None,
    )
    vkBindBufferMemory(renderer.device, buffer, memory, 0)
    return buffer, memory


class VulkanDevice:
    def __init__(self, renderer: Any) -> None:
        self.renderer = renderer

    def initialize(self) -> None:
        self._create_instance()
        self._load_instance_extensions()
        self._create_surface()
        self._pick_physical_device()
        self._create_logical_device()
        self._load_device_extensions()
        self._create_command_pool()
        self._create_vertex_buffer()

    def close(self) -> None:
        if self.renderer.device is not None and self.renderer.vertex_mapping is not None:
            vkUnmapMemory(self.renderer.device, self.renderer.vertex_memory)
        if self.renderer.device is not None and self.renderer.vertex_buffer is not None:
            vkDestroyBuffer(self.renderer.device, self.renderer.vertex_buffer, None)
        if self.renderer.device is not None and self.renderer.vertex_memory is not None:
            vkFreeMemory(self.renderer.device, self.renderer.vertex_memory, None)
        if self.renderer.device is not None and self.renderer.command_pool is not None:
            vkDestroyCommandPool(self.renderer.device, self.renderer.command_pool, None)

        if self.renderer.device is not None:
            vkDestroyDevice(self.renderer.device, None)

        if (
            self.renderer.instance is not None
            and self.renderer.surface is not None
            and self.renderer.fp_destroy_surface is not None
        ):
            self.renderer.fp_destroy_surface(self.renderer.instance, self.renderer.surface, None)
        if self.renderer.instance is not None:
            vkDestroyInstance(self.renderer.instance, None)

    def _create_instance(self) -> None:
        required_extensions = glfw.get_required_instance_extensions()
        if not required_extensions:
            raise RuntimeError("GLFW did not provide Vulkan surface extensions.")
        extension_names = [
            extension.decode() if isinstance(extension, bytes) else extension for extension in required_extensions
        ]

        app_info = VkApplicationInfo(
            pApplicationName=b"SmallOldGames",
            applicationVersion=1,
            pEngineName=b"SmallOldGames",
            engineVersion=1,
            apiVersion=VK_API_VERSION_1_0,
        )
        create_info = VkInstanceCreateInfo(
            pApplicationInfo=app_info,
            enabledExtensionCount=len(extension_names),
            ppEnabledExtensionNames=extension_names,
        )
        self.renderer.instance = vkCreateInstance(create_info, None)

    def _load_instance_extensions(self) -> None:
        self.renderer.fp_destroy_surface = vkGetInstanceProcAddr(self.renderer.instance, "vkDestroySurfaceKHR")
        self.renderer.fp_get_surface_support = vkGetInstanceProcAddr(
            self.renderer.instance, "vkGetPhysicalDeviceSurfaceSupportKHR"
        )
        self.renderer.fp_get_surface_capabilities = vkGetInstanceProcAddr(
            self.renderer.instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR"
        )
        self.renderer.fp_get_surface_formats = vkGetInstanceProcAddr(
            self.renderer.instance, "vkGetPhysicalDeviceSurfaceFormatsKHR"
        )
        self.renderer.fp_get_surface_present_modes = vkGetInstanceProcAddr(
            self.renderer.instance, "vkGetPhysicalDeviceSurfacePresentModesKHR"
        )

    def _create_surface(self) -> None:
        surface_ptr = ffi.new("VkSurfaceKHR*")
        result = glfw.create_window_surface(self.renderer.instance, self.renderer.window, None, surface_ptr)
        if result != VK_SUCCESS:
            raise RuntimeError(f"glfwCreateWindowSurface failed with VkResult {result}.")
        self.renderer.surface = surface_ptr[0]

    def _pick_physical_device(self) -> None:
        for physical_device in vkEnumeratePhysicalDevices(self.renderer.instance):
            queue_families = self._find_queue_families(physical_device)
            if queue_families is None:
                continue
            if not self._supports_swapchain_extension(physical_device):
                continue
            if not len(self.renderer.fp_get_surface_formats(physical_device, self.renderer.surface)):
                continue
            if not len(self.renderer.fp_get_surface_present_modes(physical_device, self.renderer.surface)):
                continue
            self.renderer.physical_device = physical_device
            self.renderer.queue_families = queue_families
            properties = vkGetPhysicalDeviceProperties(physical_device)
            self.renderer.gpu_timestamp_period_ns = float(properties.limits.timestampPeriod)
            self.renderer.gpu_timing_supported = self.renderer.gpu_timestamp_period_ns > 0.0
            self.renderer.msaa_samples = _max_usable_sample_count(properties)
            return
        raise RuntimeError("No Vulkan device with graphics and presentation support was found.")

    def _find_queue_families(self, physical_device) -> QueueFamilies | None:
        graphics_family = None
        present_family = None
        for index, properties in enumerate(vkGetPhysicalDeviceQueueFamilyProperties(physical_device)):
            if properties.queueCount <= 0:
                continue
            if properties.queueFlags & VK_QUEUE_GRAPHICS_BIT:
                graphics_family = index
            if self.renderer.fp_get_surface_support(physical_device, index, self.renderer.surface):
                present_family = index
            if graphics_family is not None and present_family is not None:
                return QueueFamilies(graphics=graphics_family, present=present_family)
        return None

    def _supports_swapchain_extension(self, physical_device) -> bool:
        extensions = {
            self._normalize_vulkan_string(extension.extensionName)
            for extension in vkEnumerateDeviceExtensionProperties(physical_device, None)
        }
        return VK_KHR_SWAPCHAIN_EXTENSION_NAME in extensions

    @staticmethod
    def _normalize_vulkan_string(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode()
        return ffi.string(value).decode()

    def _create_logical_device(self) -> None:
        if self.renderer.queue_families is None:
            raise RuntimeError("Cannot create logical device: no suitable queue families found")
        priorities = [1.0]
        unique_families = sorted({self.renderer.queue_families.graphics, self.renderer.queue_families.present})
        queue_infos = [
            VkDeviceQueueCreateInfo(
                queueFamilyIndex=queue_family,
                queueCount=1,
                pQueuePriorities=priorities,
            )
            for queue_family in unique_families
        ]

        create_info = VkDeviceCreateInfo(
            queueCreateInfoCount=len(queue_infos),
            pQueueCreateInfos=queue_infos,
            enabledExtensionCount=1,
            ppEnabledExtensionNames=[VK_KHR_SWAPCHAIN_EXTENSION_NAME],
            pEnabledFeatures=VkPhysicalDeviceFeatures(),
        )
        self.renderer.device = vkCreateDevice(self.renderer.physical_device, create_info, None)
        self.renderer.graphics_queue = vkGetDeviceQueue(self.renderer.device, self.renderer.queue_families.graphics, 0)
        self.renderer.present_queue = vkGetDeviceQueue(self.renderer.device, self.renderer.queue_families.present, 0)

    def _load_device_extensions(self) -> None:
        self.renderer.fp_create_swapchain = vkGetDeviceProcAddr(self.renderer.device, "vkCreateSwapchainKHR")
        self.renderer.fp_destroy_swapchain = vkGetDeviceProcAddr(self.renderer.device, "vkDestroySwapchainKHR")
        self.renderer.fp_get_swapchain_images = vkGetDeviceProcAddr(self.renderer.device, "vkGetSwapchainImagesKHR")
        self.renderer.fp_acquire_next_image = vkGetDeviceProcAddr(self.renderer.device, "vkAcquireNextImageKHR")
        self.renderer.fp_queue_present = vkGetDeviceProcAddr(self.renderer.device, "vkQueuePresentKHR")

    def _create_command_pool(self) -> None:
        create_info = VkCommandPoolCreateInfo(
            flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
            queueFamilyIndex=self.renderer.queue_families.graphics,
        )
        self.renderer.command_pool = vkCreateCommandPool(self.renderer.device, create_info, None)

    def _create_vertex_buffer(self) -> None:
        self.renderer.vertex_buffer, self.renderer.vertex_memory = create_buffer(
            self.renderer,
            MAX_VERTEX_BYTES,
            VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        )
        self.renderer.vertex_mapping = vkMapMemory(
            self.renderer.device, self.renderer.vertex_memory, 0, MAX_VERTEX_BYTES, 0
        )
