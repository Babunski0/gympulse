"""Server-side admin commands.

python -m app.cli make-admin ana@example.com
"""

import argparse
import sys

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import User
from app.models.user import Role


def make_admin(email: str) -> int:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            print(f"No user with email {email}. Register in the app first.", file=sys.stderr)
            return 1
        user.role = Role.GYM_ADMIN
        db.commit()
    print(f"{email} is now a gym administrator.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("make-admin", help="Let a user create and manage gyms").add_argument("email")
    args = parser.parse_args()
    if args.command == "make-admin":
        return make_admin(args.email)
    return 2


if __name__ == "__main__":
    sys.exit(main())
