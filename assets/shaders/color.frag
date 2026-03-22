#version 450

layout(location = 0) in vec4 frag_color;
layout(location = 1) in vec2 frag_uv;

layout(set = 0, binding = 0) uniform sampler2D atlas_texture;

layout(location = 0) out vec4 out_color;

void main() {
    out_color = texture(atlas_texture, frag_uv) * frag_color;
}
