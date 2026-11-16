from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the owner account with password validation."

    def handle(self, *args, **options):
        username = input("Nome de usuário: ").strip()
        user = get_user_model()(username=username)
        try:
            user.full_clean(exclude=["password"])
            password = getpass("Senha: ")
            if password != getpass("Confirme a senha: "):
                raise CommandError("As senhas não coincidem.")
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        user.set_password(password)
        user.save()
        self.stdout.write("Conta criada.")
