CREATE DATABASE gym_dw;
GO

USE gym_dw;
GO

-- ============================================
-- Dim_Data
-- ============================================
IF OBJECT_ID('Dim_Data', 'U') IS NULL
CREATE TABLE Dim_Data (
    SK_Data     INT IDENTITY(1,1)   NOT NULL,
    Data        DATE                NOT NULL,
    Ano         INT                 NOT NULL,
    Mes         INT                 NOT NULL,
    Dia         INT                 NOT NULL,
    Dia_Semana  VARCHAR(20)         NOT NULL,

    CONSTRAINT PK_Dim_Data PRIMARY KEY (SK_Data)
);
GO

-- ============================================
-- Dim_Aluno
-- ============================================
IF OBJECT_ID('Dim_Aluno', 'U') IS NULL
CREATE TABLE Dim_Aluno (
    SK_Aluno        INT IDENTITY(1,1)   NOT NULL,
    CPF_Aluno       VARCHAR(14)         NOT NULL,
    Nome_Plano      VARCHAR(255)        NOT NULL,
    CPF_Personal    VARCHAR(14)         NULL,
    Quantia_Treinos INT                 NOT NULL DEFAULT 0,

    CONSTRAINT PK_Dim_Aluno PRIMARY KEY (SK_Aluno)
);
GO

-- ============================================
-- Dim_Produto
-- ============================================
IF OBJECT_ID('Dim_Produto', 'U') IS NULL
CREATE TABLE Dim_Produto (
    SK_Produto      INT IDENTITY(1,1)   NOT NULL,
    ID_Produto      INT                 NOT NULL,
    Nome_Produto    VARCHAR(255)        NOT NULL,
    Preco_Unitario  DECIMAL(10,2)       NOT NULL,

    CONSTRAINT PK_Dim_Produto PRIMARY KEY (SK_Produto)
);
GO

-- ============================================
-- Fato_Venda
-- ============================================
IF OBJECT_ID('Fato_Venda', 'U') IS NULL
CREATE TABLE Fato_Venda (
    SK_Venda            INT IDENTITY(1,1) NOT NULL, 
    SK_Produto          INT NOT NULL,
    SK_Aluno            INT NOT NULL,
    SK_Data             INT NOT NULL,
    Quantia_Comprada    INT NOT NULL,

    CONSTRAINT PK_Fato_Venda PRIMARY KEY (SK_Venda),
    CONSTRAINT FK_FatoVenda_Produto FOREIGN KEY (SK_Produto) REFERENCES Dim_Produto(SK_Produto),
    CONSTRAINT FK_FatoVenda_Aluno   FOREIGN KEY (SK_Aluno)   REFERENCES Dim_Aluno(SK_Aluno),
    CONSTRAINT FK_FatoVenda_Data    FOREIGN KEY (SK_Data)    REFERENCES Dim_Data(SK_Data)
);