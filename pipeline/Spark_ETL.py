import os
import random
from datetime import date, timedelta
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, IntegerType, StringType
from dotenv import load_dotenv

load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER     = os.getenv("DB_USER", "sa")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "1433")

JDBC_URL_TRANSACIONAL = (
    f"jdbc:sqlserver://{DB_HOST}:{DB_PORT};"
    f"databaseName=gym_db;"
    f"encrypt=false;"
    f"trustServerCertificate=true;"
)

JDBC_URL_DIMENSIONAL = (
    f"jdbc:sqlserver://{DB_HOST}:{DB_PORT};"
    f"databaseName=gym_dw;"
    f"encrypt=false;"
    f"trustServerCertificate=true;"
)

JDBC_PROPS = {
    "user":     DB_USER,
    "password": DB_PASSWORD,
    "driver":   "com.microsoft.sqlserver.jdbc.SQLServerDriver",
}

spark = (
    SparkSession.builder
    .appName("gym_etl_spark_sql")
    .config("spark.jars", "mssql-jdbc-12.4.2.jre11.jar")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ============================================
# UDFs registradas para o contexto SQL
#
# spark.udf.register() torna as funções Python
# disponíveis dentro de qualquer spark.sql().
# Sem esse registro, o SQL não enxerga as
# funções — o F.udf() sozinho só funciona
# na API Python, não em strings SQL.
# ============================================
DIAS_SEMANA_PT = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}

def _gerar_data_aleatoria() -> date:
    inicio = date(2024, 1, 1)
    delta  = (date.today() - inicio).days
    return inicio + timedelta(days=random.randint(0, delta))

def _dia_semana_pt(d: date) -> str:
    return DIAS_SEMANA_PT[d.weekday()]

spark.udf.register("gerar_data",    _gerar_data_aleatoria, DateType())
spark.udf.register("dia_semana_pt", _dia_semana_pt,         StringType())

# ============================================
# HELPER — lê uma tabela do SQL Server e
# registra como view temporária do Spark.
#
# createOrReplaceTempView() expõe o DataFrame
# como uma "tabela" acessível por spark.sql().
# A view vive apenas na sessão Spark atual —
# não persiste em disco nem no banco.
#
# O particionamento por coluna numérica é
# mantido para tabelas maiores: cada worker
# lê um intervalo de IDs em paralelo via JDBC.
# ============================================
def registrar_view(jdbc_url: str, tabela: str, view: str,
                   coluna_particao: str = None,
                   lower: int = None, upper: int = None) -> None:

    if coluna_particao and lower is not None and upper is not None:
        df = spark.read.jdbc(
            url=jdbc_url,
            table=tabela,
            column=coluna_particao,
            lowerBound=lower,
            upperBound=upper,
            numPartitions=4,
            properties=JDBC_PROPS,
        )
    else:
        df = spark.read.jdbc(
            url=jdbc_url,
            table=tabela,
            properties=JDBC_PROPS,
        )

    df.createOrReplaceTempView(view)

# ============================================
# HELPER — escreve o resultado de uma query
# SQL diretamente no SQL Server via JDBC.
#
# spark.sql() retorna um DataFrame — que pode
# ser encadeado direto com .write.jdbc().
# mode="append" nunca recria a tabela,
# apenas insere os dados novos.
# ============================================
def escrever_sql(query: str, jdbc_url: str, tabela: str,
                 mode: str = "append") -> None:
    (
        spark.sql(query)
        .write
        .jdbc(
            url=jdbc_url,
            table=tabela,
            mode=mode,
            properties=JDBC_PROPS,
        )
    )

