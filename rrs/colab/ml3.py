from keras.regularizers import l2
from keras.optimizers import adam_v2
from keras.layers.embeddings import Embedding
from keras.layers import Input, Reshape, Dot
from keras.models import Model
from keras.layers import Add, Activation, Lambda
import ast
import seaborn as sns
import matplotlib.pyplot as plt
from rrs.colab.utils import prettyPrint as pp
import numpy as np  # linear algebra
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
import warnings
warnings.filterwarnings("ignore")

# plotting

subset_business = pd.DataFrame()
subset_review = pd.DataFrame()
df_final = pd.DataFrame()
rest = pd.DataFrame()
combined_business_data = pd.DataFrame()

X_train_keras = pd.DataFrame()
y_train_keras = pd.DataFrame()
X_test_keras = pd.DataFrame()
y_test_keras = pd.DataFrame()
combined_business_data_keras = pd.DataFrame()
reconstructed_model = Model


def __init__(self) -> None:
    pass


def readData():
    # import the data (chunksize returns jsonReader for iteration)
    businesses = pd.read_json("C:\\Users\\Midhun\\Downloads\\yelp_academic_dataset_business.json",
                              lines=True, orient='columns', chunksize=1000000)
    reviews = pd.read_json("C:\\Users\\Midhun\\Downloads\\yelp_academic_dataset_review.json",
                           lines=True, orient='columns', chunksize=1000000)

    # Refering to global values
    global subset_business, subset_review
    # read the data
    for business in businesses:
        subset_business = business
        break

    for review in reviews:
        subset_review = review
        break
    pp("readData: Read data")
    print(subset_business.head())
    print(subset_review.head())
    # return subset_business, subset_review


def plotCityRatings():
    global subset_business
    # peak the tables
    # print(subset_business.head(2))
    # print(subset_review.head(2))

    # City with most reviews
    color = sns.color_palette()
    # Get the distribution of the ratings
    x = subset_business['city'].value_counts()
    x = x.sort_values(ascending=False)
    x = x.iloc[0:20]
    plt.figure(figsize=(16, 4))
    ax = sns.barplot(x.index, x.values, alpha=0.8, color=color[3])
    plt.title("Which city has the most reviews?")
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45)
    plt.ylabel('# businesses', fontsize=12)
    plt.xlabel('City', fontsize=12)

    # adding the text labels
    rects = ax.patches
    labels = x.values
    for rect, label in zip(rects, labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2,
                height + 5, label, ha='center', va='bottom')

    plt.show()


def selectRestaurantsInCity(cityName):
    # print(subset_business.columns)
    # Businesses in Philadelphia and currently open business
    city = subset_business[(subset_business['city'] == cityName) & (
        subset_business['is_open'] == 1)]
    philadelphia = city[['business_id', 'name',
                         'address', 'categories', 'attributes', 'stars']]
    # print(city.shape)
    # print(philadelphia.shape)
    return philadelphia


def plotFamousBusinessInCity(philadelphia):
    business_cats = ""
    for category in philadelphia['categories']:
        if category != None:
            business_cats += ", " + category

    cats = pd.DataFrame(business_cats.split(','), columns=['category'])
    x = cats.category.value_counts()
    # print("There are ",len(x)," different types/categories of Businesses in Yelp!")
    # prep for chart
    x = x.sort_values(ascending=False)
    x = x.iloc[0:20]

    # chart
    plt.figure(figsize=(16, 4))
    ax = sns.barplot(x.index, x.values, alpha=0.8)  # ,color=color[5])
    plt.title("What are the top categories?", fontsize=25)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=80)
    plt.ylabel('# businesses', fontsize=12)
    plt.xlabel('Category', fontsize=12)

    # adding the text labels
    rects = ax.patches
    labels = x.values
    for rect, label in zip(rects, labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2,
                height + 5, label, ha='center', va='bottom')

    plt.show()


def getRestaurantsFromCity(philadelphia):
    # getting just restaurants from Philadelphia business
    rest = philadelphia[philadelphia['categories'].str.contains(
        'Restaurant.*') == True].reset_index()
    # print(rest.shape)
    return rest


# Function that extract keys from the nested dictionary
def extract_keys(attr, key):
    if attr == None:
        return "{}"
    if key in attr:
        return attr.pop(key)


# convert string to dictionary
def str_to_dict(attr):
    if attr != None:
        return ast.literal_eval(attr)
    else:
        return ast.literal_eval("{}")


