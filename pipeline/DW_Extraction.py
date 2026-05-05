"""
gym_dw Export
=============
Extrai todas as tabelas do gym_dw e gera:
- Um CSV por tabela (Dim_Data, Dim_Aluno, Dim_Produto, Fato_Venda)
- Um CSV analítico com a Fato_Venda já com os JOINs resolvidos

Uso:
    python export_dw.py
    python export_dw.py --output pasta_saida/
"""

import pandas as pd
import pyodbc
import os
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Conexão — gym_dw
# ============================================
conn = pyodbc.connect(
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost,1433;"
    "Database=gym_dw;"
    "UID=sa;"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
print("✅ Conectado ao gym_dw")


# ============================================
# 1. EXTRAÇÃO INDIVIDUAL — uma tabela por CSV
# ============================================
def exportar_tabelas(pasta: str):
    tabelas = ["Dim_Data", "Dim_Aluno", "Dim_Produto", "Fato_Venda"]

    print(f"\n📂 Exportando tabelas para: {pasta}")
    print("-" * 50)

    for tabela in tabelas:
        try:
            df = pd.read_sql(f"SELECT * FROM {tabela}", conn)
            arquivo = os.path.join(pasta, f"{tabela}.csv")
            df.to_csv(arquivo, index=False, encoding="utf-8-sig")
            print(f"   ✅ {tabela}: {len(df)} registros → {arquivo}")
        except Exception as e:
            print(f"   ❌ Erro em {tabela}: {e}")


# ============================================
# 2. EXTRAÇÃO ANALÍTICA — Fato com JOINs
# Resolve todas as SKs e entrega um CSV flat
# pronto para análise ou dashboard
# ============================================
def exportar_analitico(pasta: str):
    query = """
        SELECT
            fv.SK_Venda,
            fv.Quantia_Comprada,

            -- Dim_Produto
            dp.ID_Produto,
            dp.Nome_Produto,
            dp.Preco_Unitario,
            fv.Quantia_Comprada * dp.Preco_Unitario   AS Valor_Total,

            -- Dim_Aluno
            da.CPF_Aluno,
            da.Nome_Plano,
            da.CPF_Personal,
            da.Quantia_Treinos,

            -- Dim_Data
            dd.Data,
            dd.Ano,
            dd.Mes,
            dd.Dia,
            dd.Dia_Semana

        FROM Fato_Venda     fv
        JOIN Dim_Produto    dp ON fv.SK_Produto = dp.SK_Produto
        JOIN Dim_Aluno      da ON fv.SK_Aluno   = da.SK_Aluno
        JOIN Dim_Data       dd ON fv.SK_Data    = dd.SK_Data
        ORDER BY dd.Data, fv.SK_Venda
    """

    try:
        df = pd.read_sql(query, conn)

        # Garante que Data é datetime
        df["Data"] = pd.to_datetime(df["Data"])

        arquivo = os.path.join(pasta, "fato_venda_analitico.csv")
        df.to_csv(arquivo, index=False, encoding="utf-8-sig")

        print(f"\n📊 CSV analítico gerado: {arquivo}")
        print(f"   Registros:     {len(df)}")
        print(f"   Colunas:       {list(df.columns)}")
        print(f"   Receita total: R$ {df['Valor_Total'].sum():,.2f}")
        print(f"   Período:       {df['Data'].min().date()} → {df['Data'].max().date()}")

        return df

    except Exception as e:
        print(f"❌ Erro na extração analítica: {e}")
        return None


# ============================================
# 3. RESUMO — métricas por dimensão
# ============================================
def exportar_resumos(df_analitico: pd.DataFrame, pasta: str):
    if df_analitico is None:
        return

    print("\n📋 Gerando resumos...")

    # Vendas por produto
    por_produto = (
        df_analitico
        .groupby(["ID_Produto", "Nome_Produto", "Preco_Unitario"])
        .agg(
            Qtd_Vendida    = ("Quantia_Comprada", "sum"),
            Receita_Total  = ("Valor_Total",      "sum"),
            Num_Transacoes = ("SK_Venda",          "count")
        )
        .reset_index()
        .sort_values("Receita_Total", ascending=False)
    )
    arquivo = os.path.join(pasta, "resumo_por_produto.csv")
    por_produto.to_csv(arquivo, index=False, encoding="utf-8-sig")
    print(f"   ✅ resumo_por_produto.csv — {len(por_produto)} produtos")

    # Vendas por plano
    por_plano = (
        df_analitico
        .groupby("Nome_Plano")
        .agg(
            Num_Alunos     = ("CPF_Aluno",        "nunique"),
            Qtd_Vendida    = ("Quantia_Comprada", "sum"),
            Receita_Total  = ("Valor_Total",      "sum"),
            Media_Treinos  = ("Quantia_Treinos",  "mean")
        )
        .reset_index()
        .sort_values("Receita_Total", ascending=False)
    )
    arquivo = os.path.join(pasta, "resumo_por_plano.csv")
    por_plano.to_csv(arquivo, index=False, encoding="utf-8-sig")
    print(f"   ✅ resumo_por_plano.csv — {len(por_plano)} planos")

    # Vendas por mês
    por_mes = (
        df_analitico
        .groupby(["Ano", "Mes"])
        .agg(
            Qtd_Vendida    = ("Quantia_Comprada", "sum"),
            Receita_Total  = ("Valor_Total",      "sum"),
            Num_Transacoes = ("SK_Venda",          "count")
        )
        .reset_index()
        .sort_values(["Ano", "Mes"])
    )
    por_mes["Receita_Acumulada"] = por_mes["Receita_Total"].cumsum()
    arquivo = os.path.join(pasta, "resumo_por_mes.csv")
    por_mes.to_csv(arquivo, index=False, encoding="utf-8-sig")
    print(f"   ✅ resumo_por_mes.csv — {len(por_mes)} meses")

    # Vendas por dia da semana
    por_dia_semana = (
        df_analitico
        .groupby("Dia_Semana")
        .agg(
            Qtd_Vendida   = ("Quantia_Comprada", "sum"),
            Receita_Total = ("Valor_Total",      "sum")
        )
        .reset_index()
        .sort_values("Receita_Total", ascending=False)
    )
    arquivo = os.path.join(pasta, "resumo_por_dia_semana.csv")
    por_dia_semana.to_csv(arquivo, index=False, encoding="utf-8-sig")
    print(f"   ✅ resumo_por_dia_semana.csv — {len(por_dia_semana)} dias")


# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exporta gym_dw para CSVs")
    parser.add_argument("--output", default=None, help="Pasta de saída")
    args = parser.parse_args()

    # Pasta com timestamp
    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"dw_export_{ts}"

    Path(args.output).mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 50)
    print("🚀 Exportando gym_dw")
    print("=" * 50)

    exportar_tabelas(args.output)
    df_analitico = exportar_analitico(args.output)
    exportar_resumos(df_analitico, args.output)

    conn.close()

    print(f"\n✅ Exportação concluída!")
    print(f"📁 Arquivos em: {args.output}/")
    print(f"""
   Dim_Data.csv
   Dim_Aluno.csv
   Dim_Produto.csv
   Fato_Venda.csv
   fato_venda_analitico.csv
   resumo_por_produto.csv
   resumo_por_plano.csv
   resumo_por_mes.csv
   resumo_por_dia_semana.csv
    """)