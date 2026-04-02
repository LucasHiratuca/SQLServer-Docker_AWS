import pyodbc
from faker import Faker
from faker_br import *
import random
from datetime import date

fake = Faker('pt_BR')

# ============================================
# Conexão com o banco
# ============================================
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost,1433;'
    'DATABASE=gym_db;'
    'UID=sa;'
    'PWD=SuaSenhaForte123!'
)
cursor = conn.cursor()

# ============================================
# Plano
# ============================================
planos = [
    ('Basic',    30),
    ('Standard', 90),
    ('Premium',  180),
    ('Anual',    365),
]

for nome, duracao in planos:
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM Plano WHERE Nome_Plano = ?)
        INSERT INTO Plano (Nome_Plano, Duracao) VALUES (?, ?)
    """, nome, nome, duracao)

conn.commit()
print(f"✅ Plano: {len(planos)} registros inseridos")

# ============================================
# Personal
# ============================================
personals = []

for _ in range(10):
    cpf = fake.cpf()
    nome = fake.name()
    horario = f"{random.randint(6,20):02d}:{random.choice(['00','30'])}:00"
    telefone = fake.phone_number()[:15]

    try:
        cursor.execute("""
            INSERT INTO Personal (CPF_Personal, Nome, Horarios_Personal, Telefone_Personal)
            VALUES (?, ?, ?, ?)
        """, cpf, nome, horario, telefone)
        personals.append(cpf)
    except:
        pass

conn.commit()
print(f"✅ Personal: {len(personals)} registros inseridos")

# ============================================
# Professor
# ============================================
professores = []

for _ in range(5):
    cpf = fake.cpf()
    nome = fake.name()
    horario = f"{random.randint(6,20):02d}:{random.choice(['00','30'])}:00"
    telefone = fake.phone_number()[:15]

    try:
        cursor.execute("""
            INSERT INTO Professor (CPF_Professor, Nome, Horarios_Professor, Telefone_Professor)
            VALUES (?, ?, ?, ?)
        """, cpf, nome, horario, telefone)
        professores.append(cpf)
    except:
        pass

conn.commit()
print(f"✅ Professor: {len(professores)} registros inseridos")

# ============================================
# Aluno
# ============================================
alunos = []
nomes_plano = [p[0] for p in planos]

for _ in range(50):
    cpf = fake.cpf()
    nome = fake.name()
    telefone = fake.phone_number()[:15]
    nome_plano = random.choice(nomes_plano)
    cpf_personal = random.choice(personals)

    try:
        cursor.execute("""
            INSERT INTO Aluno (CPF_Aluno, Nome_Aluno, Telefone_Aluno, Nome_Plano, CPF_Personal)
            VALUES (?, ?, ?, ?, ?)
        """, cpf, nome, telefone, nome_plano, cpf_personal)
        alunos.append(cpf)
    except:
        pass

conn.commit()
print(f"✅ Aluno: {len(alunos)} registros inseridos")

# ============================================
# Aula
# ============================================
aulas_disponiveis = [
    'Musculacao',
    'Yoga',
    'Spinning',
    'Pilates',
    'Funcional',
]

aulas = []
for nome_aula in aulas_disponiveis:
    cpf_professor = random.choice(professores)
    try:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Aula WHERE Nome_Aula = ?)
            INSERT INTO Aula (Nome_Aula, CPF_Professor) VALUES (?, ?)
        """, nome_aula, nome_aula, cpf_professor)
        aulas.append(nome_aula)
    except:
        pass

conn.commit()
print(f"✅ Aula: {len(aulas)} registros inseridos")

# ============================================
# Aluno_Aula (N:N)
# ============================================
aluno_aula_inseridos = 0
pares_aluno_aula = set()

for aluno in alunos:
    aulas_aluno = random.sample(aulas, k=random.randint(1, 3))
    for aula in aulas_aluno:
        par = (aula, aluno)
        if par not in pares_aluno_aula:
            try:
                cursor.execute("""
                    INSERT INTO Aluno_Aula (Nome_Aula, CPF_Aluno) VALUES (?, ?)
                """, aula, aluno)
                pares_aluno_aula.add(par)
                aluno_aula_inseridos += 1
            except:
                pass

conn.commit()
print(f"✅ Aluno_Aula: {aluno_aula_inseridos} registros inseridos")

# ============================================
# Produto
# ============================================
produtos_disponiveis = [
    ('Suplemento',  'Whey Protein',     89.90),
    ('Suplemento',  'Creatina',         59.90),
    ('Suplemento',  'Pre-Treino',       79.90),
    ('Acessorio',   'Luva de Treino',   49.90),
    ('Acessorio',   'Cinto Lombar',     99.90),
    ('Roupa',       'Camiseta Dry Fit', 39.90),
    ('Roupa',       'Shorts Treino',    49.90),
    ('Bebida',      'Agua Mineral',      3.50),
    ('Bebida',      'Isotonico',         8.90),
    ('Equipamento', 'Corda de Pular',   29.90),
]

