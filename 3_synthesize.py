"""
Passo 3: Sintetiza texto com a voz clonada do Olavo de Carvalho.

Usa XTTS v2 (Coqui TTS) com zero-shot voice cloning.
Na primeira execução, baixa o modelo (~2GB). Subsequent runs são rápidas.

Uso:
    python3 3_synthesize.py                          # sintetiza trechos da Bíblia (biblia.txt)
    python3 3_synthesize.py --text "seu texto aqui"  # texto direto
    python3 3_synthesize.py --file meu_texto.txt     # arquivo de texto
    python3 3_synthesize.py --list                   # lista trechos bíblicos disponíveis
"""

import argparse
import os
import sys
import time

# Evita falhas de cache do numba/librosa em ambientes restritos.
os.environ.setdefault("NUMBA_DISABLE_CACHING", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", os.path.join(os.path.dirname(__file__), ".cache", "numba"))

REFERENCE_WAV = "reference.wav"
OUTPUT_DIR = "output"
MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# Trechos bíblicos em português (João Ferreira de Almeida)
BIBLE_PASSAGES = {
    "jo_1_1": (
        "João 1:1-5",
        "No princípio era o Verbo, e o Verbo estava com Deus, e o Verbo era Deus. "
        "Ele estava no princípio com Deus. Todas as coisas foram feitas por ele, "
        "e sem ele nada do que foi feito se fez. Nele estava a vida, e a vida era a luz dos homens. "
        "E a luz resplandece nas trevas, e as trevas não a compreenderam."
    ),
    "sl_23": (
        "Salmos 23",
        "O Senhor é o meu pastor; de nada me faltará. "
        "Deitar-me faz em verdes pastos; guia-me mansamente a águas tranquilas. "
        "Refrigera a minha alma; guia-me pelas veredas da justiça por amor do seu nome. "
        "Ainda que eu andasse pelo vale da sombra da morte, não temeria mal algum, "
        "porque tu estás comigo; o teu bordão e o teu cajado me consolam."
    ),
    "jo_3_16": (
        "João 3:16",
        "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, "
        "para que todo aquele que nele crê não pereça, mas tenha a vida eterna."
    ),
    "rm_8_38": (
        "Romanos 8:38-39",
        "Porque estou persuadido de que nem a morte, nem a vida, nem os anjos, "
        "nem os principados, nem as potestades, nem as coisas presentes, nem as futuras, "
        "nem a altura, nem a profundidade, nem alguma outra criatura nos poderá separar "
        "do amor de Deus, que está em Cristo Jesus, nosso Senhor."
    ),
    "gn_1_1": (
        "Gênesis 1:1-5",
        "No princípio, criou Deus os céus e a terra. "
        "A terra, porém, estava sem forma e vazia; havia trevas sobre a face do abismo, "
        "e o Espírito de Deus pairava sobre a face das águas. "
        "Disse Deus: haja luz. E houve luz. "
        "E Deus viu que a luz era boa; e fez Deus separação entre a luz e as trevas. "
        "E Deus chamou à luz dia e às trevas noite."
    ),
    "ap_22_13": (
        "Apocalipse 22:13",
        "Eu sou o Alfa e o Ômega, o primeiro e o último, o princípio e o fim."
    ),
}


def load_tts():
    try:
        from TTS.api import TTS
    except ImportError:
        print("ERRO: TTS não instalado. Execute setup.sh primeiro.")
        sys.exit(1)

    print("Carregando modelo XTTS v2...")
    print("(Primeira execução: download de ~2GB — aguarde)\n")

    # PyTorch 2.6+ mudou o padrão de torch.load(weights_only=True).
    # O checkpoint do XTTS (baixado pelo gerenciador oficial do Coqui TTS) pode
    # incluir objetos além de tensores e falha com `weights_only=True`.
    # Forçamos `weights_only=False` para manter compatibilidade.
    try:
        import torch
        _torch_load = torch.load

        def _torch_load_compat(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return _torch_load(*args, **kwargs)

        torch.load = _torch_load_compat  # type: ignore[assignment]
    except Exception:
        # Se a API/versão não suportar isso, segue e deixa o erro aparecer.
        pass

    tts = TTS(MODEL)
    return tts


def synthesize(tts, text: str, output_path: str, reference_wav: str):
    if not os.path.exists(reference_wav):
        print(f"ERRO: '{reference_wav}' não encontrado. Execute 2_prepare.py primeiro.")
        sys.exit(1)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    print(f"Sintetizando: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
    t0 = time.time()

    tts.tts_to_file(
        text=text,
        speaker_wav=reference_wav,
        language="pt",
        file_path=output_path,
    )

    elapsed = time.time() - t0
    print(f"  → {output_path} ({elapsed:.1f}s)\n")


def list_passages():
    print("\nTrechos bíblicos disponíveis:\n")
    for key, (ref, text) in BIBLE_PASSAGES.items():
        preview = text[:60] + "..."
        print(f"  {key:12s}  {ref}")
        print(f"               {preview}")
    print(f"\nUso: python3 3_synthesize.py --passage jo_1_1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", help="Texto para sintetizar diretamente")
    parser.add_argument("--file", help="Arquivo .txt com o texto")
    parser.add_argument("--passage", help="Chave do trecho bíblico (ex: jo_1_1)")
    parser.add_argument("--list", action="store_true", help="Lista trechos disponíveis")
    parser.add_argument("--ref", default=REFERENCE_WAV,
                        help=f"Áudio de referência (default: {REFERENCE_WAV})")
    parser.add_argument("--all", action="store_true",
                        help="Sintetiza todos os trechos bíblicos")
    args = parser.parse_args()

    if args.list:
        list_passages()
        sys.exit(0)

    tts = load_tts()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.text:
        synthesize(tts, args.text, f"{OUTPUT_DIR}/custom.wav", args.ref)

    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read().strip()
        name = os.path.splitext(os.path.basename(args.file))[0]
        synthesize(tts, text, f"{OUTPUT_DIR}/{name}.wav", args.ref)

    elif args.passage:
        if args.passage not in BIBLE_PASSAGES:
            print(f"ERRO: trecho '{args.passage}' não encontrado. Use --list para ver opções.")
            sys.exit(1)
        ref_label, text = BIBLE_PASSAGES[args.passage]
        synthesize(tts, text, f"{OUTPUT_DIR}/{args.passage}.wav", args.ref)

    elif args.all:
        print(f"Sintetizando {len(BIBLE_PASSAGES)} trechos...\n")
        for key, (ref_label, text) in BIBLE_PASSAGES.items():
            print(f"--- {ref_label} ---")
            synthesize(tts, text, f"{OUTPUT_DIR}/{key}.wav", args.ref)
        print(f"\nConcluído! Áudios em: {OUTPUT_DIR}/")

    else:
        # Padrão: sintetiza João 3:16 como demonstração
        print("Nenhum texto especificado. Sintetizando João 3:16 como demo...\n")
        ref_label, text = BIBLE_PASSAGES["jo_3_16"]
        synthesize(tts, text, f"{OUTPUT_DIR}/demo_jo_3_16.wav", args.ref)
        print(f"Use --list para ver todos os trechos disponíveis.")
        print(f"Use --all para sintetizar todos de uma vez.")
