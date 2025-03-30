import logging
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
from decide.log import logger

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)


def write_result(
    conn: DatabaseProxy,
    last_iteration: int,
    model_run_id,
    output_directory: Path,
) -> None:
    df = pd.read_sql(
        """
    SELECT
        a.p as p,
        a.issue as issue,
        a.repetion || '-' || a.iteration as pointer,
        a.numerator / a.denominator AS nbs
    FROM (SELECT
            sum(ai.position * ai.power * ai.salience) AS numerator,
            sum(ai.salience * ai.power)               AS denominator,
            r.pointer                                 AS repetion,
            i2.pointer                                AS iteration,
            m.p,
            i.name as issue
          FROM actorissue ai
            LEFT JOIN issue i ON ai.issue_id = i.id
            LEFT JOIN actor a ON ai.actor_id = a.id
            LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
            LEFT JOIN repetition r ON i2.repetition_id = r.id
            LEFT JOIN modelrun m ON r.model_run_id = m.id
          WHERE  ai.type = 'after' AND i2.pointer = ? AND m.id = ?
         GROUP BY m.id,r.id, i2.id, i.id) a
    """,
        conn._state.conn,
        params=(
            last_iteration,
            model_run_id,
        ),
        index_col=["p"],
        columns=["issue"],
    )

    logger.info("Calculating covariance", last_iteration=last_iteration, model_run_id=model_run_id)

    for p in sorted(set(df.index)):
        x = df.loc[p].pivot(index="pointer", columns="issue", values="nbs").cov().round(5)

        x.to_csv(output_directory / f"covariance.equal-{p}.csv")

        logging.info(f"writen covariance table for p={p}")


if __name__ == "__main__":
    m = Manager(os.environ.get("DATABASE_URL"))
    m.init_database()

    model_run_id = 1

    write_result(connection, 9, model_run_id, data_folder)
