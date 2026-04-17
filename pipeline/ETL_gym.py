import pandas as pd
import pyodbc
import os
import random
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Conexão — gym_db (transacional)
# ============================================
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost,1433;"
    "Database=gym_db;"
    "UID=sa;"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
cursor = conn.cursor()
cursor.fast_executemany = True

# Variável global para guardar o caminho do snapshot atual
snapshot_atual = None

# ============================================
# EXTRACT
# Exporta todas as tabelas do gym_db como CSV
# com timestamp, criando snapshot por execução
# ============================================
def extrair_todas_tabelas():
    global snapshot_atual
    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_atual = f"extract_data_{data_atual}"
    caminho_completo = f"pipeline/extractions/{snapshot_atual}"
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

    for _, row in tabelas.iterrows():
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
# HELPERS — geração de datas sintéticas
# Usado porque Produto_Aluno não possui
# Data_Compra no banco transacional.
# Em produção, essa coluna existiria na fonte.
# ============================================
DIAS_SEMANA_PT = {
    'Monday':    'Segunda-feira',
    'Tuesday':   'Terça-feira',
    'Wednesday': 'Quarta-feira',
    'Thursday':  'Quinta-feira',
    'Friday':    'Sexta-feira',
    'Saturday':  'Sábado',
    'Sunday':    'Domingo',
}

def gerar_data_aleatoria():
    inicio = date(2024, 1, 1)
    fim    = date.today()
    delta  = (fim - inicio).days
    return inicio + timedelta(days=random.randint(0, delta))

def gerar_staging_vendas():
    """
    Lê Produto_Aluno do gym_db e atribui uma data
    aleatória por registro. Salva na pasta do snapshot
    atual para rastreabilidade.
    """
    df = pd.read_sql("""
        SELECT ID_Produto, CPF_Aluno, Quantidade_Comprada
        FROM gym_db.dbo.Produto_Aluno
    """, conn)

    df['Data_Compra'] = [gerar_data_aleatoria() for _ in range(len(df))]

    caminho_snapshot = f"pipeline/extractions/{snapshot_atual}"
    os.makedirs(caminho_snapshot, exist_ok=True)
    df.to_csv(f'{caminho_snapshot}/staging_vendas.csv', index=False)
    print(f"✅ Staging de vendas gerado: {len(df)} registros")
    print(f"   📄 Salvo em: {caminho_snapshot}/staging_vendas.csv")
    return df

