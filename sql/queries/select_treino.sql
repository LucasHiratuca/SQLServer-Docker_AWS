USE gym_db
SELECT t.ID_Treino,
a.Nome_Aluno,
e.Nome_Exercicio, 
e.Parte_Trabalhada,
Carga,
te.Carga * te.Reps AS Volume_Total,
Reps
FROM Treino_Exercicio te
JOIN Treino t ON t.ID_Treino = te.ID_Treino
JOIN Exercicio e ON e.Nome_Exercicio = te.Nome_Exercicio
JOIN Aluno a ON a.CPF_Aluno = t.CPF_Aluno;
GO