# ============================================
# EXTRACT
#
# Em vez de retornar DataFrames, cada tabela
# é registrada como uma view temporária.
# O resto do pipeline referencia essas views
# diretamente nas queries SQL — sem precisar
# passar variáveis entre funções.
# ============================================
def extrair() -> None:
    print("\n" + "=" * 50)
    print("🔄 EXTRACT — lendo gym_db e registrando views...")

    registrar_view(JDBC_URL_TRANSACIONAL, "dbo.Aluno",         "aluno")
    registrar_view(JDBC_URL_TRANSACIONAL, "dbo.Treino",        "treino",
                   coluna_particao="ID_Treino", lower=1, upper=300)
    registrar_view(JDBC_URL_TRANSACIONAL, "dbo.Produto",       "produto",
                   coluna_particao="ID_Produto", lower=1, upper=20)
    registrar_view(JDBC_URL_TRANSACIONAL, "dbo.Produto_Aluno", "produto_aluno")

    print(f"   ✅ aluno:         {spark.sql('SELECT COUNT(*) AS n FROM aluno').first().n} registros")
    print(f"   ✅ treino:        {spark.sql('SELECT COUNT(*) AS n FROM treino').first().n} registros")
    print(f"   ✅ produto:       {spark.sql('SELECT COUNT(*) AS n FROM produto').first().n} registros")
    print(f"   ✅ produto_aluno: {spark.sql('SELECT COUNT(*) AS n FROM produto_aluno').first().n} registros")

# ============================================
# TRANSFORM
#
# Cada dimensão e a fato são construídas
# inteiramente em SQL via spark.sql().
# As views intermediárias (vendas, sk_*)
# são registradas para que queries posteriores
# possam referenciá-las como se fossem tabelas.
# ============================================
def transformar() -> None:
    print("\n" + "=" * 50)
    print("🔄 TRANSFORM — montando dimensões e fato em SQL...")

    # ------------------------------------------
    # Dim_Aluno
    #
    # Uso de Window function
    # ------------------------------------------
    escrever_sql("""
        SELECT
            a.CPF_Aluno,
            a.Nome_Plano,
            a.CPF_Personal,
            COUNT(COALESCE(t.Quantia_Treinos, 0)) AS Quantia_Treinos
        FROM aluno a
        LEFT JOIN treino t ON a.CPF_Aluno = t.CPF_Aluno
    """, JDBC_URL_DIMENSIONAL, "dbo.Dim_Aluno")
    print(f"   ✅ Dim_Aluno inserida")

    # ------------------------------------------
    # Dim_Produto
    #
    # Projeção simples — apenas seleciona as
    # colunas necessárias para o DW.
    # ------------------------------------------
    escrever_sql("""
        SELECT
            ID_Produto,
            Nome_Produto,
            Preco_Unitario
        FROM produto
    """, JDBC_URL_DIMENSIONAL, "dbo.Dim_Produto")
    print(f"   ✅ Dim_Produto inserida")

    # ------------------------------------------
    # Staging de vendas com datas sintéticas
    #
    # gerar_data() é a UDF registrada no topo.
    # A view "vendas" é usada tanto para a
    # Dim_Data quanto para a Fato_Venda.
    # ------------------------------------------
    spark.sql("""
        SELECT
            ID_Produto,
            CPF_Aluno,
            Quantidade_Comprada,
            gerar_data() AS Data_Compra
        FROM produto_aluno
    """).createOrReplaceTempView("vendas")

    # ------------------------------------------
    # Dim_Data
    #
    # DISTINCT para pegar apenas datas únicas.
    # YEAR/MONTH/DAY são funções SQL nativas
    # do Spark — sem UDF, sem pandas.
    # dia_semana_pt() é a UDF registrada.
    # ------------------------------------------
    escrever_sql("""
        SELECT DISTINCT
            Data_Compra                AS Data,
            YEAR(Data_Compra)          AS Ano,
            MONTH(Data_Compra)         AS Mes,
            DAY(Data_Compra)           AS Dia,
            dia_semana_pt(Data_Compra) AS Dia_Semana
        FROM vendas
    """, JDBC_URL_DIMENSIONAL, "dbo.Dim_Data")
    print(f"   ✅ Dim_Data inserida")

    # ------------------------------------------
    # Lê os SKs gerados pelo IDENTITY do DW
    # e registra como views para o JOIN final.
    #
    # É necessário ler do gym_dw porque os SKs
    # são gerados pelo banco após o insert —
    # o Spark não os conhece antes da escrita.
    # ------------------------------------------
    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Dim_Aluno",   "sk_aluno")
    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Dim_Produto",  "sk_produto")
    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Dim_Data",     "sk_data")

    # ------------------------------------------
    # Fato_Venda
    #
    # JOIN do staging com os SKs para trocar
    # as chaves naturais (CPF, ID) pelas
    # surrogate keys do DW.
    #
    # CAST(Data_Compra AS DATE) garante que o
    # tipo bate com a coluna Data do sk_data,
    # mesmo que o JDBC traga como TIMESTAMP.
    #
    # WHERE ... IS NOT NULL substitui o
    # .dropna() — descarta registros órfãos
    # onde algum SK não foi encontrado.
    # ------------------------------------------
    escrever_sql("""
        SELECT
            CAST(p.SK_Produto          AS INT) AS SK_Produto,
            CAST(a.SK_Aluno            AS INT) AS SK_Aluno,
            CAST(d.SK_Data             AS INT) AS SK_Data,
            CAST(v.Quantidade_Comprada AS INT) AS Quantia_Comprada
        FROM vendas v
        LEFT JOIN sk_aluno   a ON v.CPF_Aluno              = a.CPF_Aluno
        LEFT JOIN sk_produto p ON v.ID_Produto              = p.ID_Produto
        LEFT JOIN sk_data    d ON CAST(v.Data_Compra AS DATE) = d.Data
        WHERE
            a.SK_Aluno   IS NOT NULL
            AND p.SK_Produto IS NOT NULL
            AND d.SK_Data    IS NOT NULL
    """, JDBC_URL_DIMENSIONAL, "dbo.Fato_Venda")
    print(f"   ✅ Fato_Venda inserida")