def criar_tabelas_dw():
    """
    Cria as tabelas do Star Schema no gym_dw
    se ainda não existirem. Permite reexecutar
    o ETL sem erro de tabela duplicada.
    """
    cursor.execute("USE gym_dw")

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Dim_Data')
        CREATE TABLE Dim_Data (
            SK_Data     INT IDENTITY(1,1) PRIMARY KEY,
            Data        DATE         NOT NULL,
            Ano         INT          NOT NULL,
            Mes         INT          NOT NULL,
            Dia         INT          NOT NULL,
            Dia_Semana  VARCHAR(20)  NOT NULL
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Dim_Aluno')
        CREATE TABLE Dim_Aluno (
            SK_Aluno        INT IDENTITY(1,1) PRIMARY KEY,
            CPF_Aluno       VARCHAR(14)  NOT NULL,
            Nome_Plano      VARCHAR(255) NULL,
            CPF_Personal    VARCHAR(14)  NULL,
            Quantia_Treinos INT          NULL
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Dim_Produto')
        CREATE TABLE Dim_Produto (
            SK_Produto      INT IDENTITY(1,1) PRIMARY KEY,
            ID_Produto      INT           NOT NULL,
            Nome_Produto    VARCHAR(255)  NULL,
            Preco_Unitario  DECIMAL(10,2) NULL
        )
    """)

    # Fato criada por último — depende das dimensões já existirem
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Fato_Venda')
        CREATE TABLE Fato_Venda (
            SK_Fato          INT IDENTITY(1,1) PRIMARY KEY,
            SK_Produto       INT NOT NULL,
            SK_Aluno         INT NOT NULL,
            SK_Data          INT NOT NULL,
            Quantia_Comprada INT NOT NULL,
            FOREIGN KEY (SK_Produto) REFERENCES Dim_Produto(SK_Produto),
            FOREIGN KEY (SK_Aluno)   REFERENCES Dim_Aluno(SK_Aluno),
            FOREIGN KEY (SK_Data)    REFERENCES Dim_Data(SK_Data)
        )
    """)

    conn.commit()
    print("✅ Esquema Star Schema verificado/criado")

# ============================================
# LOAD — Star Schema gym_dw
# Ordem obrigatória: dimensões antes da fato
# ============================================
def carregar_dw():
    print("\n" + "=" * 50)
    print("🔄 Iniciando carga no gym_dw...")

    # Garante que o banco dimensional existe
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'gym_dw')
        CREATE DATABASE gym_dw
    """)
    conn.commit()
    print("✅ Banco gym_dw verificado/criado")

    cursor.execute("USE gym_dw")
    criar_tabelas_dw()

    # Gera staging de vendas com datas sintéticas
    df_vendas = gerar_staging_vendas()
    df_vendas['Data_Compra'] = pd.to_datetime(df_vendas['Data_Compra'])

    # ------------------------------------------
    # Dim_Data
    # SELECT antes do INSERT evita duplicatas
    # em reexecuções sem precisar de constraint
    # ------------------------------------------
    datas_unicas       = df_vendas['Data_Compra'].dt.date.unique()
    dim_data_inseridos = 0

    for data in datas_unicas:
        ts            = pd.Timestamp(data)
        dia_semana_pt = DIAS_SEMANA_PT[ts.strftime('%A')]

        cursor.execute("SELECT 1 FROM Dim_Data WHERE Data = ?", ts.date())
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO Dim_Data (Data, Ano, Mes, Dia, Dia_Semana)
                VALUES (?, ?, ?, ?, ?)
            """, ts.date(), ts.year, ts.month, ts.day, dia_semana_pt)
            dim_data_inseridos += 1

    conn.commit()
    print(f"✅ Dim_Data: {dim_data_inseridos} novas datas inseridas "
          f"({len(datas_unicas)} únicas no staging)")

    # ------------------------------------------
    # Dim_Aluno
    # cursor.rowcount lê o rowcount após o
    # execute — correto para INSERT...SELECT
    # ------------------------------------------
    cursor.execute("""
        INSERT INTO Dim_Aluno (CPF_Aluno, Nome_Plano, CPF_Personal, Quantia_Treinos)
        SELECT
            a.CPF_Aluno,
            a.Nome_Plano,
            a.CPF_Personal,
            COUNT(t.ID_Treino) AS Quantia_Treinos
        FROM gym_db.dbo.Aluno a
        LEFT JOIN gym_db.dbo.Treino t ON a.CPF_Aluno = t.CPF_Aluno
        WHERE NOT EXISTS (
            SELECT 1 FROM Dim_Aluno da
            WHERE da.CPF_Aluno = a.CPF_Aluno
        )
        GROUP BY a.CPF_Aluno, a.Nome_Plano, a.CPF_Personal
    """)
    inseridos_alunos = cursor.rowcount
    conn.commit()
    print(f"✅ Dim_Aluno: {inseridos_alunos} registros inseridos")

    # ------------------------------------------
    # Dim_Produto
    # ------------------------------------------
    cursor.execute("""
        INSERT INTO Dim_Produto (ID_Produto, Nome_Produto, Preco_Unitario)
        SELECT
            p.ID_Produto,
            p.Nome_Produto,
            p.Preco_Unitario
        FROM gym_db.dbo.Produto p
        WHERE NOT EXISTS (
            SELECT 1 FROM Dim_Produto dp
            WHERE dp.ID_Produto = p.ID_Produto
        )
    """)
    inseridos_produtos = cursor.rowcount
    conn.commit()
    print(f"✅ Dim_Produto: {inseridos_produtos} registros inseridos")

    # ------------------------------------------
    # Fato_Venda — carregamento em lote
    #
    # 1. Carrega dimensões inteiras como DataFrame
    # 2. Monta dicionários de mapeamento em memória
    #    (chave_natural → SK)
    # 3. Aplica via .map() — equivalente a JOINs,
    #    mas sem roundtrip ao banco por linha
    # 4. dropna descarta linhas com SK ausente
    # 5. fast_executemany insere tudo em lote
    # ------------------------------------------
    df_produtos = pd.read_sql("SELECT ID_Produto, SK_Produto FROM Dim_Produto", conn)
    df_alunos   = pd.read_sql("SELECT CPF_Aluno,  SK_Aluno  FROM Dim_Aluno",   conn)
    df_datas    = pd.read_sql("SELECT Data,        SK_Data   FROM Dim_Data",    conn)

    map_produto = dict(zip(df_produtos['ID_Produto'], df_produtos['SK_Produto']))
    map_aluno   = dict(zip(df_alunos['CPF_Aluno'],    df_alunos['SK_Aluno']))
    map_data    = dict(zip(
        pd.to_datetime(df_datas['Data']).dt.date,
        df_datas['SK_Data']
    ))

    df_vendas['SK_Produto'] = df_vendas['ID_Produto'].map(map_produto)
    df_vendas['SK_Aluno']   = df_vendas['CPF_Aluno'].map(map_aluno)
    df_vendas['SK_Data']    = pd.to_datetime(df_vendas['Data_Compra']).dt.date.map(map_data)

    df_validas = df_vendas.dropna(subset=['SK_Produto', 'SK_Aluno', 'SK_Data'])
    ignorados  = len(df_vendas) - len(df_validas)

    print(f"\n📊 Estatísticas Fato_Venda:")
    print(f"   Total no staging:              {len(df_vendas)}")
    print(f"   Vendas válidas:                {len(df_validas)}")
    print(f"   Ignorados (SK não encontrado): {ignorados}")

    # Salva ignorados para análise se houver
    if ignorados > 0:
        df_ignorados    = df_vendas[df_vendas.isnull().any(axis=1)]
        caminho_snapshot = f"pipeline/extractions/{snapshot_atual}"
        df_ignorados.to_csv(f'{caminho_snapshot}/vendas_ignoradas.csv', index=False)
        print(f"   📁 Ignorados salvos em: {caminho_snapshot}/vendas_ignoradas.csv")

    dados_insert = [
        (
            int(row['SK_Produto']),
            int(row['SK_Aluno']),
            int(row['SK_Data']),
            int(row['Quantidade_Comprada'])
        )
        for _, row in df_validas.iterrows()
    ]

    if dados_insert:
        cursor.executemany("""
            INSERT INTO Fato_Venda (SK_Produto, SK_Aluno, SK_Data, Quantia_Comprada)
            VALUES (?, ?, ?, ?)
        """, dados_insert)
        conn.commit()
        print(f"✅ Fato_Venda: {len(df_validas)} registros inseridos em lote")
    else:
        print("⚠️ Nenhum registro válido para inserir na Fato_Venda")

    print("\n✅ Carga no gym_dw concluída!")

