"""
Minecraft Skin Parser Module

Parses 64x64 Minecraft player skins and extracts body part textures.
Supports both classic (4px arms) and slim (3px arms) skin types.
Handles 64x32 skins by mirroring left arm/leg from right side.
"""

from PIL import Image
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
import numpy as np


@dataclass
class BodyPartTextures:
    """Textures for all 6 faces of a body part cuboid."""
    front: np.ndarray
    back: np.ndarray
    left: np.ndarray
    right: np.ndarray
    top: np.ndarray
    bottom: np.ndarray


# Skin layout coordinates for 64x64 format - CLASSIC (4px arms)
SKIN_LAYOUT_CLASSIC = {
    'head': {
        'right':  (0, 8, 8, 8),
        'front':  (8, 8, 8, 8),
        'left':   (16, 8, 8, 8),
        'back':   (24, 8, 8, 8),
        'top':    (8, 0, 8, 8),
        'bottom': (16, 0, 8, 8),
    },
    'head_overlay': {
        'right':  (32, 8, 8, 8),
        'front':  (40, 8, 8, 8),
        'left':   (48, 8, 8, 8),
        'back':   (56, 8, 8, 8),
        'top':    (40, 0, 8, 8),
        'bottom': (48, 0, 8, 8),
    },
    'body': {
        'right':  (16, 20, 4, 12),
        'front':  (20, 20, 8, 12),
        'left':   (28, 20, 4, 12),
        'back':   (32, 20, 8, 12),
        'top':    (20, 16, 8, 4),
        'bottom': (28, 16, 8, 4),
    },
    'body_overlay': {
        'right':  (16, 36, 4, 12),
        'front':  (20, 36, 8, 12),
        'left':   (28, 36, 4, 12),
        'back':   (32, 36, 8, 12),
        'top':    (20, 32, 8, 4),
        'bottom': (28, 32, 8, 4),
    },
    'right_arm': {
        'right':  (40, 20, 4, 12),
        'front':  (44, 20, 4, 12),
        'left':   (48, 20, 4, 12),
        'back':   (52, 20, 4, 12),
        'top':    (44, 16, 4, 4),
        'bottom': (48, 16, 4, 4),
    },
    'right_arm_overlay': {
        'right':  (40, 36, 4, 12),
        'front':  (44, 36, 4, 12),
        'left':   (48, 36, 4, 12),
        'back':   (52, 36, 4, 12),
        'top':    (44, 32, 4, 4),
        'bottom': (48, 32, 4, 4),
    },
    'left_arm': {
        'right':  (32, 52, 4, 12),
        'front':  (36, 52, 4, 12),
        'left':   (40, 52, 4, 12),
        'back':   (44, 52, 4, 12),
        'top':    (36, 48, 4, 4),
        'bottom': (40, 48, 4, 4),
    },
    'left_arm_overlay': {
        'right':  (48, 52, 4, 12),
        'front':  (52, 52, 4, 12),
        'left':   (56, 52, 4, 12),
        'back':   (60, 52, 4, 12),
        'top':    (52, 48, 4, 4),
        'bottom': (56, 48, 4, 4),
    },
    'right_leg': {
        'right':  (0, 20, 4, 12),
        'front':  (4, 20, 4, 12),
        'left':   (8, 20, 4, 12),
        'back':   (12, 20, 4, 12),
        'top':    (4, 16, 4, 4),
        'bottom': (8, 16, 4, 4),
    },
    'right_leg_overlay': {
        'right':  (0, 36, 4, 12),
        'front':  (4, 36, 4, 12),
        'left':   (8, 36, 4, 12),
        'back':   (12, 36, 4, 12),
        'top':    (4, 32, 4, 4),
        'bottom': (8, 32, 4, 4),
    },
    'left_leg': {
        'right':  (16, 52, 4, 12),
        'front':  (20, 52, 4, 12),
        'left':   (24, 52, 4, 12),
        'back':   (28, 52, 4, 12),
        'top':    (20, 48, 4, 4),
        'bottom': (24, 48, 4, 4),
    },
    'left_leg_overlay': {
        'right':  (0, 52, 4, 12),
        'front':  (4, 52, 4, 12),
        'left':   (8, 52, 4, 12),
        'back':   (12, 52, 4, 12),
        'top':    (4, 48, 4, 4),
        'bottom': (8, 48, 4, 4),
    },
}

