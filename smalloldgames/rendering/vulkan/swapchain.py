from __future__ import annotations

from typing import Any

import glfw
from vulkan import (
    VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMPONENT_SWIZZLE_IDENTITY,
    VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
    VK_FORMAT_B8G8R8A8_UNORM,
    VK_IMAGE_ASPECT_COLOR_BIT,
    VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
    VK_IMAGE_VIEW_TYPE_2D,
    VK_PRESENT_MODE_FIFO_KHR,
    VK_PRESENT_MODE_MAILBOX_KHR,
    VK_SHARING_MODE_CONCURRENT,
    VK_SHARING_MODE_EXCLUSIVE,
    VkCommandBufferAllocateInfo,
    VkComponentMapping,
    VkExtent2D,
    VkFramebufferCreateInfo,
    VkImageSubresourceRange,
    VkImageViewCreateInfo,
    VkSurfaceFormatKHR,
    VkSwapchainCreateInfoKHR,
    vkAllocateCommandBuffers,
    vkCreateFramebuffer,
    vkCreateImageView,
    vkDestroyFramebuffer,
    vkDestroyImageView,
    vkDeviceWaitIdle,
    vkFreeCommandBuffers,
)


def create_image_view(renderer: Any, image, format_code: int) -> object:
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
    return vkCreateImageView(renderer.device, create_info, None)


class VulkanSwapchain:
    def __init__(self, renderer: Any) -> None:
        self.renderer = renderer

    def initialize(self) -> None:
        self._create_swapchain()
        self.renderer.pipeline_state.create_frame_resources()
        self._create_framebuffers()
        self._create_command_buffers()

    def recreate(self) -> None:
        vkDeviceWaitIdle(self.renderer.device)
        self.cleanup()
        self.initialize()

    def cleanup(self) -> None:
        if self.renderer.command_buffers:
            vkFreeCommandBuffers(
                self.renderer.device,
                self.renderer.command_pool,
                len(self.renderer.command_buffers),
                self.renderer.command_buffers,
            )
            self.renderer.command_buffers = []
        for framebuffer in self.renderer.framebuffers:
            vkDestroyFramebuffer(self.renderer.device, framebuffer, None)
        self.renderer.framebuffers = []
        self.renderer.pipeline_state.destroy_frame_resources()
        for image_view in self.renderer.swapchain_image_views:
            vkDestroyImageView(self.renderer.device, image_view, None)
        self.renderer.swapchain_image_views = []
        if self.renderer.swapchain is not None and self.renderer.fp_destroy_swapchain is not None:
            self.renderer.fp_destroy_swapchain(self.renderer.device, self.renderer.swapchain, None)
            self.renderer.swapchain = None

    def _create_swapchain(self) -> None:
        capabilities = self.renderer.fp_get_surface_capabilities(self.renderer.physical_device, self.renderer.surface)
        formats = list(self.renderer.fp_get_surface_formats(self.renderer.physical_device, self.renderer.surface))
        present_modes = list(
            self.renderer.fp_get_surface_present_modes(self.renderer.physical_device, self.renderer.surface)
        )
        surface_format = self._choose_surface_format(formats)
        present_mode = self._choose_present_mode(present_modes)
        self.renderer.swapchain_extent = self._choose_extent(capabilities)
        self.renderer.swapchain_format = surface_format.format

        image_count = capabilities.minImageCount + 1
        if capabilities.maxImageCount > 0 and image_count > capabilities.maxImageCount:
            image_count = capabilities.maxImageCount

        indices = [self.renderer.queue_families.graphics, self.renderer.queue_families.present]
        concurrent = self.renderer.queue_families.graphics != self.renderer.queue_families.present
        create_info = VkSwapchainCreateInfoKHR(
            surface=self.renderer.surface,
            minImageCount=image_count,
            imageFormat=surface_format.format,
            imageColorSpace=surface_format.colorSpace,
            imageExtent=self.renderer.swapchain_extent,
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
        self.renderer.swapchain = self.renderer.fp_create_swapchain(self.renderer.device, create_info, None)
        self.renderer.swapchain_images = list(
            self.renderer.fp_get_swapchain_images(self.renderer.device, self.renderer.swapchain)
        )
        self.renderer.swapchain_image_views = [
            create_image_view(self.renderer, image, self.renderer.swapchain_format)
            for image in self.renderer.swapchain_images
        ]

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
        width, height = glfw.get_framebuffer_size(self.renderer.window)
        return VkExtent2D(
            width=max(capabilities.minImageExtent.width, min(capabilities.maxImageExtent.width, width)),
            height=max(capabilities.minImageExtent.height, min(capabilities.maxImageExtent.height, height)),
        )

    def _create_framebuffers(self) -> None:
        self.renderer.framebuffers = []
        for image_view in self.renderer.swapchain_image_views:
            create_info = VkFramebufferCreateInfo(
                renderPass=self.renderer.render_pass,
                attachmentCount=1,
                pAttachments=[image_view],
                width=self.renderer.swapchain_extent.width,
                height=self.renderer.swapchain_extent.height,
                layers=1,
            )
            self.renderer.framebuffers.append(vkCreateFramebuffer(self.renderer.device, create_info, None))

    def _create_command_buffers(self) -> None:
        allocate_info = VkCommandBufferAllocateInfo(
            commandPool=self.renderer.command_pool,
            level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
            commandBufferCount=len(self.renderer.framebuffers),
        )
        self.renderer.command_buffers = list(vkAllocateCommandBuffers(self.renderer.device, allocate_info))
