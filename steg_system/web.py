import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from base64 import b64encode

from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from .crypto import decrypt, encrypt
from .decoder import decode_image
from .detect import detect_steganography
from .encoder import encode_image
from .utils import HEADER_BITS, capacity_bytes

MAX_UPLOAD_SIZE = 10 * 1024 * 1024

app = FastAPI(title="Steg-System Web", description="Esteganografia LSB em imagens")


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html lang="pt-BR">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Steg-System</title>
        <style>
          :root {
            --bg: #0f0f14;
            --bg-card: #1a1a24;
            --bg-input: #252532;
            --border: #2d2d3a;
            --text: #e4e4eb;
            --text-muted: #9898a8;
            --accent: #6366f1;
            --accent-hover: #818cf8;
          }
          * { box-sizing: border-box; }
          body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 2rem;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
          }
          .container {
            max-width: 520px;
            margin: 0 auto;
          }
          h1 {
            font-size: 1.75rem;
            font-weight: 600;
            margin: 0 0 2rem 0;
            text-align: center;
          }
          section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
          }
          h2 {
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0 0 1.25rem 0;
            color: var(--text);
          }
          .form-row {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.5rem;
            margin-bottom: 1rem;
          }
          .form-row:last-of-type { margin-bottom: 0; }
          label {
            font-size: 0.9rem;
            color: var(--text-muted);
            display: block;
          }
          input[type="file"],
          input[type="text"],
          input[type="password"],
          input[type="number"],
          textarea {
            width: 100%;
            padding: 0.6rem 0.75rem;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 0.9rem;
          }
          input::file-selector-button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.4rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            margin-right: 0.5rem;
          }
          input::file-selector-button:hover { background: var(--accent-hover); }
          textarea {
            resize: vertical;
            min-height: 80px;
          }
          input:focus, textarea:focus {
            outline: none;
            border-color: var(--accent);
          }
          .checkbox-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 1rem 0;
          }
          .checkbox-row input[type="checkbox"] {
            width: auto;
            accent-color: var(--accent);
          }
          .checkbox-row label {
            margin: 0;
            cursor: pointer;
          }
          .number-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
          }
          button {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            margin-top: 0.5rem;
          }
          button:hover { background: var(--accent-hover); }
          .decode-result {
            margin-top: 1rem;
            padding: 1rem;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            white-space: pre-wrap;
            word-break: break-word;
            display: none;
          }
          .decode-result.visible { display: block; }
          .decode-result.error { border-color: #dc2626; color: #f87171; }
          .decode-result .label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }
          .decode-result .download-link { color: var(--accent); margin-top: 0.5rem; display: inline-block; }
          .capacity-info { font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem; }
          .capacity-info.warn { color: #fbbf24; }
          .capacity-info.error { color: #f87171; }
          .preview-wrapper { margin-top: 0.5rem; display: none; }
          .preview-wrapper.visible { display: flex; align-items: flex-start; gap: 0.5rem; flex-wrap: wrap; }
          .preview-box { border-radius: 8px; overflow: hidden; max-width: 200px; max-height: 150px; border: 1px solid var(--border); }
          .preview-box img { width: 100%; height: auto; display: block; }
          .clear-img-btn { padding: 0.4rem 0.75rem; background: var(--bg-input); color: var(--text-muted); border: 1px solid var(--border); border-radius: 8px; cursor: pointer; font-size: 0.85rem; }
          .clear-img-btn:hover { background: #dc2626; color: white; border-color: #dc2626; }
          .drop-zone { border: 2px dashed var(--border); border-radius: 8px; padding: 1rem; text-align: center; cursor: pointer; transition: border-color 0.2s; }
          .drop-zone:hover, .drop-zone.dragover { border-color: var(--accent); }
          .detect-result { margin-top: 1rem; padding: 1rem; background: var(--bg-input); border-radius: 8px; font-size: 0.9rem; }
          .detect-result .heuristic { font-weight: 600; margin-bottom: 0.5rem; }
          .detect-result .heuristic.stego { color: #34d399; }
          .detect-result .heuristic.clean { color: var(--text-muted); }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Steg-System Web</h1>

          <section>
            <h2>Codificar (Encode)</h2>
            <form id="encode-form" method="post" action="/encode" enctype="multipart/form-data">
              <div class="form-row">
                <label>Imagem de capa (PNG/WebP/GIF/BMP/TIFF)</label>
                <div class="drop-zone" id="encode-drop" onclick="document.getElementById('encode-cover').click()">
                  Arraste a imagem aqui ou clique para selecionar
                </div>
                <input type="file" name="cover" id="encode-cover" accept="image/*" required style="display:none" />
                <div id="encode-preview-wrap" class="preview-wrapper">
                  <div id="encode-preview" class="preview-box"></div>
                  <button type="button" class="clear-img-btn" id="encode-clear-btn">Remover imagem</button>
                </div>
                <div id="encode-capacity" class="capacity-info" style="display:none"></div>
              </div>
              <div class="form-row">
                <label>Mensagem (UTF-8)</label>
                <textarea name="message" rows="3" placeholder="Digite a mensagem secreta..."></textarea>
              </div>
              <div class="form-row">
                <label>Ou arquivo binário</label>
                <input type="file" name="payload" />
              </div>
              <div class="form-row">
                <label>Senha (opcional)</label>
                <input type="password" name="password" placeholder="Criptografar o payload" />
              </div>
              <div class="form-row number-row">
                <div>
                  <label>Canais (1=R, 3=RGB, 4=RGBA)</label>
                  <input type="number" name="channels" value="1" min="1" max="4" />
                </div>
                <div>
                  <label>Bits por canal (1 ou 2)</label>
                  <input type="number" name="bits" value="1" min="1" max="2" />
                </div>
              </div>
              <div class="checkbox-row">
                <input type="checkbox" name="compress" value="1" id="compress" checked />
                <label for="compress">Comprimir (zlib)</label>
              </div>
              <div class="form-row">
                <label>Nome do arquivo (opcional)</label>
                <input type="text" name="filename" placeholder="ex: minha_imagem_secreta" />
              </div>
              <button type="submit">Codificar e baixar imagem</button>
            </form>
          </section>

          <section>
            <h2>Decodificar (Decode)</h2>
            <form id="decode-form" method="post" enctype="multipart/form-data">
              <div class="form-row">
                <label>Imagem esteganografada (PNG/WebP/GIF/BMP/TIFF)</label>
                <div class="drop-zone" id="decode-drop" onclick="document.getElementById('decode-cover').click()">
                  Arraste a imagem aqui ou clique para selecionar
                </div>
                <input type="file" name="cover" id="decode-cover" accept="image/*" required style="display:none" />
                <div id="decode-preview-wrap" class="preview-wrapper">
                  <div id="decode-preview" class="preview-box"></div>
                  <button type="button" class="clear-img-btn" id="decode-clear-btn">Remover imagem</button>
                </div>
              </div>
              <div class="form-row">
                <label>Senha (opcional)</label>
                <input type="password" name="password" placeholder="Se usou senha na codificação" />
              </div>
              <div class="checkbox-row">
                <input type="checkbox" name="legacy" value="1" id="decode-legacy" />
                <label for="decode-legacy">Tentar decodificar imagens antigas (sem magic bytes)</label>
              </div>
              <button type="submit">Decodificar</button>
              <button type="button" id="detect-btn" style="margin-top:0.5rem; background: var(--bg-input); color: var(--text)">Detectar esteganografia</button>
            </form>
            <div id="decode-result" class="decode-result"></div>
            <div id="detect-result" class="detect-result" style="display:none"></div>
          </section>
        </div>
        <script>
          function escapeHtml(s) {
            const div = document.createElement('div');
            div.textContent = s;
            return div.innerHTML;
          }
          function base64ToBlob(b64) {
            const bin = atob(b64);
            const arr = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
            return new Blob([arr]);
          }
          function setupDropZone(dropId, inputId, previewId, wrapId, clearBtnId, capacityId, onClear) {
            const drop = document.getElementById(dropId);
            const input = document.getElementById(inputId);
            const preview = document.getElementById(previewId);
            const wrap = document.getElementById(wrapId);
            const clearBtn = document.getElementById(clearBtnId);
            const capEl = capacityId ? document.getElementById(capacityId) : null;
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
              drop.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); });
            });
            ['dragenter', 'dragover'].forEach(ev => {
              drop.addEventListener(ev, () => drop.classList.add('dragover'));
            });
            ['dragleave', 'drop'].forEach(ev => {
              drop.addEventListener(ev, () => drop.classList.remove('dragover'));
            });
            drop.addEventListener('drop', e => {
              const f = e.dataTransfer.files[0];
              if (f && f.type.startsWith('image/')) {
                if (f.size > 10 * 1024 * 1024) {
                  alert('Arquivo muito grande. Máximo: 10 MB');
                  return;
                }
                const dt = new DataTransfer();
                dt.items.add(f);
                input.files = dt.files;
                input.dispatchEvent(new Event('change'));
              }
            });
            input.addEventListener('change', () => {
              if (input.files.length && preview && wrap) {
                const f = input.files[0];
                if (f.size > 10 * 1024 * 1024) {
                  alert('Arquivo muito grande. Máximo: 10 MB');
                  input.value = '';
                  return;
                }
                const url = URL.createObjectURL(f);
                preview.innerHTML = '<img src="' + url + '" alt="Preview">';
                wrap.classList.add('visible');
              } else if (wrap) {
                wrap.classList.remove('visible');
              }
            });
            clearBtn.addEventListener('click', (e) => {
              e.preventDefault();
              if (preview.querySelector('img') && preview.querySelector('img').src) {
                URL.revokeObjectURL(preview.querySelector('img').src);
              }
              input.value = '';
              preview.innerHTML = '';
              wrap.classList.remove('visible');
              if (capEl) { capEl.style.display = 'none'; encodeCapacity = 0; }
              if (onClear) onClear();
              input.dispatchEvent(new Event('change'));
            });
          }
          setupDropZone('encode-drop', 'encode-cover', 'encode-preview', 'encode-preview-wrap', 'encode-clear-btn', 'encode-capacity', null);
          setupDropZone('decode-drop', 'decode-cover', 'decode-preview', 'decode-preview-wrap', 'decode-clear-btn', null, () => {
            document.getElementById('decode-result').style.display = 'none';
            document.getElementById('detect-result').style.display = 'none';
          });

          let encodeCapacity = 0;
          async function updateEncodeCapacity() {
            const cover = document.getElementById('encode-cover');
            const capEl = document.getElementById('encode-capacity');
            if (!cover.files.length) { capEl.style.display = 'none'; return; }
            const fd = new FormData();
            fd.append('cover', cover.files[0]);
            fd.append('channels', document.querySelector('#encode-form input[name=channels]').value);
            fd.append('bits', document.querySelector('#encode-form input[name=bits]').value);
            try {
              const res = await fetch('/capacity', { method: 'POST', body: fd });
              const d = await res.json();
              encodeCapacity = d.capacity_bytes || 0;
              capEl.innerHTML = 'Capacidade: ' + encodeCapacity + ' bytes (~' + (d.capacity_chars_est || 0) + ' caracteres com compressão)';
              capEl.className = 'capacity-info';
              capEl.style.display = 'block';
            } catch (e) {
              capEl.innerHTML = 'Não foi possível calcular a capacidade';
              capEl.className = 'capacity-info error';
              capEl.style.display = 'block';
            }
          }
          document.getElementById('encode-cover').addEventListener('change', updateEncodeCapacity);
          document.querySelectorAll('#encode-form input[name=channels], #encode-form input[name=bits]').forEach(el => {
            el.addEventListener('change', updateEncodeCapacity);
          });

          document.getElementById('encode-form').addEventListener('submit', function(e) {
            const msg = document.querySelector('#encode-form textarea[name=message]').value;
            const payload = document.querySelector('#encode-form input[name=payload]').files[0];
            const compress = document.querySelector('#encode-form input[name=compress]').checked;
            let size = 0;
            if (payload && payload.size) size = payload.size;
            else if (msg) size = new TextEncoder().encode(msg).length;
            let maxAllowed = encodeCapacity;
            if (compress && !payload && msg) maxAllowed = Math.floor(encodeCapacity * 2.5);
            if (encodeCapacity > 0 && size > maxAllowed) {
              e.preventDefault();
              alert('Mensagem muito grande! Capacidade: ' + encodeCapacity + ' bytes. Você tem: ' + size + ' bytes.');
              return false;
            }
          });

          document.getElementById('decode-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const resultEl = document.getElementById('decode-result');
            const detectEl = document.getElementById('detect-result');
            detectEl.style.display = 'none';
            resultEl.style.display = 'block';
            resultEl.className = 'decode-result visible';
            resultEl.innerHTML = 'Decodificando...';
            const formData = new FormData(form);
            try {
              const res = await fetch('/decode/json', { method: 'POST', body: formData });
              let data;
              try { data = await res.json(); } catch (_) { data = {}; }
              resultEl.classList.add('visible');
              if (!res.ok) {
                resultEl.classList.add('error');
                const msg = data.message || (Array.isArray(data.detail) ? data.detail.map(d => d.msg || d).join('; ') : data.detail) || 'Falha ao decodificar';
                resultEl.innerHTML = '<span class="label">Erro</span><br>' + escapeHtml(String(msg));
                return;
              }
              if (data.type === 'text') {
                const msg = data.content ? escapeHtml(data.content) : '<em>Nenhuma mensagem esteganográfica encontrada nesta imagem.</em>';
                resultEl.innerHTML = '<span class="label">Mensagem extraída</span><br>' + msg;
              } else {
                const blob = base64ToBlob(data.content);
                const url = URL.createObjectURL(blob);
                resultEl.innerHTML = '<span class="label">Arquivo binário extraído</span><br>' +
                  '<a class="download-link" href="' + url + '" download="' + (data.filename || 'payload.bin') + '">Baixar ' + (data.filename || 'payload.bin') + '</a>';
              }
            } catch (err) {
              resultEl.classList.add('visible', 'error');
              resultEl.innerHTML = '<span class="label">Erro</span><br>' + escapeHtml(err.message || 'Falha ao decodificar');
            }
          });

          document.getElementById('detect-btn').addEventListener('click', async () => {
            const cover = document.getElementById('decode-cover');
            const resultEl = document.getElementById('detect-result');
            const decodeResult = document.getElementById('decode-result');
            decodeResult.style.display = 'none';
            if (!cover.files.length) { alert('Selecione uma imagem primeiro'); return; }
            resultEl.innerHTML = 'Analisando...';
            resultEl.style.display = 'block';
            const fd = new FormData();
            fd.append('cover', cover.files[0]);
            try {
              const res = await fetch('/detect/json', { method: 'POST', body: fd });
              const d = await res.json();
              if (d.error) throw new Error(d.error);
              const h = d.heuristic || 'unknown';
              resultEl.innerHTML = '<div class="heuristic ' + (h === 'likely-stego' ? 'stego' : 'clean') + '">' + (h === 'likely-stego' ? 'Possível esteganografia detectada' : 'Provavelmente imagem limpa') + '</div>' +
                'Total de bits: ' + (d.total_bits || 0) + ' | Zeros: ' + (d.zeros || 0) + ' | Uns: ' + (d.ones || 0) + ' | Razão de 1s: ' + ((d.ratio_ones * 100) || 0).toFixed(2) + '%';
            } catch (err) {
              resultEl.innerHTML = 'Erro: ' + escapeHtml(err.message);
            }
          });
        </script>
      </body>
    </html>
    """


async def _save_upload(upload: UploadFile, max_size: int = MAX_UPLOAD_SIZE) -> Path:
    content = b""
    size = 0
    while chunk := await upload.read(1024 * 64):
        size += len(chunk)
        if size > max_size:
            raise HTTPException(413, f"Arquivo muito grande. Máximo: {max_size // (1024*1024)} MB")
        content += chunk
    temp = tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(upload.filename).suffix)
    temp.write(content)
    temp.close()
    return Path(temp.name)


def _sanitize_filename(name: str, default_ext: str) -> str:
    """Sanitize filename and ensure correct extension."""
    if not name or not name.strip():
        return f"imagem_esteganografada{default_ext}"
    name = "".join(c for c in name.strip() if c.isalnum() or c in "._- ")
    name = name[:80] or "imagem_esteganografada"
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name + default_ext


@app.post("/encode")
async def web_encode(
    cover: UploadFile = File(...),
    message: str = Form(""),
    payload: UploadFile | None = File(None),
    password: str | None = None,
    channels: int = Form(1),
    bits: int = Form(1),
    compress: str | None = Form(None),
    filename: str | None = Form(None),
):
    cover_path = await _save_upload(cover)
    try:
        payload_bytes = message.encode('utf-8')
        if payload is not None and payload.filename and payload.filename.strip():
            content = await payload.read()
            if len(content) > 0:
                payload_bytes = content

        if not payload_bytes:
            raise HTTPException(400, "Informe uma mensagem ou selecione um arquivo para codificar")

        if password:
            payload_bytes = encrypt(payload_bytes, password)

        out_path = Path(tempfile.NamedTemporaryFile(
            delete=False, suffix=cover_path.suffix).name)
        actual_path = encode_image(
            str(cover_path),
            str(out_path),
            payload_bytes,
            compress=compress == "1",
            channels=max(1, min(4, channels)),
            bits_per_channel=max(1, min(2, bits)),
        )
        out_path = Path(actual_path)
        download_name = _sanitize_filename(filename or "", out_path.suffix)
        return StreamingResponse(
            open(actual_path, 'rb'),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{download_name}"'},
        )
    finally:
        try:
            cover_path.unlink()
        except Exception:
            pass


def _decode_payload(cover_path: Path, password: str | None, legacy_mode: bool = False) -> bytes:
    payload = decode_image(str(cover_path), legacy_mode=legacy_mode)
    if password:
        payload = decrypt(payload, password)
    return payload


@app.post("/decode")
async def web_decode(
    cover: UploadFile = File(...),
    password: str | None = None,
    legacy: str | None = Form(None),
):
    cover_path = await _save_upload(cover)
    try:
        payload = _decode_payload(cover_path, password, legacy_mode=legacy == "1")

        try:
            text = payload.decode('utf-8')
            return PlainTextResponse(text)
        except UnicodeDecodeError:
            return StreamingResponse(
                iter([payload]),
                media_type='application/octet-stream',
                headers={
                    'Content-Disposition': 'attachment; filename="payload.bin"'},
            )
    finally:
        try:
            cover_path.unlink()
        except Exception:
            pass


@app.post("/decode/json")
async def web_decode_json(
    cover: UploadFile = File(...),
    password: str | None = Form(None),
    legacy: str | None = Form(None),
):
    cover_path = await _save_upload(cover)
    try:
        payload = _decode_payload(cover_path, password or None, legacy_mode=legacy == "1")

        try:
            text = payload.decode('utf-8')
            return JSONResponse({"type": "text", "content": text})
        except UnicodeDecodeError:
            return JSONResponse({
                "type": "binary",
                "content": b64encode(payload).decode("ascii"),
                "filename": "payload.bin",
            })
    except Exception as e:
        return JSONResponse(
            {"type": "error", "message": str(e)},
            status_code=500,
        )
    finally:
        try:
            cover_path.unlink()
        except Exception:
            pass


@app.post("/capacity")
async def web_capacity(
    cover: UploadFile = File(...),
    channels: int = Form(1),
    bits: int = Form(1),
):
    """Retorna a capacidade em bytes da imagem para os parâmetros dados."""
    cover_path = await _save_upload(cover)
    try:
        from PIL import Image, ImageSequence

        img = Image.open(cover_path)
        if img.format == "GIF" or str(cover_path).lower().endswith(".gif"):
            total_pixels = sum(f.width * f.height for f in ImageSequence.Iterator(img))
            cap = max(0, (total_pixels - HEADER_BITS) // 8)
        else:
            cap = capacity_bytes(img.width, img.height, channels, bits)
        return JSONResponse({
            "width": img.width,
            "height": img.height,
            "capacity_bytes": cap,
            "capacity_chars_est": int(cap * 2.2),
        })
    finally:
        try:
            cover_path.unlink()
        except Exception:
            pass


@app.post("/detect/json")
async def web_detect_json(cover: UploadFile = File(...)):
    """Retorna relatório heurístico de detecção de esteganografia."""
    cover_path = await _save_upload(cover)
    try:
        report = detect_steganography(str(cover_path))
        return JSONResponse(report)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        try:
            cover_path.unlink()
        except Exception:
            pass
