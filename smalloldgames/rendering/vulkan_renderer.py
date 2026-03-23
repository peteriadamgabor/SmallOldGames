from __future__ import annotations

from array import array
from pathlib import Path

import glfw
from vulkan import (
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_QUERY_RESULT_64_BIT,
    VK_QUERY_RESULT_WAIT_BIT,
    VK_SUCCESS,
    VK_TRUE,
    VkPresentInfoKHR,
    VkSubmitInfo,
    ffi,
    vkGetQueryPoolResults,
    vkQueueSubmit,
    vkResetCommandBuffer,
    vkResetFences,
    vkWaitForFences,
)

from smalloldgames.assets.sprites import SpriteAtlas

from .vulkan.constants import MAX_VERTEX_BYTES, UINT64_MAX
from .vulkan.device import VulkanDevice
from .vulkan.pipeline import VulkanPipeline
from .vulkan.resources import VulkanResources
from .vulkan.swapchain import VulkanSwapchain
from .vulkan.types import QueueFamilies


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
        self.scene_framebuffer = None
        self.scene_render_pass = None
        self.post_render_pass = None
        self.descriptor_set_layout = None
        self.descriptor_pool = None
        self.descriptor_set = None
        self.post_descriptor_set = None
        self.scene_pipeline_layout = None
        self.post_pipeline_layout = None
        self.scene_pipeline = None
        self.post_pipeline = None
        self.command_pool = None
        self.command_buffers: list = []
        self.vertex_buffer = None
        self.vertex_memory = None
        self.vertex_mapping = None
        self.gpu_timing_query_pool = None
        self.gpu_timing_supported = False
        self.gpu_timestamp_period_ns = 0.0
        self.gpu_timing_pending = False
        self.last_gpu_frame_ms = 0.0
        self.texture_image = None
        self.texture_memory = None
        self.texture_view = None
        self.texture_sampler = None
        self.offscreen_image = None
        self.offscreen_memory = None
        self.offscreen_view = None
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

        self.device_state = VulkanDevice(self)
        self.pipeline_state = VulkanPipeline(self)
        self.resource_state = VulkanResources(self)
        self.swapchain_state = VulkanSwapchain(self)

        try:
            self.device_state.initialize()
            self.pipeline_state.initialize()
            self.resource_state.initialize()
            self.swapchain_state.initialize()
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
            self.swapchain_state.recreate()

        data_size = len(vertices) * vertices.itemsize
        if data_size > MAX_VERTEX_BYTES:
            raise ValueError(f"Frame uses {data_size} bytes, above the {MAX_VERTEX_BYTES} byte vertex budget.")

        if data_size:
            ffi.memmove(self.vertex_mapping, ffi.from_buffer(vertices), data_size)

        vkWaitForFences(self.device, 1, [self.in_flight_fence], VK_TRUE, UINT64_MAX)
        self._update_gpu_timing()
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
        self.pipeline_state.record_command_buffer(command_buffer, image_index, len(vertices) // 8)

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
        if self.gpu_timing_supported and self.gpu_timing_query_pool is not None:
            self.gpu_timing_pending = True

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        if self.device is not None:
            from vulkan import vkDeviceWaitIdle

            vkDeviceWaitIdle(self.device)
        self.resource_state.close()
        self.swapchain_state.cleanup()
        self.pipeline_state.close()
        self.device_state.close()

    def _update_gpu_timing(self) -> None:
        if not self.gpu_timing_pending or self.gpu_timing_query_pool is None or self.gpu_timestamp_period_ns <= 0.0:
            return
        data = ffi.new("uint64_t[2]")
        result = vkGetQueryPoolResults(
            self.device,
            self.gpu_timing_query_pool,
            0,
            2,
            ffi.sizeof("uint64_t[2]"),
            data,
            ffi.sizeof("uint64_t"),
            VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT,
        )
        if result != VK_SUCCESS:
            return
        elapsed_ticks = max(0, int(data[1]) - int(data[0]))
        self.last_gpu_frame_ms = (elapsed_ticks * self.gpu_timestamp_period_ns) / 1_000_000.0
        self.gpu_timing_pending = False
