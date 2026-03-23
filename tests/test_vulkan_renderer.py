from __future__ import annotations

import unittest
from array import array
from types import SimpleNamespace
from unittest.mock import Mock, patch

from smalloldgames.rendering import vulkan_renderer
from smalloldgames.rendering.vulkan_renderer import VulkanRenderer


class VulkanRendererTests(unittest.TestCase):
    def _make_renderer(self) -> VulkanRenderer:
        renderer = VulkanRenderer.__new__(VulkanRenderer)
        renderer.closed = False
        renderer.window = object()
        renderer.swapchain_extent = SimpleNamespace(width=640, height=480)
        renderer.swapchain_state = SimpleNamespace(recreate=Mock(), cleanup=Mock())
        renderer.pipeline_state = SimpleNamespace(record_command_buffer=Mock(), close=Mock())
        renderer.resource_state = SimpleNamespace(close=Mock())
        renderer.device_state = SimpleNamespace(close=Mock())
        renderer.device = object()
        renderer.vertex_memory = object()
        renderer.vertex_mapping = object()
        renderer.gpu_timing_query_pool = object()
        renderer.gpu_timing_supported = True
        renderer.gpu_timestamp_period_ns = 1_000_000.0
        renderer.gpu_timing_pending = False
        renderer.last_gpu_frame_ms = 0.0
        renderer.in_flight_fence = object()
        renderer.image_available = object()
        renderer.render_finished = object()
        renderer.swapchain = object()
        renderer.graphics_queue = object()
        renderer.present_queue = object()
        renderer.command_buffers = [object()]
        renderer.fp_acquire_next_image = Mock(return_value=0)
        renderer.fp_queue_present = Mock()
        return renderer

    def test_render_skips_minimized_framebuffer(self) -> None:
        renderer = self._make_renderer()

        with patch("smalloldgames.rendering.vulkan_renderer.glfw.get_framebuffer_size", return_value=(0, 0)):
            renderer.render(array("f", [0.0] * 8))

        renderer.swapchain_state.recreate.assert_not_called()
        renderer.pipeline_state.record_command_buffer.assert_not_called()

    def test_render_recreates_swapchain_and_submits_frame(self) -> None:
        renderer = self._make_renderer()
        renderer.swapchain_extent = SimpleNamespace(width=100, height=100)
        vertices = array("f", [0.0] * 16)
        ffi_stub = SimpleNamespace(memmove=Mock(), from_buffer=lambda data: data)

        with (
            patch("smalloldgames.rendering.vulkan_renderer.glfw.get_framebuffer_size", return_value=(640, 480)),
            patch.object(vulkan_renderer, "ffi", ffi_stub),
            patch("smalloldgames.rendering.vulkan_renderer.vkWaitForFences"),
            patch("smalloldgames.rendering.vulkan_renderer.vkResetFences"),
            patch("smalloldgames.rendering.vulkan_renderer.vkResetCommandBuffer"),
            patch("smalloldgames.rendering.vulkan_renderer.vkQueueSubmit") as submit,
            patch("smalloldgames.rendering.vulkan_renderer.VkSubmitInfo", side_effect=lambda **kwargs: kwargs),
            patch("smalloldgames.rendering.vulkan_renderer.VkPresentInfoKHR", side_effect=lambda **kwargs: kwargs),
        ):
            renderer.render(vertices)

        renderer.swapchain_state.recreate.assert_called_once()
        renderer.pipeline_state.record_command_buffer.assert_called_once_with(renderer.command_buffers[0], 0, 2)
        ffi_stub.memmove.assert_called_once_with(renderer.vertex_mapping, vertices, len(vertices) * vertices.itemsize)
        submit.assert_called_once()
        renderer.fp_queue_present.assert_called_once()

    def test_render_collects_previous_gpu_timing_results(self) -> None:
        renderer = self._make_renderer()
        renderer.gpu_timing_pending = True
        vertices = array("f", [0.0] * 8)

        def write_query_results(_device, _pool, _first, _count, _size, data, _stride, _flags):
            data[0] = 10
            data[1] = 14
            return vulkan_renderer.VK_SUCCESS

        with (
            patch("smalloldgames.rendering.vulkan_renderer.glfw.get_framebuffer_size", return_value=(640, 480)),
            patch.object(
                vulkan_renderer,
                "ffi",
                SimpleNamespace(
                    memmove=Mock(),
                    from_buffer=lambda data: data,
                    new=vulkan_renderer.ffi.new,
                    sizeof=vulkan_renderer.ffi.sizeof,
                ),
            ),
            patch("smalloldgames.rendering.vulkan_renderer.vkGetQueryPoolResults", side_effect=write_query_results),
            patch("smalloldgames.rendering.vulkan_renderer.vkWaitForFences"),
            patch("smalloldgames.rendering.vulkan_renderer.vkResetFences"),
            patch("smalloldgames.rendering.vulkan_renderer.vkResetCommandBuffer"),
            patch("smalloldgames.rendering.vulkan_renderer.vkQueueSubmit"),
            patch("smalloldgames.rendering.vulkan_renderer.VkSubmitInfo", side_effect=lambda **kwargs: kwargs),
            patch("smalloldgames.rendering.vulkan_renderer.VkPresentInfoKHR", side_effect=lambda **kwargs: kwargs),
        ):
            renderer.render(vertices)

        self.assertEqual(renderer.last_gpu_frame_ms, 4.0)
        self.assertTrue(renderer.gpu_timing_pending)

    def test_render_rejects_frames_over_budget(self) -> None:
        renderer = self._make_renderer()

        with (
            patch.object(vulkan_renderer, "MAX_VERTEX_BYTES", 32),
            patch("smalloldgames.rendering.vulkan_renderer.glfw.get_framebuffer_size", return_value=(640, 480)),
            self.assertRaises(ValueError),
        ):
            renderer.render(array("f", [0.0] * 16))

    def test_close_waits_and_closes_subsystems_once(self) -> None:
        renderer = self._make_renderer()

        with patch("vulkan.vkDeviceWaitIdle") as wait_idle:
            renderer.close()
            renderer.close()

        wait_idle.assert_called_once_with(renderer.device)
        renderer.resource_state.close.assert_called_once()
        renderer.swapchain_state.cleanup.assert_called_once()
        renderer.pipeline_state.close.assert_called_once()
        renderer.device_state.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
