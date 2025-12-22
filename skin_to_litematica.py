#!/usr/bin/env python3
"""
Minecraft Skin to Litematica Converter (CLI)

Converts a 64x64 Minecraft player skin PNG into a 3D block sculpture
that can be imported into Minecraft Java Edition via Litematica.

Usage:
    python skin_to_litematica.py player.png
    python skin_to_litematica.py --username Notch
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.skin_parser import load_skin, get_all_parts, get_all_overlays, detect_slim_skin
from modules.model_builder import assemble_player_model
from modules.litematica_writer import write_litematica
from modules.skin_fetcher import fetch_skin_by_username


def main():
    parser = argparse.ArgumentParser(
        description='Convert Minecraft player skin to Litematica schematic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python skin_to_litematica.py player.png
    python skin_to_litematica.py --username Notch
    python skin_to_litematica.py player.png -o output/my_sculpture.litematic
        """
    )
    
    parser.add_argument(
        'skin_path',
        nargs='?',
        help='Path to the Minecraft skin PNG file (64x64)'
    )
    
    parser.add_argument(
        '-u', '--username',
        help='Minecraft username to fetch skin from'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output path for the .litematic file',
        default=None
    )
    
    parser.add_argument(
        '--name',
        help='Name of the schematic',
        default='Player Sculpture'
    )
    
    parser.add_argument(
        '--slim',
        action='store_true',
        help='Force slim (Alex) model'
    )
    
    parser.add_argument(
        '--classic',
        action='store_true',
        help='Force classic (Steve) model'
    )
    
    args = parser.parse_args()
    
    # Determine skin source
    skin_path = None
    is_slim = None
    
    if args.username:
        # Fetch from username
        print(f"🔍 Fetching skin for username: {args.username}")
        result = fetch_skin_by_username(args.username)
        if result:
            skin_path, is_slim = result
        else:
            print(f"❌ Could not find player: {args.username}")
            sys.exit(1)
    elif args.skin_path:
        skin_path = args.skin_path
    else:
        parser.print_help()
        print("\n❌ Please provide a skin file or username")
        sys.exit(1)
    
    # Override model type if specified
    if args.slim:
        is_slim = True
    elif args.classic:
        is_slim = False
    
    # Validate input file
    skin_file = Path(skin_path)
    if not skin_file.exists():
        print(f"❌ Skin file not found: {skin_path}")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = skin_file.parent / 'output'
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{skin_file.stem}_sculpture.litematic"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🎨 Loading skin: {skin_path}")
    
    try:
        # Load skin
        skin = load_skin(str(skin_path))
        print(f"   Skin size: {skin.size[0]}x{skin.size[1]}")
        
        # Detect model type if not specified
        if is_slim is None:
            is_slim = detect_slim_skin(skin)
        
        model_type = "Slim (Alex)" if is_slim else "Classic (Steve)"
        print(f"   Model type: {model_type}")
        
        # Extract body parts and overlays
        print("📦 Extracting body parts...")
        parts = get_all_parts(skin, is_slim)
        overlays = get_all_overlays(skin, is_slim)
        
        print(f"   Found {len(parts)} body parts")
        print(f"   Found {len(overlays)} overlay layers")
        
        # Build 3D model
        print("🔨 Building 3D model...")
        model = assemble_player_model(parts, overlays, is_slim)
        dims = model.get_dimensions()
        print(f"   Model dimensions: {dims[0]}x{dims[1]}x{dims[2]} blocks")
        print(f"   Total blocks: {model.get_block_count()}")
        
        # Write Litematica file
        print(f"💾 Writing Litematica file: {output_path}")
        result = write_litematica(
            model,
            str(output_path),
            name=args.name
        )
        
        print("\n✅ Conversion complete!")
        print(f"   📐 Dimensions: {result['dimensions'][0]} x {result['dimensions'][1]} x {result['dimensions'][2]}")
        print(f"   🧱 Total blocks: {result['total_blocks']}")
        print(f"   🎨 Unique block types: {result['palette_size']}")
        print(f"   📁 Output file: {result['file_path']}")
        print("\n💡 To use in Minecraft:")
        print("   1. Install Litematica mod")
        print("   2. Copy the .litematic file to .minecraft/schematics/")
        print("   3. In-game: Press M → Load Schematics → Select your file")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
