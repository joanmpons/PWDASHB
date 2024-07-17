# %%Import packages
import altair as alt
import json
import numpy as np
import requests as re
import pandas as pd
import streamlit as st
import time


# %%Import variables
df_topics = st.session_state.df_topics
df_groups = st.session_state.df_groups
df_dept = st.session_state.df_dept
df_dept_detail = st.session_state.df_dept_detail
df_groups_topics = st.session_state.df_groups_topics

# %%Dashboard
st.sidebar.subheader("Parámetros")
with st.sidebar:
    # ODS vs classical topics
    type_topics = st.radio(
        "Tipo de temas", ["Agenda 20/30", "Temas Clásicos"], index=0, horizontal=True
    )
    df_dept_detail = df_dept_detail[df_dept_detail["Topic type"] == type_topics]
    # Active deuputies
    active = st.radio("Sólo diputados activos", ["No", "Si"], index=1, horizontal=True)
    if active == "Si":
        df_dept_detail = df_dept_detail[df_dept_detail["active"] == 1]
    # Normalized data option
    norm = st.radio("Datos Normalizados", ["No", "Si"], index=0, horizontal=True)
    # Number of top topics selector
    n_topics = st.radio(
        "Top temas a mostrar",
        [5, 10, 15, 20, df_dept_detail["topic_name"].nunique()],
        index=1,
        horizontal=True,
    )
    # Min footprint selector
    foot_min = st.slider(
        "Huella mínima para los temas más hablados",
        0,
        df_dept_detail["topic_score"].max().astype(int),
        10,
    )
    # Max prioriy ranking selector
    priority_rank = 100 - st.slider(
        "Rango de prioridad máximo", 1, df_dept_detail["topic_shortname"].nunique(), 1
    )


# %% Defining charts
def talked_topics():
    df = pd.DataFrame(df_dept_detail)
    df = (
        df[["topic_shortname", "topic_score"]]
        .groupby(["topic_shortname"])
        .apply(lambda x: (x > foot_min).sum())
        .reset_index()
    )
    max_topics = (
        df.groupby("topic_shortname")
        .sum()
        .reset_index()
        .sort_values("topic_score", ascending=False)
        .head(n_topics)["topic_shortname"]
        .to_list()
    )
    df = df[df["topic_shortname"].isin(max_topics)]
    chart = (
        alt.Chart(df)
        .mark_bar(color="#efca53")
        .encode(
            alt.X("topic_shortname", sort="-y").title(""),
            alt.Y("topic_score").title(""),
            alt.Tooltip(["topic_shortname", "topic_score"]),
        )
        .interactive()
    )
    return chart, df.sort_values(by="topic_score", ascending=False)


def talked_stacked(dim):
    df = pd.DataFrame(df_dept_detail)
    df["new_topic_score"] = np.where(df["topic_score"] > foot_min, 1, 0)
    max_topics = (
        df.groupby("topic_shortname")
        .sum()
        .reset_index()
        .sort_values("new_topic_score", ascending=False)
        .head(n_topics)["topic_shortname"]
        .to_list()
    )

    if norm == "Si":
        df["new_topic_score"] = df.groupby([dim, "topic_shortname"])[
            "new_topic_score"
        ].transform("sum") / df.groupby([dim])["new_topic_score"].transform("count")

    df = df.groupby([dim, "topic_shortname"]).sum().reset_index().round(2)
    df = df[df["topic_shortname"].isin(max_topics)]
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X("topic_shortname", sort="-y").title(""),
            alt.Y("new_topic_score").title(""),
            alt.Color(dim, title=""),
            alt.Tooltip([dim, "topic_shortname", "new_topic_score"]),
        )
        .interactive()
    )
    return chart


def priority_topics():
    df = pd.DataFrame(df_dept_detail)[["name_x", "topic_shortname", "topic_score"]]
    df["topic_score"] = np.where(
        (
            df["topic_score"]
            == df[["name_x", "topic_score"]]
            .groupby(["name_x"])
            .transform("max")["topic_score"]
        )
        & (df["topic_score"] > 0),
        1,
        0,
    )
    max_topics = (
        df.groupby("topic_shortname")
        .sum()
        .reset_index()
        .sort_values("topic_score", ascending=False)
        .head(n_topics)["topic_shortname"]
        .to_list()
    )
    df = df[df["topic_shortname"].isin(max_topics)]
    df = df.groupby("topic_shortname").sum().reset_index()
    chart = (
        alt.Chart(df)
        .mark_bar(color="#ff6347")
        .encode(
            alt.X("topic_shortname", sort="-y").title(""),
            alt.Y("topic_score").title(""),
            alt.Tooltip(["topic_shortname", "topic_score"]),
        )
        .interactive()
    )
    return chart, df[["topic_shortname", "topic_score"]].sort_values(
        by="topic_score", ascending=False
    )


def priority_stacked(dim):
    df = pd.DataFrame(df_dept_detail)[[dim, "name_x", "topic_shortname", "topic_score"]]
    df["new_topic_score"] = np.where(
        (
            df["topic_score"]
            == df[["name_x", "topic_score"]]
            .groupby(["name_x"])
            .transform("max")["topic_score"]
        )
        & (df["topic_score"] > 0),
        1,
        0,
    )
    max_topics = (
        df.groupby("topic_shortname")
        .sum()
        .reset_index()
        .sort_values("new_topic_score", ascending=False)
        .head(n_topics)["topic_shortname"]
        .to_list()
    )

    if norm == "Si":
        df["new_topic_score"] = df.groupby([dim, "topic_shortname"])[
            "new_topic_score"
        ].transform("sum") / df.groupby([dim])["new_topic_score"].transform("count")

    df = df.groupby([dim, "topic_shortname"]).sum().reset_index().round(2)
    df = df[df["topic_shortname"].isin(max_topics)]
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X("topic_shortname", sort="-y").title(""),
            alt.Y("new_topic_score").title(""),
            alt.Color(dim, title=""),
            alt.Tooltip([dim, "topic_shortname", "new_topic_score"]),
        )
        .interactive()
    )
    return chart


