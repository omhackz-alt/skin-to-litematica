"""
Minecraft Skin Fetcher Module

Fetches player skins by username from the Mojang API.
"""

import urllib.request
import urllib.error
import json
import base64
import os
import tempfile
from typing import Optional, Tuple
from PIL import Image
import io


def get_uuid_from_username(username: str) -> Optional[str]:
    """
    Get the UUID for a Minecraft username from Mojang API.
    
    Args:
        username: Minecraft username
        
    Returns:
        UUID string or None if not found
    """
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SkinToLitematica/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('id')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception as e:
        print(f"Error fetching UUID: {e}")
        return None


def get_skin_url_from_uuid(uuid: str) -> Optional[Tuple[str, bool]]:
    """
    Get the skin URL and model type for a UUID from Mojang API.
    
    Args:
        uuid: Player UUID (without dashes)
        
    Returns:
        Tuple of (skin_url, is_slim) or None if not found
    """
    url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SkinToLitematica/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            properties = data.get('properties', [])
            for prop in properties:
                if prop.get('name') == 'textures':
                    # Decode base64 texture data
                    texture_data = base64.b64decode(prop['value'])
                    texture_json = json.loads(texture_data.decode('utf-8'))
                    
                    textures = texture_json.get('textures', {})
                    skin_info = textures.get('SKIN', {})
                    
                    skin_url = skin_info.get('url')
                    metadata = skin_info.get('metadata', {})
                    is_slim = metadata.get('model') == 'slim'
                    
                    return (skin_url, is_slim)
            
            return None
    except Exception as e:
        print(f"Error fetching skin URL: {e}")
        return None


def download_skin(skin_url: str, save_path: Optional[str] = None) -> Optional[str]:
    """
    Download a skin image from URL.
    
    Args:
        skin_url: URL to the skin image
        save_path: Path to save the image (optional, uses temp file if not provided)
        
    Returns:
        Path to the downloaded skin file or None if failed
    """
    try:
        req = urllib.request.Request(skin_url, headers={'User-Agent': 'SkinToLitematica/1.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            image_data = response.read()
            
            # Verify it's a valid image
            img = Image.open(io.BytesIO(image_data))
            
            if save_path is None:
                # Create temp file
                fd, save_path = tempfile.mkstemp(suffix='.png')
                os.close(fd)
            
            img.save(save_path, 'PNG')
            return save_path
            
    except Exception as e:
        print(f"Error downloading skin: {e}")
        return None


def fetch_skin_by_username(username: str, save_path: Optional[str] = None) -> Optional[Tuple[str, bool]]:
    """
    Fetch a player's skin by their Minecraft username.
    
    Args:
        username: Minecraft username
        save_path: Path to save the skin (optional)
        
    Returns:
        Tuple of (skin_file_path, is_slim) or None if failed
    """
    print(f"Looking up player: {username}")
    
    # Get UUID
    uuid = get_uuid_from_username(username)
    if not uuid:
        print(f"Player not found: {username}")
        return None
    
    print(f"Found UUID: {uuid}")
    
    # Get skin URL
    skin_info = get_skin_url_from_uuid(uuid)
    if not skin_info:
        print("Could not get skin URL")
        return None
    
    skin_url, is_slim = skin_info
    print(f"Skin URL: {skin_url}")
    print(f"Model: {'Slim (Alex)' if is_slim else 'Classic (Steve)'}")
    
    # Download skin
    skin_path = download_skin(skin_url, save_path)
    if not skin_path:
        print("Failed to download skin")
        return None
    
    print(f"Skin saved to: {skin_path}")
    return (skin_path, is_slim)
