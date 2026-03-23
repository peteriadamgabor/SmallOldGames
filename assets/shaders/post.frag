#version 450

layout(location = 0) in vec2 frag_uv;

layout(set = 0, binding = 0) uniform sampler2D scene_texture;

layout(location = 0) out vec4 out_color;

void main() {
    vec2 uv = frag_uv;
    vec2 centered = uv * 2.0 - 1.0;
    float radius = dot(centered, centered);
    vec2 warped_uv = clamp(uv + centered * radius * 0.006, vec2(0.0), vec2(1.0));

    vec3 color = texture(scene_texture, warped_uv).rgb;
    float scanline = 0.95 + 0.05 * sin(warped_uv.y * 960.0 * 1.2);
    float grille = 0.97 + 0.03 * sin(warped_uv.x * 540.0 * 1.8);
    float vignette = clamp(1.0 - radius * 0.12, 0.0, 1.0);

    color *= scanline * grille * vignette;
    color = pow(color, vec3(0.97));
    out_color = vec4(color, 1.0);
}
