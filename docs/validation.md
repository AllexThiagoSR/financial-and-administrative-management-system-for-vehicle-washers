# Evidências da Experiência Prática III

## RNF03 e RNF04

Teste uma instalação limpa no Windows e no Linux com Python 3.12. Em hospedagem HTTPS, confirme a persistência de um registro fictício após reinício e republicação, e teste uma restauração separada. Anote versão, ambiente e resultado.

Verifique as três telas a 320 pixels CSS, controles de 44 × 44 pixels CSS, ordem de teclado, foco visível, rótulos e mensagens compreensíveis pelo texto. Para desempenho, prepare 300 lavagens fictícias (100 pendentes), abra a primeira página do filtro com a sessão ativa e desligue o cache. Para preparar a base em ambiente local isolado, crie uma conta fictícia chamada `performance-demo` com `python manage.py create_owner` e execute `python manage.py seed_performance_data performance-demo`. Antes de hospedar a base de teste, faça uma cópia consistente e mantenha-a separada dos dados reais. No Chrome Android, simule 1,6 Mb/s de download, 750 kb/s de upload e 150 ms de latência adicional. Após um aquecimento, registre cinco tempos até `load` e calcule a mediana. Aceite abaixo de 3 s. Registre medidas na rede real e após suspensão em séries separadas.

## Duas rodadas em campo

Combine duas sessões de 20 a 25 minutos com o proprietário e registre sua concordância de forma privada. Use o POCO X7 Pro, três telas e dados fictícios. Leia o objetivo de cada tarefa sem indicar controles. Uma pista após pedido de ajuda ou um minuto sem avanço conta como ajuda direta.

1. Registre uma lavagem simples fictícia de R$ 40,00 a pagar depois e confira o estado Pendente.
2. Confirme o recebimento da lavagem certa e explique como reconheceu a confirmação. Cronometre do fim da leitura até o resultado, incluindo dúvidas e correções.
3. Lance uma despesa fictícia de R$ 30,00 com produtos de limpeza e informe se o lançamento foi confirmado.

Após as tarefas pergunte: “De 1 a 5, qual é seu nível de satisfação com o uso do sistema para registrar lavagens, confirmar pagamentos e lançar despesas pelo celular?”. 1 significa muito insatisfeito e 5, muito satisfeito.

Aprovação: 3/3 sem ajuda, tarefa 2 em até 120 s, nota de pelo menos 4 e ausência de falha crítica. Registre separadamente comportamento e opinião. Entre rodadas, vincule os problemas a ajustes e PRs e repita com cenário equivalente. Preserve versão, rede, resultados, tempos, erros, ajuda, nota, comentários e decisão de revisão, em registro privado. Esta ficha descreve a coleta prevista.
