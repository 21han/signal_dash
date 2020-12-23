import base64
import datetime
import io
import logging

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import jwt
import pandas as pd
from cryptography.fernet import Fernet, InvalidToken
from dash.dependencies import Input, Output, State

from utils import db
from utils.security import Security

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
application = app.server


@app.callback(Output('error_redirect_page', 'children'),
              Output('user_id-state', 'children'),
              [Input('catalog_service_url', 'href')])
def check_token(pathname):
    path_info = pathname.split("?token=")
    logger.info(f"path name: {pathname} | path_info: {path_info}")
    if len(path_info) != 2:
        logger.error("** token doesn't exist")
        return dcc.Location(href=Security.login_page_url, id="any"), None

    signed_token = path_info[1]

    try:
        jwt_token = Fernet(Security.fernet_secret).decrypt(signed_token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, TypeError):
        logger.error("Invalid Token Error")
        return dcc.Location(href=Security.login_page_url, id="any"), None

    post_man_bear_token = "Bearer "
    if jwt_token.startswith(post_man_bear_token):
        jwt_token = jwt_token[len(post_man_bear_token):]
    try:
        payload = jwt.decode(jwt_token, Security.jwt_secret,
                             algorithms=[Security.jwt_algo])
        logger.info(f"** payload\n{payload}")
        if payload["role"] not in {"support", "ip"}:
            logger.error("** Role not supported")
            return dcc.Location(href=Security.login_page_url,
                                id="any"), None
        else:
            logger.info("**success")
            return "", payload['user_id']
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        logger.error("** Decode/ExpiredSignatrue Errors")
        return dcc.Location(href=Security.login_page_url, id="any"), None
    return dcc.Location(href=Security.login_page_url, id="any"), None


@app.callback(
    Output('signal_data_table', 'children'),
    Input('user_id-state', 'children')
)
def signal_data_table(user_id):
    df = db.get_signals(user_id)
    return dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
    )


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    df = None
    try:
        if 'csv' in filename:
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            logger.info(f"data shape: {df.shape}\n"
                        f"data columns: {df.columns}")
        elif 'xls' in filename:
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
        html.Hr(),
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


@app.callback(Output('dash_redirect_page', 'children'),
              Input('go-to-dash', 'n_clicks'),
              Input('catalog_service_url', 'href'))
def go_to_dash(click, pathname):
    path_info = pathname.split("?token=")
    if len(path_info) != 2:
        logger.error("** token doesn't exist")
        return dcc.Location(href=Security.login_page_url, id="any")
    signed_token = path_info[1]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'go-to-dash' in changed_id:
        return dcc.Location(href=f"{Security.dash_page_url}?token={signed_token}", id="any")


@app.callback(Output('dash_redirect_page', 'children'),
              Input('go-to-alert', 'n_clicks'),
              Input('catalog_service_url', 'href'))
def go_to_dash(click, pathname):
    path_info = pathname.split("?token=")
    if len(path_info) != 2:
        logger.error("** token doesn't exist")
        return dcc.Location(href=Security.login_page_url, id="any")
    signed_token = path_info[1]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'go-to-alert' in changed_id:
        return dcc.Location(href=f"{Security.alert_page_url}?token={signed_token}", id="any")


@app.callback(Output('user_management_redirect_page', 'children'),
              Input('manage-user', 'n_clicks'),
              Input('catalog_service_url', 'href'))
def manage_user(click, pathname):
    path_info = pathname.split("?token=")
    if len(path_info) != 2:
        logger.error("** token doesn't exist")
        return dcc.Location(href=Security.login_page_url, id="any")
    signed_token = path_info[1]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'manage-user' in changed_id:
        return dcc.Location(href=f"{Security.user_page_url}?token={signed_token}", id="any")


app.layout = html.Div([
    dcc.Location(id='catalog_service_url', refresh=False),
    html.Div(id='error_redirect_page'),
    html.Button(id='user_id-state', value='Connection Established'),
    dcc.Tabs([
        dcc.Tab(label='Description', children=[
            html.Div(html.H2("Signal Dashboard Catalog"), style=style_center),
            html.Div(signal_catalog_mkd, style=style_center),
        ]),
        dcc.Tab(label='Signals', children=[
            html.Div(id='signal_data_table', style=style_center)
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
    ]),
    html.Button('Go to Dash', id='go-to-dash', n_clicks=0),
    html.Button('Manage User', id='manage-user', n_clicks=0),
    html.Button('Go to Alert', id='go-to-alert', n_clicks=0),
    html.Div(id='dash_redirect_page'),
    html.Div(id='user_management_redirect_page')
])

# https://docs.faculty.ai/user-guide/apps/examples/dash_file_upload_download.html
if __name__ == '__main__':
    app.run_server(debug=True)
