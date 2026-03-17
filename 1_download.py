"""
Passo 1: Baixa o áudio do YouTube e extrai segmentos limpos de voz.

Uso:
    python3 1_download.py
    python3 1_download.py --url "https://youtube.com/watch?v=OUTRO_VIDEO"
"""

import argparse
import os
import subprocess
import sys
from typing import Optional

URL = "https://www.youtube.com/watch?v=LbjDYjl1Dw8"
OUTPUT_DIR = "audio_raw"
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def check_dep(name):
    import shutil
    if shutil.which(name) is None:
        print(f"ERRO: '{name}' não encontrado. Execute setup.sh primeiro.")
        sys.exit(1)


def download_audio(url: str, out_dir: str, user_agent: Optional[str] = None, cookies: Optional[str] = None) -> str:
    os.makedirs(out_dir, exist_ok=True)
    out_template = os.path.join(out_dir, "olavo_original.%(ext)s")

    # YouTube frequentemente retorna 403 dependendo do "client" usado.
    # Estes flags tendem a aumentar a taxa de sucesso sem exigir login.
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",          # melhor qualidade
        "--postprocessor-args", "-ar 22050 -ac 1",  # mono 22kHz (ideal para TTS)
        "--extractor-args", "youtube:player_client=android,web",
        "-o", out_template,
        url,
    ]

    if user_agent:
        cmd.extend(["--user-agent", user_agent])
    if cookies:
        cmd.extend(["--cookies", cookies])

    print(f"Baixando áudio de:\n  {url}\n")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("ERRO ao baixar.")
        print("Dica: o YouTube pode exigir cookies. Tente:")
        print(f"  python3 1_download.py --cookies /caminho/para/cookies.txt")
        sys.exit(1)

    wav_path = os.path.join(out_dir, "olavo_original.wav")
    if not os.path.exists(wav_path):
        # yt-dlp pode ter gerado com nome diferente
        files = [f for f in os.listdir(out_dir) if f.endswith(".wav")]
        if files:
            wav_path = os.path.join(out_dir, files[0])

    print(f"\nÁudio salvo em: {wav_path}")
    return wav_path


def split_into_segments(wav_path: str, out_dir: str, segment_len: int = 15):
    """
    Divide o áudio em segmentos de `segment_len` segundos.
    Útil para selecionar os melhores trechos de voz limpa.
    """
    seg_dir = os.path.join(out_dir, "segments")
    os.makedirs(seg_dir, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-f", "segment",
        "-segment_time", str(segment_len),
        "-ar", "22050",
        "-ac", "1",
        "-c", "pcm_s16le",
        os.path.join(seg_dir, "seg_%03d.wav"),
    ]

    print(f"\nDividindo em segmentos de {segment_len}s...")
    subprocess.run(cmd, capture_output=True, check=True)

    segs = sorted(os.listdir(seg_dir))
    print(f"{len(segs)} segmentos criados em: {seg_dir}/")
    print("\nOuça os segmentos e anote os índices com voz mais clara (sem música/ruído).")
    print("Depois execute: python3 2_prepare.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=URL)
    parser.add_argument("--segment-len", type=int, default=15,
                        help="Duração dos segmentos em segundos (default: 15)")
    parser.add_argument("--user-agent", default=DEFAULT_UA,
                        help="User-Agent para o yt-dlp (ajuda a evitar 403)")
    parser.add_argument("--cookies", default=None,
                        help="Arquivo cookies.txt (Netscape format) para yt-dlp, se necessário")
    args = parser.parse_args()

    check_dep("yt-dlp")
    check_dep("ffmpeg")

    wav = download_audio(args.url, OUTPUT_DIR, user_agent=args.user_agent, cookies=args.cookies)
    split_into_segments(wav, OUTPUT_DIR, args.segment_len)
