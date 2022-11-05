from flask import Flask
from flask_restful import Api
from diskcache import Cache
from src.resources import Calendar
from src.rlka import RLKA

app = Flask(__name__)
api = Api(app, catch_all_404s=True)
rlka = RLKA(cache=Cache("cache"))

api.add_resource(Calendar, '/ical', resource_class_kwargs={'rlka': rlka})

if __name__ == '__main__':
    app.run(debug=True)
