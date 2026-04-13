-- ============================================
-- Gym Data Modeling
-- DDL - Criação das Tabelas
-- Banco: gym_db
-- ============================================

USE gym_db;
GO

-- ============================================
-- Plano
-- ============================================
IF OBJECT_ID('Plano', 'U') IS NULL
CREATE TABLE Plano (
    Nome_Plano      VARCHAR(255)    NOT NULL,
    Duracao         INT             NOT NULL,

    CONSTRAINT PK_Plano                     PRIMARY KEY (Nome_Plano),
    CONSTRAINT CK_Plano_Duracao_Positiva    CHECK (Duracao > 0)
);
GO

-- ============================================
-- Personal
-- ============================================
IF OBJECT_ID('Personal', 'U') IS NULL
CREATE TABLE Personal (
    CPF_Personal        VARCHAR(14)     NOT NULL,
    Nome                VARCHAR(255)    NOT NULL,
    Horarios_Personal   TIME            NOT NULL,
    Telefone_Personal   VARCHAR(15)     NOT NULL,

    CONSTRAINT PK_Personal PRIMARY KEY (CPF_Personal)
);
GO

-- ============================================
-- Aluno
-- ============================================
IF OBJECT_ID('Aluno', 'U') IS NULL
CREATE TABLE Aluno (
    CPF_Aluno       VARCHAR(14)     NOT NULL,
    Nome_Aluno      VARCHAR(255)    NOT NULL,
    Telefone_Aluno  VARCHAR(15)     NOT NULL,
    Nome_Plano      VARCHAR(255)    NOT NULL,
    CPF_Personal    VARCHAR(14)    NULL,

    CONSTRAINT PK_Aluno             PRIMARY KEY (CPF_Aluno),
    CONSTRAINT FK_Aluno_Plano       FOREIGN KEY (Nome_Plano)   REFERENCES Plano(Nome_Plano),
    CONSTRAINT FK_Aluno_Personal    FOREIGN KEY (CPF_Personal) REFERENCES Personal(CPF_Personal)
);
GO

-- ============================================
-- Professor
-- ============================================
IF OBJECT_ID('Professor', 'U') IS NULL
CREATE TABLE Professor (
    CPF_Professor       VARCHAR(14)     NOT NULL,
    Nome                VARCHAR(255)    NOT NULL,
    Horarios_Professor  TIME            NOT NULL,
    Telefone_Professor  VARCHAR(15)     NOT NULL,

    CONSTRAINT PK_Professor PRIMARY KEY (CPF_Professor)
);
GO

-- ============================================
-- Aula
-- ============================================
IF OBJECT_ID('Aula', 'U') IS NULL
CREATE TABLE Aula (
    Nome_Aula       VARCHAR(20)     NOT NULL,
    CPF_Professor   VARCHAR(14)     NOT NULL,

    CONSTRAINT PK_Aula              PRIMARY KEY (Nome_Aula),
    CONSTRAINT FK_Aula_Professor    FOREIGN KEY (CPF_Professor) REFERENCES Professor(CPF_Professor)
);
GO

-- ============================================
-- Aluno_Aula (N:N)
-- ============================================
IF OBJECT_ID('Aluno_Aula', 'U') IS NULL
CREATE TABLE Aluno_Aula (
    Nome_Aula   VARCHAR(20)     NOT NULL,
    CPF_Aluno   VARCHAR(14)     NOT NULL,

    CONSTRAINT PK_Aluno_Aula    PRIMARY KEY (Nome_Aula, CPF_Aluno),
    CONSTRAINT FK_AlAula_Aula   FOREIGN KEY (Nome_Aula) REFERENCES Aula(Nome_Aula),
    CONSTRAINT FK_AlAula_Aluno  FOREIGN KEY (CPF_Aluno) REFERENCES Aluno(CPF_Aluno)
);
GO

-- ============================================
-- Produto
-- ============================================
IF OBJECT_ID('Produto', 'U') IS NULL
CREATE TABLE Produto (
    ID_Produto      INT IDENTITY    NOT NULL,
    Tipo_Produto    VARCHAR(50)     NOT NULL,
    Quantidade      INT             NOT NULL,
    Nome_Produto    VARCHAR(255)    NOT NULL,
    Preco_Unitario  DECIMAL(10,2)   NOT NULL,

    CONSTRAINT PK_Produto                   PRIMARY KEY (ID_Produto),
    CONSTRAINT CK_Produto_Preco_Positivo    CHECK (Preco_Unitario > 0),
    CONSTRAINT CK_Produto_Quantidade_Valida CHECK (Quantidade >= 0)
);
GO

-- ============================================
-- Produto_Aluno (N:N)
-- ============================================
IF OBJECT_ID('Produto_Aluno', 'U') IS NULL
CREATE TABLE Produto_Aluno (
    ID_Produto          INT             NOT NULL,
    CPF_Aluno           VARCHAR(14)     NOT NULL,
    Quantidade_Comprada INT             NOT NULL,

    CONSTRAINT PK_Produto_Aluno                     PRIMARY KEY (ID_Produto, CPF_Aluno),
    CONSTRAINT FK_ProdAl_Produto                    FOREIGN KEY (ID_Produto) REFERENCES Produto(ID_Produto),
    CONSTRAINT FK_ProdAl_Aluno                      FOREIGN KEY (CPF_Aluno)  REFERENCES Aluno(CPF_Aluno),
    CONSTRAINT CK_Produto_Aluno_Quantidade_Positiva CHECK (Quantidade_Comprada > 0)
);
GO

-- ============================================
-- Treino
-- ============================================
IF OBJECT_ID('Treino', 'U') IS NULL
CREATE TABLE Treino (
    ID_Treino       INT IDENTITY    NOT NULL,
    Data_Criacao    DATE            NOT NULL,
    CPF_Aluno       VARCHAR(14)     NOT NULL,

    CONSTRAINT PK_Treino        PRIMARY KEY (ID_Treino),
    CONSTRAINT FK_Treino_Aluno  FOREIGN KEY (CPF_Aluno) REFERENCES Aluno(CPF_Aluno)
);
GO

-- ============================================
-- Exercicio
-- ============================================
IF OBJECT_ID('Exercicio', 'U') IS NULL
CREATE TABLE Exercicio (
    Nome_Exercicio      VARCHAR(255)    NOT NULL,
    Parte_Trabalhada    VARCHAR(255)    NOT NULL,

    CONSTRAINT PK_Exercicio PRIMARY KEY (Nome_Exercicio)
);
GO

-- ============================================
-- Treino_Exercicio (N:N)
-- ============================================
IF OBJECT_ID('Treino_Exercicio', 'U') IS NULL
CREATE TABLE Treino_Exercicio (
    ID_Treino       INT             NOT NULL,
    Nome_Exercicio  VARCHAR(255)    NOT NULL,
    Carga           INT             NOT NULL,
    Reps            INT             NOT NULL,

    CONSTRAINT PK_Treino_Exercicio                      PRIMARY KEY (ID_Treino, Nome_Exercicio),
    CONSTRAINT FK_TrEx_Treino                           FOREIGN KEY (ID_Treino)      REFERENCES Treino(ID_Treino),
    CONSTRAINT FK_TrEx_Exercicio                        FOREIGN KEY (Nome_Exercicio) REFERENCES Exercicio(Nome_Exercicio),
    CONSTRAINT CK_Treino_Exercicio_Carga_Nao_Negativa   CHECK (Carga >= 0),
    CONSTRAINT CK_Treino_Exercicio_Reps_Validas         CHECK (Reps BETWEEN 1 AND 100)
);
GO