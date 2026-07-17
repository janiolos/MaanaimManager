"""
Cria um superusuário no banco Django/Postgres usando hash pbkdf2_sha256 compatível.

Uso:
  cd backend
  python -m scripts.seed_admin postgresql+asyncpg://user:pass@host:5432/dbname admin admin@email.com senha123
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, ".")

from app.auth.passwords import hash_password


async def seed(dsn: str, username: str, email: str, password: str) -> None:
    engine = create_async_engine(dsn, pool_pre_ping=True)

    hashed = hash_password(password)
    print(f"🔐 Hash gerado (pbkdf2_sha256 compat Django): {hashed[:50]}...")

    async with engine.begin() as conn:
        # Verificar se o usuário já existe
        result = await conn.execute(
            text("SELECT id FROM auth_user WHERE username = :u"), {"u": username}
        )
        if result.fetchone():
            print(f"⚠️  Usuário '{username}' já existe — ignorando")
            return

        # Inserir com Django BigAutoField (sequence auth_user_id_seq)
        await conn.execute(
            text("""
                INSERT INTO auth_user
                    (username, email, first_name, last_name, password,
                     is_active, is_superuser, is_staff, date_joined)
                VALUES
                    (:username, :email, '', '', :password,
                     true, true, true, NOW())
            """),
            {"username": username, "email": email, "password": hashed},
        )

        # Descobrir o ID criado
        result = await conn.execute(
            text("SELECT id FROM auth_user WHERE username = :u"), {"u": username}
        )
        user_id = result.scalar_one()
        print(f"✅ Usuário '{username}' criado com id={user_id}")

        # Atribuir grupo Admin (se existir)
        result = await conn.execute(
            text("SELECT id FROM auth_group WHERE name = :n"), {"n": "Admin"}
        )
        group = result.fetchone()
        if group:
            await conn.execute(
                text("""
                    INSERT INTO auth_user_groups (user_id, group_id)
                    VALUES (:uid, :gid)
                    ON CONFLICT DO NOTHING
                """),
                {"uid": user_id, "gid": group[0]},
            )
            print(f"✅ Grupo 'Admin' atribuído")
        else:
            print("ℹ️  Grupo 'Admin' não encontrado — ignorando")

    await engine.dispose()
    print("\n🎉 Pronto! Login: /api/v1/auth/login com username='{username}'")


async def main():
    if len(sys.argv) < 5:
        print("Uso: python seed_admin.py <dsn> <username> <email> <password>")
        print("Exemplo: python seed_admin.py postgresql+asyncpg://eventa:eventa@localhost:5432/eventa admin admin@maanaim.com minha_senha")
        sys.exit(1)

    await seed(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    asyncio.run(main())
