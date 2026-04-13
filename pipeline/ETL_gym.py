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
    "UID=sa;"                          
    f"PWD={os.getenv('DB_PASSWORD')};" 
    "TrustServerCertificate=yes;"
)

def extrair_todas_tabelas():
    # Criar pasta para os CSVs
    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho_completo = f"pipeline/extractions/extract_{data_atual}"  # ← Guarda o caminho completo
    
    # Criar a pasta
    os.makedirs(caminho_completo, exist_ok=True)
    print(f"📁 Criando pasta: {caminho_completo}")
    
    # 1. Buscar lista de todas as tabelas do banco
    query_tabelas = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """
    
    tabelas = pd.read_sql(query_tabelas, conn)
    
    print(f"\nEncontradas {len(tabelas)} tabelas:")
    print("-" * 50)
    
    # 2. Para cada tabela, extrair e salvar
    for index, row in tabelas.iterrows():
        nome_tabela = row['TABLE_NAME']
        
        try:
            print(f"\n📥 Exportando: {nome_tabela}")
            
            # Extrair dados da tabela
            df = pd.read_sql(f"SELECT * FROM [{nome_tabela}]", conn)
            
            # Salvar como CSV - USANDO O CAMINHO COMPLETO
            arquivo_csv = f"{caminho_completo}/{nome_tabela}.csv"  # ← Corrigido!
            df.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
            
            print(f"   ✅ {len(df)} registros salvos")
            print(f"   📄 {arquivo_csv}")
            
        except Exception as e:
            print(f"   ❌ Erro na tabela {nome_tabela}: {e}")
    
    print("\n" + "="*50)
    print(f"✅ Exportação concluída!")
    print(f"📁 Arquivos salvos em: {caminho_completo}")
    
    conn.close()

# Executar
if __name__ == "__main__":
    extrair_todas_tabelas()