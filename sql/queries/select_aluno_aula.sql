USE gym_db
SELECT au.Nome_Aula,
al.Nome_Aluno,
p.Nome
FROM Aluno_Aula aa
JOIN Aluno al ON al.CPF_Aluno = aa.CPF_Aluno
JOIN Aula au ON au.Nome_Aula = aa.Nome_Aula
JOIN Professor p ON p.CPF_Professor = au.CPF_Professor;
GO