def getAttrFromNestedAttrs(rest):
    # get dummies from nested attributes
    # list(rest['attributes'])
    rest['BusinessParking'] = rest.apply(lambda x: str_to_dict(
        extract_keys(x['attributes'], 'BusinessParking')), axis=1)
    rest['Ambience'] = rest.apply(lambda x: str_to_dict(
        extract_keys(x['attributes'], 'Ambience')), axis=1)
    rest['GoodForMeal'] = rest.apply(lambda x: str_to_dict(
        extract_keys(x['attributes'], 'GoodForMeal')), axis=1)
    rest['Dietary'] = rest.apply(lambda x: str_to_dict(
        extract_keys(x['attributes'], 'Dietary')), axis=1)
    rest['Music'] = rest.apply(lambda x: str_to_dict(
        extract_keys(x['attributes'], 'Music')), axis=1)

    return rest


def createAttrsTable(rest):
    # create table with attribute dummies
    df_attr = pd.concat([rest['attributes'].apply(pd.Series), rest['BusinessParking'].apply(pd.Series),
                        rest['Ambience'].apply(
                            pd.Series), rest['GoodForMeal'].apply(pd.Series),
                        rest['Dietary'].apply(pd.Series)], axis=1)
    df_attr_dummies = pd.get_dummies(df_attr)
    print()
    return df_attr_dummies


def produceFinalDataFrame(df_attr_dummies):
    global rest
    # get dummies from categories
    df_categories_dummies = pd.Series(rest['categories']).str.get_dummies(',')

    # pull out names and stars from rest table
    result = rest[['name', 'stars']]

    # Concat all tables and drop Restaurant column
    df_final = pd.concat(
        [df_attr_dummies, df_categories_dummies, result], axis=1)
    df_final.drop('Restaurants', inplace=True, axis=1)

    # map floating point stars to an integer
    mapper = {1.0: 1, 1.5: 2, 2.0: 2, 2.5: 3,
              3.0: 3, 3.5: 4, 4.0: 4, 4.5: 5, 5.0: 5}
    df_final['stars'] = df_final['stars'].map(mapper)

    pp("produceFinalDataFrame: Final Dataframe")
    print(df_final.head())
    return df_final


def dataPreprocessing():
    global rest, df_final
    # subset_business, subset_review = readData()
    readData()
    pp("dataPreprocessing After Read data")
    print(subset_business.head())
    print(subset_review.head())
    # plotCityRatings(subset_business)
    cityName = "Philadelphia"
    # philadelphia = selectRestaurantsInCity(subset_business, city)
    philadelphia = selectRestaurantsInCity(cityName)
    # plotFamousBusinessInCity(philadelphia)
    rest = getRestaurantsFromCity(philadelphia)
    # print(rest.head(1))
    rest = getAttrFromNestedAttrs(rest)
    # print(rest.head(1))
    df_attr_dummies = createAttrsTable(rest)
    df_final = produceFinalDataFrame(df_attr_dummies)


############# Content Based Filtering: Code Starts here ##############

def knnClassifer():
    global df_final
    # Create X (all the features) and y (target)
    X = df_final.iloc[:, :-2]
    y = df_final['stars']
    # print(X.shape)
    # print(y.shape)

    # Split the data into train and test sets
    from sklearn.model_selection import train_test_split
    X_train_knn, X_test_knn, y_train_knn, y_test_knn = train_test_split(
        X, y, test_size=0.2, random_state=1)

    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.metrics import accuracy_score

    knn = KNeighborsClassifier(n_neighbors=20)
    knn.fit(X_train_knn, y_train_knn)

    #y_pred = knn.predict(X_test)
    accuracy_train = knn.score(X_train_knn, y_train_knn)
    accuracy_test = knn.score(X_test_knn, y_test_knn)

    print(f"Score on training set: {accuracy_train}")
    print(f"Score on test set: {accuracy_test}")
    return knn


def validateRes(res):
    global df_final

    validate_res = df_final[df_final["name"] == res]
    if len(validate_res) == 0:
        print("Enter valid res name")
        return
    else:
        return validate_res


