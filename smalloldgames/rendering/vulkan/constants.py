"""Shared Vulkan renderer constants."""

UINT64_MAX = (1 << 64) - 1
VERTEX_STRIDE = 32  # 8 floats * 4 bytes each (x, y, r, g, b, a, u, v)
MAX_VERTEX_BYTES = 1_048_576  # 1 MB vertex budget per frame
CLEAR_COLOR = (0.02, 0.02, 0.04, 1.0)

