import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import calendar
import folium
from streamlit_folium import st_folium


APP_TITLE = "US Flights Delay Report"

#create wrangle function
path = "Flights data/flightdata.csv"

def wrangle(path):

    df = pd.read_csv(path)

    #drop unnamed column
    df = df.drop(columns = "Unnamed: 0")

    #drop null values
    df = df.dropna()

    #remove outliers below 1% and above 90% for columns in delay_fields
    arr_01 = df["arr_delay"].quantile(0.01)
    arr_90 = df["arr_delay"].quantile(0.9)
    df = df[df["arr_delay"] > arr_01]
    df = df[df["arr_delay"] < arr_90]

    dep_01 = df["dep_delay"].quantile(0.01)
    dep_90 = df["dep_delay"].quantile(0.9)
    df = df[df["dep_delay"] > dep_01]
    df = df[df["dep_delay"] < dep_90]

    #create delay field
    df["long_delay"] =(df["dep_delay"] > 14).astype(int)
    df['long_delay'] = pd.Categorical(df.long_delay)

    return df

def flight_filters(df):
    Airline = list(df['airline'].unique())
    Airline.sort()
    Airline = st.sidebar.selectbox('Airline', Airline, len(Airline)-1)
    #st.header('Please Select Airline')
    return Airline

def airport_filter(df):
    airport_list = [''] + list(df['airport'].unique())
    airport_list.sort()
    #state_index = state_list.index(state_name) if state_name and state_name in state_list else 0
    return st.sidebar.selectbox('Airport', airport_list)

def delay_type_filter(df):
    return st.sidebar.selectbox('Delay Type', ['dep_delay', 'arr_delay'])


def display_departure1_facts(df, airline, airport, delay_type):
    df = df[(df['airline'] == airline) & (df['airport'] == airport)]
    if delay_type == "dep_delay":
        total = df["dep_delay"].sum()
        title = "Total Departure Delay Time (secs)"
    else:
        total = df["arr_delay"].sum()
        title = "Total Arrival Delay Time (secs)"
    df.drop_duplicates(inplace=True)
    st.metric(title, total)



def display_departure_facts(df, airline, airport, delay_type):
    df = df[(df['airline'] == airline) & (df['airport'] == airport)]
    total = df["dep_delay"].sum()
    title = "Total Departure Delay Time (secs)"
    df.drop_duplicates(inplace=True)
    st.metric(title, total)

def display_arrival_facts(df, airline, airport, delay_type):
    df = df[(df['airline'] == airline) & (df['airport'] == airport)]
    total = df["arr_delay"].sum()
    title = "Total Arrival Delay Time (secs)"
    df.drop_duplicates(inplace=True)
    st.metric(title, total)



def airport_histogram(df):

    dl = df.query("long_delay == 1")
    dl["long_delay"] = dl["long_delay"].astype(int)

    airport_delay = (
        dl.groupby(by=["airport"]).sum()[["long_delay"]].sort_values(by="long_delay")
    )
    fig = px.bar(
        airport_delay,
        x="long_delay",
        y=airport_delay.index,
        orientation="h",
        title="<b>Long Delays By Airport</b>",
        color_discrete_sequence=["#0083B8"] * len(airport_delay),
        template="plotly_white",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    st.plotly_chart(fig, use_container_width=False)

def airline_histogram(df):

    dl = df.query("long_delay == 1")
    dl["long_delay"] = dl["long_delay"].astype(int)

    airline_delay = (
        dl.groupby(by=["airline"]).sum()[["long_delay"]].sort_values(by="long_delay")
    )
    fig = px.bar(
        airline_delay,
        x="long_delay",
        y=airline_delay.index,
        orientation="h",
        title="<b>Long Delays By Airline</b>",
        color_discrete_sequence=["#0083B8"] * len(airline_delay),
        template="plotly_white",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    st.plotly_chart(fig, use_container_width=False)



#create unique airports    
#unique_airport = df[~df[["airport"]].duplicated()].reset_index(drop=True)

def map_airport1(df,  zoom):
    
    lat_map=38
    lon_map=-96.5
    f = folium.Figure(width=1000, height=500)
    m = folium.Map(location=[38, -96.5], zoom_start=4, scrollWheelZoom=False, tiles='CartoDB positron').add_to(f)

        
    for i in range(0,len(df)):
        folium.Marker(location=[df["lat"][i],df["lon"][i]],
                      popup='<i>International Airport</i>', 
                      tooltip = df.airport[i], 
                      icon=folium.Icon(icon_color='white',icon ='plane',prefix='fa')).add_to(m)

    choropleth = folium.Choropleth(
        geo_data='geo-json/us-state-boundaries.geojson',
        data=df,
        columns=('airport', "avgdelay"),
        key_on='feature.properties.name',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(m)

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['name'], labels=False)
    )
    
    st_map = st_folium(m, width=700, height=450)

    return st_map




def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)

    #LOAD DATA
    df = wrangle(path)
    

    #create unique airports    
    unique_airport = df[~df[["airport"]].duplicated()].reset_index(drop=True)
    #st.write(unique_airport)

    #---SIDE BAR---

    #st.sidebar.header("Please Filter Here:")
    #Airline = st.sidebar.multiselect(
    #"Select the Airline:",
    #options=df["airline"].unique(),
    #default=df["airline"].unique()
    #)

    

    #DISPLAY FILtERS and MAP
    airline = flight_filters(df)
    airport = airport_filter(df)
    delay_type = delay_type_filter(df)
    map = map_airport1(unique_airport, 1)

    #DISPLAY METRICS
    note = "Note: A negative value indicates no delay, and a positive value indicates a delay"
    
    st.subheader(f'{airline} delay facts for {airport} Airport')
    st.caption(note)
   

    col1, col2 = st.columns(2)
    with col1:
        display_departure_facts(df, airline, airport, "dep_delay")
    with col2:
        display_arrival_facts(df, airline, airport, "arr_delay")

    st.markdown("---")


    #DISPLAY HISTOGRAMS

    

    left_column, right_column = st.columns(2)
    with left_column:
        airport_histogram(df)
    with right_column:
        airline_histogram(df)




if __name__ == "__main__":
    main()