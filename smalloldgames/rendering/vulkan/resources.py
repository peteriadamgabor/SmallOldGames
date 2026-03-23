from __future__ import annotations

from typing import Any

from vulkan import (
    VK_ACCESS_SHADER_READ_BIT,
    VK_ACCESS_TRANSFER_WRITE_BIT,
    VK_BORDER_COLOR_INT_OPAQUE_BLACK,
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
    VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
    VK_FENCE_CREATE_SIGNALED_BIT,
    VK_FILTER_NEAREST,
    VK_FORMAT_R8G8B8A8_UNORM,
    VK_IMAGE_ASPECT_COLOR_BIT,
    VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
    VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
    VK_IMAGE_LAYOUT_UNDEFINED,
    VK_IMAGE_TILING_OPTIMAL,
    VK_IMAGE_TYPE_2D,
    VK_IMAGE_USAGE_SAMPLED_BIT,
    VK_IMAGE_USAGE_TRANSFER_DST_BIT,
    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_QUERY_TYPE_TIMESTAMP,
    VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
    VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
    VK_PIPELINE_STAGE_TRANSFER_BIT,
    VK_QUEUE_FAMILY_IGNORED,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
    VK_SAMPLER_MIPMAP_MODE_NEAREST,
    VK_SHARING_MODE_EXCLUSIVE,
    VkBufferImageCopy,
    VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo,
    VkDescriptorImageInfo,
    VkDescriptorPoolCreateInfo,
    VkDescriptorPoolSize,
    VkDescriptorSetAllocateInfo,
    VkExtent3D,
    VkFenceCreateInfo,
    VkImageCreateInfo,
    VkImageMemoryBarrier,
    VkImageSubresourceLayers,
    VkImageSubresourceRange,
    VkMemoryAllocateInfo,
    VkOffset3D,
    VkQueryPoolCreateInfo,
    VkSamplerCreateInfo,
    VkSemaphoreCreateInfo,
    VkSubmitInfo,
    VkWriteDescriptorSet,
    vkAllocateCommandBuffers,
    vkAllocateDescriptorSets,
    vkAllocateMemory,
    vkBeginCommandBuffer,
    vkBindImageMemory,
    vkCmdCopyBufferToImage,
    vkCmdPipelineBarrier,
    vkCreateDescriptorPool,
    vkCreateFence,
    vkCreateImage,
    vkCreateQueryPool,
    vkCreateSampler,
    vkCreateSemaphore,
    vkDestroyBuffer,
    vkDestroyDescriptorPool,
    vkDestroyFence,
    vkDestroyImage,
    vkDestroyImageView,
    vkDestroyQueryPool,
    vkDestroySampler,
    vkDestroySemaphore,
    vkEndCommandBuffer,
    vkFreeCommandBuffers,
    vkFreeMemory,
    vkGetImageMemoryRequirements,
    vkMapMemory,
    vkQueueSubmit,
    vkQueueWaitIdle,
    vkUnmapMemory,
    vkUpdateDescriptorSets,
)

from .device import create_buffer, find_memory_type
from .swapchain import create_image_view


