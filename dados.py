from pathlib import Path

import duckdb
import pandas as pd

ARQUIVO = Path(__file__).resolve().parent / "data" / "notas.parquet"
COLUNAS = ["aluno", "materia", "bimestre", "nota"]


def carregar() -> pd.DataFrame:
    if not ARQUIVO.exists():
        return pd.DataFrame(columns=COLUNAS)
    return duckdb.sql(
        f"SELECT * FROM read_parquet('{ARQUIVO}') ORDER BY aluno, materia, bimestre"
    ).df()


def salvar(aluno: str, materia: str, bimestre: int, nota: float) -> None:
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    atual = carregar()
    nova = pd.DataFrame([{
        "aluno": aluno,
        "materia": materia,
        "bimestre": bimestre,
        "nota": nota,
    }])
    resultado = nova if atual.empty else pd.concat([atual, nova], ignore_index=True)
    resultado.to_parquet(ARQUIVO, index=False)


def limpar() -> bool:
    if ARQUIVO.exists():
        ARQUIVO.unlink()
        return True
    return False
