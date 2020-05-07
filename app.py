#################################################
# Dependencies
#################################################
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Station, Measurement = Base.classes.station, Base.classes.measurement
# finding date range from the database...
session = Session(engine)
dt_range = session.query(func.min(Measurement.date), func.max(Measurement.date)).first()
session.close()
#('2010-01-01', '2017-08-23')
#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to the Climate Analysis and Exploration Home Page!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start/2010-01-01<br/>"
        f"/api/v1.0/startend/2010-01-01/2017-08-23<br/>"
        f" <br/>"
        f"Note: For routes with date option use yyyy/mm/dd format otherwise you will get not found message"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Convert the precipitation data as json"""

    print("Server received request for precipitation page...")
    print("after open session and before max date query...")
    session = Session(engine)
    mdt = session.query(func.max(Measurement.date)).one()
    maxdt = mdt[0]
    todt = datetime.datetime.strptime(maxdt, "%Y-%m-%d")
    frdt = todt - datetime.timedelta(days=365)
    print("before main query");
    results1 = session.query(Measurement.date,Measurement.prcp).\
                    filter(func.DATE(Measurement.date) >= func.DATE(frdt), \
                       func.DATE(Measurement.date) <= func.DATE(todt)).all()
    session.close()
    all_dates = []
    for row in results1:
        date_dict = {}
        date_dict[row[0]] = row[1]
        all_dates.append(date_dict)

    return jsonify(all_dates)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset"""

    print("Server received request for precipitation page...")
    session = Session(engine)
    results2 = session.query(Station.station).order_by(Station.station).all()
#     results2 = session.query(Station.station,Station.name).order_by(Station.station).all()
    session.close()
    all_stations = []
    all_stations = list(np.ravel(results2))
#     for row in results2:
#         sta_dict = {}
#         sta_dict[row[0]] = row[1]
#         all_stations.append(sta_dict)
    
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations (TOBS) for the previous year"""

    print("Server received request for precipitation page...")
    session = Session(engine)
    tresult = session.query(Measurement.station, func.max(Measurement.date)).\
                filter(Station.station == Measurement.station).group_by(Measurement.station).\
                order_by(func.count(Measurement.station).desc()).first()

    sfrdt = datetime.datetime.strptime(tresult[1], "%Y-%m-%d") - datetime.timedelta(days=365)
    results3 = session.query(Measurement.date,Measurement.tobs).\
                    filter(Measurement.station == tresult[0]).\
                    filter(func.DATE(Measurement.date) >= func.DATE(sfrdt), \
                           func.DATE(Measurement.date) <= func.DATE(tresult[1])).all()
    session.close()
    all_tobs = dict(results3)
    all_tobs = []
    for row in results3:
        tobs_dict = {}
        tobs_dict[row[0]] = row[1]
        all_tobs.append(tobs_dict)
    
    return jsonify(all_tobs)

@app.route("/api/v1.0/start/<start_date>")
def start(start_date):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start"""
    print("Server received request for start period search page...")
    if len(start_date) == 10:
        session = Session(engine)
        sel = [Measurement.station,
                func.min(Measurement.tobs),
                func.max(Measurement.tobs),
                func.avg(Measurement.tobs)
              ]
        results4=session.query(*sel).filter(func.DATE(Measurement.date) >= func.DATE(start_date)).\
                                group_by(Measurement.station).order_by(Measurement.station).all()
        session.close()
        if len(results4) > 0:
            all_starts = []
            for row in results4:
                start_dict = {}
                start_dict[row[0]] = f"Min. Temperature :{row[1]}, Max. Temperature :{row[2]}, Avg. Temperature :{round(row[3],2)}"
                all_starts.append(start_dict)
            return jsonify(all_starts)
        else:
            return jsonify({"Warning": f"No records found for this date {start_date}. Try another date!!!"}), 404
    else:
        return jsonify({"error": f"Invalid Date format {start_date}.  Please use YYYY-MM-DD format and try again!!!"}), 404

    return jsonify(all_starts)


@app.route("/api/v1.0/startend/<start_date>/<end_date>")
def start_end(start_date,end_date):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start-end range"""
    print(start_date, end_date)
    print("Server received request for start and end period search page...")
    if len(start_date) == 10 & len(end_date) == 10:
        session = Session(engine)
        sel = [Measurement.station,
                func.min(Measurement.tobs),
                func.max(Measurement.tobs),
                func.avg(Measurement.tobs)
              ]
        results5 = session.query(*sel).filter(func.DATE(Measurement.date) >= func.DATE(start_date),\
                    func.DATE(Measurement.date) <= func.DATE(end_date)).group_by(Measurement.station).\
                    order_by(Measurement.station).all()
        session.close()
        if len(results5) > 0:
            all_ends = []
            for row in results5:
                end_dict = {}
                end_dict[row[0]] = f"Min. Temperature :{row[1]}, Max. Temperature :{row[2]}, Avg. Temperature :{round(row[3],2)}"
                all_ends.append(end_dict)
            return jsonify(all_ends)
        else:
            return jsonify({"Warning": f"No records found for the date range {start_date} - {end_date}. Try another date!!!",
                            "Info": f"Valid data ranges are from {dt_range[0]} thru {dt_range[1]}. Please use YYYY-MM-DD format and try again!!!"}), 404
    else:
        return jsonify({"error": f"Invalid Date format {start_date} - {end_date}.",
                            "Info": f"Valid data ranges are from {dt_range[0]} thru {dt_range[1]}. Please use YYYY-MM-DD format and try again!!!"}), 404

if __name__ == "__main__":
    app.run(debug=True)
