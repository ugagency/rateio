#!/usr/bin/env python3
"""
Extrai dados de pixels de uma imagem para uso em animações de partículas.

Produz um JSON com coordenadas (x, y) e cor (r, g, b) de cada pixel amostrado,
pronto para ser embutido no JavaScript da animação.

Uso:
    python extract_pixels.py <imagem> [--sample-rate 4] [--min-alpha 128] [--max-width 400]
    python extract_pixels.py <imagem> --output pixels.json

Saída:
    JSON array com objetos {x, y, r, g, b} em stdout ou arquivo.
"""

import sys
import json
import argparse
from pathlib import Path


def extract_pixels(
    image_path: str,
    sample_rate: int = 4,
    min_alpha: int = 128,
    max_width: int = 400,
) -> tuple[list[dict], dict]:
    """
    Extrai pixels amostrados de uma imagem.
    
    Retorna:
        (pixels, metadata) onde pixels é lista de {x, y, r, g, b}
        e metadata contém informações sobre a extração.
    """
    from PIL import Image
    import numpy as np

    img = Image.open(image_path).convert("RGBA")

    # Redimensionar se muito grande
    original_size = img.size
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    data = np.array(img)
    h, w = data.shape[:2]

    pixels = []
    for y in range(0, h, sample_rate):
        for x in range(0, w, sample_rate):
            r, g, b, a = data[y, x]
            if a >= min_alpha:
                pixels.append({
                    "x": int(x),
                    "y": int(y),
                    "r": int(r),
                    "g": int(g),
                    "b": int(b),
                })

    metadata = {
        "original_width": original_size[0],
        "original_height": original_size[1],
        "processed_width": w,
        "processed_height": h,
        "sample_rate": sample_rate,
        "min_alpha": min_alpha,
        "total_pixels": w * h,
        "sampled_pixels": len(pixels),
        "compression_ratio": round(len(pixels) / (w * h) * 100, 2),
    }

    return pixels, metadata


def main():
    parser = argparse.ArgumentParser(description="Extrai pixels de imagem para animação")
    parser.add_argument("image_path", help="Caminho da imagem")
    parser.add_argument("--sample-rate", "-s", type=int, default=4,
                        help="A cada N pixels (default: 4). Maior = menos partículas")
    parser.add_argument("--min-alpha", "-a", type=int, default=128,
                        help="Alpha mínimo para incluir pixel (0-255, default: 128)")
    parser.add_argument("--max-width", "-w", type=int, default=400,
                        help="Largura máxima para processamento (default: 400)")
    parser.add_argument("--output", "-o", help="Salvar resultado em arquivo JSON")
    parser.add_argument("--stats-only", action="store_true",
                        help="Mostrar apenas estatísticas, sem os dados")
    args = parser.parse_args()

    path = Path(args.image_path)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    pixels, metadata = extract_pixels(
        str(path),
        sample_rate=args.sample_rate,
        min_alpha=args.min_alpha,
        max_width=args.max_width,
    )

    # Sempre mostrar metadata
    print(f"[INFO] Imagem: {metadata['original_width']}x{metadata['original_height']}"
          f" → {metadata['processed_width']}x{metadata['processed_height']}", file=sys.stderr)
    print(f"[INFO] Partículas: {metadata['sampled_pixels']:,} "
          f"({metadata['compression_ratio']}% dos pixels)", file=sys.stderr)

    if args.stats_only:
        print(json.dumps(metadata, indent=2))
        return

    result = {"metadata": metadata, "pixels": pixels}

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f)
        print(f"[INFO] Salvo em: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
