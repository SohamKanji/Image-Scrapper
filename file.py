import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import logging
import os
from flask import Flask, render_template, request, jsonify
import pymongo
from dotenv import load_dotenv

# configuring logging mode
logging.basicConfig(filename="scrapper.log", level=logging.INFO)
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

app = Flask(__name__)


# our homepage
@app.route("/", methods=["GET"])
def homepage():
    return render_template("index.html")


@app.route("/scrap", methods=["POST"])
def index():
    try:
        # getting the query from the form
        query = request.form["content"].replace(" ", "")

        # this is the name of the directory we are saving our images to. If the directory doesn't exist, we are creating one
        save_dir = "images/"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # fake user age to avoid getting blocked by google
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }

        # fetching search results page
        response = requests.get(
            f"https://www.google.com/search?q={query}&tbm=isch&ved=2ahUKEwi0qf69ipmCAxVZ5DgGHUm-CZYQ2-cCegQIABAA&oq=eminem&gs_lcp=CgNpbWcQAzIECCMQJzIHCAAQigUQQzIKCAAQigUQsQMQQzIICAAQgAQQsQMyCAgAEIAEELEDMggIABCABBCxAzIICAAQgAQQsQMyBQgAEIAEMgUIABCABDIICAAQgAQQsQM6BAgAEAM6CAgAELEDEIMBUOEJWO8ZYN8baABwAHgAgAGcAYgB0Q2SAQQwLjEymAEAoAEBqgELZ3dzLXdpei1pbWfAAQE&sclient=img&ei=8Ss9ZfTsBdnI4-EPyfymsAk&bih=695&biw=1536&rlz=1C1RXQR_enIN1068IN1068",
            headers=headers,
        )

        # soup beautify
        soup = BeautifulSoup(response.content, "html.parser")

        image_tags = soup.find_all("img")
        del image_tags[0]
        image_data_mongo = []
        for i in image_tags:
            image_url = i["src"]

            # getting the actual image out
            image_data = requests.get(image_url).content
            mydic = {"index": image_url, "image": image_data}
            image_data_mongo.append(mydic)

            # saving the image in our directory
            with open(
                os.path.join(save_dir, f"{query}_{image_tags.index(i)}.jpg"), "wb"
            ) as f:
                f.write(image_data)
        client = pymongo.MongoClient(MONGODB_URI)
        db = client["image_scrap"]
        review_col = db["image_scrap_data"]
        review_col.insert_many(image_data_mongo)
        return "Image Loaded"
    except Exception as e:
        logging.info(e)
        return "Something went wrong!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
