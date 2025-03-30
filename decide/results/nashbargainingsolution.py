import os
from pathlib import Path
from zipfile import Path

import numpy as np
import pandas as pd
from click.types import Path
from matplotlib.path import Path
from peewee import DatabaseProxy

from decide import data_folder
from decide.data.database import Manager
from decide.data.database import connection
from decide.log import logger
from decide.results.helpers import list_to_sql_param


def write_summary_result(
    conn: DatabaseProxy, model_run_ids: list[int], output_directory: Path, ai_type="before"
) -> None:
    x_type = "preference" if ai_type == "before" else "voting"

    df = pd.read_sql(
        f"""
    SELECT
      a.p as p,
      a.issue as issue,
      a.round as round,
      a.repetion as repetion,
      a.numerator / a.denominator AS mds
    FROM (SELECT
            sum(ai.position * ai.power * ai.salience) AS numerator,
            sum(ai.salience * ai.power)               AS denominator,
            r.pointer                                 AS repetion,
            i2.pointer + 1                                AS round,
            m.p,
      i.name as issue
          FROM actorissue ai
            LEFT JOIN issue i ON ai.issue_id = i.id
            LEFT JOIN actor a ON ai.actor_id = a.id
            LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
            LEFT JOIN repetition r ON i2.repetition_id = r.id
            LEFT JOIN modelrun m ON r.model_run_id = m.id
          WHERE  ai.type = '{ai_type}' AND m.id IN ({list_to_sql_param(model_run_ids)})
         GROUP BY m.id,r.id, i2.id, i.id) a
    """,
        conn._state.conn,
        index_col="p",
        columns=["mds"],
    )
    try:
        table_avg = pd.pivot_table(
            df,
            index=["issue", "p"],
            columns=["round"],
            values=["mds"],
            aggfunc="average",
        )
        table_avg.to_csv(output_directory / f"mds_average_{x_type}.csv")
    except Exception as e:
        logger.exception(e)

    try:
        table_var = pd.pivot_table(
            df,
            index=["issue", "p"],
            columns=["round"],
            values=["mds"],
            aggfunc="var",
        )
        table_var.to_csv(output_directory / f"mds_variance_{x_type}.csv")
    except Exception as e:
        logger.exception(e)

    sql_2 = f"""SELECT issue.name, issue.id
FROM issue
INNER JOIN dataset d on issue.data_set_id = d.id
INNER JOIN modelrun m on d.id = m.data_set_id
WHERE m.id IN ({list_to_sql_param(model_run_ids)})
GROUP BY issue.name, issue.id
ORDER BY issue.name"""

    cursor = conn.execute_sql(sql=sql_2, params=[])
    issues = cursor.fetchall()

    # %%

    for name, issue_id in issues:
        df = pd.read_sql(
            f"""SELECT a.p                         as p,
       a.issue                     as issue,
       a.round                 as round,
       a.repetion                  as repetion,
       a.numerator / a.denominator AS mds
FROM (SELECT sum(ai.position * ai.power * ai.salience) AS numerator,
             sum(ai.salience * ai.power)
                                                       AS denominator,
             r.pointer
                                                       AS repetion,
             i2.pointer +1
                                                       AS round,
             m.p,
             i.name                                    as issue
      FROM actorissue ai
               LEFT JOIN issue i ON ai.issue_id = i.id
               LEFT JOIN actor a ON ai.actor_id = a.id
               LEFT JOIN iteration i2 ON ai.iteration_id = i2.id
               LEFT JOIN repetition r ON i2.repetition_id = r.id
               LEFT JOIN modelrun m ON r.model_run_id = m.id
               LEFT JOIN dataset d ON a.data_set_id = d.id
      WHERE ai.type = '{ai_type}'
        AND m.id IN({list_to_sql_param(model_run_ids)})
        AND i.id = {issue_id}
      GROUP BY m.id, r.id, i2.id, i.id) a
        """,
            conn._state.conn,
            index_col="p",
            columns=["mds"],
        )

        try:
            table = pd.pivot_table(
                df,
                index=["round"],
                columns=["p"],
                values=["mds"],
                numeric_only=True,
            )
            plt = table.plot()

            plt.set_title(name)
            plt.set_ylim(0, 110)

            lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)

            plt.figure.savefig(
                output_directory / f"mds_{name}_{x_type}.png",
                bbox_extra_artists=(lgd,),
                bbox_inches="tight",
            )
        except Exception as e:
            logger.exception(e)


if __name__ == "__main__":
    m = Manager(os.environ.get("DATABASE_URL"))
    m.init_database()

    model_run_ids = [43, 44]

    write_summary_result(connection, model_run_ids, data_folder)
