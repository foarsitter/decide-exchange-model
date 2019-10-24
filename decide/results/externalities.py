import os

import pandas as pd
from decide import data_folder
from decide.data.database import connection, Manager
from decide.results.helpers import list_to_sql_param
from environs import Env

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)


def write_summary_result(conn, model_run_ids, output_directory):
    sql = """SELECT SUM(e.own)            as own,
           SUM(e.inner_positive) as inner_positive,
           SUM(e.inner_negative) as inner_negative,
           SUM(e.outer_positive) as outer_positive,
           SUM(e.outer_negative) as outer_negative,
           a.name                   actor,
           m.p
    FROM externality e
             JOIN actor a on e.actor_id = a.id
             JOIN iteration i on e.iteration_id = i.id
             JOIN repetition r on i.repetition_id = r.id
             JOIN modelrun m on r.model_run_id = m.id         
    WHERE m.id IN(%s)
    GROUP BY e.actor_id, m.id""" % list_to_sql_param(model_run_ids)

    df = pd.read_sql_query(
        sql,
        con=conn,
        index_col=['p'],
    )

    df_inner_positive = pd.pivot_table(df, index=['p'], columns=['actor'], values=['inner_positive'])
    df_inner_positive.to_csv(os.path.join(output_directory, 'externalities_inner_positive.csv'))

    plt = df_inner_positive.plot()

    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.set_title('Inner Positive')
    plt.set_xticks(df_inner_positive.index)
    plt.figure.savefig(os.path.join(
        output_directory, 'externalities_inner_positive.png'),
        bbox_extra_artists=(lgd,),
        bbox_inches="tight",
    )

    df_inner_negative = pd.pivot_table(df, index=['p'], columns=['actor'], values=['inner_negative'])
    df_inner_negative.to_csv(os.path.join(output_directory, 'externalities_inner_negative.csv'))

    plt = df_inner_negative.plot()

    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.set_title('Inner Negative')
    plt.set_xticks(df_inner_negative.index)
    plt.figure.savefig(os.path.join(
        output_directory, 'externalities_inner_negative.png'),
        bbox_extra_artists=(lgd,),
        bbox_inches="tight",
    )

    # OUTER POSITIVE

    df_outer_positive = pd.pivot_table(df, index=['p'], columns=['actor'], values=['outer_positive'])
    df_outer_positive.to_csv(os.path.join(output_directory, 'externalities_outer_positive.csv'))

    plt = df_outer_positive.plot()

    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.set_title('Outer Positive')
    plt.set_xticks(df_outer_positive.index)
    plt.figure.savefig(os.path.join(
        output_directory, 'externalities_outer_positive.png'),
        bbox_extra_artists=(lgd,),
        bbox_inches="tight",
    )

    # OUTER NEGATIVE

    df_outer_negative = pd.pivot_table(df, index=['p'], columns=['actor'], values=['outer_negative'])
    df_outer_negative.to_csv(os.path.join(output_directory, 'externalities_outer_negative.csv'))

    plt = df_outer_negative.plot()

    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.set_title('Outer negative')
    plt.set_xticks(df_outer_negative.index)
    plt.figure.savefig(
        os.path.join(output_directory, 'externalities_outer_negative.png'),
        bbox_extra_artists=(lgd,),
        bbox_inches="tight",
    )


if __name__ == '__main__':
    env = Env()
    Env.read_env()  # read .env file, if it exists

    url = env('DATABASE_URL')

    m = Manager(url)
    m.init_database()

    model_run_id = 1

    write_summary_result(connection, [model_run_id], data_folder)
