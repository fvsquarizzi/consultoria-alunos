import duckdb
import pandas as pd

import dados


def setup_function():
    # roda antes de cada teste e zera o arquivo de notas pra cada caso comecar limpo
    if dados.ARQUIVO.exists():
        dados.ARQUIVO.unlink()


def test_carregar_vazio_quando_nao_tem_arquivo():
    # espera que, sem o parquet existindo, carregar() devolva um DataFrame vazio (e nao quebre)
    df = dados.carregar()
    assert df.empty


def test_salvar_e_carregar_uma_nota():
    # espera que salvar uma nota e carregar de volta retorne exatamente os mesmos valores gravados
    dados.salvar("Ana", "Matematica", 1, 7.5)
    df = dados.carregar()
    assert len(df) == 1
    assert df.iloc[0]["aluno"] == "Ana"
    assert df.iloc[0]["materia"] == "Matematica"
    assert df.iloc[0]["bimestre"] == 1
    assert df.iloc[0]["nota"] == 7.5


def test_salvar_duas_notas():
    # espera que duas chamadas seguidas de salvar acumulem no arquivo (nao sobrescrevam)
    dados.salvar("Ana", "Matematica", 1, 7.0)
    dados.salvar("Ana", "Matematica", 2, 8.0)
    df = dados.carregar()
    assert len(df) == 2


def test_limpar_apaga_o_arquivo():
    # espera que, com dados gravados, limpar() devolva True e o carregamento subsequente venha vazio
    dados.salvar("Ana", "Matematica", 1, 7.5)
    assert dados.limpar() is True
    assert dados.carregar().empty


def test_limpar_retorna_false_se_nao_tem_arquivo():
    # espera que limpar() devolva False quando nao existe arquivo pra apagar (sem erro)
    assert dados.limpar() is False


def test_meta_nao_passa_de_10():
    # espera que a regra de crescimento de 10% respeite o teto de nota 10 (9.5 * 1.10 = 10.45, mas vira 10.0)
    df = pd.DataFrame([{"nota": 9.5}])
    resultado = duckdb.sql("SELECT LEAST(10.0, nota * 1.10) AS meta FROM df").df()
    assert resultado.iloc[0]["meta"] == 10.0


def test_meta_normal_quando_nota_e_baixa():
    # espera que, longe do teto, a meta seja exatamente nota * 1.10 (5.0 -> 5.5)
    df = pd.DataFrame([{"nota": 5.0}])
    resultado = duckdb.sql("SELECT LEAST(10.0, nota * 1.10) AS meta FROM df").df()
    assert resultado.iloc[0]["meta"] == 5.5


def test_evolucao_entre_bimestres():
    # espera que o calculo de evolucao percentual entre bimestres consecutivos esteja correto (5 -> 7 = +40%)
    df = pd.DataFrame([
        {"bimestre": 1, "nota": 5.0},
        {"bimestre": 2, "nota": 7.0},
    ])
    resultado = duckdb.sql("""
        SELECT
            bimestre,
            (nota - LAG(nota) OVER (ORDER BY bimestre))
              / LAG(nota) OVER (ORDER BY bimestre) * 100 AS evolucao
        FROM df
        ORDER BY bimestre
    """).df()
    assert resultado.iloc[1]["evolucao"] == 40.0
