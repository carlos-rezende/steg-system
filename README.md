# Steg-System

Sistema de esteganografia LSB em imagens (PNG, WebP, GIF, BMP, TIFF).

## Formato e compatibilidade

- **Novo formato (v1)**: Payload com magic bytes `STEG` para evitar falsos positivos em imagens limpas.
- **Imagens antigas**: Use `--legacy` (CLI) ou marque "Tentar decodificar imagens antigas" (web) para decodificar imagens codificadas antes do magic bytes. _Risco de falsos positivos._

## Setup

1. Activate the virtual environment:

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

### CLI (command-line)

Encode text into an image (PNG/WebP/GIF/BMP/TIFF):

```powershell
python -m steg_system encode --input input.png --output output.png --message "Secret"
```

Encode a binary payload into an image:

```powershell
python -m steg_system encode --input input.png --output output.png --payload-file secret.bin
```

Decode from an image:

```powershell
python -m steg_system decode --input output.png
```

Decode and save payload to a file:

```powershell
python -m steg_system decode --input output.png --output secret.bin
```

Decode and print base64 when payload is non-text:

```powershell
python -m steg_system decode --input output.png --raw
```

Decode images encoded before magic bytes (legacy):

```powershell
python -m steg_system decode --input old_image.png --legacy
```

### Optional: encrypt the payload

```powershell
python -m steg_system encode --input input.png --output output.png --message "Secret" --password "s3cret"
python -m steg_system decode --input output.png --password "s3cret"
```

### Optional: compression and capacity

- **Compression (zlib)**: Enabled by default. Use `--no-compress` for already-compressed files (e.g. ZIP, JPEG).
- **Multi-channels**: Use `--channels 3` (RGB) or `--channels 4` (RGBA) to increase capacity.
- **Multi-bits**: Use `--bits 2` for 2 bits per channel (higher capacity, more detectable).

```powershell
python -m steg_system encode -i input.png -o output.png -m "Long message..." --channels 3
python -m steg_system encode -i input.png -o output.png -m "Secret" --no-compress
```

### Detect steganography (heuristic)

```powershell
python -m steg_system detect --input output.png
```

### Web interface (FastAPI)

Run the server and open the UI in your browser:

```powershell
uvicorn steg_system.web:app --reload --port 8011
```

Acesse: http://127.0.0.1:8011

**Recursos da interface web:**

- Indicador de capacidade ao selecionar imagem
- Validação prévia (mensagem vs capacidade)
- Preview da imagem e drag & drop
- Botão "Remover imagem" para limpar o upload
- Botão "Detectar esteganografia" (análise heurística)
- Nome personalizado para o arquivo de saída
- Modo legado para imagens antigas
- Limite de upload: 10 MB
- Formatos: PNG, WebP, GIF, BMP, TIFF

### Docker

```powershell
docker build -t steg-system .
docker run -p 8011:8011 steg-system
```

### Testes

```powershell
pytest tests/ -v
```
