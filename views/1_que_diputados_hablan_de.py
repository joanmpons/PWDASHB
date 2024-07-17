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
 
#%%Define charts and dfs
def data_by_metric():
    df = pd.DataFrame(df_dept_detail)
    if metric == "Temas más hablados":
            df = df[df["topic_shortname"].isin(topics_select)]
            df = df.groupby("name_x").filter(lambda x: (x['topic_score'] > foot_min).all())
    elif metric == "Temas priorizados":
        df["new_topic_score"] = np.where((df["topic_score"] == df[["name_x","topic_score"]].groupby(["name_x"]).transform("max")["topic_score"]) &
                                        (df["topic_score"] > 0), 1, 0)
        df = df[df["topic_shortname"].isin(topics_select)]
        df = df.groupby("name_x").filter(lambda x: (x['new_topic_score'] == 1).all())
    else:
        df["new_topic_score"] = df.groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
        df["new_topic_score"] = df["new_topic_score"].fillna(100)
        df["new_topic_score"] = 100 - df["new_topic_score"]
        df = df[df["topic_shortname"].isin(topics_select)]
        df = df.groupby("name_x").filter(lambda x: ((x['new_topic_score'] >= priority_rank) & (x['topic_score'] > foot_min)).all())
    return df

def pie_chart(dim):
    df = data_by_metric()
    df["new_topic_score"] = 1 
    df = df.groupby([dim]).sum().reset_index().round(2)
    chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta="new_topic_score",
        color=alt.Color(f"{dim}:N").title("")
        ).interactive()
    return chart

def bar_chart():
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
    df = df[df["topic_shortname"].isin(topics_select)].groupby("topic_shortname").sum().reset_index().round(2)
    chart = alt.Chart(df).mark_bar(color='#efca53').encode(
            alt.X('topic_shortname', sort='-y').title(""),
            alt.Y('new_topic_score').title(""),
            alt.Tooltip(['topic_shortname', 'new_topic_score']),
        ).interactive()
    return chart


#%%Page Layout
container = st.container(border=True)

with container:
    col11, col12, col13 = st.columns(3)

    with col11:
        st.subheader("Segmentación por género")
        st.altair_chart(pie_chart("gender"), theme="streamlit", use_container_width=False)
        
    with col12:
        st.subheader("Segmentación por edad")
        st.altair_chart(pie_chart("age_bin"), theme="streamlit", use_container_width=False)

    with col13:
        st.subheader("Segmentación por región")
        st.altair_chart(pie_chart("Region"), theme="streamlit", use_container_width=False)

col21, col22 = st.columns(2)

with col21:
        deputy_list = data_by_metric()
        deputy_list["agg_score"] = deputy_list.groupby("name_x").transform("sum")["topic_score"]
        deputy_list = deputy_list.sort_values("agg_score", ascending = False)[["name_x","gender","age_bin","constituency","topic_shortname","topic_score"]]

        st.dataframe(data = deputy_list, column_config = {"name_x": "Diputados",
                                                        "gender":"Género",
                                                        "age_bin": "Edad",
                                                        "constituency":"Circunscripción",
                                                        "topic_shortname":"Tema",
                                                        "topic_score":"Huella"}, use_container_width=True, hide_index=True)

with col22:
    container2 = st.container(border=True)

    with container2:
        st.altair_chart(bar_chart(), theme="streamlit", use_container_width=True)

#
st.dataframe(data_by_metric())