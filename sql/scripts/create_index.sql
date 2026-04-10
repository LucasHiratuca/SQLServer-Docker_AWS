USE gym_db;
GO

-- ============================================
-- Aluno
-- FK: Nome_Plano → Plano
-- FK: CPF_Personal → Personal
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Aluno_Nome_Plano' AND object_id = OBJECT_ID('Aluno'))
CREATE INDEX IX_Aluno_Nome_Plano
ON Aluno (Nome_Plano);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Aluno_CPF_Personal' AND object_id = OBJECT_ID('Aluno'))
CREATE INDEX IX_Aluno_CPF_Personal
ON Aluno (CPF_Personal);
GO

-- ============================================
-- Aula
-- FK: CPF_Professor → Professor
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Aula_CPF_Professor' AND object_id = OBJECT_ID('Aula'))
CREATE INDEX IX_Aula_CPF_Professor
ON Aula (CPF_Professor);
GO

-- ============================================
-- Aluno_Aula
-- FK: Nome_Aula → Aula
-- FK: CPF_Aluno → Aluno
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Aluno_Aula_Nome_Aula' AND object_id = OBJECT_ID('Aluno_Aula'))
CREATE INDEX IX_Aluno_Aula_Nome_Aula
ON Aluno_Aula (Nome_Aula);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Aluno_Aula_CPF_Aluno' AND object_id = OBJECT_ID('Aluno_Aula'))
CREATE INDEX IX_Aluno_Aula_CPF_Aluno
ON Aluno_Aula (CPF_Aluno);
GO

-- ============================================
-- Produto_Aluno
-- FK: ID_Produto → Produto
-- FK: CPF_Aluno → Aluno
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Produto_Aluno_ID_Produto' AND object_id = OBJECT_ID('Produto_Aluno'))
CREATE INDEX IX_Produto_Aluno_ID_Produto
ON Produto_Aluno (ID_Produto);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Produto_Aluno_CPF_Aluno' AND object_id = OBJECT_ID('Produto_Aluno'))
CREATE INDEX IX_Produto_Aluno_CPF_Aluno
ON Produto_Aluno (CPF_Aluno);
GO

-- ============================================
-- Treino
-- FK: CPF_Aluno → Aluno
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Treino_CPF_Aluno' AND object_id = OBJECT_ID('Treino'))
CREATE INDEX IX_Treino_CPF_Aluno
ON Treino (CPF_Aluno);
GO

-- Extra: acelerar consultas por período
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Treino_Data_Criacao' AND object_id = OBJECT_ID('Treino'))
CREATE INDEX IX_Treino_Data_Criacao
ON Treino (Data_Criacao);
GO

-- ============================================
-- Treino_Exercicio
-- FK: ID_Treino → Treino
-- FK: Nome_Exercicio → Exercicio
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Treino_Exercicio_ID_Treino' AND object_id = OBJECT_ID('Treino_Exercicio'))
CREATE INDEX IX_Treino_Exercicio_ID_Treino
ON Treino_Exercicio (ID_Treino);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Treino_Exercicio_Nome_Exercicio' AND object_id = OBJECT_ID('Treino_Exercicio'))
CREATE INDEX IX_Treino_Exercicio_Nome_Exercicio
ON Treino_Exercicio (Nome_Exercicio);
GO

-- Extra: acelerar JOIN com filtro de carga
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Treino_Exercicio_ID_Carga' AND object_id = OBJECT_ID('Treino_Exercicio'))
CREATE INDEX IX_Treino_Exercicio_ID_Carga
ON Treino_Exercicio (ID_Treino, Carga);
GO