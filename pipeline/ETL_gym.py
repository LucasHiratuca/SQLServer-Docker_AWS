import pandas as pd
import pyodbc
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# ============================================
# Conexão
# ============================================
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost,1433;"
    "Database=gym_db;"
    "UID=sa;"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
conn.autocommit = True
cursor = conn.cursor()

# ============================================
# EXTRACT
# ============================================
def extrair_todas_tabelas():
    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho_completo = f"pipeline/extractions/extract_data_{data_atual}"
    os.makedirs(caminho_completo, exist_ok=True)
    print(f"📁 Criando pasta: {caminho_completo}")

    query_tabelas = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """

    tabelas = pd.read_sql(query_tabelas, conn)
    print(f"\nEncontradas {len(tabelas)} tabelas:")
    print("-" * 50)

    for index, row in tabelas.iterrows():
        nome_tabela = row['TABLE_NAME']
        try:
            print(f"\n📥 Exportando: {nome_tabela}")
            df = pd.read_sql(f"SELECT * FROM [{nome_tabela}]", conn)
            arquivo_csv = f"{caminho_completo}/{nome_tabela}.csv"
            df.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
            print(f"   ✅ {len(df)} registros salvos")
            print(f"   📄 {arquivo_csv}")
        except Exception as e:
            print(f"   ❌ Erro na tabela {nome_tabela}: {e}")

    print("\n" + "=" * 50)
    print(f"✅ Extração concluída!")
    print(f"📁 Arquivos salvos em: {caminho_completo}")

# ============================================
# TRANSFORM
# ============================================
def transformar():
    print("\n" + "=" * 50)
    print("🔄 Iniciando transformações...")

    cursor.execute("USE gym_dw")

    # ----------------------------------------
    # Ranking de alunos mais ativos
    # (por número de treinos registrados)
    # ----------------------------------------
    cursor.execute("""
        IF OBJECT_ID('transform_ranking_alunos', 'U') IS NOT NULL
            DROP TABLE transform_ranking_alunos

        SELECT
            a.CPF_Aluno,
            a.Nome_Aluno,
            a.Nome_Plano,
            COUNT(t.ID_Treino)                                          AS Total_Treinos,
            DENSE_RANK() OVER (ORDER BY COUNT(t.ID_Treino) DESC)        AS Ranking
        INTO gym_dw.dbo.transform_ranking_alunos
        FROM gym_db.dbo.Treino t
        JOIN gym_db.dbo.Aluno  a ON t.CPF_Aluno = a.CPF_Aluno
        GROUP BY a.CPF_Aluno, a.Nome_Aluno, a.Nome_Plano
    """)
    print(f"✅ transform_ranking_alunos: {cursor.rowcount} registros")

    # ----------------------------------------
    # Ranking de exercícios mais realizados
    # por alunos, com média de carga e reps
    # ----------------------------------------
    cursor.execute("""
        IF OBJECT_ID('transform_ranking_exercicios', 'U') IS NOT NULL
            DROP TABLE transform_ranking_exercicios

        SELECT
            e.Nome_Exercicio,
            e.Parte_Trabalhada,
            COUNT(*)                                                     AS Total_Execucoes,
            AVG(te.Carga)                                                AS Carga_Media,
            AVG(te.Reps)                                                 AS Reps_Media,
            MAX(te.Carga)                                                AS Carga_Maxima,
            DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)                   AS Ranking
        INTO gym_dw.dbo.transform_ranking_exercicios
        FROM gym_db.dbo.Treino_Exercicio te
        JOIN gym_db.dbo.Exercicio        e  ON te.Nome_Exercicio = e.Nome_Exercicio
        GROUP BY e.Nome_Exercicio, e.Parte_Trabalhada
    """)
    print(f"✅ transform_ranking_exercicios: {cursor.rowcount} registros")

    # ----------------------------------------
    # Ranking de partes do corpo mais treinadas
    # agrupando todos os exercícios por região
    # ----------------------------------------
    cursor.execute("""
        IF OBJECT_ID('transform_ranking_partes', 'U') IS NOT NULL
            DROP TABLE transform_ranking_partes

        SELECT
            e.Parte_Trabalhada,
            COUNT(*)                                                     AS Total_Execucoes,
            COUNT(DISTINCT te.ID_Treino)                                 AS Total_Treinos,
            AVG(te.Carga)                                                AS Carga_Media,
            DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)                   AS Ranking
        INTO gym_dw.dbo.transform_ranking_partes
        FROM gym_db.dbo.Treino_Exercicio te
        JOIN gym_db.dbo.Exercicio        e  ON te.Nome_Exercicio = e.Nome_Exercicio
        GROUP BY e.Parte_Trabalhada
    """)
    print(f"✅ transform_ranking_partes: {cursor.rowcount} registros")

    # ----------------------------------------
    # Evolução de treinos por mês
    # permite ver sazonalidade e engajamento
    # ----------------------------------------
    cursor.execute("""
        IF OBJECT_ID('transform_treinos_por_mes', 'U') IS NOT NULL
            DROP TABLE transform_treinos_por_mes

        SELECT
            YEAR(t.Data_Criacao)                                         AS Ano,
            MONTH(t.Data_Criacao)                                        AS Mes,
            COUNT(DISTINCT t.ID_Treino)                                  AS Total_Treinos,
            COUNT(DISTINCT t.CPF_Aluno)                                  AS Alunos_Ativos,
            SUM(COUNT(DISTINCT t.ID_Treino)) OVER (
                ORDER BY YEAR(t.Data_Criacao), MONTH(t.Data_Criacao)
            )                                                            AS Treinos_Acumulados
        INTO gym_dw.dbo.transform_treinos_por_mes
        FROM gym_db.dbo.Treino t
        GROUP BY YEAR(t.Data_Criacao), MONTH(t.Data_Criacao)
    """)
    print(f"✅ transform_treinos_por_mes: {cursor.rowcount} registros")

    # ----------------------------------------
    # Perfil de treino por plano
    # mostra se planos mais caros treinam mais
    # ----------------------------------------
    cursor.execute("""
        IF OBJECT_ID('transform_treino_por_plano', 'U') IS NOT NULL
            DROP TABLE transform_treino_por_plano

        SELECT
            a.Nome_Plano,
            COUNT(DISTINCT a.CPF_Aluno)                                  AS Total_Alunos,
            COUNT(t.ID_Treino)                                           AS Total_Treinos,
            CAST(COUNT(t.ID_Treino) AS DECIMAL(10,2)) /
                NULLIF(COUNT(DISTINCT a.CPF_Aluno), 0)                   AS Media_Treinos_Por_Aluno
        INTO gym_dw.dbo.transform_treino_por_plano
        FROM gym_db.dbo.Aluno  a
        LEFT JOIN gym_db.dbo.Treino t ON a.CPF_Aluno = t.CPF_Aluno
        GROUP BY a.Nome_Plano
    """)
    print(f"✅ transform_treino_por_plano: {cursor.rowcount} registros")

    print("✅ Transformações concluídas!")

# ============================================
# LOAD
# ============================================
def carregar_dw():
    print("\n" + "=" * 50)
    print("🔄 Iniciando carga no gym_dw...")

    # Cria o banco dimensional se não existir
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'gym_dw')
        CREATE DATABASE gym_dw
    """)
    print("✅ Banco gym_dw verificado/criado")

    cursor.execute("USE gym_dw")

    # ----------------------------------------
    # Aqui você vai adicionar as suas tabelas
    # do Star Schema após modelar.
    # Exemplo da estrutura esperada:
    #
    # cursor.execute("""
    #     IF OBJECT_ID('dim_aluno', 'U') IS NULL
    #     CREATE TABLE dim_aluno (
    #         SK_Aluno   INT IDENTITY NOT NULL,
    #         ...
    #         CONSTRAINT PK_dim_aluno PRIMARY KEY (SK_Aluno)
    #     )
    # """)
    #
    # cursor.execute("""
    #     INSERT INTO gym_dw.dbo.dim_aluno (...)
    #     SELECT ... FROM gym_db.dbo.Aluno
    #     WHERE NOT EXISTS (...)
    # """)
    # ----------------------------------------

    print("✅ Carga concluída!")

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    try:
        extrair_todas_tabelas()
        carregar_dw()
        transformar()
    finally:
        cursor.close()
        conn.close()
        print("\n🔒 Conexão encerrada")