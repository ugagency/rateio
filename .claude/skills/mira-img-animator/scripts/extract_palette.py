#!/usr/bin/env python3
"""
Extrai as cores dominantes de uma imagem usando K-Means clustering.

Uso:
    python extract_palette.py <caminho_da_imagem> [--colors 6] [--format hex|rgb|json]

Saída:
    Lista de cores dominantes ordenadas por frequência.
"""

import sys
import json
import argparse
from pathlib import Path


def extract_palette(image_path: str, n_colors: int = 6) -> list[dict]:
    """Extrai cores dominantes usando K-Means."""
    from PIL import Image
    import numpy as np

    img = Image.open(image_path).convert("RGB")

    # Redimensionar para acelerar o clustering
    max_dim = 200
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    pixels = np.array(img).reshape(-1, 3).astype(float)

    # K-Means simples (sem sklearn para menos dependências)
    # Inicializar centroids aleatoriamente
    np.random.seed(42)
    indices = np.random.choice(len(pixels), n_colors, replace=False)
    centroids = pixels[indices].copy()

    for _ in range(20):  # iterações
        # Atribuir cada pixel ao centroid mais próximo
        distances = np.sqrt(((pixels[:, np.newaxis] - centroids[np.newaxis]) ** 2).sum(axis=2))
        labels = distances.argmin(axis=1)

        # Atualizar centroids
        new_centroids = np.array([
            pixels[labels == k].mean(axis=0) if (labels == k).sum() > 0 else centroids[k]
            for k in range(n_colors)
        ])

        if np.allclose(centroids, new_centroids, atol=1):
            break
        centroids = new_centroids

    # Calcular proporção de cada cor
    unique, counts = np.unique(labels, return_counts=True)
    total = counts.sum()

    palette = []
    for idx in np.argsort(-counts):  # ordenar por frequência
        k = unique[idx]
        r, g, b = centroids[k].astype(int)
        proportion = counts[idx] / total
        palette.append({
            "r": int(r), "g": int(g), "b": int(b),
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgb": f"rgb({r},{g},{b})",
            "proportion": round(float(proportion), 4),
        })

    return palette


def main():
    parser = argparse.ArgumentParser(description="Extrai paleta de cores de imagem")
    parser.add_argument("image_path", help="Caminho da imagem")
    parser.add_argument("--colors", "-n", type=int, default=6,
                        help="Número de cores dominantes (default: 6)")
    parser.add_argument("--format", choices=["hex", "rgb", "json"], default="json",
                        help="Formato de saída (default: json)")
    args = parser.parse_args()

    path = Path(args.image_path)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    palette = extract_palette(str(path), args.colors)

    if args.format == "json":
        print(json.dumps(palette, indent=2))
    elif args.format == "hex":
        for color in palette:
            print(f"{color['hex']}  ({color['proportion']*100:.1f}%)")
    elif args.format == "rgb":
        for color in palette:
            print(f"{color['rgb']}  ({color['proportion']*100:.1f}%)")


if __name__ == "__main__":
    main()
