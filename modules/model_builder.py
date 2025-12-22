"""
3D Model Builder Module

Constructs a 3D voxel model by mapping 2D skin textures onto body parts.
Supports slim skins and renders overlays as separate outer layers.

IMPORTANT: Front face is rendered LAST so its blocks take priority at corners.
"""

from typing import Dict, Tuple, Optional, List
import numpy as np
from .skin_parser import (
    BodyPartTextures, 
    get_part_dimensions, 
    get_overlay_dimensions,
    BODY_PART_DIMENSIONS_CLASSIC,
    BODY_PART_DIMENSIONS_SLIM
)
from .color_mapper import get_block_for_pixel


class VoxelModel:
    """A 3D voxel model represented as a sparse dictionary of block positions."""
    
    def __init__(self):
        self.blocks: Dict[Tuple[int, int, int], str] = {}
        self.min_pos = [float('inf'), float('inf'), float('inf')]
        self.max_pos = [float('-inf'), float('-inf'), float('-inf')]
    
    def set_block(self, x: int, y: int, z: int, block_id: str):
        """Set a block at the given position."""
        if block_id is None:
            return
        
        self.blocks[(x, y, z)] = block_id
        
        self.min_pos[0] = min(self.min_pos[0], x)
        self.min_pos[1] = min(self.min_pos[1], y)
        self.min_pos[2] = min(self.min_pos[2], z)
        self.max_pos[0] = max(self.max_pos[0], x)
        self.max_pos[1] = max(self.max_pos[1], y)
        self.max_pos[2] = max(self.max_pos[2], z)
    
    def get_block(self, x: int, y: int, z: int) -> Optional[str]:
        """Get the block at the given position."""
        return self.blocks.get((x, y, z))
    
    def has_block(self, x: int, y: int, z: int) -> bool:
        """Check if there is a block at the given position."""
        return (x, y, z) in self.blocks
    
    def get_dimensions(self) -> Tuple[int, int, int]:
        """Get the dimensions of the model's bounding box."""
        if not self.blocks:
            return (0, 0, 0)
        
        return (
            int(self.max_pos[0] - self.min_pos[0] + 1),
            int(self.max_pos[1] - self.min_pos[1] + 1),
            int(self.max_pos[2] - self.min_pos[2] + 1)
        )
    
    def normalize_positions(self):
        """Shift all blocks so the minimum position is at origin."""
        if not self.blocks:
            return
        
        offset_x = int(self.min_pos[0])
        offset_y = int(self.min_pos[1])
        offset_z = int(self.min_pos[2])
        
        new_blocks = {}
        for (x, y, z), block_id in self.blocks.items():
            new_blocks[(x - offset_x, y - offset_y, z - offset_z)] = block_id
        
        self.blocks = new_blocks
        
        dims = (
            self.max_pos[0] - self.min_pos[0],
            self.max_pos[1] - self.min_pos[1],
            self.max_pos[2] - self.min_pos[2]
        )
        self.min_pos = [0, 0, 0]
        self.max_pos = [dims[0], dims[1], dims[2]]
    
    def get_block_count(self) -> int:
        """Get the total number of blocks in the model."""
        return len(self.blocks)
    
    def get_unique_blocks(self) -> List[str]:
        """Get a list of unique block types in the model."""
        return list(set(self.blocks.values()))


def get_pixel_block(texture: np.ndarray, tx: int, ty: int) -> Optional[str]:
    """Get the block for a texture pixel, handling bounds."""
    if texture is None:
        return None
    if tx < 0 or ty < 0 or tx >= texture.shape[1] or ty >= texture.shape[0]:
        return None
    pixel = tuple(texture[ty, tx])
    return get_block_for_pixel(pixel)


def create_body_part_surface(
    textures: BodyPartTextures,
    dimensions: Tuple[int, int, int],
    position: Tuple[int, int, int],
    model: VoxelModel
):
    """
    Create only the surface blocks of a body part (1 block thick shell).
    
    FRONT FACE IS RENDERED LAST so its blocks take priority at corners.
    """
    width, height, depth = dimensions
    pos_x, pos_y, pos_z = position
    
    # BACK face - rendered first (lowest priority)
    for y in range(height):
        for x in range(width):
            block = get_pixel_block(textures.back, width - 1 - x, y)
            if block:
                wy = pos_y + (height - 1 - y)
                model.set_block(pos_x + x, wy, pos_z + depth - 1, block)
    
    # BOTTOM face
    for z in range(depth):
        for x in range(width):
            block = get_pixel_block(textures.bottom, x, z)
            if block:
                model.set_block(pos_x + x, pos_y, pos_z + z, block)
    
    # TOP face
    for z in range(depth):
        for x in range(width):
            block = get_pixel_block(textures.top, x, depth - 1 - z)
            if block:
                model.set_block(pos_x + x, pos_y + height - 1, pos_z + z, block)
    
    # LEFT face
    for y in range(height):
        for z in range(depth):
            block = get_pixel_block(textures.left, depth - 1 - z, y)
            if block:
                wy = pos_y + (height - 1 - y)
                model.set_block(pos_x, wy, pos_z + z, block)
    
    # RIGHT face
    for y in range(height):
        for z in range(depth):
            block = get_pixel_block(textures.right, z, y)
            if block:
                wy = pos_y + (height - 1 - y)
                model.set_block(pos_x + width - 1, wy, pos_z + z, block)
    
    # FRONT face - rendered LAST (highest priority, overwrites corners)
    for y in range(height):
        for x in range(width):
            block = get_pixel_block(textures.front, x, y)
            if block:
                wy = pos_y + (height - 1 - y)
                model.set_block(pos_x + x, wy, pos_z, block)


