# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#https://stackoverflow.com/questions/63945811/assigning-points-discrete-colors-in-plotly-mapbox-scatter color stuff

from dash import Dash, dash_table, dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from gbfs.services import SystemDiscoveryService
from gbfs.client import GBFSClient
from datetime import *
import plotly.offline as py
import plotly.graph_objs as go


app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

systemError = False
#Get a list of the systems available on GBFS
#available_stations = pd.read_csv("https://raw.githubusercontent.com/NABSA/gbfs/master/systems.csv")
available_stations = pd.read_csv("https://raw.githubusercontent.com/MobilityData/gbfs/master/systems.csv")
available_stations = available_stations[available_stations["Country Code"] == "US"]
available_stations = available_stations[["Name","Auto-Discovery URL"]]
available_stations = available_stations.rename(columns={"Name":"label", "Auto-Discovery URL":"value"})
available_stations = available_stations.to_dict(orient='records')
# Add filtering feature to see if a URL is live and if not, don't put it in the list

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='GBFS Feed Explorer',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    html.Div(children='A tool to help visualize GBFS bike data.', style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    html.Center([
    dcc.Dropdown(id="stationdropdown",options = available_stations,placeholder="Select a bike service", value="https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json",style={
        'textAlign': 'center',
        'width': '100%'
    })]),
    
    html.Div(id="data_field",children=[
        dbc.Placeholder(
            html.Div([html.H1(id="business-title", children="Test Station",style={
            'textAlign': 'center',
            'color': colors['text']
        })]),
            className="w-100",
            animation="wave",
        ),
        html.Center([
        html.Span([
            dbc.Button(
            [
                "Total Stations",
                dbc.Badge("2056", color="light", text_color="primary", className="ms-1",id = "total-station-badge"),
            ],
            color="primary",
        ),
            dbc.Button(
            [
                "Stations Online",
                dbc.Badge("2056", color="light", text_color="primary", className="ms-1",id = "online-station-badge"),
            ],
            color="success",
        ),
            dbc.Button(
            [
                "Stations Offline",
                dbc.Badge("2056", color="light", text_color="primary", className="ms-1",id = "offline-station-badge",),
            ],
            color="danger",
        )], style = {'width' : '100%'})]),
        html.Div(id = "station-information-div",children = [
        html.Div(["Click on a dot to see information for a specific station"],style={
            'textAlign': 'center',
            'color': colors['text'],
            'margin-top' : '20px'
        }),
        html.Div(id = "infoDIV", children=[
        html.H3(children="Station Information",style={
            'textAlign': 'center',
            'color': colors['text'],
            'margin-top' : '20px'
        }),
        html.H3(id = "station-name", children="Station Name",style={
            'textAlign': 'center',
            'color': colors['text'],
            'margin-top' : '20px'
        }),
        html.H4(id = "station-hours", children="Station Name",style={
            'textAlign': 'center',
            'color': colors['text'],
            'margin-top' : '20px'
        }),
        html.Center([
            html.Span([
                html.Div([html.H3(id = "classic-count"),
                          html.H4("Classic")], style={'display': 'inline-block', 'margin-right': '20px','color': colors['text']}),
                
                html.Div([html.H3(id = "electric-count", children = ["⚡8"]),
                          html.H4("EBikes")], style={'display': 'inline-block', 'margin-right': '20px','color': colors['text']}),
                html.Div([html.H3(id = "dock-count"),
                          html.H4("Docks")], style={'display': 'inline-block', 'margin-right': '20px','color': colors['text']}),
            ])
        ],style={'width': '100%','display': 'inline-block'})],style={'display' : 'none'}),
    ],style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top','margin-top': '10px'}),
    html.Div([
        dcc.Loading(children=[
        dcc.Graph(id="graph",style={
            'textAlign': 'center',
            'color': colors['text'],
            'width': '100%'
        }),
        html.Div(id="click-output", style={"color": colors["text"]})])
    ,
    ], style={'width': '50%', 'display': 'inline-block','margin-top': '10px'}),
     dcc.Loading(children=[
        dcc.Graph(id="hourlygraph",style={
            'textAlign': 'center',
            'color': colors['text'],
            'width': '100%',
            'display': 'None'
        })]),
        html.H6(f"Information last polled at {datetime.now().strftime('%H:%M:%S')}", style={'color' : 'white',
                                                           'width' : '100%',
                                                           'text-align' : 'center'})
    ]),
    html.H6("Made with ❤️ by TheDeadGPU",style={'color' : 'white',
                                                           'width' : '100%',
                                                           'text-align' : 'center'}),])