############# 1) Content Based Filtering - Model ##############
def contentBasedFiltering():
    global df_final

    ########### KNN Classifier ###########
    knn = knnClassifer()

    ########### Enter restaurant name here ############
    res_name = "Adelita Taqueria & Restaurant"

    test_set = validateRes(res_name).iloc[:, :-2]
    # print(test_set.shape)
    test_sample = df_final
    # print(test_sample.shape)
    test_sample = test_sample.drop(test_sample.index[test_set.index])
    # print(test_sample.shape)

    y_val = test_sample['stars']
    # print(y_val.shape)

    X_val = test_sample.iloc[:, :-2]
    # print(X_val.shape)

    print(test_set.shape)
    # print(X_val.shape)
    # print(y_val.shape)

    # fit model with validation set
    n_knn = knn.fit(X_val, y_val)

    # distances and indeces from validation set
    n_knn.kneighbors(test_set)
    # n_knn.kneighbors(test_set)[1][0]

    # create table distances and indeces from validattion restaurant
    final_table = pd.DataFrame(n_knn.kneighbors(test_set)[
                               0][0], columns=['distance'])
    final_table['index'] = n_knn.kneighbors(test_set)[1][0]
    final_table.set_index('index')

    # get names of the restaurant that similar to the validattion restaurant
    result = final_table.join(df_final, on='index')
    pp("Top restaurants based on KNN")
    print(result[['distance', 'index', 'name', 'stars']].head(5))


def genKerasData():
    global combined_business_data, subset_review, rest
# pull out needed columns from subset_review table
    df_review = subset_review[['user_id', 'business_id', 'stars', 'date']]
    # df_review

    # pull out names and addresses of the restaurants from rest table
    restaurant = rest[['business_id', 'name', 'address']]
    # restaurant

    # combine df_review and restaurant table
    combined_business_data = pd.merge(df_review, restaurant, on='business_id')
    # combined_business_data

############### 2) Collaboritive Filtering - Model ##################


def collaborititveFiltering():
    # Imports
    import sklearn
    from sklearn.decomposition import TruncatedSVD
    from sklearn.metrics import accuracy_score

    # Globals
    global combined_business_data, rest, subset_review

    # looking at the columns of subset_review table
    # subset_review.columns
    genKerasData()
    # the most POPULAR restaurants by stars.
    pp("collaborititveFiltering: Most popular restaurants by stars")
    print(combined_business_data.groupby('business_id')[
          'stars'].count().sort_values(ascending=False).head())

    # see the NAME of the most popular restaurant
    # Filter = combined_business_data['business_id'] == 'EtKSTHV5Qx_Q7Aur9o4kQQ'
    # print("Name: ", combined_business_data[Filter]['name'].unique())
    # print("Address:", combined_business_data[Filter]['address'].unique())

    # create a user-item matrix
    rating_crosstab = combined_business_data.pivot_table(
        values='stars', index='user_id', columns='name', fill_value=0)
    pp("Rating Crosstab head")
    print(rating_crosstab.head())

    # shape of the Utility matrix (original matrix)
    pp("Rating Crosstab shape")
    print(rating_crosstab.shape)

    # Transpose the Utility matrix
    X = rating_crosstab.values.T
    pp("X matix shape")
    print(X.shape)

    SVD = TruncatedSVD(n_components=12, random_state=17)
    result_matrix = SVD.fit_transform(X)

    pp("Result Matrix")
    print(result_matrix.shape)

    # PearsonR coef
    corr_matrix = np.corrcoef(result_matrix)
    pp("Correlation Matix shape")
    print(corr_matrix.shape)

    # get the index of the popular restaurant
    restaurant_names = rating_crosstab.columns
    restaurants_list = list(restaurant_names)

    # Filter = combined_business_data['business_id'] == 'j-qtdD55OLfSqfsWuQTDJg'
    # print("Name: ", combined_business_data[Filter]['name'].unique())
    # popular_res_name = combined_business_data[Filter]['name'].unique()
    popular_res_name = "Village Whiskey"
    popular_rest = restaurants_list.index(popular_res_name)
    print("index of the popular restaurant: ", popular_rest)

    # restaurant of interest
    corr_popular_rest = corr_matrix[popular_rest]
    pp("Correlation popular matix shape")
    print(corr_popular_rest.shape)
    pp("Top restaurants using SVD")
    print(restaurant_names[(corr_popular_rest < 1.0)
          & (corr_popular_rest > 0.9)])


############# Keras Model: Code Starts here ##############

