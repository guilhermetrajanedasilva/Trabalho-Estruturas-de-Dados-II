"""
Salvar no Google Drive (Google Colab) — Projeto NetVision (Grupo 15)

Usado por todos os scripts com a opção --drive. No Colab, monta o Drive e usa uma pasta dentro de "Meu Drive"
como raiz do projeto: data/, reports/ e models/ passam a ser gravados lá. Se a pasta ainda não tem config/,
copia a config/ que está ao lado dos scripts.

Exemplos (numa célula do Colab, depois de enviar a pasta do projeto):
  !python coleta_bruta.py --drive                 # usa MyDrive/netvision
  !python coleta_bruta.py --drive projeto_g15     # usa MyDrive/projeto_g15
Cria a pasta (com data/raw, data/interim, data/processed, reports e models) se ela não existir; se já existir, só grava nela.
Use a MESMA pasta em todas as tarefas, para a Tarefa 2 achar o bruto da Tarefa 1, e assim por diante.
"""
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