class VulkanResources:
    def __init__(self, renderer: Any) -> None:
        self.renderer = renderer

    def initialize(self) -> None:
        self._create_texture_resources()
        self._create_sync_objects()
        self._create_gpu_timing_resources()

    def close(self) -> None:
        if self.renderer.device is not None and self.renderer.image_available is not None:
            vkDestroySemaphore(self.renderer.device, self.renderer.image_available, None)
        if self.renderer.device is not None and self.renderer.render_finished is not None:
            vkDestroySemaphore(self.renderer.device, self.renderer.render_finished, None)
        if self.renderer.device is not None and self.renderer.in_flight_fence is not None:
            vkDestroyFence(self.renderer.device, self.renderer.in_flight_fence, None)
        if self.renderer.device is not None and self.renderer.gpu_timing_query_pool is not None:
            vkDestroyQueryPool(self.renderer.device, self.renderer.gpu_timing_query_pool, None)
        if self.renderer.device is not None and self.renderer.texture_sampler is not None:
            vkDestroySampler(self.renderer.device, self.renderer.texture_sampler, None)
        if self.renderer.device is not None and self.renderer.texture_view is not None:
            vkDestroyImageView(self.renderer.device, self.renderer.texture_view, None)
        if self.renderer.device is not None and self.renderer.texture_image is not None:
            vkDestroyImage(self.renderer.device, self.renderer.texture_image, None)
        if self.renderer.device is not None and self.renderer.texture_memory is not None:
            vkFreeMemory(self.renderer.device, self.renderer.texture_memory, None)
        if self.renderer.device is not None and self.renderer.descriptor_pool is not None:
            vkDestroyDescriptorPool(self.renderer.device, self.renderer.descriptor_pool, None)

    def _create_texture_resources(self) -> None:
        staging_buffer, staging_memory = create_buffer(
            self.renderer,
            len(self.renderer.sprite_atlas.rgba_bytes),
            VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        )
        try:
            mapped = vkMapMemory(self.renderer.device, staging_memory, 0, len(self.renderer.sprite_atlas.rgba_bytes), 0)
            mapped[: len(self.renderer.sprite_atlas.rgba_bytes)] = self.renderer.sprite_atlas.rgba_bytes
            vkUnmapMemory(self.renderer.device, staging_memory)

            image_info = VkImageCreateInfo(
                imageType=VK_IMAGE_TYPE_2D,
                format=VK_FORMAT_R8G8B8A8_UNORM,
                extent=VkExtent3D(
                    width=self.renderer.sprite_atlas.width,
                    height=self.renderer.sprite_atlas.height,
                    depth=1,
                ),
                mipLevels=1,
                arrayLayers=1,
                samples=VK_SAMPLE_COUNT_1_BIT,
                tiling=VK_IMAGE_TILING_OPTIMAL,
                usage=VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                sharingMode=VK_SHARING_MODE_EXCLUSIVE,
                initialLayout=VK_IMAGE_LAYOUT_UNDEFINED,
            )
            self.renderer.texture_image = vkCreateImage(self.renderer.device, image_info, None)
            requirements = vkGetImageMemoryRequirements(self.renderer.device, self.renderer.texture_image)
            self.renderer.texture_memory = vkAllocateMemory(
                self.renderer.device,
                VkMemoryAllocateInfo(
                    allocationSize=requirements.size,
                    memoryTypeIndex=find_memory_type(
                        self.renderer,
                        requirements.memoryTypeBits,
                        VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
                    ),
                ),
                None,
            )
            vkBindImageMemory(self.renderer.device, self.renderer.texture_image, self.renderer.texture_memory, 0)

            self._transition_image_layout(
                self.renderer.texture_image,
                VK_IMAGE_LAYOUT_UNDEFINED,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                0,
                VK_ACCESS_TRANSFER_WRITE_BIT,
            )
            self._copy_buffer_to_image(
                staging_buffer,
                self.renderer.texture_image,
                self.renderer.sprite_atlas.width,
                self.renderer.sprite_atlas.height,
            )
            self._transition_image_layout(
                self.renderer.texture_image,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
                VK_ACCESS_TRANSFER_WRITE_BIT,
                VK_ACCESS_SHADER_READ_BIT,
            )
        finally:
            vkDestroyBuffer(self.renderer.device, staging_buffer, None)
            vkFreeMemory(self.renderer.device, staging_memory, None)

        self.renderer.texture_view = create_image_view(self.renderer, self.renderer.texture_image, VK_FORMAT_R8G8B8A8_UNORM)
        self.renderer.texture_sampler = vkCreateSampler(
            self.renderer.device,
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

        self.renderer.descriptor_pool = vkCreateDescriptorPool(
            self.renderer.device,
            VkDescriptorPoolCreateInfo(
                maxSets=1,
                pPoolSizes=[VkDescriptorPoolSize(type=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, descriptorCount=1)],
            ),
            None,
        )
        self.renderer.descriptor_set = vkAllocateDescriptorSets(
            self.renderer.device,
            VkDescriptorSetAllocateInfo(
                descriptorPool=self.renderer.descriptor_pool,
                descriptorSetCount=1,
                pSetLayouts=[self.renderer.descriptor_set_layout],
            ),
        )[0]
        image_info = VkDescriptorImageInfo(
            sampler=self.renderer.texture_sampler,
            imageView=self.renderer.texture_view,
            imageLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        )
        write = VkWriteDescriptorSet(
            dstSet=self.renderer.descriptor_set,
            dstBinding=0,
            dstArrayElement=0,
            descriptorCount=1,
            descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
            pImageInfo=[image_info],
        )
        vkUpdateDescriptorSets(self.renderer.device, 1, [write], 0, None)

    def _create_sync_objects(self) -> None:
        semaphore_info = VkSemaphoreCreateInfo()
        fence_info = VkFenceCreateInfo(flags=VK_FENCE_CREATE_SIGNALED_BIT)
        self.renderer.image_available = vkCreateSemaphore(self.renderer.device, semaphore_info, None)
        self.renderer.render_finished = vkCreateSemaphore(self.renderer.device, semaphore_info, None)
        self.renderer.in_flight_fence = vkCreateFence(self.renderer.device, fence_info, None)

    def _create_gpu_timing_resources(self) -> None:
        if not self.renderer.gpu_timing_supported:
            return
        self.renderer.gpu_timing_query_pool = vkCreateQueryPool(
            self.renderer.device,
            VkQueryPoolCreateInfo(
                queryType=VK_QUERY_TYPE_TIMESTAMP,
                queryCount=2,
            ),
            None,
        )

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
            self.renderer.device,
            VkCommandBufferAllocateInfo(
                commandPool=self.renderer.command_pool,
                level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                commandBufferCount=1,
            ),
        )[0]
        vkBeginCommandBuffer(
            command_buffer,
            VkCommandBufferBeginInfo(flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT),
        )
        return command_buffer

    def _end_single_use_command_buffer(self, command_buffer) -> None:
        vkEndCommandBuffer(command_buffer)
        submit_info = VkSubmitInfo(commandBufferCount=1, pCommandBuffers=[command_buffer])
        vkQueueSubmit(self.renderer.graphics_queue, 1, [submit_info], None)
        vkQueueWaitIdle(self.renderer.graphics_queue)
        vkFreeCommandBuffers(self.renderer.device, self.renderer.command_pool, 1, [command_buffer])
