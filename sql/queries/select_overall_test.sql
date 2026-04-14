USE gym_db
SELECT *
FROM Aula;
GO

SELECT *
FROM Professor
WHERE CPF_Professor = '416.972.853-09'
OR CPF_Professor = '968.054.713-20';
GO

SELECT *
FROM Produto_Aluno;
GO

SELECT *
FROM Aluno
WHERE CPF_Aluno IN (SELECT CPF_Aluno FROM Produto_Aluno)
GO