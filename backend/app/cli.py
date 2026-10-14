"""Server-side admin commands.

python -m app.cli make-admin ana@example.com   # app administrator: enters all gyms
python -m app.cli expire-sessions              # close forgotten check-outs now
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
        user.role = Role.APP_ADMIN
        db.commit()
    print(f"{email} is now the app administrator. Log out and back in to see Administration.")
    return 0


def expire_sessions() -> int:
    from app.services.attendance import expire_stale_sessions

    with SessionLocal() as db:
        closed = expire_stale_sessions(db)
    print(f"Closed {closed} forgotten check-in(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("make-admin", help="Let a user enter and manage all gyms").add_argument("email")
    sub.add_parser("expire-sessions", help="Close check-ins older than the allowed visit length")
    args = parser.parse_args()
    if args.command == "make-admin":
        return make_admin(args.email)
    if args.command == "expire-sessions":
        return expire_sessions()
    return 2


if __name__ == "__main__":
    sys.exit(main())