# Skin layout for SLIM skins (3px arms)
SKIN_LAYOUT_SLIM = {
    **SKIN_LAYOUT_CLASSIC,
    'right_arm': {
        'right':  (40, 20, 4, 12),
        'front':  (44, 20, 3, 12),
        'left':   (47, 20, 4, 12),
        'back':   (51, 20, 3, 12),
        'top':    (44, 16, 3, 4),
        'bottom': (47, 16, 3, 4),
    },
    'right_arm_overlay': {
        'right':  (40, 36, 4, 12),
        'front':  (44, 36, 3, 12),
        'left':   (47, 36, 4, 12),
        'back':   (51, 36, 3, 12),
        'top':    (44, 32, 3, 4),
        'bottom': (47, 32, 3, 4),
    },
    'left_arm': {
        'right':  (32, 52, 4, 12),
        'front':  (36, 52, 3, 12),
        'left':   (39, 52, 4, 12),
        'back':   (43, 52, 3, 12),
        'top':    (36, 48, 3, 4),
        'bottom': (39, 48, 3, 4),
    },
    'left_arm_overlay': {
        'right':  (48, 52, 4, 12),
        'front':  (52, 52, 3, 12),
        'left':   (55, 52, 4, 12),
        'back':   (59, 52, 3, 12),
        'top':    (52, 48, 3, 4),
        'bottom': (55, 48, 3, 4),
    },
}

BODY_PART_DIMENSIONS_CLASSIC = {
    'head': (8, 8, 8),
    'body': (8, 12, 4),
    'right_arm': (4, 12, 4),
    'left_arm': (4, 12, 4),
    'right_leg': (4, 12, 4),
    'left_leg': (4, 12, 4),
}

BODY_PART_DIMENSIONS_SLIM = {
    'head': (8, 8, 8),
    'body': (8, 12, 4),
    'right_arm': (3, 12, 4),
    'left_arm': (3, 12, 4),
    'right_leg': (4, 12, 4),
    'left_leg': (4, 12, 4),
}

OVERLAY_DIMENSIONS_CLASSIC = {
    'head': (10, 10, 10),
    'body': (10, 14, 6),
    'right_arm': (6, 14, 6),
    'left_arm': (6, 14, 6),
    'right_leg': (6, 14, 6),
    'left_leg': (6, 14, 6),
}

OVERLAY_DIMENSIONS_SLIM = {
    'head': (10, 10, 10),
    'body': (10, 14, 6),
    'right_arm': (5, 14, 6),
    'left_arm': (5, 14, 6),
    'right_leg': (6, 14, 6),
    'left_leg': (6, 14, 6),
}


def load_skin(path: str) -> Image.Image:
    """Load a Minecraft skin PNG file."""
    img = Image.open(path)
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if img.size not in [(64, 64), (64, 32)]:
        raise ValueError(f"Invalid skin dimensions: {img.size}. Expected 64x64 or 64x32.")
    
    return img


def is_old_format(skin: Image.Image) -> bool:
    """Check if this is a 64x32 (old format) skin."""
    return skin.size == (64, 32)


def detect_slim_skin(skin: Image.Image) -> bool:
    """Detect if a skin is slim (Alex model)."""
    if is_old_format(skin):
        return False  # Old format skins are always classic
    
    pixels = np.array(skin)
    
    test_positions = [
        (50, 20), (50, 25), (50, 30),
        (54, 20), (54, 25), (54, 30),
    ]
    
    transparent_count = 0
    for x, y in test_positions:
        if y < pixels.shape[0] and x < pixels.shape[1]:
            alpha = pixels[y, x, 3]
            if alpha < 128:
                transparent_count += 1
    
    return transparent_count >= 4


def extract_face(skin: Image.Image, coords: Tuple[int, int, int, int]) -> np.ndarray:
    """Extract a face texture from the skin image."""
    x, y, w, h = coords
    region = skin.crop((x, y, x + w, y + h))
    return np.array(region)


def mirror_texture(texture: np.ndarray) -> np.ndarray:
    """Mirror a texture horizontally."""
    return np.fliplr(texture)


def has_visible_pixels(texture: np.ndarray, threshold: int = 10) -> bool:
    """Check if a texture has any visible (non-transparent) pixels."""
    if texture.shape[2] < 4:
        return True
    alpha = texture[:, :, 3]
    return np.sum(alpha > 128) >= threshold


