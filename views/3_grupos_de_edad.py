# %%Import packages
import altair as alt
import json
import numpy as np
import requests as re
import pandas as pd
import streamlit as st

# %%Import variables
df_topics = st.session_state.df_topics
df_groups = st.session_state.df_groups
df_dept = st.session_state.df_dept
df_dept_detail = st.session_state.df_dept_detail
df_groups_topics = st.session_state.df_groups_topics

# %%
st.header("In development")
