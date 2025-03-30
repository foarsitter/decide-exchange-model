import os
from pathlib import Path
from zipfile import Path

import pandas as pd
from click.types import Path
from matplotlib.path import Path
from peewee import DatabaseProxy

from decide import data_folder
from decide.data.database import Manager
from decide.data.database import connection
from decide.results.helpers import list_to_sql_param

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)


def write_summary_result(
    conn: DatabaseProxy, model_run_ids: list[int], output_directory: Path
) -> None:
    df = pd.read_sql(
        f"""
    SELECT
            a.name AS actor,
            i.name as issue,
            AVG(ai.position) as position,
            i2.pointer + 1                                AS round,
            m.p,
            m.id
          FROM actorissue ai
            LEFT JOIN issue i ON ai.issue_id = i.id
            LEFT JOIN actor a ON ai.actor_id = a.id
            LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
            LEFT JOIN repetition r ON i2.repetition_id = r.id
            LEFT JOIN modelrun m ON r.model_run_id = m.id
          WHERE  ai.type = 'before' AND m.id IN({list_to_sql_param(model_run_ids)})
         GROUP BY m.id, i2.pointer, a.id, i.id;
    """,
        conn._state.conn,
        index_col=["issue", "actor", "p"],
        columns=["position"],
    )

    table = pd.pivot_table(
        df,
        index=["issue", "actor", "round"],
        columns=["p"],
        values=["position"],
    )
    table.to_csv(output_directory / "issues_preference.csv")

    df = pd.read_sql(
        f"""
    SELECT
            a.name AS actor,
            i.name as issue,
            AVG(ai.position) as position,
            i2.pointer + 1                                AS round,
            m.p,
            m.id
          FROM actorissue ai
            LEFT JOIN issue i ON ai.issue_id = i.id
            LEFT JOIN actor a ON ai.actor_id = a.id
            LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
            LEFT JOIN repetition r ON i2.repetition_id = r.id
            LEFT JOIN modelrun m ON r.model_run_id = m.id
          WHERE  ai.type = 'after' AND m.id IN({list_to_sql_param(model_run_ids)})
         GROUP BY m.id, i2.pointer, a.id, i.id;
    """,
        conn._state.conn,
        index_col=["issue", "actor", "p"],
        columns=["position"],
    )

    table = pd.pivot_table(
        df,
        index=["issue", "actor", "round"],
        columns=["p"],
        values=["position"],
    )
    table.to_csv(output_directory / "issues_voting.csv")


if __name__ == "__main__":
    m = Manager(os.environ.get("DATABASE_URL"))
    m.init_database()

    model_run_id = 1

    write_summary_result(connection, [model_run_id], data_folder)
