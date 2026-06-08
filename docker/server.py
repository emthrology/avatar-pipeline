"""
VRM → GLB 변환 API 서버.
POST /convert  multipart/form-data, field: file (.vrm)
               → GLB binary 반환
"""
import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BLENDER = '/opt/blender/blender'
SCRIPT  = '/app/vroid_to_glb.py'
MAX_MB  = 20


@app.route('/health')
def health():
    return jsonify(status='ok')


@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify(error='field "file" required'), 400

    vrm_file = request.files['file']
    if not vrm_file.filename.lower().endswith('.vrm'):
        return jsonify(error='only .vrm files accepted'), 400

    # 크기 검사 (스트림 길이)
    vrm_file.stream.seek(0, 2)
    size_mb = vrm_file.stream.tell() / 1024 / 1024
    vrm_file.stream.seek(0)
    if size_mb > MAX_MB:
        return jsonify(error=f'file too large ({size_mb:.1f}MB > {MAX_MB}MB)'), 413

    with tempfile.TemporaryDirectory() as tmpdir:
        vrm_path = os.path.join(tmpdir, 'input.vrm')
        glb_path = os.path.join(tmpdir, 'output.glb')
        vrm_file.save(vrm_path)

        result = subprocess.run(
            [BLENDER, '--background', '--python', SCRIPT, '--', vrm_path, glb_path],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0 or not os.path.exists(glb_path):
            return jsonify(
                error='conversion failed',
                detail=result.stderr[-2000:]  # 마지막 2000자만
            ), 500

        return send_file(
            glb_path,
            mimetype='model/gltf-binary',
            as_attachment=True,
            download_name='avatar.glb'
        )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
