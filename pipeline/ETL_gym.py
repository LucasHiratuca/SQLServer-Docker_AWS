import pandas as pd
import pyodbc
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configuração da conexão
conn = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost,1433;"           
    "Database=gym_db;"                 
    "UID=sa;"                          # ← Usuário padrão do SQL Server no Docker
    f"PWD={os.getenv('DB_PASSWORD')};" # ← Pega a senha do .env
    "TrustServerCertificate=yes;"
)

def extrair_todas_tabelas():
    # Criar pasta para os CSVs
    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta_saida = f"extract_data_{data_atual}"
    os.makedirs(f"pipeline/extractions/{pasta_saida}", exist_ok=True)
    
    # 1. Buscar lista de todas as tabelas do banco
    query_tabelas = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """
    
    tabelas = pd.read_sql(query_tabelas, conn)
    
    print(f"Encontradas {len(tabelas)} tabelas:")
    print("-" * 50)
    
    # 2. Para cada tabela, extrair e salvar
    for index, row in tabelas.iterrows():
        nome_tabela = row['TABLE_NAME']
        
        try:
            print(f"\n📥 Exportando: {nome_tabela}")
            
            # Extrair dados da tabela
            df = pd.read_sql(f"SELECT * FROM [{nome_tabela}]", conn)
            
            # Salvar como CSV
            arquivo_csv = f"{pasta_saida}/{nome_tabela}.csv"
            df.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
            
            print(f"   ✅ {len(df)} registros salvos em {arquivo_csv}")
            
        except Exception as e:
            print(f"   ❌ Erro na tabela {nome_tabela}: {e}")
    
    print("\n" + "="*50)
    print(f"✅ Exportação concluída! Arquivos salvos em: {pasta_saida}")
    
    conn.close()

# Executar
extrair_todas_tabelas()