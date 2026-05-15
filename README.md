# consultoria-alunos

Sistema de linha de comando para professores registrarem notas de alunos por bimestre e gerarem **metas de evolução** com base no histórico. As consultas analíticas (evolução percentual e projeção de meta) são feitas em **DuckDB**, e os dados ficam persistidos em **Parquet**.

## Stack

- **Python 3.12**
- **DuckDB 1.1.3** — window functions (`LAG`) para comparar bimestres
- **Pandas 2.2.3** — manipulação dos DataFrames
- **PyArrow 18.1.0** — engine de leitura/escrita do Parquet
- **pytest 8.3.4** — bateria de testes
- **Docker / docker compose** — execução reprodutível

## Estrutura do projeto

```
consultoria-alunos/
├── main.py            # menu CLI, validacao de input e formatacao da saida
├── dados.py           # camada de persistencia (carregar / salvar / limpar)
├── test.py            # testes unitarios da camada de dados e das regras de meta
├── data/
│   └── notas.parquet  # gerado em tempo de execucao
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Funcionalidades

1. **Adicionar nota** — recebe `aluno`, `matéria`, `bimestre (1-4)` e `nota (0-10)`; valida intervalos e rejeita duplicata de `(aluno, matéria, bimestre)`.
2. **Listar notas** — imprime todas as notas registradas.
3. **Gerar metas** — para cada nota mostra:
   - a **evolução percentual** em relação ao bimestre anterior (via `LAG` no DuckDB);
   - a **meta para o próximo bimestre** = `nota × 1.10`, limitada a 10;
   - mensagens contextuais para o 1º bimestre (sem comparação) e para o 4º (sem próxima meta).
4. **Limpar dados** — apaga o arquivo Parquet após confirmação.

## Como rodar

### Docker (recomendado)

```bash
docker compose run --rm app      # roda o menu interativo
docker compose run --rm test     # roda os testes
```

O volume `./data` é montado dentro do container, então as notas ficam persistidas no host entre execuções.

### Local

```bash
pip install -r requirements.txt
python main.py
python -m pytest test.py -v
```

## Regras de negócio

- **Nota**: float entre 0 e 10 (vírgula ou ponto aceitos).
- **Bimestre**: inteiro entre 1 e 4.
- **Duplicidade**: não permite duas notas para o mesmo `(aluno, matéria, bimestre)`.
- **Meta**: crescimento alvo de **+10%** sobre a nota atual, com teto de 10.
- **Evolução**: calculada apenas quando existe nota do bimestre imediatamente anterior do mesmo aluno e matéria.

## Testes

Cobrem a camada de persistência e as regras analíticas (DuckDB):

| Teste | O que verifica |
|---|---|
| `test_carregar_vazio_quando_nao_tem_arquivo` | `carregar()` devolve DataFrame vazio quando o Parquet não existe |
| `test_salvar_e_carregar_uma_nota` | round-trip de uma nota individual |
| `test_salvar_duas_notas` | duas chamadas acumulam (não sobrescrevem) |
| `test_limpar_apaga_o_arquivo` | `limpar()` retorna `True` e zera os dados |
| `test_limpar_retorna_false_se_nao_tem_arquivo` | `limpar()` retorna `False` sem dar erro quando não há arquivo |
| `test_meta_nao_passa_de_10` | regra do teto: `9.5 × 1.10 = 10.45 → 10.0` |
| `test_meta_normal_quando_nota_e_baixa` | meta exata `5.0 → 5.5` longe do teto |
| `test_evolucao_entre_bimestres` | `LAG` calcula corretamente: `5 → 7 = +40%` |

## Exemplo de saída

```
João • Matemática • Bimestre 1: nota 7.00. Primeiro bimestre, ainda sem evolução para comparar. Meta para o próximo bimestre: 7.70.
João • Matemática • Bimestre 2: nota 8.00. Evolução de +14.29% em relação ao bimestre anterior. Meta para o próximo bimestre: 8.80.
João • Matemática • Bimestre 4: nota 9.50. Evolução de +5.56% em relação ao bimestre anterior. Bimestre final — sem meta para o próximo.
```
