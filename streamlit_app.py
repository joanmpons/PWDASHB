import json
import numpy as np
import requests as re
import pandas as pd
import streamlit as st
import time

pages = [
    st.Page(
        "views/0_de_que_hablan_los_diputados.py",
        title="¿De qué hablan los diputados...?",
    ),
    st.Page(
        "views/1_que_diputados_hablan_de.py", title="1 ¿Qué diputados hablan de...?"
    ),
    st.Page("views/2_genero.py", title="2 Género"),
    st.Page("views/3_grupos_de_edad.py", title="3 Grupos de edad"),
    st.Page("views/4_regiones.py", title="4 Regiones"),
]


pg = st.navigation(pages)

# %%Page Config
st.set_page_config(
    page_title="De qué hablan los diputados?",
    # page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)


# %%Data Extraction
# Caching data fetched from the API. The values will be updated every 24h
@st.cache_data(ttl=86400, show_spinner="Actualizando los datos...")
def api_call():
    response = re.get("https://api.quehacenlosdiputados.es/topics/")
    topics = json.loads(response.content)
    df_topics = pd.json_normalize(topics)
    df_topics.rename(columns={"shortname": "topic_shortname"}, inplace=True)

    # Getting political groups
    response = re.get(
        "https://api.quehacenlosdiputados.es/parliamentary-groups/?compact=true"
    )
    groups = json.loads(response.content)
    df_groups = pd.json_normalize(groups)

    # Getting deputies
    response = re.get("https://api.quehacenlosdiputados.es/deputies/?compact=true")
    deputies = json.loads(response.content)
    df_dept = pd.DataFrame(deputies)

    # Deputy detail
    dept_details = []
    # limit this loop with .head() if the API does not support all calls
    for dept in pd.unique(df_dept["id"]):
        response = re.get(f"https://api.quehacenlosdiputados.es/deputies/{dept}")
        dept_details.append(json.loads(response.content))

    for element in dept_details:
        if element.get("party_name") == None:
            element.update({"party_name": "Unknown"})

    df_dept_detail = pd.json_normalize(
        dept_details,
        "footprint_by_topics",
        [
            "active",
            "constituency",
            "parliamentarygroup",
            "party_name",
            "name",
            "age",
            "gender",
            "footprint",
        ],
        record_prefix="topic_",
    )

    # Getting footprint by parlamentary group
    foot_pg_topics = []
    foot_pg = []

    for pg in pd.unique(df_groups["name"]):
        response = re.get(
            f"https://api.quehacenlosdiputados.es/footprint/by-parliamentarygroup?parliamentarygroup={pg}"
        )
        foot_pg_topics.append(json.loads(response.content))

    for i in range(len(foot_pg_topics)):
        foot_pg.append({k: v for (k, v) in foot_pg_topics[i].items() if k != "topics"})

    foot_pg_topics = pd.json_normalize(
        foot_pg_topics, "topics", ["id"], record_prefix="topic_"
    )
    foot_pg = pd.json_normalize(foot_pg)

    success = st.success("Los resultados se han actualizado correctamente!")
    time.sleep(3)
    success.empty()
    return df_topics, df_groups, df_dept, df_dept_detail, foot_pg, foot_pg_topics


df_topics, df_groups, df_dept, df_dept_detail, foot_pg, foot_pg_topics = api_call()

# %%Creating final dfs
# Age bins
df_dept_detail["age_bin"] = np.where(
    df_dept_detail["age"] < 35,
    "Under 35",
    np.where(
        df_dept_detail["age"] < 45,
        "35 - 45",
        np.where(
            df_dept_detail["age"] <= 55,
            "45 - 55",
            np.where(df_dept_detail["age"] > 55, "Over 55", np.nan),
        ),
    ),
)
df_dept_detail = df_dept_detail.merge(
    df_topics[["topic_shortname", "name"]], left_on="topic_name", right_on="name"
)
# Rural/Urban regions
rur_zones = pd.read_csv("Rural_zones.csv", sep=";", thousands=".")
rur_zones = rur_zones[
    (rur_zones["Sexo"] == "Total")
    & (rur_zones["Zona"] == "Total")
    & (rur_zones["Tipo de vivienda"] == "Población Total")
    & (rur_zones["Zonas"].isin(["Total urbano", "Zona rural"]))
]
rur_zones = rur_zones.pivot(
    index="Provincias", columns="Zonas", values="Total"
).reset_index()
rur_zones["Region"] = np.where(
    rur_zones["Zona rural"].astype(float)
    / (rur_zones["Zona rural"].astype(float) + rur_zones["Total urbano"].astype(float))
    * 100
    > 55,
    "Rural",
    "Urban",
)
df_dept_detail = pd.merge(
    df_dept_detail,
    rur_zones[["Provincias", "Region"]],
    left_on="constituency",
    right_on="Provincias",
    how="left",
).drop("Provincias", axis=1)
df_dept_detail["Region"] = np.where(
    df_dept_detail["constituency"].isin(["Ceuta", "Melilla"]),
    "Urban",
    df_dept_detail["Region"],
)
# Identifying ODS topics vs classic topics
df_dept_detail["Topic type"] = np.where(
    df_dept_detail["topic_shortname"].str.contains("ODS"),
    "Agenda 20/30",
    "Temas Clásicos",
)
# Final groups dfs, probably not needed though
df_groups = df_groups.merge(foot_pg, on="id")
df_groups_topics = df_groups.merge(foot_pg_topics, on="id")
df_groups_topics = df_groups_topics.merge(
    df_topics[["topic_shortname", "name"]], left_on="topic_name", right_on="name"
)

# %%Updating session state dict
if "df_topics" not in st.session_state:
    st.session_state.df_topics = df_topics
if "df_groups" not in st.session_state:
    st.session_state.df_groups = df_groups
if "df_dept" not in st.session_state:
    st.session_state.df_dept = df_dept
if "df_dept_detail" not in st.session_state:
    st.session_state.df_dept_detail = df_dept_detail
if "df_groups_topics" not in st.session_state:
    st.session_state.df_groups_topics = df_groups_topics

pg.run()
