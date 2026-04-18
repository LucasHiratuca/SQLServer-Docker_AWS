USE gym_db
SELECT p.Nome_Produto,
a.Nome_Aluno,
p.Preco_Unitario,
pa.Quantidade_Comprada,
pa.Quantidade_Comprada * p.Preco_Unitario AS Preço_Final
FROM Produto_Aluno pa
JOIN Produto p ON p.ID_Produto = pa.ID_Produto
JOIN Aluno a ON a.CPF_Aluno = pa.CPF_Aluno;
GO