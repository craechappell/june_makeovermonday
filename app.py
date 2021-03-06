import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.tools import mpl_to_plotly
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.io as pio
import pandas as pd 
import matplotlib.pyplot as plt 
from pywaffle import Waffle 

plotly_template = pio.templates["plotly_dark"]

data = pd.read_csv('June_MM_Data.csv')

#Populating the drop down menu with the unique column names
dropdown = data.columns[2:].to_list()

#Populating the radio buttons with the unique continent names
    #User can pick all or just one at a time.
radio = list(data['CONTINENT'].dropna().unique())
radio.append('ALL')
radio.insert(0, radio.pop(-1))


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', '/assets/typography.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.server.static_folder = 'assets'
app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

server = app.server
colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

#chart_colors = ['#7FDBFF','#FFA37F', '#9BFF7F', '#E37FFF', '#ffea7f', '#d47fff']

color_dict = {'#7FDBFF': ['YES', 'MALE ONLY', 'UNKNOWN'],
              '#FF624C': ['NO', 'ANY GENDER', 'DEATH'], 
              '#9BFF7F': ['DE FACTO'], 
              '#FF8F4C': ['FOR LIFE'], 
              '#FFE84C': ['11-20 years'], 
              '#BCFF4C': ['1-10 years']}

styles = {'width': '30%',
               'padding-left': '5%',
               'display': 'inline-block',
               'color': colors['text'],
               'background':colors['background'],
               'line-height': '1',
               'height': '3vh'}

#Where the page is designed
#header, filters, and the graphs
app.layout = html.Div(style={'background': colors['background']}, children =[
    html.H2("Worldwide LGBT+ Rights",
            style={
            'textAlign': 'center',
            'color': colors['text'],
            'height': '5%'
            }
    ),

    html.Div(
        [
            dcc.Dropdown(
                id="Field",
                options=[{
                    'label': i,
                    'value': i
                } for i in dropdown],
                value = 'CRIMINALISATION_CONSENSUAL_SAME_SEX_SEXUAL_ACTS_LEGAL'
               ),
        ],
        style= styles
    ),

    #Stacked bar chart
    dcc.Graph(id='funnel-graph', style={'height':'38vh'}),
    html.Div(
        dcc.RadioItems(
                id='Continent',
                options=[{
                    'label': i,
                    'value': i
                } for i in radio],
                value='ALL',
                labelStyle={'display': 'inline-block'}
            ),
        style = styles
    ),
    html.Div(
        [
        dcc.Graph(id='waffle-graph', style={'width':'42%', 'height':'42vh', 'float':'left' }),
        html.P("This map is included to highlight the geospatial aspects of the first, and primary, question of this project: What countries criminalize consensual same-sex sexual acts between adults? We draw attention to those countries that changed their stance on this topic between 2017 and 2019, to highlight the evolving nature of international legislation on this topic.",
                style={'width':'14%','height':'42vh', 'float':'left', 'color':colors['text'], 'margin-top':'10px','font-size':'14px', 'margin-right':'5px'}),
        html.Iframe(src="//www.arcgis.com/apps/Embed/index.html?webmap=329d5a3d0cc841c485cf4b2f4a685f3f&extent=-180,-60.1031,180,81.9124&zoom=true&previewImage=false&scale=true&legendlayers=true&disable_scroll=true&theme=dark", 
            style={'width':'41%', 'height':'42vh', 'float':'left'})
            
        ]
    )
])

def clean_df(df_plot, Field):
    df_plot[Field] = df_plot[Field].str.strip()

    if Field == 'CRIMINALISATION_MAX_PENALTY':
        df_plot.loc[df_plot[Field].str.contains('death', case=False), Field] = "DEATH"
        df_plot = df_plot.replace({Field: 'UNDETERMINED'}, {Field: 'UNKNOWN'})
        df_plot = df_plot.replace({Field: ['1', '2', '3', '4', '5','6','7','8','9','10']}, {Field: '1-10 years'})
        df_plot = df_plot.replace({Field: ['11', '12', '13', '14', '15','16','17','18','19','20']}, {Field: '11-20 years'})
        df_plot = df_plot[df_plot['CRIMINALISATION_MAX_PENALTY']!= 'DOES NOT APPLY']

    elif Field == 'CRIMINALISATION_GENDER':
        df_plot = df_plot.replace({Field: 'M ONLY'}, {Field: 'MALE ONLY'})
        df_plot = df_plot[df_plot['CRIMINALISATION_GENDER']!= 'DOES NOT APPLY']

    else:
        df_plot = df_plot.replace({Field: 'Y'}, {Field: 'YES'})
        df_plot = df_plot.replace({Field: 'N'}, {Field: 'NO'})

    return df_plot


