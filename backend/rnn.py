import pickle
from os import path

import numpy as np
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.models import Sequential
from keras.saving import load_model
from sklearn.preprocessing import MinMaxScaler


def build_regressor(dataset_train, sc):
    training_set = dataset_train.iloc[:, 3:4].values
    training_set_scaled = sc.fit_transform(training_set)

    x_train = []
    y_train = []
    for i in range(60, 1600):
        x_train.append(training_set_scaled[i - 60:i, 0])
        y_train.append(training_set_scaled[i, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    regressor = Sequential()

    regressor.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    regressor.add(Dropout(0.1))

    regressor.add(LSTM(units=50, return_sequences=True))
    regressor.add(Dropout(0.1))

    regressor.add(LSTM(units=50, return_sequences=True))
    regressor.add(Dropout(0.1))

    regressor.add(LSTM(units=50))
    regressor.add(Dropout(0.1))

    regressor.add(Dense(units=1))
    regressor.compile(optimizer="adam", loss="mean_squared_error")
    regressor.fit(x_train, y_train, epochs=100, batch_size=32)
    with open("scaler.pkl", "wb") as f:
        pickle.dump(sc, f)

    regressor.save("regressor_model.keras")

    return regressor


def get_regressor(dataset_train):
    if path.exists("regressor_model.keras"):
        regressor = load_model("regressor_model.keras")
        with open("scaler.pkl", "rb") as f:
            sc = pickle.load(f)
        return regressor, sc
    else:
        sc = MinMaxScaler(feature_range=(0, 1))
        return build_regressor(dataset_train, sc), sc
