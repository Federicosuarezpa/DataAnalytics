from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import pandas as pd
from spacy.lang.en import English
from tqdm import tqdm
import re
from bs4 import BeautifulSoup
from os import path
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from wordcloud import WordCloud
nltk.download('stopwords')

parser = English()

app = Dash(__name__)

reviews_over_time_data = ""
year_array = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012]
year_array_series = pd.Series(year_array)
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
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


def read_data(file_name):
    return pd.read_csv(file_name)


def write_data(data):
    data_reset = data.reset_index(drop=True)
    data_reset.to_csv('Processed_reviews.csv', index=False)


def preprocessing_data(raw_data):
    preprocessed_data = raw_data.drop_duplicates(subset=['UserId', 'ProfileName', 'Time', 'Text'], keep='first',
                                                 inplace=False)
    stopwords_array = stopwords.words('english')

    preprocessed_reviews = []
    # tqdm is for printing the status bar
    for sentance in tqdm(preprocessed_data['Text'].values):
        sentance = re.sub(r"http\S+", "", sentance)
        # removing html tags
        sentance = BeautifulSoup(sentance, 'html.parser').get_text()
        sentance = decontracted(sentance)
        # removing extra spaces and numbers
        sentance = re.sub("\S*\d\S*", "", sentance).strip()
        # removing non alphabels
        sentance = re.sub('[^A-Za-z]+', ' ', sentance)
        sentance = ' '.join(e.lower() for e in sentance.split() if e.lower() not in stopwords_array)
        preprocessed_reviews.append(sentance.strip())

    preprocessed_data['clean_text'] = preprocessed_reviews

    clean_data = preprocessed_data

    return clean_data


def reviews_over_time(processed_data):
    processed_data['date'] = pd.to_datetime(processed_data['Time'], unit='s')
    data_reviews = processed_data[['date', 'Score']]
    data_reviews.date = processed_data.date.dt.strftime('%Y-%m')
    dff = data_reviews.sort_values(by=['date']).reset_index(drop=True)
    data_score_one = dff[dff['Score'] == 1]
    data_score_two = dff[dff['Score'] == 2]
    data_score_three = dff[dff['Score'] == 3]
    data_score_four = dff[dff['Score'] == 4]
    data_score_five = dff[dff['Score'] == 5]

    processed_data['sentiment'] = processed_data['Score'].apply(lambda rating: +1 if rating > 3 else -1)

    # Calculate the number of revies positive >= 4, neutral = 3, negative <= 2
    number_positive = data_score_four['Score'].count() + data_score_five['Score'].count()
    number_neutral = data_score_three['Score'].count()
    number_negative = data_score_one['Score'].count() + data_score_two['Score'].count()

    data_score_one = data_score_one.groupby('date')['Score'].count().reset_index()
    data_score_two = data_score_two.groupby('date')['Score'].count().reset_index()
    data_score_three = data_score_three.groupby('date')['Score'].count().reset_index()
    data_score_four = data_score_four.groupby('date')['Score'].count().reset_index()
    data_score_five = data_score_five.groupby('date')['Score'].count().reset_index()

    # We group the reviews in different labels and dates
    dataset_score_one = {'label': '1 star', 'year': data_score_one['date'], 'reviews': data_score_one['Score']}
    dataset_score_one = pd.DataFrame(dataset_score_one)
    dataset_score_two = {'label': '2 stars', 'year': data_score_two['date'], 'reviews': data_score_two['Score']}
    dataset_score_two = pd.DataFrame(dataset_score_two)
    dataset_score_three = {'label': '3 stars', 'year': data_score_three['date'], 'reviews': data_score_three['Score']}
    dataset_score_three = pd.DataFrame(dataset_score_three)
    dataset_score_four = {'label': '4 stars', 'year': data_score_four['date'], 'reviews': data_score_four['Score']}
    dataset_score_four = pd.DataFrame(dataset_score_four)
    dataset_score_five = {'label': '5 stars', 'year': data_score_five['date'], 'reviews': data_score_five['Score']}
    dataset_score_five = pd.DataFrame(dataset_score_five)

    total_reviews = pd.concat([dataset_score_one,
                               dataset_score_two,
                               dataset_score_three,
                               dataset_score_four,
                               dataset_score_five])
    return total_reviews, number_negative, number_positive, number_neutral, processed_data


def decontracted(phrase):
    phrase = re.sub(r"won't", "will not", phrase)
    phrase = re.sub(r"can\'t", "can not", phrase)
    phrase = re.sub(r"n\'t", " not", phrase)
    phrase = re.sub(r"\'re", " are", phrase)
    phrase = re.sub(r"\'s", " is", phrase)
    phrase = re.sub(r"\'d", " would", phrase)
    phrase = re.sub(r"\'ll", " will", phrase)
    phrase = re.sub(r"\'t", " not", phrase)
    phrase = re.sub(r"\'ve", " have", phrase)
    phrase = re.sub(r"\'m", " am", phrase)

    return phrase


def calculate_sentimental_analysys_words(positive_reviews, negative_reviews, neutral_reviews, data):
    total_number_reviews = neutral_reviews + negative_reviews + positive_reviews
    percentage_positive_reviews = (positive_reviews / total_number_reviews) * 100
    percentage_neutral_reviews = (neutral_reviews / total_number_reviews) * 100
    percentage_negative_reviews = (negative_reviews / total_number_reviews) * 100
    print("Positive reviews: ", percentage_positive_reviews, "%")
    print("Negative reviews: ", percentage_negative_reviews, "%")
    print("Neutral reviews: ", percentage_neutral_reviews, "%")

    positive = data[data['sentiment'] == 1]
    negative = data[data['sentiment'] == -1]

    stopwords_array = set(stopwords.words('english'))
    stopwords_array.update(["br", "href", "good", "great"])
    pos = " ".join(review for review in positive.Summary)
    wordcloud2 = WordCloud(stopwords=stopwords_array).generate(pos)
    plt.imshow(wordcloud2, interpolation='bilinear')
    plt.savefig('wordcloudPositive.png')
    plt.axis("off")
    plt.show()

    neg = " ".join(str(review) for review in negative.Summary)
    wordcloud3 = WordCloud(stopwords=stopwords_array).generate(neg)
    plt.imshow(wordcloud3, interpolation='bilinear')
    plt.savefig('wordcloudNegative.png')
    plt.axis("off")
    plt.show()
    write_data(data)



def get_most_reviewed_products(data):
    n = 10
    return data['ProductId'].value_counts()[:n].index.tolist()


if __name__ == '__main__':
    if path.exists("Processed_reviews.csv"):
        data_frame = read_data("Processed_reviews.csv")
    else:
        preprocessed_data = read_data("Reviews.csv")
        data_frame = preprocessing_data(preprocessed_data)

    reviews_over_time_data, number_negative, number_positive, number_neutral, data = reviews_over_time(data_frame)
    calculate_sentimental_analysys_words(number_positive, number_negative, number_neutral, data_frame)
    most_reviewed_products = get_most_reviewed_products(data_frame)
    print(most_reviewed_products)


