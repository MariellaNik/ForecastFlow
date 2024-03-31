import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sklearn.cluster import KMeans
from starlette.responses import FileResponse

from common_functions import setup_logging, parse_config
from rnn import get_regressor

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


config = parse_config("default_config.yaml")
script_logging = config["script_logging"]
logger = setup_logging(script_logging)


@app.post("/generate_segmentation_data")
def generate_segmentation_data():
    try:
        filename = "groceries.csv"
        logger.info(f"Processing file {filename}")
        data = pd.read_csv(filename, on_bad_lines="skip")
        data.dropna(subset=["CustomerID"], inplace=True)
        data["Quantity"] = data["Quantity"].astype(float)
        data["UnitPrice"] = data["UnitPrice"].astype(float)
        data["CustomerID"] = data["CustomerID"].astype(int)
        data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"])
        data = data[(data["Quantity"] > 0) & (data["UnitPrice"] > 0)]

        snapshot_date = max(data["InvoiceDate"]) + pd.DateOffset(days=1)

        data["Total"] = data["Quantity"] * data["UnitPrice"]

        rfm = data.groupby("CustomerID").agg({
            "InvoiceDate": lambda i: (snapshot_date - i.max()).days,
            "InvoiceNo": "nunique",
            "Total": "sum"
        })

        rfm.rename(columns={"InvoiceDate": "Recency", "InvoiceNo": "Frequency", "Total": "MonetaryValue"}, inplace=True)
        rfm.head()

        recency_bins = [rfm["Recency"].min() - 1, 20, 50, 150, 250, rfm["Recency"].max()]
        frequency_bins = [rfm["Frequency"].min() - 1, 2, 3, 10, 100, rfm["Frequency"].max()]
        monetary_bins = [rfm["MonetaryValue"].min() - 3, 300, 600, 2000, 5000, rfm["MonetaryValue"].max()]

        rfm["R_Score"] = pd.cut(rfm["Recency"], bins=recency_bins, labels=range(1, 6), include_lowest=True)
        rfm["R_Score"] = 5 - rfm["R_Score"].astype(int) + 1

        rfm["F_Score"] = pd.cut(rfm["Frequency"], bins=frequency_bins, labels=range(1, 6), include_lowest=True).astype(
            int)
        rfm["M_Score"] = pd.cut(rfm["MonetaryValue"], bins=monetary_bins, labels=range(1, 6),
                                include_lowest=True).astype(int)

        x = rfm[["R_Score", "F_Score", "M_Score"]]

        best_kmeans = KMeans(n_clusters=4, n_init=10, random_state=42)
        rfm["Cluster"] = best_kmeans.fit_predict(x)
        cluster_counts = rfm["Cluster"].value_counts()

        colors = ["#F1C40F", "#007BFF", "#E74C3C", "#9B59B6"]
        total_customers = cluster_counts.sum()
        percentage_customers = (cluster_counts / total_customers) * 100

        labels = ["Power Shoppers", "Loyal Customers", "At-risk Customers", "Recent Customers"]

        plt.figure(figsize=(10, 10), dpi=200)
        plt.pie(percentage_customers, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        plt.title("Percentage of Customers in Each Segment")
        plt.legend(title="Segment", loc="upper left")

        plt.savefig("final.png", bbox_inches="tight")
        logger.info(f"Successfully processed file {filename}")
        plt.clf()
        return FileResponse("final.png")
    except Exception:
        message = "An exception occurred while processing file"
        logger.exception(message)
        raise HTTPException(status_code=400, detail=message)


@app.post("/generate_prediction")
def generate_prediction():
    try:
        dataset_train = pd.read_csv("groceries_bread_1.csv")
        regressor, sc = get_regressor(dataset_train)
        dataset_test = pd.read_csv("groceries_bread_2.csv")

        dataset_total = pd.concat((dataset_train["quantity"], dataset_test["quantity"]), axis=0)
        inputs = dataset_total[len(dataset_total) - len(dataset_test) - 60:].values
        inputs = inputs.reshape(-1, 1)
        inputs = sc.transform(inputs)
        x_test = []
        for i in range(60, 80):
            x_test.append(inputs[i - 60:i, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
        predicted_quantity = regressor.predict(x_test)
        predicted_quantity = sc.inverse_transform(predicted_quantity)

        plt.plot(predicted_quantity, color="blue", label="Predicted Bread Quantity Needed")
        plt.title("Bread Quantity Prediction")
        plt.xlabel("Time")
        plt.ylabel("Bread Quantity")
        plt.legend()
        plt.savefig("bread_quantity.png", bbox_inches="tight")
        logger.info("Successfully made prediction")
        plt.clf()
        return FileResponse("bread_quantity.png")

    except Exception:
        logger.exception("An exception occurred while making the request")
        raise HTTPException(status_code=400)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
