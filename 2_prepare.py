"""
Passo 2: Prepara o áudio de referência para clonagem de voz.

- Seleciona e concatena os melhores segmentos (voz limpa, sem ruído)
- Normaliza volume
- Salva como reference.wav (usado pelo XTTS v2)

Uso:
    python3 2_prepare.py --segments 2,3,5,7   (índices dos melhores segmentos)
    python3 2_prepare.py --segments all        (usa todos)
    python3 2_prepare.py --file caminho.wav    (usa arquivo WAV direto)
"""

import argparse
import os
import subprocess
import sys

SEG_DIR = "audio_raw/segments"
OUTPUT_REF = "reference.wav"
# XTTS v2 precisa de pelo menos 6s, ideal 10–30s de voz limpa
MIN_DURATION = 6


def get_duration(wav_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def normalize_and_merge(input_files: list[str], output: str):
    if len(input_files) == 1:
        cmd = [
            "ffmpeg", "-y", "-i", input_files[0],
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "22050", "-ac", "1",
            output,
        ]
        subprocess.run(cmd, capture_output=True, check=True)
    else:
        # Cria arquivo de lista para concat
        list_file = "/tmp/concat_list.txt"
        with open(list_file, "w") as f:
            for p in input_files:
                f.write(f"file '{os.path.abspath(p)}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "22050", "-ac", "1",
            output,
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    dur = get_duration(output)
    print(f"reference.wav criado: {dur:.1f}s → {output}")


def list_segments():
    if not os.path.isdir(SEG_DIR):
        print(f"ERRO: diretório '{SEG_DIR}' não encontrado.")
        print("Execute primeiro: python3 1_download.py")
        sys.exit(1)

    segs = sorted([f for f in os.listdir(SEG_DIR) if f.endswith(".wav")])
    print(f"\n{len(segs)} segmentos disponíveis em {SEG_DIR}/:")
    for i, s in enumerate(segs):
        path = os.path.join(SEG_DIR, s)
        dur = get_duration(path)
        print(f"  [{i:3d}] {s}  ({dur:.0f}s)")
    print("\nUse --segments 0,1,3 para selecionar os melhores (voz clara, sem música/ruído).")
    return segs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default=None,
                        help="Índices dos segmentos separados por vírgula, ou 'all'")
    parser.add_argument("--file", default=None,
                        help="Caminho para WAV direto (pula seleção de segmentos)")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"ERRO: arquivo não encontrado: {args.file}")
            sys.exit(1)
        normalize_and_merge([args.file], OUTPUT_REF)
        sys.exit(0)

    segs = list_segments()

    if args.segments is None:
        print("\nExecute novamente com --segments para preparar o áudio de referência.")
        sys.exit(0)

    if args.segments == "all":
        chosen = segs
    else:
        indices = [int(x.strip()) for x in args.segments.split(",")]
        chosen = [segs[i] for i in indices if i < len(segs)]

    if not chosen:
        print("ERRO: nenhum segmento selecionado.")
        sys.exit(1)

    paths = [os.path.join(SEG_DIR, s) for s in chosen]
    print(f"\nSegmentos selecionados: {chosen}")
    normalize_and_merge(paths, OUTPUT_REF)

    dur = get_duration(OUTPUT_REF)
    if dur < MIN_DURATION:
        print(f"AVISO: áudio de referência muito curto ({dur:.1f}s). "
              f"Adicione mais segmentos para melhor qualidade.")
    else:
        print(f"✓ Pronto! Execute: python3 3_synthesize.py")