# ============================================
# TRANSFORM
# Valida o resultado do Load exibindo os dados
# da Fato_Venda com e sem joins nas dimensões
# ============================================
def transformar():
    cursor.execute("USE gym_dw")

    print("\n📊 Fato_Venda — SKs (TOP 20):")
    df_sk = pd.read_sql("""
        SELECT TOP 20
            SK_Fato,
            SK_Produto,
            SK_Aluno,
            SK_Data,
            Quantia_Comprada
        FROM Fato_Venda
    """, conn)
    print(df_sk.to_string())

    print("\n📊 Fato_Venda — Dados legíveis (TOP 20):")
    df_completo = pd.read_sql("""
        SELECT TOP 20
            f.SK_Fato,
            p.ID_Produto,
            p.Nome_Produto,
            a.CPF_Aluno,
            d.Data,
            d.Dia_Semana,
            f.Quantia_Comprada
        FROM Fato_Venda f
        JOIN Dim_Produto p ON f.SK_Produto = p.SK_Produto
        JOIN Dim_Aluno   a ON f.SK_Aluno   = a.SK_Aluno
        JOIN Dim_Data    d ON f.SK_Data    = d.SK_Data
    """, conn)
    print(df_completo.to_string())

# ============================================
# EXECUÇÃO
# Ordem: Extract → Load → Transform
# ============================================
if __name__ == "__main__":
    try:
        extrair_todas_tabelas()
        carregar_dw()
        transformar()
        print("\n" + "=" * 50)
        print("🎉 ETL executado com sucesso!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ ERRO durante a execução: {e}")
        conn.rollback()
        print("🔄 Rollback executado")
    finally:
        cursor.close()
        conn.close()
        print("\n🔒 Conexão encerrada")