##### Stacked Bar Chart section
#updates the stacked bar chart when the filter is applied
@app.callback(
    dash.dependencies.Output('funnel-graph', 'figure'),
    [dash.dependencies.Input('Field', 'value')]
)

def update_graph(Field):
    df_plot = data.copy()
    df_plot = df_plot[['CONTINENT', 'COUNTRY', Field]].dropna()
    df_plot = clean_df(df_plot, Field)
    pv = pd.pivot_table(
      df_plot,
      index=['CONTINENT'],
      columns=[Field],
      values=['COUNTRY'],
      aggfunc=pd.Series.nunique,
      fill_value=0)

    return_data = []
    for i,column in enumerate(pv.columns.sortlevel(level=1, ascending=False)[0]):
        color_bar = ''
        for color_list in color_dict:
            options = color_dict.get(color_list)
            if column[1] in options:
                color_bar = color_list
        trace = go.Bar(x=pv.index, y=pv[column], name = column[1], marker = dict(color=color_bar))
        return_data.append(trace)

    #Actual figure being created is returned
    return {
        'data': return_data,
        'layout':
            go.Layout(
                title={'text' : "Number of Countries with {}".format(Field), "x": 0.5,  "yref": "paper","y" : 1, "yanchor" : "bottom"},
                barmode='stack',
                margin=dict(l=40, r=20, t=40, b=40),
                hovermode = 'closest',
                hoverlabel=dict(
                    font_size=24, 
                    font_family="Rockwell"
                ),
                template = 'plotly_dark'    
            )
    }


##### Waffle chart section
@app.callback(
    dash.dependencies.Output('waffle-graph', 'figure'),
    [dash.dependencies.Input('Field', 'value'),
     dash.dependencies.Input('Continent', 'value')]
)


def update_waffle(Field, Continent):
    title = Continent

    df_plot = data.copy()
    waffle_df = df_plot[['CONTINENT', 'COUNTRY', Field]].dropna()
    rows = 10
    #use entire dataset if all is chosen- otherwise fitler by continent radio button
    if Continent != 'ALL':
      waffle_df = waffle_df[waffle_df['CONTINENT']== Continent]
      rows = 5
    #prepping the data by grouping by the field. either yes or no
    waffle_df = clean_df(waffle_df, Field)
    grouped = waffle_df.groupby(Field).count()
    grouped = pd.DataFrame(grouped).sort_index(ascending=False)
    group_series = grouped.to_dict()
    ds = pd.Series(group_series['CONTINENT'])
    #ds = group_series.sort_index(ascending=False)


    Xlim = 16
    Ylim = 13
    Xpos = 0
    Ypos = 6 ##change to zero for upwards
    series = []
    for name, count in ds.iteritems():
        x = []
        y = []
        countries = []
        waffle_colors = []
        for color_list in color_dict:
          options = color_dict.get(color_list)
          if name in options:
            color = color_list
        response = waffle_df[waffle_df[Field]== name].reset_index()
        for j in range(0, count):
            if Xpos == Xlim:
                Xpos = 0
                Ypos -= 1 ##change to positive for upwards
            x.append(Xpos)
            y.append(Ypos)
            countries.append(response['COUNTRY'][j])
            waffle_colors.append(color)
            Xpos += 1
        series.append(go.Scatter(x=x, y=y, mode='markers', marker={'symbol': 'square', 'size': 12, 'color': waffle_colors}, name=f'{name}: {count}', hovertext = countries, hoverinfo = 'text' ))


    return go.Figure(
        dict(
            data=series, 
            layout=go.Layout(
                title={'text': title, 'x': 0.5,  "yref": "paper","y" : 1, "yanchor" : "bottom" },
                paper_bgcolor=colors['background'],#'rgba(255,255,255,1)',
                plot_bgcolor=colors['background'],
                margin=dict(l=40, r=20, t=40, b=30),
                xaxis=dict(showgrid=False,zeroline= False, showline=False, visible=False, showticklabels=False),
                yaxis=dict(showgrid=False,zeroline= False, showline=False, visible=False, showticklabels=False),
                template = 'plotly_dark',
                hoverlabel=dict(
                    font_size=24, 
                    font_family="Rockwell"
                )
                )
            )
   )
    


#Runs the entire script and starts the server
if __name__ == '__main__':
    app.run_server(debug=True)
