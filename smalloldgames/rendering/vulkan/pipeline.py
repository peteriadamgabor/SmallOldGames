from __future__ import annotations

from array import array
from pathlib import Path
from typing import Any

from vulkan import (
    VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
    VK_ATTACHMENT_LOAD_OP_CLEAR,
    VK_ATTACHMENT_LOAD_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_STORE,
    VK_BLEND_FACTOR_ONE,
    VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
    VK_BLEND_FACTOR_SRC_ALPHA,
    VK_BLEND_OP_ADD,
    VK_COLOR_COMPONENT_A_BIT,
    VK_COLOR_COMPONENT_B_BIT,
    VK_COLOR_COMPONENT_G_BIT,
    VK_COLOR_COMPONENT_R_BIT,
    VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
    VK_CULL_MODE_NONE,
    VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
    VK_FORMAT_R32G32_SFLOAT,
    VK_FORMAT_R32G32B32A32_SFLOAT,
    VK_FRONT_FACE_COUNTER_CLOCKWISE,
    VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
    VK_IMAGE_LAYOUT_UNDEFINED,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
    VK_POLYGON_MODE_FILL,
    VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SHADER_STAGE_FRAGMENT_BIT,
    VK_SHADER_STAGE_VERTEX_BIT,
    VK_SUBPASS_CONTENTS_INLINE,
    VK_SUBPASS_EXTERNAL,
    VK_VERTEX_INPUT_RATE_VERTEX,
    VkAttachmentDescription,
    VkAttachmentReference,
    VkClearColorValue,
    VkClearValue,
    VkCommandBufferBeginInfo,
    VkDescriptorSetLayoutBinding,
    VkDescriptorSetLayoutCreateInfo,
    VkExtent2D,
    VkGraphicsPipelineCreateInfo,
    VkOffset2D,
    VkPipelineColorBlendAttachmentState,
    VkPipelineColorBlendStateCreateInfo,
    VkPipelineInputAssemblyStateCreateInfo,
    VkPipelineLayoutCreateInfo,
    VkPipelineMultisampleStateCreateInfo,
    VkPipelineRasterizationStateCreateInfo,
    VkPipelineShaderStageCreateInfo,
    VkPipelineVertexInputStateCreateInfo,
    VkPipelineViewportStateCreateInfo,
    VkRect2D,
    VkRenderPassBeginInfo,
    VkRenderPassCreateInfo,
    VkShaderModuleCreateInfo,
    VkSubpassDependency,
    VkSubpassDescription,
    VkVertexInputAttributeDescription,
    VkVertexInputBindingDescription,
    VkViewport,
    vkBeginCommandBuffer,
    vkCmdBeginRenderPass,
    vkCmdBindDescriptorSets,
    vkCmdBindPipeline,
    vkCmdBindVertexBuffers,
    vkCmdDraw,
    vkCmdEndRenderPass,
    vkCmdResetQueryPool,
    vkCmdWriteTimestamp,
    vkCreateDescriptorSetLayout,
    vkCreateGraphicsPipelines,
    vkCreatePipelineLayout,
    vkCreateRenderPass,
    vkCreateShaderModule,
    vkDestroyDescriptorSetLayout,
    vkDestroyPipeline,
    vkDestroyPipelineLayout,
    vkDestroyRenderPass,
    vkDestroyShaderModule,
    vkEndCommandBuffer,
)

from .constants import CLEAR_COLOR, VERTEX_STRIDE


