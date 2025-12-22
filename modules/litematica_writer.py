"""
Litematica Writer Module

Generates .litematic schematic files using the litemapy library.
This library properly handles all the complex NBT formatting and bit-packing.
"""

import time
from typing import Dict, Tuple
from litemapy import Schematic, Region, BlockState
from .model_builder import VoxelModel


def write_litematica(
    model: VoxelModel,
    output_path: str,
    name: str = "Player Sculpture",
    author: str = "Skin to Litematica Converter",
    description: str = "Converted from player skin"
) -> Dict:
    """
    Write a VoxelModel to a Litematica .litematic file.
    
    Uses the litemapy library for proper NBT formatting.
    """
    dims = model.get_dimensions()
    width, height, depth = dims
    
    if width == 0 or height == 0 or depth == 0:
        raise ValueError("Model has zero dimensions")
    
    # Create a new schematic with the model dimensions
    # Region coordinates in litemapy are (x, y, z) with dimensions (width, height, depth)
    reg = Region(0, 0, 0, width, height, depth)
    
    # Cache for block states to avoid creating duplicates
    block_state_cache: Dict[str, BlockState] = {}
    
    # Set all blocks in the region
    for (x, y, z), block_id in model.blocks.items():
        if block_id:
            # Get or create block state
            if block_id not in block_state_cache:
                block_state_cache[block_id] = BlockState(block_id)
            
            # Set the block in the region
            reg.setblock(x, y, z, block_state_cache[block_id])
    
    # Create schematic with the region
    schem = Schematic(
        name=name,
        author=author,
        description=description,
        regions={"Main": reg}
    )
    
    # Save to file
    schem.save(output_path)
    
    return {
        'dimensions': dims,
        'total_blocks': model.get_block_count(),
        'palette_size': len(block_state_cache) + 1,  # +1 for air
        'file_path': output_path
    }
