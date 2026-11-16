# Gestão do Lavador

Aplicação web para registrar lavagens, consultar pendências, confirmar pagamentos e lançar receitas avulsas e despesas.

## Desenvolvimento

Requer Python 3.12. Crie um ambiente virtual com `python -m venv .venv` e ative com `.venv\Scripts\Activate.ps1` no PowerShell ou `source .venv/bin/activate` no Linux. Depois execute:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py create_owner
python manage.py runserver
```

Acesse http://127.0.0.1:8000. Crie a conta com `create_owner` para aplicar os validadores de senha. Use dados fictícios durante os testes.

## Implantação

Use uma instância Linux com Python 3.12, servidor WSGI, HTTPS, arquivos estáticos servidos de `staticfiles/` e disco persistente fora da raiz pública. Exporte as variáveis de `.env.example` no ambiente do processo. Gere um segredo exclusivo, configure o domínio e aponte `DATABASE_PATH` para o arquivo no disco persistente. Mantenha HTTPS também entre o proxy e a aplicação ou configure o Django para confiar exclusivamente no cabeçalho HTTPS sobrescrito pelo proxy de confiança.

Execute `migrate`, `collectstatic --noinput` e `check --deploy` antes de iniciar `config.wsgi:application`. Confira cotas e suspensão do plano. Use a API de backup do SQLite para cópias consistentes, mantenha a cópia fora da hospedagem em acesso restrito e verifique a restauração em outro arquivo antes de trocar a base ativa.

## Verificação

Execute `python manage.py test`. A CI verifica configuração, migrações, arquivos estáticos e testes. O [roteiro de validação](docs/validation.md) descreve como registrar as medições e as duas rodadas presenciais.
