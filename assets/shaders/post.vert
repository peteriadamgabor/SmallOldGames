#version 450

layout(location = 0) out vec2 frag_uv;

vec2 POSITIONS[3] = vec2[](
    vec2(-1.0, -1.0),
    vec2(3.0, -1.0),
    vec2(-1.0, 3.0)
);

void main() {
    vec2 position = POSITIONS[gl_VertexIndex];
    gl_Position = vec4(position, 0.0, 1.0);
    frag_uv = vec2(position.x * 0.5 + 0.5, 1.0 - (position.y * 0.5 + 0.5));
}
