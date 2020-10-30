from utils import db
import dash
import dash_table
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

PAGE_SIZE = 5
USER_TYPE = "admin"

df = db.get_signals(0)
df['strategy_name'] = df['strategy_name'].apply(lambda s: f"[{s}](https://www.google.com)")
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', '`'):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


@app.callback(
    Output('table-filtering', "data"),
    [Input('table-filtering', "page_current"),
     Input('table-filtering', "page_size"),
     Input('table-filtering', "filter_query")])
def update_table(page_current,page_size, filter):
    print(filter)
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')


def signal_data_table():
    _columns = []
    for i in df.columns:
        if i == 'strategy_name':
            _columns.append({"name": i, "id": i, 'presentation': 'markdown'})
        else:
            _columns.append({"name": i, "id": i})
    return dash_table.DataTable(
        id='table-filtering',
        columns=_columns,
        page_current=0,
        style_cell={
            'textAlign': 'right',
            'fontSize': 15,
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
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


signal_catalog_mkd = dcc.Markdown('''

**Signal Dashboard Catalog is the entry point to other services**:

* Signal Dashboad Service
* Alert Service
* Test Data Upload Service
* Documentations 

''')


app.layout = html.Div([
    html.H2("Signal Dashboard Catalog"),
    signal_catalog_mkd,
    signal_data_table()
])

if __name__ == '__main__':
    app.run_server(debug=True)