ids_produto = []
for tipo, nome, preco in produtos_disponiveis:
    quantidade = random.randint(10, 100)
    try:
        cursor.execute("""
            INSERT INTO Produto (Tipo_Produto, Quantidade, Nome_Produto, Preco_Unitario)
            VALUES (?, ?, ?, ?)
        """, tipo, quantidade, nome, preco)
        ids_produto.append(cursor.execute("SELECT @@IDENTITY").fetchval())
    except:
        pass

# Busca IDs reais inseridos
cursor.execute("SELECT ID_Produto FROM Produto")
ids_produto = [row[0] for row in cursor.fetchall()]

conn.commit()
print(f"✅ Produto: {len(ids_produto)} registros inseridos")

# ============================================
# Produto_Aluno (N:N)
# ============================================
produto_aluno_inseridos = 0
pares_produto_aluno = set()

for aluno in random.sample(alunos, k=min(30, len(alunos))):
    produtos_aluno = random.sample(ids_produto, k=random.randint(1, 3))
    for id_produto in produtos_aluno:
        par = (id_produto, aluno)
        if par not in pares_produto_aluno:
            try:
                cursor.execute("""
                    INSERT INTO Produto_Aluno (ID_Produto, CPF_Aluno, Quantidade_Comprada) VALUES (?, ?, ?)
                """, id_produto, aluno, random.randint(1, 10))
                pares_produto_aluno.add(par)
                produto_aluno_inseridos += 1
            except:
                pass

conn.commit()
print(f"✅ Produto_Aluno: {produto_aluno_inseridos} registros inseridos")

# ============================================
# Exercicio
# ============================================
exercicios_disponiveis = [
    ('Supino Reto',         'Peito'),
    ('Supino Inclinado',    'Peito'),
    ('Agachamento',         'Pernas'),
    ('Leg Press',           'Pernas'),
    ('Remada Curvada',      'Costas'),
    ('Puxada Frontal',      'Costas'),
    ('Desenvolvimento',     'Ombros'),
    ('Elevacao Lateral',    'Ombros'),
    ('Rosca Direta',        'Biceps'),
    ('Triceps Pulley',      'Triceps'),
    ('Panturrilha',         'Pernas'),
    ('Abdominal',           'Core'),
]

for nome, parte in exercicios_disponiveis:
    try:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Exercicio WHERE Nome_Exercicio = ?)
            INSERT INTO Exercicio (Nome_Exercicio, Parte_Trabalhada) VALUES (?, ?)
        """, nome, nome, parte)
    except:
        pass

conn.commit()
print(f"✅ Exercicio: {len(exercicios_disponiveis)} registros inseridos")

# ============================================
# Treino
# ============================================
treinos = []

for aluno in alunos:
    num_treinos = random.randint(1, 5)
    for _ in range(num_treinos):
        data = fake.date_between(start_date=date(2024, 1, 1), end_date=date.today())
        try:
            cursor.execute("""
                INSERT INTO Treino (Data_Criacao, CPF_Aluno) VALUES (?, ?)
            """, data, aluno)
            treinos.append(cursor.execute("SELECT @@IDENTITY").fetchval())
        except:
            pass

# Busca IDs reais inseridos
cursor.execute("SELECT ID_Treino FROM Treino")
treinos = [row[0] for row in cursor.fetchall()]

conn.commit()
print(f"✅ Treino: {len(treinos)} registros inseridos")

# ============================================
# Treino_Exercicio (N:N)
# ============================================
nomes_exercicio = [e[0] for e in exercicios_disponiveis]
treino_exercicio_inseridos = 0

for id_treino in treinos:
    exercicios_treino = random.sample(nomes_exercicio, k=random.randint(3, 6))
    for exercicio in exercicios_treino:
        carga = random.randint(10, 120)
        reps = random.randint(6, 15)
        try:
            cursor.execute("""
                INSERT INTO Treino_Exercicio (ID_Treino, Nome_Exercicio, Carga, Reps)
                VALUES (?, ?, ?, ?)
            """, id_treino, exercicio, carga, reps)
            treino_exercicio_inseridos += 1
        except:
            pass

conn.commit()
print(f"✅ Treino_Exercicio: {treino_exercicio_inseridos} registros inseridos")

# ============================================
# Encerra conexão
# ============================================
cursor.close()
conn.close()
print("\n🏋️ Dados inseridos com sucesso no gym_db!")