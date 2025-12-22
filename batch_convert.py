#!/usr/bin/env python3
"""
Batch Player Converter

Converts multiple Minecraft players to a single Litematica file
with all sculptures arranged in a row.

Usage:
    1. Edit the PLAYERS list below with your usernames
    2. Run: python batch_convert.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.skin_parser import load_skin, get_all_parts, get_all_overlays, detect_slim_skin
from modules.model_builder import assemble_player_model, VoxelModel
from modules.litematica_writer import write_litematica
from modules.skin_fetcher import fetch_skin_by_username


# ============================================================
# EDIT THIS LIST WITH YOUR PLAYER USERNAMES
# ============================================================
PLAYERS = [
    "Notch",
    "jeb_",
    # Add more usernames here...
]

# Output file path
OUTPUT_FILE = "output/all_players_sculpture.litematic"

# Space between sculptures (in blocks)
SPACING = 4
# ============================================================


def convert_multiple_players(usernames: list, output_path: str, spacing: int = 5):
    """Convert multiple players to a single Litematica file."""
    combined_model = VoxelModel()
    current_x = 0
    successful = 0
    failed = []
    
    # Remove duplicates while preserving order
    seen = set()
    unique_usernames = []
    for u in usernames:
        if u.lower() not in seen:
            seen.add(u.lower())
            unique_usernames.append(u)
    
    for i, username in enumerate(unique_usernames):
        username = username.strip()
        if not username:
            continue
            
        print(f"\n[{i+1}/{len(unique_usernames)}] Processing: {username}")
        
        try:
            result = fetch_skin_by_username(username)
            if not result:
                print(f"   ❌ Player not found: {username}")
                failed.append(username)
                continue
            
            skin_path, is_slim = result
            skin = load_skin(skin_path)
            parts = get_all_parts(skin, is_slim)
            overlays = get_all_overlays(skin, is_slim)
            model = assemble_player_model(parts, overlays, is_slim)
            dims = model.get_dimensions()
            
            for (x, y, z), block_id in model.blocks.items():
                combined_model.set_block(current_x + x, y, z, block_id)
            
            print(f"   ✅ Added at X={current_x} ({dims[0]}x{dims[1]}x{dims[2]}, {len(model.blocks)} blocks)")
            
            current_x += dims[0] + spacing
            successful += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed.append(username)
            continue
    
    if successful == 0:
        print("\n❌ No players were converted successfully!")
        return None
    
    combined_model.normalize_positions()
    
    print(f"\n💾 Writing combined schematic to: {output_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    result = write_litematica(
        combined_model,
        output_path,
        name=f"{successful} Player Sculptures",
        description=f"Combined sculpture of {successful} players"
    )
    
    print("\n" + "=" * 50)
    print("✅ BATCH CONVERSION COMPLETE!")
    print("=" * 50)
    print(f"   📐 Total dimensions: {result['dimensions'][0]} x {result['dimensions'][1]} x {result['dimensions'][2]}")
    print(f"   🧱 Total blocks: {result['total_blocks']:,}")
    print(f"   🎨 Unique block types: {result['palette_size']}")
    print(f"   👥 Players converted: {successful}")
    if failed:
        print(f"   ❌ Failed: {len(failed)} ({', '.join(failed[:10])}{'...' if len(failed) > 10 else ''})")
    print(f"   📁 Output file: {result['file_path']}")
    
    return result


def main():
    if not PLAYERS or PLAYERS == ["Notch", "jeb_"]:
        print("⚠️  Please edit batch_convert.py and add your player usernames to the PLAYERS list!")
        print("    Look for the PLAYERS = [...] section at the top of the file.")
        return
    
    print("🎮 Batch Skin to Litematica Converter")
    print("=" * 50)
    print(f"Converting {len(PLAYERS)} players...")
    
    output_path = str(Path(__file__).parent / OUTPUT_FILE)
    convert_multiple_players(PLAYERS, output_path, spacing=SPACING)


if __name__ == '__main__':
    main()
