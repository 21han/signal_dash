from utils import db
from utils import helper
import base64
import datetime
import io
import pandas as pd
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

PAGE_SIZE = 5
USER_TYPE = "admin"

# TODO: discuss with Zhicheng how to get USER ID from him
USER_ID = 0

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
application = app.server


@app.callback(
    Output('table-filtering', "data"),
    [Input('table-filtering', "page_current"),
     Input('table-filtering', "page_size"),
     Input('table-filtering', "filter_query")])
def update_table(page_current, page_size, _filter):
    filtering_expressions = _filter.split(' && ')
    df = db.get_signals(USER_ID)
    df['signal_name'] = df['signal_name'].apply(lambda s: f"[{s}](https://dash-gallery.plotly.host/dash-time-series/)")
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = helper.split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            df = df.loc[getattr(df[col_name], operator)(filter_value)]
        elif operator == 'contains':
            df = df.loc[df[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            df = df.loc[df[col_name].str.startswith(filter_value)]

    return df.iloc[
           page_current * page_size:(page_current + 1) * page_size
           ].to_dict('records')


def signal_data_table():
    _columns = []
    df = db.get_signals(USER_ID)
    df['signal_name'] = df['signal_name'].apply(lambda s: f"[{s}](https://dash-gallery.plotly.host/dash-time-series/)")
    for i in df.columns:
        if i == 'signal_name':
            _columns.append({"name": i, "id": i, 'presentation': 'markdown'})
        else:
            _columns.append({"name": i, "id": i})
    return dash_table.DataTable(
        id='table-filtering',
        columns=_columns,
        page_current=0,
        style_cell={
            'textAlign': 'left',
        },
        page_size=PAGE_SIZE,
        page_action='custom',
        filter_action='custom',
        filter_query='',
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
    )


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    df = None
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            logger.info(f"data shape: {df.shape}\n"
                        f"data columns: {df.columns}")
            # TODO: send this file to S3
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


signal_catalog_mkd = dcc.Markdown('''

**Signal Dashboard Catalog is the entry point to other services**:

* Signal Dashboad Service
* Alert Service
* Test Data Upload Service
* Documentations 

''')

style_center = {
    'width': '100%',
    'display': 'flex',
    'align-items': 'center',
    'justify-content': 'center',
}

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Description', children=[
            html.Div(html.H2("Signal Dashboard Catalog"), style=style_center),
            html.Div(signal_catalog_mkd, style=style_center),
        ]),
        dcc.Tab(label='Signals', children=[
            html.Div(signal_data_table(), style=style_center)
        ]),
        dcc.Tab(label='Upload Data', children=[
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files', style={'color': 'blue', 'fontSize': 16})
                ]),
                style=style_center,
                # Allow multiple files to be uploaded
                multiple=True
            ),
            html.Div(id='output-data-upload', style=style_center),
        ])
    ])
])

# https://docs.faculty.ai/user-guide/apps/examples/dash_file_upload_download.html
if __name__ == '__main__':
    app.run_server(debug=True)
