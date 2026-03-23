#version 450

layout(location = 0) in vec2 frag_uv;

layout(set = 0, binding = 0) uniform sampler2D scene_texture;

layout(location = 0) out vec4 out_color;

void main() {
    vec2 uv = frag_uv;
    vec2 centered = uv * 2.0 - 1.0;
    float radius = dot(centered, centered);
    vec2 warped_uv = uv + centered * radius * 0.02;

    if (warped_uv.x < 0.0 || warped_uv.x > 1.0 || warped_uv.y < 0.0 || warped_uv.y > 1.0) {
        out_color = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec3 color = texture(scene_texture, warped_uv).rgb;
    float scanline = 0.92 + 0.08 * sin(warped_uv.y * 960.0 * 1.4);
    float grille = 0.96 + 0.04 * sin(warped_uv.x * 540.0 * 2.2);
    float vignette = clamp(1.0 - radius * 0.35, 0.0, 1.0);

    color *= scanline * grille * vignette;
    color = pow(color, vec3(0.95));
    out_color = vec4(color, 1.0);
}
