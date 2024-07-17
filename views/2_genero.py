#%%Import packages
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

#%%Import variables
df_topics = st.session_state.df_topics
df_groups = st.session_state.df_groups
df_dept = st.session_state.df_dept
df_dept_detail = st.session_state.df_dept_detail
df_groups_topics = st.session_state.df_groups_topics

#%%Dashboard
st.sidebar.subheader("Parámetros")

with st.sidebar:
    #ODS vs classical topics
    type_topics = st.radio("Tipo de temas", ["Agenda 20/30","Temas Clásicos"], index = 0, horizontal=True)
    df_dept_detail = df_dept_detail[df_dept_detail["Topic type"] == type_topics]
    if type_topics == "Agenda 20/30":
        default_topics = ["ODS 16", "ODS 10", "ODS 8"]
    else:
        default_topics = ["Democracia","Infancia"]
    #Topics selector
    topics_select = st.multiselect(
        'Temas',
        pd.unique(df_dept_detail["topic_shortname"]),
        default = default_topics)
    #Active deuputies
    active = st.radio("Sólo diputados activos", ["No","Si"], index = 1, horizontal=True)
    if active == "Si":
        df_dept_detail = df_dept_detail[df_dept_detail["active"] == 1]
    #Normalized data option
    norm = st.radio("Datos Normalizados", ["No","Si"], index = 0, horizontal=True)
    #Min footprint selector
    foot_min = st.slider('Huella mínima para los temas más hablados', 0, df_dept_detail["topic_score"].max().astype(int), 10)
    #Max prioriy ranking selector
    priority_rank = 100 - st.slider('Rango de prioridad máximo', 1, df_dept_detail["topic_shortname"].nunique(), 1)
    #Metric selection
    metric = st.radio("Métrica", ["Temas más hablados","Temas priorizados", "Mixto"], index = 0, horizontal=True)
    
#%%Define charts
def pie_chart(dim):
    if metric == "Temas más hablados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where(df["topic_score"] > foot_min, 1, 0)
    elif metric == "Temas priorizados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where((df["topic_score"] == df[["name_x","topic_score"]].groupby(["name_x"]).transform("max")["topic_score"]) &
                                         (df["topic_score"] > 0), 1, 0)
    else:
        df = pd.DataFrame(df_dept_detail)
        df = df[df["topic_score"]> foot_min]
        df["new_topic_score"] = 100 - df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
        df["new_topic_score"] = (df["new_topic_score"] - df["new_topic_score"].min())/(df["new_topic_score"].max()-df["new_topic_score"].min())
        df = df[df["new_topic_score"] > priority_rank/100]
    df = df[df["topic_shortname"].isin(topics_select)]
    df = df.groupby([dim]).sum().reset_index().round(2)
    chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta="new_topic_score",
        color=alt.Color(f"{dim}:N").title("")
        ).interactive()
    return chart

def gender_chart():
    if metric == "Temas más hablados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where(df["topic_score"] > foot_min, 1, 0)
    elif metric == "Temas priorizados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where((df["topic_score"] == df[["name_x","topic_score"]].groupby(["name_x"]).transform("max")["topic_score"]) &
                                         (df["topic_score"] > 0), 1, 0)
    else:
        df = pd.DataFrame(df_dept_detail)
        df = df[df["topic_score"]> foot_min]
        df["new_topic_score"] = 100 - df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
        df["new_topic_score"] = (df["new_topic_score"] - df["new_topic_score"].min())/(df["new_topic_score"].max()-df["new_topic_score"].min())
        df = df[df["new_topic_score"] > priority_rank/100]
    df = df[df["topic_shortname"].isin(topics_select)].groupby(["gender","topic_name"]).sum().reset_index()
    chart = alt.Chart(df).mark_bar().encode(
        alt.Y('new_topic_score').title(""),
        alt.X('topic_name', sort='-y').title(""),
        alt.Color('gender').title("")
    ).interactive()
    return chart

def topics_chart(gender,color):
    if metric == "Temas más hablados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where(df["topic_score"] > foot_min, 1, 0)
    elif metric == "Temas priorizados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where((df["topic_score"] == df[["name_x","topic_score"]].groupby(["name_x"]).transform("max")["topic_score"]) &
                                         (df["topic_score"] > 0), 1, 0)
    else:
        df = pd.DataFrame(df_dept_detail)
        df = df[df["topic_score"]> foot_min]
        df["new_topic_score"] = 100 - df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
        df["new_topic_score"] = (df["new_topic_score"] - df["new_topic_score"].min())/(df["new_topic_score"].max()-df["new_topic_score"].min())
        df = df[df["new_topic_score"] > priority_rank/100]
    df = df[df["gender"]==gender]
    max_topics = df.groupby("topic_shortname").sum().reset_index().sort_values("topic_score",ascending=False).head(10)["topic_shortname"].to_list()
    df = df[df["topic_shortname"].isin(max_topics)].groupby("topic_shortname").sum().reset_index()
    chart = alt.Chart(df).mark_bar(color=color).encode(
            alt.Y('topic_shortname', sort='-x', axis=alt.Axis(title='', orient= "right", labels=True)),
            alt.X('new_topic_score').title(""),
            alt.Tooltip(['topic_shortname', 'new_topic_score']),
        ).interactive()
    return chart

def heatmap(dim):
    if metric == "Temas más hablados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where(df["topic_score"] > foot_min, 1, 0)
    elif metric == "Temas priorizados":
        df = pd.DataFrame(df_dept_detail)
        df["new_topic_score"] = np.where((df["topic_score"] == df[["name_x","topic_score"]].groupby(["name_x"]).transform("max")["topic_score"]) &
                                         (df["topic_score"] > 0), 1, 0)
    else:
        df = pd.DataFrame(df_dept_detail)
        df = df[df["topic_score"]> foot_min]
        df["new_topic_score"] = 100 - df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
        df["new_topic_score"] = (df["new_topic_score"] - df["new_topic_score"].min())/(df["new_topic_score"].max()-df["new_topic_score"].min())
        df = df[df["new_topic_score"] > priority_rank/100]
    df = df.groupby([dim,"topic_shortname"]).sum().reset_index().round(2)
    df["new_topic_score"] = (df['new_topic_score'] - df.groupby(dim)["new_topic_score"].transform("min")) / (df.groupby(dim)["new_topic_score"].transform("max")- df.groupby(dim)["new_topic_score"].transform("min"))
    df["new_topic_score"] = df["new_topic_score"].round(2)
    heatmap = alt.Chart(df).mark_rect().encode(
        y=alt.Y(f'{dim}:O').title(""),
        x=alt.X('topic_shortname:O').title(""),
        color=alt.Color('sum(new_topic_score):Q').title("")
    )
    return heatmap

#%%Page Layout
container2 = st.container(border=False)
with container2:
    col21, col22 = st.columns(2)

    with col22:
        st.subheader(f"{metric} por hombres")
        st.altair_chart(topics_chart("Hombre","#29b09d"), theme="streamlit", use_container_width=True)

    with col21:
        st.subheader(f"{metric} por mujeres")
        st.altair_chart(topics_chart("Mujer","#efca53"), theme="streamlit", use_container_width=True)
    

container1 = st.container(border=False)
with container1:
        col11, col12 = st.columns(2)

        with col11:
            st.subheader("Segmentación por género")
            st.altair_chart(pie_chart("gender"), theme="streamlit", use_container_width=False)

        with col12:
            st.subheader(f"Selección {metric}")
            st.altair_chart(gender_chart(), theme="streamlit", use_container_width=True)
        st.altair_chart(heatmap("gender"), theme="streamlit", use_container_width=True)