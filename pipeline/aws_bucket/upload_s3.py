import pandas as pd
import pyodbc
import boto3
import os
import io
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Configurações
# ============================================
BUCKET_NAME = os.getenv("AWS_BUCKET")
PASTA_S3    = "gym_dw/fato_venda"  # pasta fixa — sobrescreve a cada execução

# ============================================
# Conexão — gym_dw (dimensional)
# ============================================
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost,1433;"
    "Database=gym_dw;"
    "UID=sa;"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)

# ============================================
# HELPERS
# ============================================
def df_para_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Converte DataFrame para bytes CSV em memória.
    Evita salvar arquivo local antes de subir —
    o upload vai direto do DataFrame para o S3.
    """
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding='utf-8-sig')
    return buffer.getvalue().encode('utf-8-sig')

def upload_s3(s3_client, dados: bytes, nome_arquivo: str):
    """
    Faz upload de bytes para o bucket S3 na pasta fixa.
    A chave (caminho) é sempre a mesma — sobrescreve
    o arquivo anterior a cada execução.
    """
    chave = f"{PASTA_S3}/{nome_arquivo}"
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=chave,
        Body=dados,
        ContentType='text/csv'
    )
    print(f"   ✅ s3://{BUCKET_NAME}/{chave}")

# ============================================
# EXTRACT — lê os dois SELECTs da Fato_Venda
# ============================================
def extrair_fato_venda():
    print("🔄 Extraindo dados da Fato_Venda...")

    # SELECT 1 — SKs brutos
    # Replica o primeiro SELECT da função transformar() do ETL
    df_sk = pd.read_sql("""
        SELECT
            SK_Fato,
            SK_Produto,
            SK_Aluno,
            SK_Data,
            Quantia_Comprada
        FROM Fato_Venda
    """, conn)
    print(f"   ✅ fato_venda_sks: {len(df_sk)} registros")

    # SELECT 2 — dados legíveis com JOIN nas dimensões
    # Replica o segundo SELECT da função transformar() do ETL
    df_completo = pd.read_sql("""
        SELECT
            f.SK_Fato,
            p.ID_Produto,
            p.Nome_Produto,
            p.Preco_Unitario,
            a.CPF_Aluno,
            a.Nome_Plano,
            a.Quantia_Treinos,
            d.Data,
            d.Ano,
            d.Mes,
            d.Dia,
            d.Dia_Semana,
            f.Quantia_Comprada,
            f.Quantia_Comprada * p.Preco_Unitario AS Total_Venda
        FROM Fato_Venda f
        JOIN Dim_Produto p ON f.SK_Produto = p.SK_Produto
        JOIN Dim_Aluno   a ON f.SK_Aluno   = a.SK_Aluno
        JOIN Dim_Data    d ON f.SK_Data    = d.SK_Data
    """, conn)
    print(f"   ✅ fato_venda_completo: {len(df_completo)} registros")

    return df_sk, df_completo

# ============================================
# LOAD — sobe os CSVs para o S3
# ============================================
def subir_para_s3(df_sk: pd.DataFrame, df_completo: pd.DataFrame):
    print(f"\n🔄 Iniciando upload para s3://{BUCKET_NAME}/{PASTA_S3}/")

    # Credenciais lidas automaticamente de ~/.aws/credentials
    # ou das variáveis de ambiente AWS_ACCESS_KEY_ID /
    # AWS_SECRET_ACCESS_KEY se configuradas no .env
    s3 = boto3.client(
        's3',
        region_name=os.getenv("AWS_REGION", "sa-east-1")
    )

    upload_s3(s3, df_para_csv_bytes(df_sk),       "fato_venda_sks.csv")
    upload_s3(s3, df_para_csv_bytes(df_completo), "fato_venda_completo.csv")

    print(f"\n✅ Upload concluído — 2 arquivos em s3://{BUCKET_NAME}/{PASTA_S3}/")
    print(f"   📄 fato_venda_sks.csv")
    print(f"   📄 fato_venda_completo.csv")

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    try:
        df_sk, df_completo = extrair_fato_venda()
        subir_para_s3(df_sk, df_completo)
        print("\n🎉 upload_s3.py executado com sucesso!")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    finally:
        conn.close()
        print("🔒 Conexão encerrada")