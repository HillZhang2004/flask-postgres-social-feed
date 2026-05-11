from flask.cli import FlaskGroup
from project import app, db


cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    print("Schema is managed by services/postgres/schema.sql — no action taken.")


if __name__ == "__main__":
    cli()