def dataLabelEncoder(combined_business_data):
    global combined_business_data_keras
    # create the copy of combined_business_data table
    combined_business_data_keras = combined_business_data.copy()
    print(combined_business_data_keras.head(1))

    from sklearn.preprocessing import LabelEncoder
    n_factors = 50
    user_encode = LabelEncoder()

    combined_business_data_keras['user'] = user_encode.fit_transform(
        combined_business_data_keras['user_id'].values)
    n_users = combined_business_data_keras['user'].nunique()

    item_encode = LabelEncoder()

    combined_business_data_keras['business'] = item_encode.fit_transform(
        combined_business_data_keras['business_id'].values)
    n_rests = combined_business_data_keras['business'].nunique()

    # .astype(np.float32)
    combined_business_data_keras['stars'] = combined_business_data_keras['stars'].values

    min_rating = min(combined_business_data_keras['stars'])
    max_rating = max(combined_business_data_keras['stars'])

    print(n_users, n_rests, min_rating, max_rating)
    return n_users, n_rests, n_factors, min_rating, max_rating


def trainTestSplit(combined_business_data_keras):
    # Imports
    from sklearn.model_selection import train_test_split

    # Globals
    global X_train_keras, y_train_keras, X_test_keras, y_test_keras
    X = combined_business_data_keras[['user', 'business']].values
    y = combined_business_data_keras['stars'].values

    X_train_keras, X_test_keras, y_train_keras, y_test_keras = train_test_split(
        X, y, test_size=0.2, random_state=42)

    print(X_train_keras.shape, X_test_keras.shape,
          y_train_keras.shape, y_test_keras.shape)

    X_train_array = [X_train_keras[:, 0], X_train_keras[:, 1]]
    X_test_array = [X_test_keras[:, 0], X_test_keras[:, 1]]

    pp("train test split")
    print(X_train_array)
    print(X_test_array)
    return X_train_array, X_test_array


class EmbeddingLayer:
    def __init__(self, n_items, n_factors):
        self.n_items = n_items
        self.n_factors = n_factors

    def __call__(self, x):
        x = Embedding(self.n_items, self.n_factors,
                      embeddings_initializer='he_normal', embeddings_regularizer=l2(1e-6))(x)
        x = Reshape((self.n_factors,))(x)

        return x


def Recommender(n_users, n_rests, n_factors, min_rating, max_rating):
    user = Input(shape=(1,))
    u = EmbeddingLayer(n_users, n_factors)(user)
    ub = EmbeddingLayer(n_users, 1)(user)

    restaurant = Input(shape=(1,))
    m = EmbeddingLayer(n_rests, n_factors)(restaurant)
    mb = EmbeddingLayer(n_rests, 1)(restaurant)

    x = Dot(axes=1)([u, m])
    x = Add()([x, ub, mb])
    x = Activation('sigmoid')(x)
    x = Lambda(lambda x: x * (max_rating - min_rating) + min_rating)(x)

    model = Model(inputs=[user, restaurant], outputs=x)
    opt = adam_v2.Adam(learning_rate=0.001)
    model.compile(loss='mean_squared_error', optimizer=opt)

    return model


def trainModel(keras_model, X_train_array, X_test_array):
    # Global
    global y_test_keras, y_train_keras

    keras_model.fit(x=X_train_array, y=y_train_keras, batch_size=64,
                    epochs=10, verbose=1, validation_data=(X_test_array, y_test_keras))
    return keras_model


def saveModel(keras_model):
    keras_model.save(
        "C:/Users/Midhun/Desktop/FYP/Restuarant_Recommendation/rrs/colab/model/modelrss_model")


def loadModel(X_test_array):
    # Imports
    import keras.models as keras_model

    # Globals
    global reconstructed_model

    reconstructed_model = keras_model.load_model(
        "C:/Users/Midhun/Desktop/FYP/Restuarant_Recommendation/rrs/colab/model/modelrss_model")
    predictions = reconstructed_model.predict(X_test_array)
    return predictions


def predResultTable(predictions):
    global X_test_keras
    # create the df_test table with prediction results
    df_test = pd.DataFrame(X_test_keras[:, 0])
    df_test.rename(columns={0: "user"}, inplace=True)
    df_test['business'] = X_test_keras[:, 1]
    df_test['stars'] = y_test_keras
    df_test["predictions"] = predictions
    print(df_test.head())
    return df_test