def top_priorities_topics():
    df = pd.DataFrame(df_dept_detail)[["name_x", "topic_shortname", "topic_score"]]
    df = df[df["topic_score"] > foot_min]
    df["topic_score"] = (
        100
        - df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
    )
    df["topic_score"] = (df["topic_score"] - df["topic_score"].min()) / (
        df["topic_score"].max() - df["topic_score"].min()
    )
    df = df[df["topic_score"] > priority_rank / 100]
    max_topics = (
        df.groupby("topic_shortname")
        .sum()
        .reset_index()
        .sort_values("topic_score", ascending=False)
        .head(n_topics)["topic_shortname"]
        .to_list()
    )
    df = df[df["topic_shortname"].isin(max_topics)]
    df = df.groupby("topic_shortname").sum().reset_index().round()
    chart = (
        alt.Chart(df)
        .mark_bar(color="#DAF7A6")
        .encode(
            alt.X("topic_shortname", sort="-y").title(""),
            alt.Y("topic_score").title(""),
            alt.Tooltip(["topic_shortname", "topic_score"]),
        )
        .interactive()
    )
    return chart, df[["topic_shortname", "topic_score"]].sort_values(
        by="topic_score", ascending=False
    )


def top_priorities_stacked(dim):
    df = pd.DataFrame(df_dept_detail)[[dim, "name_x", "topic_shortname", "topic_score"]]
    df = df[df["topic_score"] > foot_min]
    df["new_topic_score"] = (
        100
        - df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
    )
    df["new_topic_score"] = (df["new_topic_score"] - df["new_topic_score"].min()) / (
        df["new_topic_score"].max() - df["new_topic_score"].min()
    )
    df = df[df["new_topic_score"] > priority_rank / 100]
    max_topics = (
        df.groupby("topic_shortname")
        .sum()
        .reset_index()
        .sort_values("new_topic_score", ascending=False)
        .head(n_topics)["topic_shortname"]
        .to_list()
    )

    if norm == "Si":
        df["new_topic_score"] = df.groupby([dim, "topic_shortname"])[
            "new_topic_score"
        ].transform("sum") / df.groupby([dim])["new_topic_score"].transform("count")
        df["new_topic_score"] = (
            df["new_topic_score"] - df["new_topic_score"].min()
        ) / (df["new_topic_score"].max() - df["new_topic_score"].min())
    df = df.groupby([dim, "topic_shortname"]).sum().reset_index().round(2)
    df = df[df["topic_shortname"].isin(max_topics)]
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X("topic_shortname", sort="-y").title(""),
            alt.Y("new_topic_score").title(""),
            alt.Color(dim, title=""),
            alt.Tooltip([dim, "topic_shortname", "new_topic_score"]),
        )
        .interactive()
    )
    return chart


# Creating chart and df variables
talked_chart, talked_df = talked_topics()
priority_chart, priority_df = priority_topics()
top_prorities_chart, top_prorities_df = top_priorities_topics()

# Defining tab groups and labels
tab_labels = ["Género", "Edad", "Partidos", "Región"]
groups_labels = ["gender", "age_bin", "party_name", "Region"]
groups_tabs_col1_list = []
groups_tabs_col2_list = []
groups_tabs_col3_list = []

# %%Page Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Los temas más hablados")
    tab1, tab2 = st.tabs(["Graph", "Data"])
    tab1.altair_chart(talked_chart, theme="streamlit", use_container_width=True)
    tab2.dataframe(talked_df, hide_index=True)
    st.subheader("Los temas más hablados por segmentos")
    # Creating tab variables, needs to be done inside the column
    for n, tab in enumerate(st.tabs(tab_labels)):
        globals()[f"group_tab_col1_{n}"] = tab
        groups_tabs_col1_list.append(tab)

    for tab, group in zip(groups_tabs_col1_list, groups_labels):
        tab.altair_chart(
            talked_stacked(group), theme="streamlit", use_container_width=True
        )

with col2:
    st.subheader("Los temas más priorizados")
    tab1, tab2 = st.tabs(["Graph", "Data"])
    tab1.altair_chart(priority_chart, theme="streamlit", use_container_width=True)
    tab2.dataframe(priority_df, hide_index=True)

    st.subheader("Los temas más priorizados por segmentos")

    for n, tab in enumerate(st.tabs(tab_labels)):
        globals()[f"group_tab_col2_{n}"] = tab
        groups_tabs_col2_list.append(tab)

    for tab, group in zip(groups_tabs_col2_list, groups_labels):
        tab.altair_chart(
            priority_stacked(group), theme="streamlit", use_container_width=True
        )

with col3:
    st.subheader("Temas más hablados y priorizados")
    tab1, tab2 = st.tabs(["Graph", "Data"])
    tab1.altair_chart(top_prorities_chart, theme="streamlit", use_container_width=True)
    tab2.dataframe(top_prorities_df, hide_index=True)

    st.subheader("Los temas más hablados y priorizados por segmentos")

    for n, tab in enumerate(st.tabs(tab_labels)):
        globals()[f"group_tab_col3_{n}"] = tab
        groups_tabs_col3_list.append(tab)

    for tab, group in zip(groups_tabs_col3_list, groups_labels):
        tab.altair_chart(
            top_priorities_stacked(group), theme="streamlit", use_container_width=True
        )
