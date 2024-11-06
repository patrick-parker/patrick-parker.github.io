from flask import Flask, render_template, request
from requests.exceptions import ConnectionError

from database import Search
from web_scrape import Citizendium, Wikipedia


app = Flask(__name__)
wikipedia = Wikipedia()
citizendium = Citizendium()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        results = {}
        key_word = request.form["key_word"]
        if key_word:
            for obj, website in zip((wikipedia, citizendium), ("Wikipedia", "Citizendium")):
                try:
                    results[website] = obj.search(key_word)
                except ConnectionError:
                    results[f"{website} error"] = "You are not connected to the Internet"
                except TimeoutError:
                    results[f"{website} error"] = f"{website} took too long to respond"
                except Exception as error:
                    results[f"{website} error"] = error
            return render_template(
                "index.html",
                key_word=key_word,
                wiki_result=results.get("Wikipedia"),
                citizen_result=results.get("Citizendium"),
                wiki_error=f"An unexpected error occured: {results.get("Wikipedia error")}",
                citizen_error=f"An unexpected error occured: {results.get("Citizendium error")}",
                wiki_disambiguated=wikipedia.disambiguated,
                citizen_disambiguated=citizendium.disambiguated,
            )
    return render_template("index.html")


@app.route("/history/", methods=["GET", "POST"])
def history():    
    if request.method == "POST":
        Search.delete().execute()
    empty = len(Search.select()) == 0
    return render_template("history.html", query=Search.select(), empty=empty)
    

if __name__ == "__main__":
    app.run(debug=True)

