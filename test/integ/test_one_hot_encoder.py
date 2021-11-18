#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2021 Snowflake Computing Inc. All rights reserved.
#
from test.utils import Utils

import pytest

from snowflake.connector import ProgrammingError
from snowflake.snowpark import Row
from snowflake.snowpark.ml.transformers.one_hot_encoder import OneHotEncoder

TABLENAME = "table_temp"


def test_fit(session):
    input_df = session.createDataFrame(
        [
            Row(1, "a", -1.0),
            Row(2, "a", 8.3),
            Row(3, "b", 2.0),
            Row(4, "c", 3.5),
            Row(5, "d", 2.5),
            Row(6, "b", 4.0),
        ]
    ).toDF("id", "input_value", "float")

    encoder = OneHotEncoder(session=session, input_col="input_value")
    encoder.fit(input_df)

    expected_df = session.createDataFrame(
        [
            Row("a", 1),
            Row("b", 2),
            Row("c", 3),
            Row("d", 4),
        ]
    ).toDF("distinct_value", "index")
    actual_df = session.table(TABLENAME)

    Utils.check_answer(expected_df, actual_df)

    # input_df does not contain input_col
    missing_input_col_input_df = session.createDataFrame(
        [
            Row(1, "a", -1.0),
            Row(2, "a", 8.3),
            Row(3, "b", 2.0),
            Row(4, "c", 3.5),
            Row(5, "d", 2.5),
            Row(6, "b", 4.0),
        ]
    ).toDF("id", "str", "float")

    with pytest.raises(ProgrammingError) as ex_info:
        encoder.fit(missing_input_col_input_df)
    assert "invalid identifier 'INPUT_VALUE'" in str(ex_info)

    # string indexer with session as None
    none_session_indexer = OneHotEncoder(session=None, input_col="input_value")

    with pytest.raises(AttributeError) as ex_info:
        none_session_indexer.fit(input_df)
    assert "'NoneType' object has no attribute 'sql'" in str(ex_info)

    # string indexer with input_col as None
    none_input_col_indexer = OneHotEncoder(session=session, input_col=None)

    with pytest.raises(TypeError) as ex_info:
        none_input_col_indexer.fit(input_df)
    assert "The select() input must be Column, str, or list" in str(ex_info)

    # input_df type is not DataFrame
    with pytest.raises(TypeError) as ex_info:
        encoder.fit(None)
    assert (
        "OneHotEncoder.fit() input type must be DataFrame. Got: <class 'NoneType'>"
        in str(ex_info)
    )

    with pytest.raises(TypeError) as ex_info:
        encoder.fit("df")
    assert (
        "OneHotEncoder.fit() input type must be DataFrame. Got: <class 'str'>"
        in str(ex_info)
    )

    with pytest.raises(TypeError) as ex_info:
        encoder.fit(0)
    assert (
        "OneHotEncoder.fit() input type must be DataFrame. Got: <class 'int'>"
        in str(ex_info)
    )


def test_transform(session):
    input_df = session.createDataFrame(
        [
            Row(1, "a", -1.0),
            Row(2, "b", 2.0),
            Row(3, "c", 3.5),
            Row(4, "b", 4.0),
            Row(5, "d", 2.5),
            Row(6, "a", 8.3),
        ]
    ).toDF("id", "input_value", "float")

    encoder = OneHotEncoder(session=session, input_col="input_value")
    encoder.fit(input_df)

    df = session.createDataFrame(["b", "d", "z", "a"]).toDF("value")

    expected_df = session.createDataFrame(
        [
            '[\n  "2",\n  "4",\n  "1"\n]',
            '[\n  "4",\n  "4",\n  "1"\n]',
            '[\n  "-1",\n  "4",\n  "1"\n]',
            '[\n  "1",\n  "4",\n  "1"\n]',
        ]
    ).toDF("expected")
    actual_df = df.select(encoder.transform(df["value"]))

    Utils.check_answer(expected_df, actual_df)

    # col type is not Column
    with pytest.raises(TypeError) as ex_info:
        df.select(encoder.transform(None))
    assert (
        "OneHotEncoder.transform() input type must be Column. Got: <class 'NoneType'>"
        in str(ex_info)
    )

    with pytest.raises(TypeError) as ex_info:
        df.select(encoder.transform("value"))
    assert (
        "OneHotEncoder.transform() input type must be Column. Got: <class 'str'>"
        in str(ex_info)
    )

    with pytest.raises(TypeError) as ex_info:
        df.select(encoder.transform(0))
    assert (
        "OneHotEncoder.transform() input type must be Column. Got: <class 'int'>"
        in str(ex_info)
    )

    with pytest.raises(TypeError) as ex_info:
        df.select(encoder.transform(df))
    assert (
        "OneHotEncoder.transform() input type must be Column. Got: <class 'snowflake.snowpark.dataframe.DataFrame'>"
        in str(ex_info)
    )