def create_overlay_surface(
    textures: BodyPartTextures,
    base_dimensions: Tuple[int, int, int],
    position: Tuple[int, int, int],
    model: VoxelModel
):
    """
    Create overlay layer 1 block outside the base part.
    FRONT FACE IS RENDERED LAST so its blocks take priority at corners.
    """
    width, height, depth = base_dimensions
    pos_x, pos_y, pos_z = position
    
    # Overlay is 1 block expanded on each side
    overlay_pos_x = pos_x - 1
    overlay_pos_y = pos_y - 1
    overlay_pos_z = pos_z - 1
    overlay_depth = depth + 2
    overlay_width = width + 2
    overlay_height = height + 2
    
    # BACK face - rendered first (lowest priority)
    for y in range(height):
        for x in range(width):
            block = get_pixel_block(textures.back, width - 1 - x, y)
            if block:
                wy = overlay_pos_y + 1 + (height - 1 - y)
                model.set_block(overlay_pos_x + 1 + x, wy, overlay_pos_z + overlay_depth - 1, block)
    
    # BOTTOM face
    for z in range(depth):
        for x in range(width):
            block = get_pixel_block(textures.bottom, x, z)
            if block:
                model.set_block(overlay_pos_x + 1 + x, overlay_pos_y, overlay_pos_z + 1 + z, block)
    
    # TOP face
    for z in range(depth):
        for x in range(width):
            block = get_pixel_block(textures.top, x, depth - 1 - z)
            if block:
                model.set_block(overlay_pos_x + 1 + x, overlay_pos_y + overlay_height - 1, overlay_pos_z + 1 + z, block)
    
    # LEFT face
    for y in range(height):
        for z in range(depth):
            block = get_pixel_block(textures.left, depth - 1 - z, y)
            if block:
                wy = overlay_pos_y + 1 + (height - 1 - y)
                model.set_block(overlay_pos_x, wy, overlay_pos_z + 1 + z, block)
    
    # RIGHT face
    for y in range(height):
        for z in range(depth):
            block = get_pixel_block(textures.right, z, y)
            if block:
                wy = overlay_pos_y + 1 + (height - 1 - y)
                model.set_block(overlay_pos_x + overlay_width - 1, wy, overlay_pos_z + 1 + z, block)
    
    # FRONT face - rendered LAST (highest priority, overwrites corners)
    for y in range(height):
        for x in range(width):
            block = get_pixel_block(textures.front, x, y)
            if block:
                wy = overlay_pos_y + 1 + (height - 1 - y)
                model.set_block(overlay_pos_x + 1 + x, wy, overlay_pos_z, block)


def assemble_player_model(
    parts: Dict[str, BodyPartTextures],
    overlays: Dict[str, BodyPartTextures] = None,
    is_slim: bool = False
) -> VoxelModel:
    """
    Assemble all body parts into a complete player model.
    """
    model = VoxelModel()
    
    dims = BODY_PART_DIMENSIONS_SLIM if is_slim else BODY_PART_DIMENSIONS_CLASSIC
    
    arm_width = 3 if is_slim else 4
    
    part_positions = {
        'head': (-4, 24, 0),
        'body': (-4, 12, 2),
        'right_arm': (-4 - arm_width, 12, 2),
        'left_arm': (4, 12, 2),
        'right_leg': (-4, 0, 2),
        'left_leg': (0, 0, 2),
    }
    
    # Build base body parts
    for part_name, textures in parts.items():
        if part_name not in dims:
            continue
        
        dimensions = dims[part_name]
        position = part_positions.get(part_name, (0, 0, 0))
        
        create_body_part_surface(textures, dimensions, position, model)
    
    # Build overlays as outer layer
    if overlays:
        for part_name, overlay_textures in overlays.items():
            if part_name not in dims:
                continue
            
            base_dims = dims[part_name]
            position = part_positions.get(part_name, (0, 0, 0))
            
            create_overlay_surface(overlay_textures, base_dims, position, model)
    
    model.normalize_positions()
    
    return model