# ============================================
# LOAD
#
# Nessa versão SQL o load já acontece dentro
# do transformar() via escrever_sql().
# Esta função existe apenas para manter a
# interface do pipeline e emitir o log final.
# ============================================
def carregar() -> None:
    print("\n" + "=" * 50)
    print("✅ Carga no gym_dw concluída!")
    print("   (escrita realizada dentro do transformar via escrever_sql)")

# ============================================
# VALIDAR
#
# Registra as tabelas do DW como views e
# exibe o resultado em SQL puro.
# ============================================
def validar() -> None:
    print("\n" + "=" * 50)
    print("🔄 VALIDAR — conferindo Fato_Venda no gym_dw...")

    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Fato_Venda",  "fato")
    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Dim_Aluno",   "dim_aluno")
    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Dim_Produto",  "dim_produto")
    registrar_view(JDBC_URL_DIMENSIONAL, "dbo.Dim_Data",     "dim_data")

    print("\n📊 Fato_Venda — SKs brutos (TOP 20):")
    spark.sql("SELECT * FROM fato LIMIT 20").show(truncate=False)

    print("\n📊 Fato_Venda — Dados legíveis (TOP 20):")
    spark.sql("""
        SELECT
            f.SK_Fato,
            p.ID_Produto,
            p.Nome_Produto,
            a.CPF_Aluno,
            d.Data,
            d.Dia_Semana,
            f.Quantia_Comprada
        FROM fato f
        LEFT JOIN dim_produto p ON f.SK_Produto = p.SK_Produto
        LEFT JOIN dim_aluno   a ON f.SK_Aluno   = a.SK_Aluno
        LEFT JOIN dim_data    d ON f.SK_Data     = d.SK_Data
        LIMIT 20
    """).show(truncate=False)

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    try:
        extrair()
        transformar()
        carregar()
        validar()

        print("\n" + "=" * 50)
        print("🎉 ETL Spark SQL executado com sucesso!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        raise
    finally:
        spark.stop()
        print("\n🔒 SparkSession encerrada")