def plotPredResults(predictions, df_test):
    # Plotting the distribution of actual and predicted stars
    import matplotlib.pyplot as plt
    import seaborn as sns
    values, counts = np.unique(df_test['stars'], return_counts=True)

    plt.figure(figsize=(8, 6))
    plt.bar(values, counts, tick_label=[
            '1', '2', '3', '4', '5'], label='true value')
    plt.hist(predictions, color='orange', label='predicted value')
    plt.xlabel("Ratings")
    plt.ylabel("Frequency")
    plt.title("Ratings Histogram")
    plt.legend()
    plt.show()

    # plot
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(15, 6))

    ax1 = sns.distplot(df_test['stars'], hist=False,
                       color="r", label="Actual Value")
    sns.distplot(predictions, hist=False, color="g",
                 label="model2 Fitted Values", ax=ax1)

    plt.title('Actual vs Fitted Values for Restaurant Ratings')
    plt.xlabel('Stars')
    plt.ylabel('Proportion of Ratings')
    plt.show()
    plt.close()


def prepareForRecommedation(reconstructed_model):
    # Extract embeddings
    emb = reconstructed_model.get_layer('embedding_2')
    emb_weights = emb.get_weights()[0]

    print("The shape of embedded weights: ", emb_weights.shape)
    print("The length of embedded weights: ", len(emb_weights))

    # normalize and reshape embedded weights
    emb_weights = emb_weights / \
        np.linalg.norm(emb_weights, axis=1).reshape((-1, 1))
    len(emb_weights)

    # get all unique business_ids (restaurants)
    rest_id_emb = combined_business_data_keras["business_id"].unique()
    len(rest_id_emb)
    # rest_id_emb

    rest_pd = pd.DataFrame(emb_weights)
    # rest_pd
    rest_pd["business_id"] = rest_id_emb
    rest_pd = rest_pd.set_index("business_id")
    rest_pd

    # merging rest_pd and temp tables to get the name of the restaurants.
    temp = combined_business_data_keras[[
        'business_id', 'name']].drop_duplicates()
    df_recommend = pd.merge(rest_pd, temp, on='business_id')
    df_recommend

    # exrtract the target restaurant from the df_recommend table
    target = df_recommend[df_recommend['name'] == 'Village Whiskey']
    target.iloc[:, 1:51]
    return df_recommend


def find_similarity_total(rest_name, df_recommend):
    """Recommends restaurant based on the cosine similarity between restaurants"""
    cosine_list_total = []
    result = []

    for i in range(0, df_recommend.shape[0]):
        sample_name = df_recommend[df_recommend["name"]
                                   == rest_name].iloc[:, 1:51]
        row = df_recommend.iloc[i, 1:51]
        cosine_total = np.dot(sample_name, row)

        recommended_name = df_recommend.iloc[i, 51]
        cosine_list_total.append(cosine_total)
        result.append(recommended_name)

    cosine_df_total = pd.DataFrame(
        {"similar_rest": result, "cosine": cosine_list_total})
    # head of result table
    print(cosine_df_total.head())
    return cosine_df_total


'''
- function that replace '[]' to empty str
- convert string to float
'''


def convert(input):
    return float(str(input).replace('[', '').replace(']', ''))


def kerasModel(rest_name, n):
    n_users, n_rests, n_factors, min_rating, max_rating = dataLabelEncoder(
        combined_business_data)
    X_train_array, X_test_array = trainTestSplit(combined_business_data_keras)
    keras_model = Recommender(
        n_users, n_rests, n_factors, min_rating, max_rating)
    keras_model.summary()
    # keras_model = trainModel(keras_model, X_train_array, X_test_array)
    # saveModel(keras_model)
    predictions = loadModel(X_test_array)
    df_test = predResultTable(predictions)
    plotPredResults(predictions, df_test)
    df_recommend = prepareForRecommedation(reconstructed_model)
    result = find_similarity_total(rest_name, df_recommend)
    # create new column called "cos" in result table
    result['cos'] = result.apply(lambda x: convert(x['cosine']), axis=1)

    # drop original 'cosine' column (which had values with np.array)
    result.drop('cosine', axis=1, inplace=True)

    # sort values with cos
    res = result.sort_values('cos', ascending=False).head(n)
    return res["similar_rest"]


def run(rest_name, n):
    dataPreprocessing()
    genKerasData()
    # contentBasedFiltering()
    # collaborititveFiltering()
    result = kerasModel(rest_name, n)
    return result