class VulkanPipeline:
    def __init__(self, renderer: Any) -> None:
        self.renderer = renderer

    def initialize(self) -> None:
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
        self.renderer.descriptor_set_layout = vkCreateDescriptorSetLayout(self.renderer.device, create_info, None)

    def create_frame_resources(self) -> None:
        self._create_render_pass()
        self._create_pipeline()

    def destroy_frame_resources(self) -> None:
        if self.renderer.pipeline is not None:
            vkDestroyPipeline(self.renderer.device, self.renderer.pipeline, None)
            self.renderer.pipeline = None
        if self.renderer.pipeline_layout is not None:
            vkDestroyPipelineLayout(self.renderer.device, self.renderer.pipeline_layout, None)
            self.renderer.pipeline_layout = None
        if self.renderer.render_pass is not None:
            vkDestroyRenderPass(self.renderer.device, self.renderer.render_pass, None)
            self.renderer.render_pass = None

    def close(self) -> None:
        if self.renderer.device is not None and self.renderer.descriptor_set_layout is not None:
            vkDestroyDescriptorSetLayout(self.renderer.device, self.renderer.descriptor_set_layout, None)

    def record_command_buffer(self, command_buffer, image_index: int, vertex_count: int) -> None:
        begin_info = VkCommandBufferBeginInfo(flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT)
        vkBeginCommandBuffer(command_buffer, begin_info)
        if self.renderer.gpu_timing_query_pool is not None:
            vkCmdResetQueryPool(command_buffer, self.renderer.gpu_timing_query_pool, 0, 2)
            vkCmdWriteTimestamp(
                command_buffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, self.renderer.gpu_timing_query_pool, 0
            )

        clear_value = VkClearValue(color=VkClearColorValue(float32=CLEAR_COLOR))
        render_pass_begin = VkRenderPassBeginInfo(
            renderPass=self.renderer.render_pass,
            framebuffer=self.renderer.framebuffers[image_index],
            renderArea=VkRect2D(offset=VkOffset2D(x=0, y=0), extent=self.renderer.swapchain_extent),
            clearValueCount=1,
            pClearValues=[clear_value],
        )
        vkCmdBeginRenderPass(command_buffer, render_pass_begin, VK_SUBPASS_CONTENTS_INLINE)
        vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.renderer.pipeline)
        vkCmdBindDescriptorSets(
            command_buffer,
            VK_PIPELINE_BIND_POINT_GRAPHICS,
            self.renderer.pipeline_layout,
            0,
            1,
            [self.renderer.descriptor_set],
            0,
            None,
        )
        vkCmdBindVertexBuffers(command_buffer, 0, 1, [self.renderer.vertex_buffer], [0])
        if vertex_count:
            vkCmdDraw(command_buffer, vertex_count, 1, 0, 0)
        vkCmdEndRenderPass(command_buffer)
        if self.renderer.gpu_timing_query_pool is not None:
            vkCmdWriteTimestamp(
                command_buffer,
                VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                self.renderer.gpu_timing_query_pool,
                1,
            )
        vkEndCommandBuffer(command_buffer)

    def _create_render_pass(self) -> None:
        attachment = VkAttachmentDescription(
            format=self.renderer.swapchain_format,
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
        self.renderer.render_pass = vkCreateRenderPass(self.renderer.device, create_info, None)

    def _create_pipeline(self) -> None:
        self.renderer.pipeline_layout = vkCreatePipelineLayout(
            self.renderer.device,
            VkPipelineLayoutCreateInfo(
                setLayoutCount=1,
                pSetLayouts=[self.renderer.descriptor_set_layout],
            ),
            None,
        )

        vert_module = self._create_shader_module(self.renderer.shader_dir / "color.vert.spv")
        frag_module = self._create_shader_module(self.renderer.shader_dir / "color.frag.spv")
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
                VkVertexInputAttributeDescription(
                    location=1, binding=0, format=VK_FORMAT_R32G32B32A32_SFLOAT, offset=8
                ),
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
                layout=self.renderer.pipeline_layout,
                renderPass=self.renderer.render_pass,
                subpass=0,
            )
            self.renderer.pipeline = vkCreateGraphicsPipelines(self.renderer.device, None, 1, [pipeline_info], None)[0]
        finally:
            vkDestroyShaderModule(self.renderer.device, vert_module, None)
            vkDestroyShaderModule(self.renderer.device, frag_module, None)

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
        return vkCreateShaderModule(self.renderer.device, create_info, None)

    def _content_viewport(self) -> tuple[float, float, float, float, VkRect2D]:
        scale = min(
            self.renderer.swapchain_extent.width / self.renderer.canvas_width,
            self.renderer.swapchain_extent.height / self.renderer.canvas_height,
        )
        viewport_width = float(self.renderer.canvas_width * scale)
        viewport_height = float(self.renderer.canvas_height * scale)
        offset_x = int((self.renderer.swapchain_extent.width - viewport_width) * 0.5)
        offset_y = int((self.renderer.swapchain_extent.height - viewport_height) * 0.5)
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
