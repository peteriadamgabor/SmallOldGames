from __future__ import annotations

from array import array
from dataclasses import dataclass
from pathlib import Path

import glfw
from vulkan import (
    VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
    VK_ACCESS_SHADER_READ_BIT,
    VK_ACCESS_TRANSFER_WRITE_BIT,
    VK_API_VERSION_1_0,
    VK_ATTACHMENT_LOAD_OP_CLEAR,
    VK_ATTACHMENT_LOAD_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_STORE,
    VK_BLEND_FACTOR_ONE,
    VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
    VK_BLEND_FACTOR_SRC_ALPHA,
    VK_BLEND_OP_ADD,
    VK_BORDER_COLOR_INT_OPAQUE_BLACK,
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
    VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    VK_COLOR_COMPONENT_A_BIT,
    VK_COLOR_COMPONENT_B_BIT,
    VK_COLOR_COMPONENT_G_BIT,
    VK_COLOR_COMPONENT_R_BIT,
    VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    VK_COMPONENT_SWIZZLE_IDENTITY,
    VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
    VK_CULL_MODE_NONE,
    VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
    VK_FENCE_CREATE_SIGNALED_BIT,
    VK_FILTER_NEAREST,
    VK_FORMAT_B8G8R8A8_UNORM,
    VK_FORMAT_R32G32B32A32_SFLOAT,
    VK_FORMAT_R32G32_SFLOAT,
    VK_FORMAT_R8G8B8A8_UNORM,
    VK_FRONT_FACE_COUNTER_CLOCKWISE,
    VK_IMAGE_ASPECT_COLOR_BIT,
    VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
    VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
    VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
    VK_IMAGE_LAYOUT_UNDEFINED,
    VK_IMAGE_TILING_OPTIMAL,
    VK_IMAGE_TYPE_2D,
    VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
    VK_IMAGE_USAGE_SAMPLED_BIT,
    VK_IMAGE_USAGE_TRANSFER_DST_BIT,
    VK_IMAGE_VIEW_TYPE_2D,
    VK_KHR_SWAPCHAIN_EXTENSION_NAME,
    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
    VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
    VK_PIPELINE_STAGE_TRANSFER_BIT,
    VK_POLYGON_MODE_FILL,
    VK_PRESENT_MODE_FIFO_KHR,
    VK_PRESENT_MODE_MAILBOX_KHR,
    VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    VK_QUEUE_FAMILY_IGNORED,
    VK_QUEUE_GRAPHICS_BIT,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
    VK_SAMPLER_MIPMAP_MODE_NEAREST,
    VK_SHADER_STAGE_FRAGMENT_BIT,
    VK_SHADER_STAGE_VERTEX_BIT,
    VK_SHARING_MODE_CONCURRENT,
    VK_SHARING_MODE_EXCLUSIVE,
    VK_SUBPASS_CONTENTS_INLINE,
    VK_SUBPASS_EXTERNAL,
    VK_SUCCESS,
    VK_TRUE,
    VK_VERTEX_INPUT_RATE_VERTEX,
    VkApplicationInfo,
    VkAttachmentDescription,
    VkAttachmentReference,
    VkBufferCreateInfo,
    VkBufferImageCopy,
    VkClearColorValue,
    VkClearValue,
    VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo,
    VkCommandPoolCreateInfo,
    VkComponentMapping,
    VkDescriptorImageInfo,
    VkDescriptorPoolCreateInfo,
    VkDescriptorPoolSize,
    VkDescriptorSetAllocateInfo,
    VkDescriptorSetLayoutBinding,
    VkDescriptorSetLayoutCreateInfo,
    VkDeviceCreateInfo,
    VkDeviceQueueCreateInfo,
    VkExtent2D,
    VkExtent3D,
    VkFenceCreateInfo,
    VkFramebufferCreateInfo,
    VkGraphicsPipelineCreateInfo,
    VkImageCreateInfo,
    VkImageMemoryBarrier,
    VkImageSubresourceLayers,
    VkImageSubresourceRange,
    VkImageViewCreateInfo,
    VkInstanceCreateInfo,
    VkMemoryAllocateInfo,
    VkOffset2D,
    VkOffset3D,
    VkPhysicalDeviceFeatures,
    VkPipelineColorBlendAttachmentState,
    VkPipelineColorBlendStateCreateInfo,
    VkPipelineInputAssemblyStateCreateInfo,
    VkPipelineLayoutCreateInfo,
    VkPipelineMultisampleStateCreateInfo,
    VkPipelineRasterizationStateCreateInfo,
    VkPipelineShaderStageCreateInfo,
    VkPipelineVertexInputStateCreateInfo,
    VkPipelineViewportStateCreateInfo,
    VkPresentInfoKHR,
    VkRect2D,
    VkRenderPassBeginInfo,
    VkRenderPassCreateInfo,
    VkSamplerCreateInfo,
    VkSemaphoreCreateInfo,
    VkShaderModuleCreateInfo,
    VkSubmitInfo,
    VkSubpassDependency,
    VkSubpassDescription,
    VkSurfaceFormatKHR,
    VkSwapchainCreateInfoKHR,
    VkVertexInputAttributeDescription,
    VkVertexInputBindingDescription,
    VkViewport,
    VkWriteDescriptorSet,
    ffi,
    vkAllocateCommandBuffers,
    vkAllocateDescriptorSets,
    vkAllocateMemory,
    vkBeginCommandBuffer,
    vkBindBufferMemory,
    vkBindImageMemory,
    vkCmdBeginRenderPass,
    vkCmdBindDescriptorSets,
    vkCmdBindPipeline,
    vkCmdBindVertexBuffers,
    vkCmdCopyBufferToImage,
    vkCmdDraw,
    vkCmdEndRenderPass,
    vkCmdPipelineBarrier,
    vkCreateBuffer,
    vkCreateCommandPool,
    vkCreateDescriptorPool,
    vkCreateDescriptorSetLayout,
    vkCreateDevice,
    vkCreateFence,
    vkCreateFramebuffer,
    vkCreateGraphicsPipelines,
    vkCreateImage,
    vkCreateImageView,
    vkCreateInstance,
    vkCreatePipelineLayout,
    vkCreateRenderPass,
    vkCreateSampler,
    vkCreateSemaphore,
    vkCreateShaderModule,
    vkDestroyBuffer,
    vkDestroyCommandPool,
    vkDestroyDescriptorPool,
    vkDestroyDescriptorSetLayout,
    vkDestroyDevice,
    vkDestroyFence,
    vkDestroyFramebuffer,
    vkDestroyImage,
    vkDestroyImageView,
    vkDestroyInstance,
    vkDestroyPipeline,
    vkDestroyPipelineLayout,
    vkDestroyRenderPass,
    vkDestroySampler,
    vkDestroySemaphore,
    vkDestroyShaderModule,
    vkDeviceWaitIdle,
    vkEndCommandBuffer,
    vkEnumerateDeviceExtensionProperties,
    vkEnumeratePhysicalDevices,
    vkFreeCommandBuffers,
    vkFreeMemory,
    vkGetBufferMemoryRequirements,
    vkGetDeviceProcAddr,
    vkGetDeviceQueue,
    vkGetImageMemoryRequirements,
    vkGetInstanceProcAddr,
    vkGetPhysicalDeviceMemoryProperties,
    vkGetPhysicalDeviceQueueFamilyProperties,
    vkMapMemory,
    vkQueueSubmit,
    vkQueueWaitIdle,
    vkResetCommandBuffer,
    vkResetFences,
    vkUnmapMemory,
    vkUpdateDescriptorSets,
    vkWaitForFences,
)

