USE gym_dw;
GO

-- ============================================
-- Fato_Venda
-- FK: SK_Aluno → Aluno
-- FK: SK_Produto → Produto
-- FK: SK_Data → Data
-- ============================================

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Fato_Venda_SK_Aluno' AND object_id = OBJECT_ID('Fato_Venda'))
CREATE INDEX IX_Fato_Venda_SK_Aluno
ON Fato_Venda (SK_Aluno);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Fato_Venda_SK_Produto' AND object_id = OBJECT_ID('Fato_Venda'))
CREATE INDEX IX_Fato_Venda_SK_Produto
ON Fato_Venda (SK_Produto);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Fato_Venda_SK_Data' AND object_id = OBJECT_ID('Fato_Venda'))
CREATE INDEX IX_Fato_Venda_SK_Data
ON Fato_Venda (SK_Data);
GO
