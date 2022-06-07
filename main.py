from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import pandas as pd
from spacy.lang.en import English
from os import path
import utilities_food_analysis as aux_func

parser = English()

app = Dash(__name__)

if path.exists("Processed_reviews.csv"):
    data_frame = aux_func.read_data("Processed_reviews.csv")
else:
    preprocessed_data = aux_func.read_data("Reviews.csv")
    data_frame = aux_func.preprocessing_data(preprocessed_data)

reviews_over_time_data, number_negative, number_positive, number_neutral, data = aux_func.reviews_over_time(data_frame)
aux_func.calculate_sentimental_analysys_words(number_positive, number_negative, number_neutral, data_frame)
most_reviewed_products_names, most_reviewed_products_quantity = aux_func.get_most_reviewed_products(data_frame)

year_array = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012]
year_array_series = pd.Series(year_array)
df = pd.DataFrame({
    "Reviews": ["Neutral", "Negative", "Positive"],
    "Amount": [number_neutral, number_negative, number_positive],
    "Type Review": ["Neutral", "Negative", "Positive"]
})

df_most_reviewed_products = pd.DataFrame({
    "ProductId": most_reviewed_products_names,
    "Amount": most_reviewed_products_quantity,
    "Product Id": most_reviewed_products_names
})

fig = px.bar(df, x="Reviews", y="Amount", color="Type Review")
fig_most_reviewed_products = px.bar(df_most_reviewed_products, x="ProductId", y="Amount", color="Product Id")
app.layout = html.Div(children=[
    # All elements from the top of the page
    html.Div([
        dcc.Graph(id='graph-with-slider'),
        dcc.Slider(
            year_array_series.min(),
            year_array_series.max(),
            step=None,
            value=year_array_series.max(),
            marks={str(year): str(year) for year in year_array_series.unique()},
            id='year-slider'
        )
    ]),
    html.Div(children='''
        '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
    html.Div(children='''
        '''),

    dcc.Graph(
        id='example-graph-2',
        figure=fig_most_reviewed_products
    ),

])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    reviews_over_time_data_filtered = reviews_over_time_data[reviews_over_time_data.year <= str(selected_year)]
    fig = px.scatter(reviews_over_time_data_filtered, x="year", y="reviews",
                     size="reviews", color="label",
                     hover_name="label")

    fig.update_layout(transition_duration=500)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)