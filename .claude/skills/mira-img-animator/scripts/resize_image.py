#!/usr/bin/env python3
"""
Redimensiona uma imagem para otimizar performance da animação.

Uso:
    python resize_image.py <imagem> --max-width 800 --output resized.png
    python resize_image.py <imagem> --max-pixels 500000

Saída:
    Imagem redimensionada salva no caminho especificado.
"""

import sys
import argparse
from pathlib import Path


def resize_image(
    image_path: str,
    output_path: str,
    max_width: int | None = None,
    max_height: int | None = None,
    max_pixels: int | None = None,
) -> dict:
    """Redimensiona imagem mantendo aspect ratio."""
    from PIL import Image

    img = Image.open(image_path)
    original_size = img.size
    w, h = img.size

    if max_pixels and (w * h) > max_pixels:
        ratio = (max_pixels / (w * h)) ** 0.5
        w = int(w * ratio)
        h = int(h * ratio)
    elif max_width and w > max_width:
        ratio = max_width / w
        w = max_width
        h = int(h * ratio)
    elif max_height and h > max_height:
        ratio = max_height / h
        h = max_height
        w = int(w * ratio)
    else:
        # Sem redimensionamento necessário
        img.save(output_path)
        return {
            "original": list(original_size),
            "output": list(original_size),
            "resized": False,
        }

    img = img.resize((w, h), Image.LANCZOS)
    img.save(output_path)

    return {
        "original": list(original_size),
        "output": [w, h],
        "resized": True,
        "scale": round(w / original_size[0], 3),
    }


def main():
    parser = argparse.ArgumentParser(description="Redimensiona imagem para animação")
    parser.add_argument("image_path", help="Caminho da imagem")
    parser.add_argument("--output", "-o", required=True, help="Caminho de saída")
    parser.add_argument("--max-width", type=int, help="Largura máxima")
    parser.add_argument("--max-height", type=int, help="Altura máxima")
    parser.add_argument("--max-pixels", type=int, default=500000,
                        help="Número máximo de pixels total (default: 500000)")
    args = parser.parse_args()

    path = Path(args.image_path)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    result = resize_image(
        str(path), args.output,
        max_width=args.max_width,
        max_height=args.max_height,
        max_pixels=args.max_pixels,
    )

    if result["resized"]:
        orig = result["original"]
        out = result["output"]
        print(f"[INFO] Redimensionado: {orig[0]}x{orig[1]} → {out[0]}x{out[1]} "
              f"(scale: {result['scale']})", file=sys.stderr)
    else:
        print("[INFO] Imagem já está dentro dos limites, não precisou redimensionar.",
              file=sys.stderr)
    print(f"[INFO] Salvo em: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
