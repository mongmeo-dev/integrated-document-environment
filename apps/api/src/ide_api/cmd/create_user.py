import argparse
import asyncio
from getpass import getpass

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.auth.repository import AuthRepository


async def create_user(*, email: str, display_name: str, password: str) -> User:
    normalized_email = email.strip().lower()
    if not normalized_email or not display_name.strip() or not password:
        raise ValueError("Email, display name, and password are required.")

    async with async_session() as session:
        repository = AuthRepository(session)
        if await repository.get_user_by_email(normalized_email) is not None:
            raise ValueError("A user with this email already exists.")

        user = User(
            email=normalized_email,
            display_name=display_name.strip(),
            password_hash=hash_password(password),
        )
        session.add(user)
        await session.commit()
        return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an internal Document IDE user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    args = parser.parse_args()
    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    try:
        user = asyncio.run(
            create_user(
                email=args.email,
                display_name=args.display_name,
                password=password,
            )
        )
    except ValueError as error:
        parser.error(str(error))

    print(f"Created internal user {user.email} ({user.id}).")


if __name__ == "__main__":
    main()
