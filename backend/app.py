import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from sklearn.cluster import KMeans
from starlette.responses import Response, FileResponse

from backend.common_functions import setup_logging, parse_config

app = FastAPI()


class Order(BaseModel):
    InvoiceNo: str
    Description: str
    Quantity: int
    InvoiceDate: datetime
    UnitPrice: float
    CustomerID: int
    Country: str


config = parse_config("default_config.yaml")
script_logging = config["script_logging"]
logger = setup_logging(script_logging)


def check_file_valid(file_name):
    try:
        file_name, file_extension = os.path.splitext(file_name)
        return file_extension.lower() in [".csv", ".xls", ".xlsx"]
    except Exception:
        logger.exception(f"An error occurred while processing file ({file_name})")
        return False


@app.post("/generate_segmentation_data")
async def generate_segmentation_data(file: UploadFile):
    try:
        filename = file.filename
        logger.info(f"Processing file {filename}")
        if not check_file_valid(filename):
            message = "File type not supported"
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)

        if filename.endswith(".csv"):
            data = pd.read_csv(file.file, on_bad_lines="skip")
        else:
            data = pd.read_excel(file.file.read())

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

        # inertia = []
        # for k in range(2, 11):
        #     kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        #     kmeans.fit(x)
        #     inertia.append(kmeans.inertia_)

        best_kmeans = KMeans(n_clusters=4, n_init=10, random_state=42)
        rfm["Cluster"] = best_kmeans.fit_predict(x)
        cluster_summary = rfm.groupby("Cluster").agg({
            "R_Score": "mean",
            "F_Score": "mean",
            "M_Score": "mean"
        }).reset_index()

        cluster_counts = rfm["Cluster"].value_counts()

        colors = ["#F1C40F", "#007BFF", "#E74C3C", "#9B59B6"]
        total_customers = cluster_counts.sum()
        percentage_customers = (cluster_counts / total_customers) * 100

        labels = ["Power Shoppers", "Loyal Customers", "At-risk Customers", "Recent Customers"]

        plt.figure(figsize=(8, 8), dpi=200)
        plt.pie(percentage_customers, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        plt.title("Percentage of Customers in Each Cluster")
        plt.legend(cluster_summary["Cluster"], title="Cluster", loc="upper left")

        plt.savefig("final.png", bbox_inches="tight")
        logger.info(f"Successfully processed file {filename}")
        return FileResponse("final.png")
    except Exception:
        message = "An exception occurred while processing file"
        logger.exception(message)
        raise HTTPException(status_code=400, detail=message)


@app.post("/generate_product_suggestion")
async def generate_product_suggestion(file: UploadFile, customer_id: str):
    try:
        # customer_id = order.customer_id
        if customer_id is not str:
            message = "Customer ID must be an integer"
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)

        filename = file.filename
        logger.info(f"Processing file {filename}")
        if not check_file_valid(filename):
            message = "File type not supported"
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)

        if filename.endswith(".csv"):
            data = pd.read_csv(file.file, on_bad_lines="skip")
        else:
            data = pd.read_excel(file.file.read())

        product_counts_by_country = (
            data.groupby(["Country", "ProductID"])
            .size()
            .to_frame(name="count")
            .reset_index()
        )
        user_present = customer_id in data["CustomerID"].tolist()
        if not user_present:
            most_bought_product = product_counts_by_country[
                product_counts_by_country["Country"] == "Great Britain"
                ]["ProductID"].iloc[0]

            return most_bought_product
    except Exception:
        logger.error("An exception occurred while making the request")
        raise HTTPException(status_code=400)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
