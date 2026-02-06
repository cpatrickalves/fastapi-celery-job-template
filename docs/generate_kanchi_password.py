"""Gera o hash de senha e secrets para autenticação do Kanchi.

Uso:
    python docs/generate_kanchi_password.py

A senha é lida via input() para não ficar no histórico do shell.
Cole os valores gerados no seu arquivo .env.
Os '$' no hash já saem escapados como '$$' para o Docker Compose.
"""

import base64
import hashlib
import os
from getpass import getpass


def generate_password_hash(password: str) -> str:
    salt = base64.b64encode(os.urandom(16)).decode().strip("=")
    iterations = 260_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    hash_b64 = base64.b64encode(dk).decode()
    return f"pbkdf2_sha256${iterations}${salt}${hash_b64}"


def generate_secret() -> str:
    return os.urandom(32).hex()


def main() -> None:
    password = getpass("Digite a senha do Kanchi: ")
    if not password:
        print("Erro: senha vazia.")
        return

    password_hash = generate_password_hash(password)
    session_secret = generate_secret()
    token_secret = generate_secret()

    print("\n# Cole as linhas abaixo no seu .env:\n")
    escaped_hash = password_hash.replace("$", "$$")
    print(f"KANCHI_AUTH_PASSWORD_HASH={escaped_hash}")
    print(f"KANCHI_SESSION_SECRET={session_secret}")
    print(f"KANCHI_TOKEN_SECRET={token_secret}")


if __name__ == "__main__":
    main()
