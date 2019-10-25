from typing import Iterable


def get_all_actors(connection, model_run_ids=None, data_set_id=None):
    assert not (model_run_ids and data_set_id), 'Provide only one of both arguments'

    if model_run_ids:
        sql = get_all_actors_by_model_run_ids_sql(model_run_ids)
    else:
        sql = get_all_actors_by_data_set_id_sql(data_set_id)

    cursor = connection.execute(sql)

    return cursor.fetchall()


def get_all_actors_by_model_run_ids_sql(model_run_ids):
    assert isinstance(model_run_ids, Iterable), 'model_run_ids should be an list of integers'

    model_run_id_param = list_to_sql_param(model_run_ids)

    sql = """SELECT a.name, a.id
    FROM actor a
             INNER JOIN dataset d on a.data_set_id = d.id
             INNER JOIN modelrun m on d.id = m.data_set_id
    WHERE m.id in (%s)
    GROUP BY a.name, a.id 
    ORDER BY a.name""" % model_run_id_param

    return sql


def get_all_actors_by_data_set_id_sql(data_set_id):
    assert isinstance(data_set_id, int), 'data_set_id should be an integer '

    sql = """SELECT a.name, a.id
    FROM actor a
    WHERE a.data_set_id = %s
    GROUP BY a.name, a.id""" % str(data_set_id)

    return sql


def list_to_sql_param(list_object):
    """
    In some way the database API of python does not handle IN(?) very well.
    Therefor we need to create a string of our values
    :param list_object:'
    :return:
    """
    return ','.join(list(map(lambda x: "\'{}\'".format(x), list_object)))


def handle_data_frame(df, file_name, title):
    df.to_csv(file_name.format('csv'))

    plt = df.plot()  # .bar()

    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.set_title(title)
    plt.set_xticks(df.index)
    plt.figure.savefig(
        file_name.format('png'),
        bbox_extra_artists=(lgd,),
        bbox_inches="tight",
    )
