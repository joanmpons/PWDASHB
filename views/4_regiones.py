#%%Import packages
import altair as alt
import numpy as np
import pandas as pd
import geopandas as gpd
import streamlit as st
import folium, matplotlib, mapclassify
from streamlit_folium import st_folium

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
#%%

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
        df["new_topic_score"] = df[df["topic_score"] > foot_min].groupby(["name_x"]).rank(method="dense", ascending=False)["topic_score"]
        df["new_topic_score"] = df["new_topic_score"].fillna(100)
        df["new_topic_score"] = 100 - df["new_topic_score"]
        df = df[df["topic_shortname"].isin(topics_select)]
        df = df.groupby("name_x").filter(lambda x: (x['new_topic_score'] >= priority_rank).all())
    return df
df = data_by_metric()
st.dataframe(df)

st.header("In development")
constit_coords = gpd.read_file("gadm41_ESP_2.json.zip")
#Test
constit_coords["metric"] = np.random.randint(0,400,52)
st_folium(constit_coords.explore(column="metric",zoom_start=5),use_container_width=True)