def extract_body_part(skin: Image.Image, part_name: str, is_slim: bool = False) -> BodyPartTextures:
    """Extract all face textures for a body part."""
    layout = SKIN_LAYOUT_SLIM if is_slim else SKIN_LAYOUT_CLASSIC
    old_format = is_old_format(skin)
    
    # For 64x32 skins, mirror left arm/leg from right
    if old_format and part_name == 'left_arm':
        # Get right arm and mirror it
        right_arm = extract_body_part(skin, 'right_arm', is_slim)
        return BodyPartTextures(
            front=mirror_texture(right_arm.front),
            back=mirror_texture(right_arm.back),
            left=mirror_texture(right_arm.right),   # Swap left/right
            right=mirror_texture(right_arm.left),   # Swap left/right
            top=mirror_texture(right_arm.top),
            bottom=mirror_texture(right_arm.bottom),
        )
    
    if old_format and part_name == 'left_leg':
        # Get right leg and mirror it
        right_leg = extract_body_part(skin, 'right_leg', is_slim)
        return BodyPartTextures(
            front=mirror_texture(right_leg.front),
            back=mirror_texture(right_leg.back),
            left=mirror_texture(right_leg.right),   # Swap left/right
            right=mirror_texture(right_leg.left),   # Swap left/right
            top=mirror_texture(right_leg.top),
            bottom=mirror_texture(right_leg.bottom),
        )
    
    if part_name not in layout:
        raise ValueError(f"Unknown body part: {part_name}")
    
    part_layout = layout[part_name]
    faces = {}
    
    for face_name, coords in part_layout.items():
        face_texture = extract_face(skin, coords)
        faces[face_name] = face_texture
    
    return BodyPartTextures(**faces)


def extract_overlay(skin: Image.Image, part_name: str, is_slim: bool = False) -> Optional[BodyPartTextures]:
    """Extract overlay textures for a body part."""
    old_format = is_old_format(skin)
    
    # 64x32 skins don't have overlays except for head
    if old_format and part_name != 'head':
        return None
    
    layout = SKIN_LAYOUT_SLIM if is_slim else SKIN_LAYOUT_CLASSIC
    overlay_name = f"{part_name}_overlay"
    
    if overlay_name not in layout:
        return None
    
    overlay_layout = layout[overlay_name]
    faces = {}
    has_any_content = False
    
    for face_name, coords in overlay_layout.items():
        # Check if coords are within skin bounds
        x, y, w, h = coords
        if y + h > skin.size[1]:
            # Out of bounds for this skin
            faces[face_name] = np.zeros((h, w, 4), dtype=np.uint8)
        else:
            face_texture = extract_face(skin, coords)
            faces[face_name] = face_texture
            if has_visible_pixels(face_texture):
                has_any_content = True
    
    if not has_any_content:
        return None
    
    return BodyPartTextures(**faces)


def get_all_parts(skin: Image.Image, is_slim: bool = None) -> Dict[str, BodyPartTextures]:
    """Extract all body part textures from the skin."""
    if is_slim is None:
        is_slim = detect_slim_skin(skin)
        print(f"   Detected skin type: {'Slim (Alex)' if is_slim else 'Classic (Steve)'}")
    
    parts = {}
    base_parts = ['head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg']
    
    for part_name in base_parts:
        parts[part_name] = extract_body_part(skin, part_name, is_slim)
    
    return parts


def get_all_overlays(skin: Image.Image, is_slim: bool = None) -> Dict[str, BodyPartTextures]:
    """Extract all overlay textures from the skin."""
    if is_slim is None:
        is_slim = detect_slim_skin(skin)
    
    overlays = {}
    base_parts = ['head', 'body', 'right_arm', 'left_arm', 'right_leg', 'left_leg']
    
    for part_name in base_parts:
        overlay = extract_overlay(skin, part_name, is_slim)
        if overlay is not None:
            overlays[part_name] = overlay
    
    return overlays


def get_part_dimensions(part_name: str, is_slim: bool = False) -> Tuple[int, int, int]:
    """Get the dimensions (width, height, depth) of a body part."""
    dims = BODY_PART_DIMENSIONS_SLIM if is_slim else BODY_PART_DIMENSIONS_CLASSIC
    return dims.get(part_name, (4, 4, 4))


def get_overlay_dimensions(part_name: str, is_slim: bool = False) -> Tuple[int, int, int]:
    """Get the dimensions for an overlay."""
    dims = OVERLAY_DIMENSIONS_SLIM if is_slim else OVERLAY_DIMENSIONS_CLASSIC
    return dims.get(part_name, (6, 6, 6))
