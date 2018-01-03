import os
import re
from flask import Flask, jsonify, render_template, request, url_for
from flask_jsglue import JSGlue

from cs50 import SQL
from helpers import lookup

# configure application
app = Flask(__name__)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")

# for wrapping stuff used in db.execute's because I dont like the semicolons
def w(i):
    try:
        out = str(i)
    except:
        out = i
    return "'" + out + "'"

@app.route("/")
def index():
    """Render map."""
    if not os.environ.get("API_KEY"):
        raise RuntimeError("API_KEY not set")
    return render_template("index.html", key=os.environ.get("API_KEY"))

@app.route("/articles")
def articles():
    """Look up articles for geo."""
    # GET geo ;)
    geo = request.args.get("geo")
    # get articles
    articles = lookup(geo)

    # return JSON object of python object (o.0)
    return jsonify(articles)

@app.route("/search")
def search():
    """Search for places that match query.
    algorithm
    for symbol in potential seperator list
        for word in symbol seperated list of words derived from query
            try to find place by word
            if found place
                add place
    return out
    else :/
    """

    # output
    out = []

    # GET query ;)
    q = request.args.get("q")

    # for symbol in potential seperator list
    for symbol in [",", " "]:

        # for word in symbol seperated list of words dervied from query
        # try to find word
        # if found place
        #     return place
        for word in q.split(symbol):

            # try finding by postal_code
            byPostalCode = db.execute("SELECT * FROM places WHERE postal_code = " + w(word))
            if (len(byPostalCode) > 0):
                out += byPostalCode

            # try finding by place_name
            byPlaceName = db.execute("SELECT * FROM places WHERE place_name = " + w(word))
            if (len(byPlaceName) > 1):
                out += byPlaceName

            # try finding by admin_name1
            byAdminName1 = db.execute("SELECT * FROM places WHERE admin_name1 = " + w(word))
            if (len(byAdminName1) > 1):
                out += byAdminName1

            # try finding by admin_code1
            byAdminCode1 = db.execute("SELECT * FROM places WHERE admin_code1 = " + w(word))
            if (len(byAdminCode1) > 1):
                out += byAdminCode1

            # try finding by admin_name2
            byAdminName2 = db.execute("SELECT * FROM places WHERE admin_name2 = " + w(word))
            if (len(byAdminName2) > 1):
                out += byAdminName2

            # try finding by admin_code2
            byAdminCode2 = db.execute("SELECT * FROM places WHERE admin_code2 = " + w(word))
            if (len(byAdminCode2) > 1):
                out += byAdminCode2

            # try finding by latitude
            byLatitude = db.execute("SELECT * FROM places WHERE latitude = " + w(word))
            if (len(byLatitude) > 1):
                out += byLatitude

            # try finding by longitude
            byLongitude = db.execute("SELECT * FROM places WHERE longitude = " + w(word))
            if (len(byLongitude) > 1):
                out += byLongitude

            # if CS parsing worked, return, otherwise try space seperated parsing
            # and if space seperated parsing worked, return it even
            # though the next line of code would do it anyway
            if len(out) > 0:
                return jsonify(out)

    # else :/
    return jsonify(out)

@app.route("/update")
def update():
    """Find up to 10 places within view."""

    # ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # explode southwest corner into two variables
    (sw_lat, sw_lng) = [float(s) for s in request.args.get("sw").split(",")]

    # explode northeast corner into two variables
    (ne_lat, ne_lng) = [float(s) for s in request.args.get("ne").split(",")]

    # find 10 cities within view, pseudorandomly chosen if more within view
    if (sw_lng <= ne_lng):

        # doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
            WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
            GROUP BY country_code, place_name, admin_code1
            ORDER BY RANDOM()
            LIMIT 10""",
            sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
            WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
            GROUP BY country_code, place_name, admin_code1
            ORDER BY RANDOM()
            LIMIT 10""",
            sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # output places as JSON
    return jsonify(rows)