from smalloldgames.assets.sprites import SpriteAtlas

UINT64_MAX = (1 << 64) - 1
VERTEX_STRIDE = 32
MAX_VERTEX_BYTES = 1_048_576


@dataclass(slots=True)
class QueueFamilies:
    graphics: int
    present: int


class VulkanRenderer:
    def __init__(
        self,
        window: glfw._GLFWwindow,
        *,
        shader_dir: Path,
        sprite_atlas: SpriteAtlas,
        canvas_width: int = 540,
        canvas_height: int = 960,
    ) -> None:
        self.window = window
        self.shader_dir = shader_dir
        self.sprite_atlas = sprite_atlas
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        self.instance = None
        self.surface = None
        self.physical_device = None
        self.device = None
        self.graphics_queue = None
        self.present_queue = None
        self.queue_families: QueueFamilies | None = None
        self.swapchain = None
        self.swapchain_extent = None
        self.swapchain_format = None
        self.swapchain_images: list = []
        self.swapchain_image_views: list = []
        self.framebuffers: list = []
        self.render_pass = None
        self.descriptor_set_layout = None
        self.descriptor_pool = None
        self.descriptor_set = None
        self.pipeline_layout = None
        self.pipeline = None
        self.command_pool = None
        self.command_buffers: list = []
        self.vertex_buffer = None
        self.vertex_memory = None
        self.texture_image = None
        self.texture_memory = None
        self.texture_view = None
        self.texture_sampler = None
        self.image_available = None
        self.render_finished = None
        self.in_flight_fence = None
        self.closed = False

        self.fp_destroy_surface = None
        self.fp_get_surface_support = None
        self.fp_get_surface_capabilities = None
        self.fp_get_surface_formats = None
        self.fp_get_surface_present_modes = None
        self.fp_create_swapchain = None
        self.fp_destroy_swapchain = None
        self.fp_get_swapchain_images = None
        self.fp_acquire_next_image = None
        self.fp_queue_present = None

        try:
            self._create_instance()
            self._load_instance_extensions()
            self._create_surface()
            self._pick_physical_device()
            self._create_logical_device()
            self._load_device_extensions()
            self._create_descriptor_set_layout()
            self._create_swapchain()
            self._create_render_pass()
            self._create_command_pool()
            self._create_texture_resources()
            self._create_pipeline()
            self._create_framebuffers()
            self._create_vertex_buffer()
            self._create_command_buffers()
            self._create_sync_objects()
        except Exception:
            self.close()
            raise

    def render(self, vertices: array) -> None:
        if self.closed:
            raise RuntimeError("Renderer already closed.")
        framebuffer_width, framebuffer_height = glfw.get_framebuffer_size(self.window)
        if framebuffer_width <= 0 or framebuffer_height <= 0:
            return
        if (
            self.swapchain_extent is None
            or self.swapchain_extent.width != framebuffer_width
            or self.swapchain_extent.height != framebuffer_height
        ):
            self._recreate_swapchain()

        vertex_count = len(vertices) // 8
        data_size = len(vertices) * vertices.itemsize
        if data_size > MAX_VERTEX_BYTES:
            raise ValueError(f"Frame uses {data_size} bytes, above the {MAX_VERTEX_BYTES} byte vertex budget.")

        if data_size:
            mapped = vkMapMemory(self.device, self.vertex_memory, 0, data_size, 0)
            ffi.memmove(mapped, ffi.from_buffer(vertices), data_size)
            vkUnmapMemory(self.device, self.vertex_memory)

        vkWaitForFences(self.device, 1, [self.in_flight_fence], VK_TRUE, UINT64_MAX)
        vkResetFences(self.device, 1, [self.in_flight_fence])

        image_index = int(
            self.fp_acquire_next_image(
                self.device,
                self.swapchain,
                UINT64_MAX,
                self.image_available,
                None,
            )
        )

        command_buffer = self.command_buffers[image_index]
        vkResetCommandBuffer(command_buffer, 0)
        self._record_command_buffer(command_buffer, image_index, vertex_count)

        submit_info = VkSubmitInfo(
            waitSemaphoreCount=1,
            pWaitSemaphores=[self.image_available],
            pWaitDstStageMask=[VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT],
            commandBufferCount=1,
            pCommandBuffers=[command_buffer],
            signalSemaphoreCount=1,
            pSignalSemaphores=[self.render_finished],
        )
        vkQueueSubmit(self.graphics_queue, 1, [submit_info], self.in_flight_fence)

        present_info = VkPresentInfoKHR(
            waitSemaphoreCount=1,
            pWaitSemaphores=[self.render_finished],
            swapchainCount=1,
            pSwapchains=[self.swapchain],
            pImageIndices=[image_index],
        )
        self.fp_queue_present(self.present_queue, present_info)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True

        if self.device is not None:
            vkDeviceWaitIdle(self.device)

        if self.device is not None and self.image_available is not None:
            vkDestroySemaphore(self.device, self.image_available, None)
        if self.device is not None and self.render_finished is not None:
            vkDestroySemaphore(self.device, self.render_finished, None)
        if self.device is not None and self.in_flight_fence is not None:
            vkDestroyFence(self.device, self.in_flight_fence, None)
        if self.device is not None and self.vertex_buffer is not None:
            vkDestroyBuffer(self.device, self.vertex_buffer, None)
        if self.device is not None and self.vertex_memory is not None:
            vkFreeMemory(self.device, self.vertex_memory, None)
        if self.device is not None and self.texture_sampler is not None:
            vkDestroySampler(self.device, self.texture_sampler, None)
        if self.device is not None and self.texture_view is not None:
            vkDestroyImageView(self.device, self.texture_view, None)
        if self.device is not None and self.texture_image is not None:
            vkDestroyImage(self.device, self.texture_image, None)
        if self.device is not None and self.texture_memory is not None:
            vkFreeMemory(self.device, self.texture_memory, None)
        if self.device is not None and self.descriptor_pool is not None:
            vkDestroyDescriptorPool(self.device, self.descriptor_pool, None)
        if self.device is not None and self.descriptor_set_layout is not None:
            vkDestroyDescriptorSetLayout(self.device, self.descriptor_set_layout, None)
        if self.device is not None and self.command_pool is not None:
            vkDestroyCommandPool(self.device, self.command_pool, None)

        if self.device is not None:
            for framebuffer in self.framebuffers:
                vkDestroyFramebuffer(self.device, framebuffer, None)
            if self.pipeline is not None:
                vkDestroyPipeline(self.device, self.pipeline, None)
            if self.pipeline_layout is not None:
                vkDestroyPipelineLayout(self.device, self.pipeline_layout, None)
            if self.render_pass is not None:
                vkDestroyRenderPass(self.device, self.render_pass, None)
            for image_view in self.swapchain_image_views:
                vkDestroyImageView(self.device, image_view, None)
            if self.swapchain is not None and self.fp_destroy_swapchain is not None:
                self.fp_destroy_swapchain(self.device, self.swapchain, None)
            vkDestroyDevice(self.device, None)

        if self.instance is not None and self.surface is not None and self.fp_destroy_surface is not None:
            self.fp_destroy_surface(self.instance, self.surface, None)
        if self.instance is not None:
            vkDestroyInstance(self.instance, None)

    def _create_instance(self) -> None:
        required_extensions = glfw.get_required_instance_extensions()
        if not required_extensions:
            raise RuntimeError("GLFW did not provide Vulkan surface extensions.")
        extension_names = [
            extension.decode() if isinstance(extension, bytes) else extension
            for extension in required_extensions
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
        self.instance = vkCreateInstance(create_info, None)

    def _load_instance_extensions(self) -> None:
        self.fp_destroy_surface = vkGetInstanceProcAddr(self.instance, "vkDestroySurfaceKHR")
        self.fp_get_surface_support = vkGetInstanceProcAddr(self.instance, "vkGetPhysicalDeviceSurfaceSupportKHR")
        self.fp_get_surface_capabilities = vkGetInstanceProcAddr(self.instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR")
        self.fp_get_surface_formats = vkGetInstanceProcAddr(self.instance, "vkGetPhysicalDeviceSurfaceFormatsKHR")
        self.fp_get_surface_present_modes = vkGetInstanceProcAddr(self.instance, "vkGetPhysicalDeviceSurfacePresentModesKHR")

    def _create_surface(self) -> None:
        surface_ptr = ffi.new("VkSurfaceKHR*")
        result = glfw.create_window_surface(self.instance, self.window, None, surface_ptr)
        if result != VK_SUCCESS:
            raise RuntimeError(f"glfwCreateWindowSurface failed with VkResult {result}.")
        self.surface = surface_ptr[0]

    def _pick_physical_device(self) -> None:
        for physical_device in vkEnumeratePhysicalDevices(self.instance):
            queue_families = self._find_queue_families(physical_device)
            if queue_families is None:
                continue
            if not self._supports_swapchain_extension(physical_device):
                continue
            if not len(self.fp_get_surface_formats(physical_device, self.surface)):
                continue
            if not len(self.fp_get_surface_present_modes(physical_device, self.surface)):
                continue
            self.physical_device = physical_device
            self.queue_families = queue_families
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
            if self.fp_get_surface_support(physical_device, index, self.surface):
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
        assert self.queue_families is not None
        priorities = [1.0]
        unique_families = sorted({self.queue_families.graphics, self.queue_families.present})
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
        self.device = vkCreateDevice(self.physical_device, create_info, None)
        self.graphics_queue = vkGetDeviceQueue(self.device, self.queue_families.graphics, 0)
        self.present_queue = vkGetDeviceQueue(self.device, self.queue_families.present, 0)

    def _load_device_extensions(self) -> None:
        self.fp_create_swapchain = vkGetDeviceProcAddr(self.device, "vkCreateSwapchainKHR")
        self.fp_destroy_swapchain = vkGetDeviceProcAddr(self.device, "vkDestroySwapchainKHR")
        self.fp_get_swapchain_images = vkGetDeviceProcAddr(self.device, "vkGetSwapchainImagesKHR")
        self.fp_acquire_next_image = vkGetDeviceProcAddr(self.device, "vkAcquireNextImageKHR")
        self.fp_queue_present = vkGetDeviceProcAddr(self.device, "vkQueuePresentKHR")

    def _create_descriptor_set_layout(self) -> None:
        binding = VkDescriptorSetLayoutBinding(
            binding=0,
            descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
            descriptorCount=1,
            stageFlags=VK_SHADER_STAGE_FRAGMENT_BIT,
        )
        create_info = VkDescriptorSetLayoutCreateInfo(
            bindingCount=1,
            pBindings=[binding],
        )
        self.descriptor_set_layout = vkCreateDescriptorSetLayout(self.device, create_info, None)

    def _create_swapchain(self) -> None:
        capabilities = self.fp_get_surface_capabilities(self.physical_device, self.surface)
        formats = list(self.fp_get_surface_formats(self.physical_device, self.surface))
        present_modes = list(self.fp_get_surface_present_modes(self.physical_device, self.surface))
        surface_format = self._choose_surface_format(formats)
        present_mode = self._choose_present_mode(present_modes)
        self.swapchain_extent = self._choose_extent(capabilities)
        self.swapchain_format = surface_format.format

        image_count = capabilities.minImageCount + 1
        if capabilities.maxImageCount > 0 and image_count > capabilities.maxImageCount:
            image_count = capabilities.maxImageCount

        indices = [self.queue_families.graphics, self.queue_families.present]
        concurrent = self.queue_families.graphics != self.queue_families.present
        create_info = VkSwapchainCreateInfoKHR(
            surface=self.surface,
            minImageCount=image_count,
            imageFormat=surface_format.format,
            imageColorSpace=surface_format.colorSpace,
            imageExtent=self.swapchain_extent,
            imageArrayLayers=1,
            imageUsage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
            imageSharingMode=VK_SHARING_MODE_CONCURRENT if concurrent else VK_SHARING_MODE_EXCLUSIVE,
            queueFamilyIndexCount=len(indices) if concurrent else 0,
            pQueueFamilyIndices=indices if concurrent else None,
            preTransform=capabilities.currentTransform,
            compositeAlpha=VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
            presentMode=present_mode,
            clipped=True,
            oldSwapchain=None,
        )
        self.swapchain = self.fp_create_swapchain(self.device, create_info, None)
        self.swapchain_images = list(self.fp_get_swapchain_images(self.device, self.swapchain))
        self.swapchain_image_views = [self._create_image_view(image, self.swapchain_format) for image in self.swapchain_images]

    def _choose_surface_format(self, formats: list[VkSurfaceFormatKHR]) -> VkSurfaceFormatKHR:
        for surface_format in formats:
            if (
                surface_format.format == VK_FORMAT_B8G8R8A8_UNORM
                and surface_format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR
            ):
                return surface_format
        return formats[0]

    @staticmethod
    def _choose_present_mode(present_modes: list[int]) -> int:
        return VK_PRESENT_MODE_MAILBOX_KHR if VK_PRESENT_MODE_MAILBOX_KHR in present_modes else VK_PRESENT_MODE_FIFO_KHR

    def _choose_extent(self, capabilities) -> VkExtent2D:
        if capabilities.currentExtent.width != 0xFFFFFFFF:
            return capabilities.currentExtent
        width, height = glfw.get_framebuffer_size(self.window)
        return VkExtent2D(
            width=max(capabilities.minImageExtent.width, min(capabilities.maxImageExtent.width, width)),
            height=max(capabilities.minImageExtent.height, min(capabilities.maxImageExtent.height, height)),
        )

    def _create_image_view(self, image, format_code: int) -> object:
        create_info = VkImageViewCreateInfo(
            image=image,
            viewType=VK_IMAGE_VIEW_TYPE_2D,
            format=format_code,
            components=VkComponentMapping(
                r=VK_COMPONENT_SWIZZLE_IDENTITY,
                g=VK_COMPONENT_SWIZZLE_IDENTITY,
                b=VK_COMPONENT_SWIZZLE_IDENTITY,
                a=VK_COMPONENT_SWIZZLE_IDENTITY,
            ),
            subresourceRange=VkImageSubresourceRange(
                aspectMask=VK_IMAGE_ASPECT_COLOR_BIT,
                baseMipLevel=0,
                levelCount=1,
                baseArrayLayer=0,
                layerCount=1,
            ),
        )
        return vkCreateImageView(self.device, create_info, None)

    def _create_render_pass(self) -> None:
        attachment = VkAttachmentDescription(
            format=self.swapchain_format,
            samples=VK_SAMPLE_COUNT_1_BIT,
            loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR,
            storeOp=VK_ATTACHMENT_STORE_OP_STORE,
            stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE,
            stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE,
            initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
            finalLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
        )
        color_attachment_ref = VkAttachmentReference(
            attachment=0,
            layout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
        )
        subpass = VkSubpassDescription(
            pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS,
            colorAttachmentCount=1,
            pColorAttachments=[color_attachment_ref],
        )
        dependency = VkSubpassDependency(
            srcSubpass=VK_SUBPASS_EXTERNAL,
            dstSubpass=0,
            srcStageMask=VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            dstStageMask=VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            dstAccessMask=VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
        )
        create_info = VkRenderPassCreateInfo(
            attachmentCount=1,
            pAttachments=[attachment],
            subpassCount=1,
            pSubpasses=[subpass],
            dependencyCount=1,
            pDependencies=[dependency],
        )
        self.render_pass = vkCreateRenderPass(self.device, create_info, None)

    def _create_command_pool(self) -> None:
        create_info = VkCommandPoolCreateInfo(
            flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
            queueFamilyIndex=self.queue_families.graphics,
        )
        self.command_pool = vkCreateCommandPool(self.device, create_info, None)

    def _create_texture_resources(self) -> None:
        staging_buffer, staging_memory = self._create_buffer(
            len(self.sprite_atlas.rgba_bytes),
            VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        )
        try:
            mapped = vkMapMemory(self.device, staging_memory, 0, len(self.sprite_atlas.rgba_bytes), 0)
            mapped[: len(self.sprite_atlas.rgba_bytes)] = self.sprite_atlas.rgba_bytes
            vkUnmapMemory(self.device, staging_memory)

            image_info = VkImageCreateInfo(
                imageType=VK_IMAGE_TYPE_2D,
                format=VK_FORMAT_R8G8B8A8_UNORM,
                extent=VkExtent3D(width=self.sprite_atlas.width, height=self.sprite_atlas.height, depth=1),
                mipLevels=1,
                arrayLayers=1,
                samples=VK_SAMPLE_COUNT_1_BIT,
                tiling=VK_IMAGE_TILING_OPTIMAL,
                usage=VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                sharingMode=VK_SHARING_MODE_EXCLUSIVE,
                initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
            )
            self.texture_image = vkCreateImage(self.device, image_info, None)
            requirements = vkGetImageMemoryRequirements(self.device, self.texture_image)
            self.texture_memory = vkAllocateMemory(
                self.device,
                VkMemoryAllocateInfo(
                    allocationSize=requirements.size,
                    memoryTypeIndex=self._find_memory_type(
                        requirements.memoryTypeBits,
                        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
                    ),
                ),
                None,
            )
            vkBindImageMemory(self.device, self.texture_image, self.texture_memory, 0)

            self._transition_image_layout(
                self.texture_image,
                VK_IMAGE_LAYOUT_UNDEFINED,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                0,
                VK_ACCESS_TRANSFER_WRITE_BIT,
            )
            self._copy_buffer_to_image(staging_buffer, self.texture_image, self.sprite_atlas.width, self.sprite_atlas.height)
            self._transition_image_layout(
                self.texture_image,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
                VK_ACCESS_TRANSFER_WRITE_BIT,
                VK_ACCESS_SHADER_READ_BIT,
            )
        finally:
            vkDestroyBuffer(self.device, staging_buffer, None)
            vkFreeMemory(self.device, staging_memory, None)

        self.texture_view = self._create_image_view(self.texture_image, VK_FORMAT_R8G8B8A8_UNORM)
        self.texture_sampler = vkCreateSampler(
            self.device,
            VkSamplerCreateInfo(
                magFilter=VK_FILTER_NEAREST,
                minFilter=VK_FILTER_NEAREST,
                mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST,
                addressModeU=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
                addressModeV=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
                addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
                mipLodBias=0.0,
                anisotropyEnable=False,
                maxAnisotropy=1.0,
                compareEnable=False,
                minLod=0.0,
                maxLod=0.0,
                borderColor=VK_BORDER_COLOR_INT_OPAQUE_BLACK,
                unnormalizedCoordinates=False,
            ),
            None,
        )

        self.descriptor_pool = vkCreateDescriptorPool(
            self.device,
            VkDescriptorPoolCreateInfo(
                maxSets=1,
                pPoolSizes=[VkDescriptorPoolSize(type=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, descriptorCount=1)],
            ),
            None,
        )
        self.descriptor_set = vkAllocateDescriptorSets(
            self.device,
            VkDescriptorSetAllocateInfo(
                descriptorPool=self.descriptor_pool,
                descriptorSetCount=1,
                pSetLayouts=[self.descriptor_set_layout],
            ),
        )[0]
        image_info = VkDescriptorImageInfo(
            sampler=self.texture_sampler,
            imageView=self.texture_view,
            imageLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        )
        write = VkWriteDescriptorSet(
            dstSet=self.descriptor_set,
            dstBinding=0,
            dstArrayElement=0,
            descriptorCount=1,
            descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
            pImageInfo=[image_info],
        )
        vkUpdateDescriptorSets(self.device, 1, [write], 0, None)

    def _create_pipeline(self) -> None:
        self.pipeline_layout = vkCreatePipelineLayout(
            self.device,
            VkPipelineLayoutCreateInfo(
                setLayoutCount=1,
                pSetLayouts=[self.descriptor_set_layout],
            ),
            None,
        )

        vert_module = self._create_shader_module(self.shader_dir / "color.vert.spv")
        frag_module = self._create_shader_module(self.shader_dir / "color.frag.spv")
        try:
            stages = [
                VkPipelineShaderStageCreateInfo(stage=VK_SHADER_STAGE_VERTEX_BIT, module=vert_module, pName=b"main"),
                VkPipelineShaderStageCreateInfo(stage=VK_SHADER_STAGE_FRAGMENT_BIT, module=frag_module, pName=b"main"),
            ]
            binding_description = VkVertexInputBindingDescription(
                binding=0,
                stride=VERTEX_STRIDE,
                inputRate=VK_VERTEX_INPUT_RATE_VERTEX,
            )
            attribute_descriptions = [
                VkVertexInputAttributeDescription(location=0, binding=0, format=VK_FORMAT_R32G32_SFLOAT, offset=0),
                VkVertexInputAttributeDescription(location=1, binding=0, format=VK_FORMAT_R32G32B32A32_SFLOAT, offset=8),
                VkVertexInputAttributeDescription(location=2, binding=0, format=VK_FORMAT_R32G32_SFLOAT, offset=24),
            ]
            vertex_input = VkPipelineVertexInputStateCreateInfo(
                vertexBindingDescriptionCount=1,
                pVertexBindingDescriptions=[binding_description],
                vertexAttributeDescriptionCount=len(attribute_descriptions),
                pVertexAttributeDescriptions=attribute_descriptions,
            )
            input_assembly = VkPipelineInputAssemblyStateCreateInfo(
                topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
                primitiveRestartEnable=False,
            )
            viewport_x, viewport_y, viewport_width, viewport_height, scissor = self._content_viewport()
            viewport = VkViewport(
                x=viewport_x,
                y=viewport_y,
                width=viewport_width,
                height=-viewport_height,
                minDepth=0.0,
                maxDepth=1.0,
            )
            viewport_state = VkPipelineViewportStateCreateInfo(
                viewportCount=1,
                pViewports=[viewport],
                scissorCount=1,
                pScissors=[scissor],
            )
            rasterizer = VkPipelineRasterizationStateCreateInfo(
                depthClampEnable=False,
                rasterizerDiscardEnable=False,
                polygonMode=VK_POLYGON_MODE_FILL,
                cullMode=VK_CULL_MODE_NONE,
                frontFace=VK_FRONT_FACE_COUNTER_CLOCKWISE,
                depthBiasEnable=False,
                lineWidth=1.0,
            )
            multisampling = VkPipelineMultisampleStateCreateInfo(
                rasterizationSamples=VK_SAMPLE_COUNT_1_BIT,
                sampleShadingEnable=False,
            )
            blend_attachment = VkPipelineColorBlendAttachmentState(
                blendEnable=True,
                srcColorBlendFactor=VK_BLEND_FACTOR_SRC_ALPHA,
                dstColorBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
                colorBlendOp=VK_BLEND_OP_ADD,
                srcAlphaBlendFactor=VK_BLEND_FACTOR_ONE,
                dstAlphaBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
                alphaBlendOp=VK_BLEND_OP_ADD,
                colorWriteMask=(
                    VK_COLOR_COMPONENT_R_BIT
                    | VK_COLOR_COMPONENT_G_BIT
                    | VK_COLOR_COMPONENT_B_BIT
                    | VK_COLOR_COMPONENT_A_BIT
                ),
            )
            blending = VkPipelineColorBlendStateCreateInfo(
                logicOpEnable=False,
                attachmentCount=1,
                pAttachments=[blend_attachment],
            )
            pipeline_info = VkGraphicsPipelineCreateInfo(
                stageCount=len(stages),
                pStages=stages,
                pVertexInputState=vertex_input,
                pInputAssemblyState=input_assembly,
                pViewportState=viewport_state,
                pRasterizationState=rasterizer,
                pMultisampleState=multisampling,
                pColorBlendState=blending,
                layout=self.pipeline_layout,
                renderPass=self.render_pass,
                subpass=0,
            )
            self.pipeline = vkCreateGraphicsPipelines(self.device, None, 1, [pipeline_info], None)[0]
        finally:
            vkDestroyShaderModule(self.device, vert_module, None)
            vkDestroyShaderModule(self.device, frag_module, None)

    def _create_shader_module(self, shader_path: Path) -> object:
        code = shader_path.read_bytes()
        if len(code) % 4 != 0:
            raise RuntimeError(f"Shader binary {shader_path} is not aligned to 4-byte SPIR-V words.")
        code_words = array("I")
        code_words.frombytes(code)
        create_info = VkShaderModuleCreateInfo(
            codeSize=len(code),
            pCode=code_words,
        )
        return vkCreateShaderModule(self.device, create_info, None)

    def _create_framebuffers(self) -> None:
        self.framebuffers = []
        for image_view in self.swapchain_image_views:
            create_info = VkFramebufferCreateInfo(
                renderPass=self.render_pass,
                attachmentCount=1,
                pAttachments=[image_view],
                width=self.swapchain_extent.width,
                height=self.swapchain_extent.height,
                layers=1,
            )
            self.framebuffers.append(vkCreateFramebuffer(self.device, create_info, None))

    def _create_vertex_buffer(self) -> None:
        self.vertex_buffer, self.vertex_memory = self._create_buffer(
            MAX_VERTEX_BYTES,
            VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        )

    def _create_buffer(self, size: int, usage: int, memory_properties: int) -> tuple[object, object]:
        buffer_info = VkBufferCreateInfo(
            size=size,
            usage=usage,
            sharingMode=VK_SHARING_MODE_EXCLUSIVE,
        )
        buffer = vkCreateBuffer(self.device, buffer_info, None)
        requirements = vkGetBufferMemoryRequirements(self.device, buffer)
        memory = vkAllocateMemory(
            self.device,
            VkMemoryAllocateInfo(
                allocationSize=requirements.size,
                memoryTypeIndex=self._find_memory_type(requirements.memoryTypeBits, memory_properties),
            ),
            None,
        )
        vkBindBufferMemory(self.device, buffer, memory, 0)
        return buffer, memory

    def _find_memory_type(self, type_filter: int, properties: int) -> int:
        memory_properties = vkGetPhysicalDeviceMemoryProperties(self.physical_device)
        for index in range(memory_properties.memoryTypeCount):
            memory_type = memory_properties.memoryTypes[index]
            if (type_filter & (1 << index)) and (memory_type.propertyFlags & properties) == properties:
                return index
        raise RuntimeError("No suitable Vulkan memory type found.")

    def _create_command_buffers(self) -> None:
        allocate_info = VkCommandBufferAllocateInfo(
            commandPool=self.command_pool,
            level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
            commandBufferCount=len(self.framebuffers),
        )
        self.command_buffers = list(vkAllocateCommandBuffers(self.device, allocate_info))

    def _recreate_swapchain(self) -> None:
        vkDeviceWaitIdle(self.device)
        self._cleanup_swapchain()
        self._create_swapchain()
        self._create_render_pass()
        self._create_pipeline()
        self._create_framebuffers()
        self._create_command_buffers()

    def _cleanup_swapchain(self) -> None:
        if self.command_buffers:
            vkFreeCommandBuffers(self.device, self.command_pool, len(self.command_buffers), self.command_buffers)
            self.command_buffers = []
        for framebuffer in self.framebuffers:
            vkDestroyFramebuffer(self.device, framebuffer, None)
        self.framebuffers = []
        if self.pipeline is not None:
            vkDestroyPipeline(self.device, self.pipeline, None)
            self.pipeline = None
        if self.pipeline_layout is not None:
            vkDestroyPipelineLayout(self.device, self.pipeline_layout, None)
            self.pipeline_layout = None
        if self.render_pass is not None:
            vkDestroyRenderPass(self.device, self.render_pass, None)
            self.render_pass = None
        for image_view in self.swapchain_image_views:
            vkDestroyImageView(self.device, image_view, None)
        self.swapchain_image_views = []
        if self.swapchain is not None:
            self.fp_destroy_swapchain(self.device, self.swapchain, None)
            self.swapchain = None

    def _content_viewport(self) -> tuple[float, float, float, float, VkRect2D]:
        scale = min(
            self.swapchain_extent.width / self.canvas_width,
            self.swapchain_extent.height / self.canvas_height,
        )
        viewport_width = float(self.canvas_width * scale)
        viewport_height = float(self.canvas_height * scale)
        offset_x = int((self.swapchain_extent.width - viewport_width) * 0.5)
        offset_y = int((self.swapchain_extent.height - viewport_height) * 0.5)
        scissor = VkRect2D(
            offset=VkOffset2D(x=offset_x, y=offset_y),
            extent=VkExtent2D(width=int(viewport_width), height=int(viewport_height)),
        )
        return (
            float(offset_x),
            float(offset_y + int(viewport_height)),
            float(int(viewport_width)),
            float(int(viewport_height)),
            scissor,
        )

    def _create_sync_objects(self) -> None:
        semaphore_info = VkSemaphoreCreateInfo()
        fence_info = VkFenceCreateInfo(flags=VK_FENCE_CREATE_SIGNALED_BIT)
        self.image_available = vkCreateSemaphore(self.device, semaphore_info, None)
        self.render_finished = vkCreateSemaphore(self.device, semaphore_info, None)
        self.in_flight_fence = vkCreateFence(self.device, fence_info, None)

    def _record_command_buffer(self, command_buffer, image_index: int, vertex_count: int) -> None:
        begin_info = VkCommandBufferBeginInfo(flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT)
        vkBeginCommandBuffer(command_buffer, begin_info)

        clear_value = VkClearValue(color=VkClearColorValue(float32=(0.02, 0.02, 0.04, 1.0)))
        render_pass_begin = VkRenderPassBeginInfo(
            renderPass=self.render_pass,
            framebuffer=self.framebuffers[image_index],
            renderArea=VkRect2D(offset=VkOffset2D(x=0, y=0), extent=self.swapchain_extent),
            clearValueCount=1,
            pClearValues=[clear_value],
        )
        vkCmdBeginRenderPass(command_buffer, render_pass_begin, VK_SUBPASS_CONTENTS_INLINE)
        vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)
        vkCmdBindDescriptorSets(
            command_buffer,
            VK_PIPELINE_BIND_POINT_GRAPHICS,
            self.pipeline_layout,
            0,
            1,
            [self.descriptor_set],
            0,
            None,
        )
        vkCmdBindVertexBuffers(command_buffer, 0, 1, [self.vertex_buffer], [0])
        if vertex_count:
            vkCmdDraw(command_buffer, vertex_count, 1, 0, 0)
        vkCmdEndRenderPass(command_buffer)
        vkEndCommandBuffer(command_buffer)

    def _transition_image_layout(
        self,
        image,
        old_layout: int,
        new_layout: int,
        src_stage: int,
        dst_stage: int,
        src_access: int,
        dst_access: int,
    ) -> None:
        command_buffer = self._begin_single_use_command_buffer()
        barrier = VkImageMemoryBarrier(
            srcAccessMask=src_access,
            dstAccessMask=dst_access,
            oldLayout=old_layout,
            newLayout=new_layout,
            srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
            dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
            image=image,
            subresourceRange=VkImageSubresourceRange(
                aspectMask=VK_IMAGE_ASPECT_COLOR_BIT,
                baseMipLevel=0,
                levelCount=1,
                baseArrayLayer=0,
                layerCount=1,
            ),
        )
        vkCmdPipelineBarrier(command_buffer, src_stage, dst_stage, 0, 0, None, 0, None, 1, [barrier])
        self._end_single_use_command_buffer(command_buffer)

    def _copy_buffer_to_image(self, buffer, image, width: int, height: int) -> None:
        command_buffer = self._begin_single_use_command_buffer()
        region = VkBufferImageCopy(
            bufferOffset=0,
            bufferRowLength=0,
            bufferImageHeight=0,
            imageSubresource=VkImageSubresourceLayers(
                aspectMask=VK_IMAGE_ASPECT_COLOR_BIT,
                mipLevel=0,
                baseArrayLayer=0,
                layerCount=1,
            ),
            imageOffset=VkOffset3D(x=0, y=0, z=0),
            imageExtent=VkExtent3D(width=width, height=height, depth=1),
        )
        vkCmdCopyBufferToImage(command_buffer, buffer, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, [region])
        self._end_single_use_command_buffer(command_buffer)

    def _begin_single_use_command_buffer(self):
        command_buffer = vkAllocateCommandBuffers(
            self.device,
            VkCommandBufferAllocateInfo(
                commandPool=self.command_pool,
                level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                commandBufferCount=1,
            ),
        )[0]
        vkBeginCommandBuffer(command_buffer, VkCommandBufferBeginInfo(flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT))
        return command_buffer

    def _end_single_use_command_buffer(self, command_buffer) -> None:
        vkEndCommandBuffer(command_buffer)
        submit_info = VkSubmitInfo(commandBufferCount=1, pCommandBuffers=[command_buffer])
        vkQueueSubmit(self.graphics_queue, 1, [submit_info], None)
        vkQueueWaitIdle(self.graphics_queue)
        vkFreeCommandBuffers(self.device, self.command_pool, 1, [command_buffer])