# Application Callback
def DumpStationData(url):
    client = GBFSClient(url)
    system_Info = client.request_feed('system_information').get('data')
    return ""

def CreateDataFrameFromGBFS(url):
    try:
        client = GBFSClient(url)
        station_Data = client.request_feed('station_information').get('data').get('stations')
        stationStatus_Data = client.request_feed('station_status').get('data').get('stations')
        #Create the DataFrames
        station_DF = pd.DataFrame(station_Data)
        stationStatus_DF = pd.DataFrame(stationStatus_Data)
        # Merge based on the 'id' column
        merged_df = pd.merge(station_DF, stationStatus_DF, on='station_id', how='inner')

        #Clean Data and add things
        merged_df['color'] = merged_df.apply(updateColor,axis=1)
        merged_df['is_renting'] = merged_df.apply(updateRentalStatus, axis=1)
        #merged_df['is_renting'] = merged_df["is_renting"].astype(str)
        DumpStationData(url)
        return merged_df
    except:
        print("An error has occured")
        systemError = True

def updateColor(row):
    if row['is_renting'] == 1:
        return "green"
    else:
        return "red"
def updateRentalStatus(row):
    if row['is_renting'] == 1:
        return True
    else:
        return False

@app.callback(
    Output("graph", "figure"),
    #Output("data-table","data"),
    Output("offline-station-badge", "children"),
    Output("online-station-badge", "children"),
    Output("total-station-badge", "children"),
    Output("business-title", "children"),
    Input("stationdropdown", "value"))
def display_choropleth(value):
    df = CreateDataFrameFromGBFS(value)
    band_colors_list = ['green', 'red']
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data=["num_bikes_available","station_id"],
        size = "num_bikes_available",
        size_max=10,
        #color_continuous_scale=["red", "green"],
        color_discrete_sequence=["green","Red"],
        category_orders={"is_renting" : [True,False]},
        color="is_renting",
        zoom=10,
        center=dict(lat=df.loc[0, 'lat'],lon=df.loc[0, 'lon']),
        
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(mapbox_bounds={"west": -180, "east": -50, "south": 20, "north": 90})
    #fig.update_layout(coloraxis_showscale=False)

    #Display the stats
    totalStations = len(df.index)
    totalOffline = len(df[df["is_renting"] == False].index)
    totalOnline = len(df[df["is_renting"] == True].index)
    ava = pd.DataFrame(available_stations)
    stationName = ava[ava["value"] == value]['label'].values[0]
    global sharedDF
    sharedDF = df
    columns_to_include = ['name','station_id']
    data_dict = df[columns_to_include].to_dict(orient='records')
    #dataout = df['name']
    #dataout = dataout.to_dict('records')
    return fig, totalOffline,totalOnline, totalStations, stationName

@app.callback(
    Output("station-name", "children"),
    Output("classic-count", "children"),
    Output("electric-count", "children"),
    Output("dock-count", "children"),
    Output("infoDIV", "style"),
    Input("graph", "clickData"),
    State("stationdropdown", "value"))
def handle_click(clickData, selected_station):
    if clickData is not None and selected_station is not None:
        #point_indices = clickData["points"][0]["pointIndex"]
        stationID = clickData["points"][0]["customdata"][1]
        print(f"Clicked station ID: {stationID}")
        #fig = CreateHourlyRentalData(stationID)
        tmpDF = sharedDF[sharedDF['station_id'] == stationID]
        name = tmpDF['name'].values[0]
        eBikeCount = tmpDF['num_ebikes_available'].values[0]
        classicBikeCount = tmpDF['num_bikes_available'].values[0]
        #tmpDF.to_csv("mergedSS.csv")
        print(tmpDF)
        #return [name],[classicBikeCount],["⚡",eBikeCount],["?"],{}
        return name,classicBikeCount,["⚡",eBikeCount],"?",{}
    return "","","","",{'display' : 'none'} 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)
