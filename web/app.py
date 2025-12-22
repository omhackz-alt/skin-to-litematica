"""
Skin to Litematica Web Application

Flask backend for converting Minecraft skins to Litematica schematics.
"""

import os
import sys
import uuid
import json
import tempfile
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add parent directory to path for modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.skin_parser import load_skin, get_all_parts, get_all_overlays
from modules.model_builder import assemble_player_model
from modules.litematica_writer import write_litematica
from modules.skin_fetcher import fetch_skin_by_username
from modules.color_mapper import get_block_color

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'static' / 'uploads'
app.config['OUTPUT_FOLDER'] = Path(__file__).parent / 'static' / 'output'

# Ensure folders exist
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(parents=True, exist_ok=True)

# Store conversion results temporarily
conversion_cache = {}


def cleanup_old_files():
    """Remove files older than 1 hour."""
    import time
    now = time.time()
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        for f in folder.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > 3600:
                f.unlink()


@app.route('/')
def index():
    """Serve main page."""
    return render_template('index.html')


@app.route('/api/convert/username', methods=['POST'])
def convert_by_username():
    """Convert skins by username(s)."""
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        
        if not usernames:
            return jsonify({'success': False, 'error': 'No usernames provided'})
        
        # Limit to 20 usernames at once
        usernames = usernames[:20]
        
        results = []
        for username in usernames:
            username = username.strip()
            if not username:
                continue
            
            try:
                result = process_username(username)
                if result:
                    results.append(result)
                else:
                    results.append({
                        'username': username,
                        'success': False,
                        'error': 'Player not found'
                    })
            except Exception as e:
                results.append({
                    'username': username,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({'success': True, 'results': results})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/convert/upload', methods=['POST'])
def convert_by_upload():
    """Convert uploaded skin file."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.lower().endswith('.png'):
            return jsonify({'success': False, 'error': 'Only PNG files allowed'})
        
        # Save uploaded file
        file_id = str(uuid.uuid4())[:8]
        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / f"{file_id}_{filename}"
        file.save(str(filepath))
        
        # Process the skin
        result = process_skin_file(str(filepath), filename.replace('.png', ''))
        
        if result:
            return jsonify({'success': True, 'results': [result]})
        else:
            return jsonify({'success': False, 'error': 'Failed to process skin'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/preview/<result_id>')
def get_preview(result_id):
    """Get 3D preview data for a conversion result."""
    if result_id not in conversion_cache:
        return jsonify({'success': False, 'error': 'Result not found'})
    
    cached = conversion_cache[result_id]
    return jsonify({
        'success': True,
        'blocks': cached['blocks'],
        'dimensions': cached['dimensions']
    })


@app.route('/api/download/<result_id>')
def download_file(result_id):
    """Download a converted schematic file."""
    if result_id not in conversion_cache:
        return jsonify({'success': False, 'error': 'Result not found'}), 404
    
    cached = conversion_cache[result_id]
    filepath = cached['filepath']
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"{cached['name']}_sculpture.litematic"
    )


@app.route('/api/download/batch', methods=['POST'])
def download_batch():
    """Download multiple schematics as a ZIP file."""
    try:
        data = request.get_json()
        result_ids = data.get('ids', [])
        
        if not result_ids:
            return jsonify({'success': False, 'error': 'No files to download'})
        
        # Create ZIP file
        zip_path = app.config['OUTPUT_FOLDER'] / f"batch_{uuid.uuid4().hex[:8]}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for result_id in result_ids:
                if result_id in conversion_cache:
                    cached = conversion_cache[result_id]
                    if os.path.exists(cached['filepath']):
                        zipf.write(
                            cached['filepath'],
                            f"{cached['name']}_sculpture.litematic"
                        )
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name='sculptures.zip'
        )
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def process_username(username: str) -> dict:
    """Process a single username and return result."""
    result = fetch_skin_by_username(username)
    if not result:
        return None
    
    skin_path, is_slim = result
    return process_skin_file(skin_path, username, is_slim)


def process_skin_file(filepath: str, name: str, is_slim: bool = None) -> dict:
    """Process a skin file and return result with preview data."""
    skin = load_skin(filepath)
    
    if is_slim is None:
        from modules.skin_parser import detect_slim_skin
        is_slim = detect_slim_skin(skin)
    
    parts = get_all_parts(skin, is_slim)
    overlays = get_all_overlays(skin, is_slim)
    model = assemble_player_model(parts, overlays, is_slim)
    
    # Generate unique ID
    result_id = str(uuid.uuid4())[:8]
    
    # Save litematic file
    output_path = app.config['OUTPUT_FOLDER'] / f"{result_id}.litematic"
    write_result = write_litematica(model, str(output_path), name=f"{name}'s Sculpture")
    
    # Generate preview data (blocks with colors)
    blocks_preview = []
    for (x, y, z), block_id in model.blocks.items():
        color = get_block_color(block_id)
        hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
        blocks_preview.append({
            'x': x, 'y': y, 'z': z,
            'color': hex_color
        })
    
    # Cache the result
    conversion_cache[result_id] = {
        'name': name,
        'filepath': str(output_path),
        'blocks': blocks_preview,
        'dimensions': list(write_result['dimensions'])
    }
    
    return {
        'id': result_id,
        'name': name,
        'success': True,
        'dimensions': write_result['dimensions'],
        'total_blocks': write_result['total_blocks'],
        'preview_url': f'/api/preview/{result_id}',
        'download_url': f'/api/download/{result_id}'
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
