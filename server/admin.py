"""Manual subscriber management — for support requests until email delivery is wired up.

Usage:
    python -m server.admin lookup <token>
    python -m server.admin issue <email> [--plan byok|managed_free|managed_paid] [--inactive]
    python -m server.admin deactivate <token>
    python -m server.admin activate <token>
"""
import argparse

from server import db


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lookup = sub.add_parser("lookup", help="Show a subscriber's record")
    p_lookup.add_argument("token")

    p_issue = sub.add_parser("issue", help="Manually issue a token (e.g. for a support/refund case)")
    p_issue.add_argument("email")
    p_issue.add_argument(
        "--plan", choices=[db.PLAN_BYOK, db.PLAN_FREE, db.PLAN_PAID], default=db.PLAN_BYOK,
    )
    p_issue.add_argument("--inactive", action="store_true", help="Create as inactive")

    p_deactivate = sub.add_parser("deactivate", help="Deactivate a subscriber")
    p_deactivate.add_argument("token")

    p_activate = sub.add_parser("activate", help="Reactivate a subscriber")
    p_activate.add_argument("token")

    args = parser.parse_args()
    db.init_db()

    if args.cmd == "lookup":
        subscriber = db.get_subscriber(args.token)
        print(subscriber or "No subscriber with that token.")

    elif args.cmd == "issue":
        token = db.create_manual(email=args.email, plan=args.plan, active=not args.inactive)
        print(f"Issued {args.plan} token for {args.email}:\n{token}")

    elif args.cmd == "deactivate":
        found = db.set_active_by_token(args.token, False)
        print("Deactivated." if found else "No subscriber with that token.")

    elif args.cmd == "activate":
        found = db.set_active_by_token(args.token, True)
        print("Activated." if found else "No subscriber with that token.")


if __name__ == "__main__":
    main()
