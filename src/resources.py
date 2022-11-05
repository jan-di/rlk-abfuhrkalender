from flask import Response
from flask_restful import Resource, reqparse
from src.rlka import RLKA


class Calendar(Resource):
    def __init__(self, rlka: RLKA):
        self.rlka = rlka

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'place', type=int, required=True, help='Place ID must be defined', location='args')
        parser.add_argument(
            'street', type=int, required=True, help='Street ID must be defined', location='args')
        args = parser.parse_args()

        return Response(self.rlka.get_ical(place=args['place'], street=args['street']), mimetype='text/calendar')
