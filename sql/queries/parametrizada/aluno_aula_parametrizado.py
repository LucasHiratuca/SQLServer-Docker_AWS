import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Conexão com SQL Server
# ============================================
conn = pyodbc.connect(
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost,1433;"
    "Database=gym_db;"
    "UID=sa;"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
cursor = conn.cursor()

# ============================================
# BLOCO 1 - CONSULTA POR ALUNO
# ============================================
print("\n" + "="*60)
print("🔍 CONSULTA POR ALUNO")
print("="*60)

nome_aluno = input("Digite o nome do aluno: ").strip()

query_aluno = """
    SELECT 
        au.Nome_Aula,
        al.Nome_Aluno,
        p.Nome AS Nome_Professor
    FROM Aluno_Aula aa
    JOIN Aluno al ON al.CPF_Aluno = aa.CPF_Aluno
    JOIN Aula au ON au.Nome_Aula = aa.Nome_Aula
    JOIN Professor p ON p.CPF_Professor = au.CPF_Professor
    WHERE al.Nome_Aluno LIKE ?
"""

cursor.execute(query_aluno, f"%{nome_aluno}%")
resultados_aluno = cursor.fetchall()

print(f"\n📚 AULAS DO ALUNO: {nome_aluno}")
print("-" * 50)
print(f"{'Aula':<30} {'Professor':<25}")
print("-" * 50)

if resultados_aluno:
    for row in resultados_aluno:
        print(f"{row.Nome_Aula:<30} {row.Nome_Professor:<25}")
    print("-" * 50)
    print(f"Total: {len(resultados_aluno)} aulas")
else:
    print("❌ Nenhuma aula encontrada")
print("="*60)


# ============================================
# BLOCO 2 - CONSULTA POR AULA
# ============================================
print("\n" + "="*60)
print("🔍 CONSULTA POR AULA")
print("="*60)

nome_aula = input("Digite o nome da aula: ").strip()

query_aula = """
    SELECT 
        au.Nome_Aula,
        al.Nome_Aluno,
        p.Nome AS Nome_Professor
    FROM Aluno_Aula aa
    JOIN Aluno al ON al.CPF_Aluno = aa.CPF_Aluno
    JOIN Aula au ON au.Nome_Aula = aa.Nome_Aula
    JOIN Professor p ON p.CPF_Professor = au.CPF_Professor
    WHERE au.Nome_Aula LIKE ?
"""

cursor.execute(query_aula, f"%{nome_aula}%")
resultados_aula = cursor.fetchall()

print(f"\n🏋️ ALUNOS DA AULA: {nome_aula}")
print("-" * 50)
print(f"{'Aluno':<30} {'Professor':<25}")
print("-" * 50)

if resultados_aula:
    professor = resultados_aula[0].Nome_Professor
    for row in resultados_aula:
        print(f"{row.Nome_Aluno:<30} {row.Nome_Professor:<25}")
    print("-" * 50)
    print(f"Professor: {professor}")
    print(f"Total: {len(resultados_aula)} alunos")
else:
    print("❌ Nenhum aluno encontrado")
print("="*60)

# ============================================
# Fechar conexão
# ============================================
cursor.close()
conn.close()
print("\n🔒 Conexão encerrada")