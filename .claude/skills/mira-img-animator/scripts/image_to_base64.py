#!/usr/bin/env python3
"""
Converte uma imagem em string base64 para embutir em HTML.

Uso:
    python image_to_base64.py <caminho_da_imagem> [--convert-to png|jpg|webp]
    python image_to_base64.py <caminho_da_imagem> --output arquivo.txt

Saída:
    Data URI completa (data:image/png;base64,...) em stdout ou arquivo.
"""

import sys
import base64
import argparse
import mimetypes
from pathlib import Path


def get_mime_type(filepath: str) -> str:
    """Detecta o MIME type da imagem."""
    mime, _ = mimetypes.guess_type(filepath)
    if mime and mime.startswith("image/"):
        return mime
    ext = Path(filepath).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
        ".ico": "image/x-icon",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return mime_map.get(ext, "image/png")


def convert_image(input_path: str, target_format: str) -> tuple[bytes, str]:
    """Converte imagem para outro formato usando Pillow."""
    from PIL import Image

    img = Image.open(input_path)

    # Converter RGBA → RGB se necessário para JPEG
    if target_format.upper() == "JPEG" and img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg

    import io
    buffer = io.BytesIO()
    fmt = target_format.upper()
    if fmt == "JPG":
        fmt = "JPEG"
    img.save(buffer, format=fmt)
    
    mime_map = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
    return buffer.getvalue(), mime_map.get(fmt, "image/png")


def image_to_base64(filepath: str, convert_to: str | None = None) -> str:
    """Converte imagem para data URI base64."""
    if convert_to:
        data, mime = convert_image(filepath, convert_to)
    else:
        with open(filepath, "rb") as f:
            data = f.read()
        mime = get_mime_type(filepath)

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def main():
    parser = argparse.ArgumentParser(description="Converte imagem para base64 data URI")
    parser.add_argument("image_path", help="Caminho da imagem")
    parser.add_argument("--convert-to", choices=["png", "jpg", "webp"],
                        help="Converter para outro formato antes de codificar")
    parser.add_argument("--output", "-o", help="Salvar resultado em arquivo")
    parser.add_argument("--stats", action="store_true", help="Mostrar estatísticas")
    args = parser.parse_args()

    path = Path(args.image_path)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    data_uri = image_to_base64(str(path), args.convert_to)

    if args.stats:
        original_size = path.stat().st_size
        b64_size = len(data_uri)
        print(f"[INFO] Arquivo original: {original_size:,} bytes", file=sys.stderr)
        print(f"[INFO] Base64 data URI: {b64_size:,} caracteres", file=sys.stderr)
        print(f"[INFO] Razão: {b64_size / original_size:.1f}x", file=sys.stderr)

    if args.output:
        with open(args.output, "w") as f:
            f.write(data_uri)
        print(f"[INFO] Salvo em: {args.output}", file=sys.stderr)
    else:
        print(data_uri)


if __name__ == "__main__":
    main()
