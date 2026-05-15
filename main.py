import duckdb
import pandas as pd

from dados import carregar, limpar, salvar

NOTA_MAXIMA = 10.0
CRESCIMENTO_ALVO = 1.10


def adicionar_nota() -> None:
    aluno = input("Aluno: ").strip()
    materia = input("Matéria: ").strip()
    if not aluno or not materia:
        print("Aluno e matéria são obrigatórios.")
        return
    try:
        bimestre = int(input("Bimestre (1-4): ").strip())
        nota = float(input("Nota (0-10): ").strip().replace(",", "."))
    except ValueError:
        print("Bimestre e nota precisam ser numéricos.")
        return
    if not 1 <= bimestre <= 4:
        print("Bimestre deve estar entre 1 e 4.")
        return
    if not 0 <= nota <= NOTA_MAXIMA:
        print("Nota deve estar entre 0 e 10.")
        return
    df = carregar()
    if not df.empty:
        ja_existe = (
            (df["aluno"] == aluno)
            & (df["materia"] == materia)
            & (df["bimestre"] == bimestre)
        ).any()
        if ja_existe:
            print(f"Já existe nota para {aluno} em {materia} no bimestre {bimestre}.")
            return
    salvar(aluno, materia, bimestre, nota)
    print(f"Nota {nota:.2f} registrada para {aluno} em {materia} (bimestre {bimestre}).")


def listar_notas() -> None:
    df = carregar()
    if df.empty:
        print("Nenhuma nota cadastrada.")
        return
    print("\n--- Notas registradas ---")
    print(df.to_string(index=False))


def gerar_metas() -> None:
    df = carregar()
    if df.empty:
        print("Sem dados para gerar metas.")
        return
    resultado = duckdb.sql(f"""
        WITH base AS (
            SELECT
                aluno,
                materia,
                bimestre,
                nota,
                LAG(nota) OVER (PARTITION BY aluno, materia ORDER BY bimestre) AS anterior
            FROM df
        )
        SELECT
            aluno,
            materia,
            bimestre,
            nota,
            ROUND((nota - anterior) / NULLIF(anterior, 0) * 100, 2) AS evolucao_percentual,
            CASE
                WHEN bimestre < 4
                THEN ROUND(LEAST({NOTA_MAXIMA}, nota * {CRESCIMENTO_ALVO}), 2)
                ELSE NULL
            END AS meta_proximo_bimestre
        FROM base
        ORDER BY aluno, materia, bimestre
    """).df()
    print("\n--- Evolução e metas ---")
    for linha in resultado.itertuples(index=False):
        cabecalho = (
            f"{linha.aluno} • {linha.materia} • Bimestre {linha.bimestre}: "
            f"nota {linha.nota:.2f}."
        )
        if pd.notna(linha.evolucao_percentual):
            evolucao = f" Evolução de {linha.evolucao_percentual:+.2f}% em relação ao bimestre anterior."
        elif linha.bimestre == 1:
            evolucao = " Primeiro bimestre, ainda sem evolução para comparar."
        else:
            evolucao = " Sem bimestre anterior registrado para comparar."

        if linha.bimestre == 4:
            meta = " Bimestre final — sem meta para o próximo."
        else:
            meta = f" Meta para o próximo bimestre: {linha.meta_proximo_bimestre:.2f}."

        print(cabecalho + evolucao + meta)


def limpar_dados() -> None:
    confirmacao = input("Apagar TODAS as notas? (s/N): ").strip().lower()
    if confirmacao != "s":
        print("Operação cancelada.")
        return
    if limpar():
        print("Dados removidos.")
    else:
        print("Nada para remover.")


def main() -> None:
    opcoes = {
        "1": ("Adicionar nota", adicionar_nota),
        "2": ("Listar notas", listar_notas),
        "3": ("Gerar metas", gerar_metas),
        "4": ("Limpar dados", limpar_dados),
    }
    while True:
        print("\n=== Sistema de Notas ===")
        for chave, (rotulo, _) in opcoes.items():
            print(f"{chave} - {rotulo}")
        print("0 - Sair")
        escolha = input("Escolha: ").strip()
        if escolha == "0":
            print("Até logo!")
            break
        acao = opcoes.get(escolha)
        if acao is None:
            print("Opção inválida.")
            continue
        acao[1]()


if __name__ == "__main__":
    main()
