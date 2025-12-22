"""
Color to Minecraft Block Mapper Module

Maps RGB pixel colors to the closest matching Minecraft block.
Limited palette: ONLY wool, concrete, terracotta (no falling blocks, no quartz)
"""

from typing import Dict, Tuple, Optional
import numpy as np

# Block palette - ONLY wool, concrete, terracotta
# NO concrete powder (falls), NO quartz

BLOCK_COLORS = {
    # === CONCRETE (16 colors) ===
    'minecraft:white_concrete': (207, 213, 214),
    'minecraft:orange_concrete': (224, 97, 1),
    'minecraft:magenta_concrete': (169, 48, 159),
    'minecraft:light_blue_concrete': (36, 137, 199),
    'minecraft:yellow_concrete': (241, 175, 21),
    'minecraft:lime_concrete': (94, 169, 25),
    'minecraft:pink_concrete': (214, 101, 143),
    'minecraft:gray_concrete': (55, 58, 62),
    'minecraft:light_gray_concrete': (125, 125, 115),
    'minecraft:cyan_concrete': (21, 119, 136),
    'minecraft:purple_concrete': (100, 32, 156),
    'minecraft:blue_concrete': (45, 47, 143),
    'minecraft:brown_concrete': (96, 60, 32),
    'minecraft:green_concrete': (73, 91, 36),
    'minecraft:red_concrete': (142, 33, 33),
    'minecraft:black_concrete': (8, 10, 15),
    
    # === WOOL (16 colors) ===
    'minecraft:white_wool': (234, 236, 237),
    'minecraft:orange_wool': (241, 118, 20),
    'minecraft:magenta_wool': (190, 69, 180),
    'minecraft:light_blue_wool': (58, 175, 217),
    'minecraft:yellow_wool': (249, 198, 40),
    'minecraft:lime_wool': (113, 187, 26),
    'minecraft:pink_wool': (238, 141, 172),
    'minecraft:gray_wool': (63, 68, 72),
    'minecraft:light_gray_wool': (143, 143, 135),
    'minecraft:cyan_wool': (21, 138, 145),
    'minecraft:purple_wool': (122, 42, 173),
    'minecraft:blue_wool': (53, 57, 157),
    'minecraft:brown_wool': (114, 72, 41),
    'minecraft:green_wool': (85, 110, 27),
    'minecraft:red_wool': (161, 39, 35),
    'minecraft:black_wool': (21, 21, 26),
    
    # === TERRACOTTA (17 colors - great for skin tones) ===
    'minecraft:terracotta': (152, 94, 67),
    'minecraft:white_terracotta': (210, 178, 161),
    'minecraft:orange_terracotta': (162, 84, 38),
    'minecraft:magenta_terracotta': (150, 88, 109),
    'minecraft:light_blue_terracotta': (113, 109, 138),
    'minecraft:yellow_terracotta': (186, 133, 35),
    'minecraft:lime_terracotta': (103, 118, 53),
    'minecraft:pink_terracotta': (162, 78, 79),
    'minecraft:gray_terracotta': (58, 42, 36),
    'minecraft:light_gray_terracotta': (135, 107, 98),
    'minecraft:cyan_terracotta': (87, 91, 91),
    'minecraft:purple_terracotta': (118, 70, 86),
    'minecraft:blue_terracotta': (74, 60, 91),
    'minecraft:brown_terracotta': (77, 51, 36),
    'minecraft:green_terracotta': (76, 83, 42),
    'minecraft:red_terracotta': (143, 61, 47),
    'minecraft:black_terracotta': (37, 23, 16),
}

# Cache
_color_cache: Dict[Tuple[int, int, int], str] = {}
_block_names = None
_block_lab = None


def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert RGB to LAB color space."""
    rgb_norm = rgb.astype(np.float32) / 255.0
    
    mask = rgb_norm > 0.04045
    rgb_linear = np.where(mask, ((rgb_norm + 0.055) / 1.055) ** 2.4, rgb_norm / 12.92)
    
    matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])
    
    if rgb_linear.ndim == 1:
        xyz = matrix @ rgb_linear
    else:
        xyz = rgb_linear @ matrix.T
    
    ref = np.array([0.95047, 1.0, 1.08883])
    xyz_norm = xyz / ref
    
    mask = xyz_norm > 0.008856
    f_xyz = np.where(mask, xyz_norm ** (1/3), (903.3 * xyz_norm + 16) / 116)
    
    if f_xyz.ndim == 1:
        L = 116 * f_xyz[1] - 16
        a = 500 * (f_xyz[0] - f_xyz[1])
        b = 200 * (f_xyz[1] - f_xyz[2])
        return np.array([L, a, b])
    else:
        L = 116 * f_xyz[:, 1] - 16
        a = 500 * (f_xyz[:, 0] - f_xyz[:, 1])
        b = 200 * (f_xyz[:, 1] - f_xyz[:, 2])
        return np.stack([L, a, b], axis=1)


def _init_colors():
    """Initialize color arrays."""
    global _block_names, _block_lab
    if _block_names is not None:
        return
    
    _block_names = list(BLOCK_COLORS.keys())
    rgb_array = np.array([BLOCK_COLORS[name] for name in _block_names], dtype=np.float32)
    _block_lab = _rgb_to_lab(rgb_array)


def _is_skin_tone(r: int, g: int, b: int) -> bool:
    """Check if a color is likely a skin tone."""
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    
    if max_c == 0:
        return False
    
    saturation = (max_c - min_c) / max_c
    avg = (int(r) + int(g) + int(b)) / 3  # Use int to avoid overflow
    
    is_warm = r >= g and g >= b * 0.8
    is_low_sat = saturation < 0.6
    is_medium_bright = 50 < avg < 230
    
    return is_warm and is_low_sat and is_medium_bright


def find_closest_block(rgb: Tuple[int, int, int]) -> str:
    """Find the closest matching Minecraft block for an RGB color."""
    _init_colors()
    
    if rgb in _color_cache:
        return _color_cache[rgb]
    
    r, g, b = rgb
    input_lab = _rgb_to_lab(np.array(rgb))
    
    # Calculate distances
    diff = _block_lab - input_lab
    distances = np.sqrt(np.sum(diff ** 2, axis=1))
    
    # If this looks like a skin tone, prefer terracotta
    if _is_skin_tone(r, g, b):
        for i, name in enumerate(_block_names):
            if 'yellow' in name and 'terracotta' not in name:
                distances[i] *= 2.5  # Penalize yellow (not terracotta)
            if 'terracotta' in name:
                distances[i] *= 0.85  # Bonus for terracotta
    
    closest_idx = np.argmin(distances)
    result = _block_names[closest_idx]
    
    _color_cache[rgb] = result
    return result


def get_block_for_pixel(rgba: Tuple[int, int, int, int], alpha_threshold: int = 128) -> Optional[str]:
    """Get the block for a pixel, returning None for transparent pixels."""
    r, g, b, a = rgba
    
    if a < alpha_threshold:
        return None
    
    return find_closest_block((r, g, b))


def get_block_color(block_id: str) -> Tuple[int, int, int]:
    """Get the RGB color for a block ID."""
    return BLOCK_COLORS.get(block_id, (128, 128, 128))


def build_block_palette() -> Dict[str, Tuple[int, int, int]]:
    """Return the full block color palette."""
    return BLOCK_COLORS.copy()
