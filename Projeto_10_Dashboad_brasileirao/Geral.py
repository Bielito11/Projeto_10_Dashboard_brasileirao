import streamlit as st
import plotly.express as px
import pandas as pd
st.set_page_config(layout='wide')

df = pd.read_csv('Tabela_Clubes.csv')
df['Gols_Feitos'] = df['GolsF/S'].apply(lambda x: int(x.split(':')[0]))
df['Gols_Sofridos'] = df['GolsF/S'].apply(lambda x: int(x.split(':')[1]))

# ============================== SIDEBAR
lista_anos = df['Ano'].unique().tolist()
filtro_anos = st.sidebar.multiselect('Ano', lista_anos, default=lista_anos)

# ============================== BODY
df = df[df['Ano'].apply(lambda x: x in filtro_anos)]

with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric('Quantidade de Estrangeiros', df['Estrangeiros'].sum())

    with col2:
        with st.container(border=True):
            idade_media = df['Idade_Media'].apply(lambda x: float(x.replace(',', '.'))).mean()
            st.metric('Idade média dos jogadores', f'{idade_media:.0f}')


    with col3:
        with st.container(border=True):
            valor_medio = df['Valor_total'].mean()
            st.metric('Valor médio dos times', f'R$ {df['Valor_total'].mean():,.0f}')


with st.container():
    col1, col2 = st.columns(2)
    with col1:
        with st.container(width='stretch'):
            podio = df[df['Pos.'] <=5][['Ano', 'Pos.', 'Clubes']].sort_values(['Ano', 'Pos.'])
            st.table(podio)

    with col2:
        with st.container(width='stretch'):
            g1 = px.bar(df, x='Clubes', y='Gols_Feitos', title='Total de Gols Feitos')
            st.plotly_chart(g1)

            g2 = px.line(df, x='Ano', y='Valor_total', color='Clubes', markers='*', title='Valor Total dos times através dos anos')
            st.plotly_chart(g2)