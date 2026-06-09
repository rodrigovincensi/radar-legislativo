import subprocess
import sys
from pathlib import Path

BASE = Path(r"c:\Rodrigo\Xperiun\Pós Tech\Squad\Projeto Integrador I\Scripts Python")

notebooks = [
    "02_extracao_dados.ipynb",
    "03_transformacao_carga.ipynb",
    "04_ia_resumos.ipynb",
    "05_classificacao_temas.ipynb",
]

for nb in notebooks:
    path = BASE / nb
    print(f"Executando {nb}...")
    result = subprocess.run(
        [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
         "--execute", "--inplace", str(path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERRO em {nb}:\n{result.stderr}")
        sys.exit(1)
    print(f"{nb} concluido.")

print("Pipeline concluido com sucesso.")
