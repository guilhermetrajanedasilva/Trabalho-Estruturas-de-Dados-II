import shutil
from pathlib import Path

PASTA_PADRAO = "netvision"
RAIZ_DRIVE = Path("/content/drive/MyDrive")


def resolver_base(base_dir: Path, drive) -> Path:
    """Devolve a raiz do projeto. `drive` é None (não usa o Drive) ou o nome da subpasta de Meu Drive."""
    if drive is None:
        return base_dir.resolve()
    try:
        from google.colab import drive as colab_drive
    except ImportError:
        raise SystemExit("--drive só funciona no Google Colab. Fora do Colab, use --base-dir com o caminho da pasta.")
    if not RAIZ_DRIVE.exists():
        colab_drive.mount("/content/drive")
    destino = RAIZ_DRIVE / (drive or PASTA_PADRAO)
    # cria a pasta no Drive se ainda não existir; se já existir, só reaproveita (os arquivos são gravados nela)
    ja_existia = destino.exists()
    for sub in ("", "data/raw", "data/interim", "data/processed", "reports", "models"):
        (destino / sub).mkdir(parents=True, exist_ok=True)  # equivale a: !mkdir -p /content/drive/MyDrive/<pasta>
    print(f"Pasta {'já existia' if ja_existia else 'criada'}: {destino}")
    origem_cfg = Path(__file__).resolve().parent / "config"
    if not (destino / "config").exists() and origem_cfg.exists():
        shutil.copytree(origem_cfg, destino / "config")
        print(f"config/ copiada para {destino}")
    print(f"Raiz do projeto no Drive: {destino}")
    return destino.resolve()
