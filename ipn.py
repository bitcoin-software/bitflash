from flask import Flask
from flask_restful import Resource, Api, reqparse, request
import time
import datetime
from charge import get_invoice
from db import new_status

app = Flask(__name__)
api = Api(app)


class Ipn(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id')
        args = parser.parse_args()
        try:
            id = args['id']
        except KeyError as e:
            print(dtime + ': error on handling callback from charge - ' + str(e))
            return False
        dtime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        print(dtime + ": " + id + ' received')
        invoice_data = get_invoice(id=id)
        print(dtime + ": " + id + ' ' + invoice_data['status'])
        if invoice_data['status'] == 'paid':
            print('updating db..')
            new_status(id, 'paid')
            print('db updated!')
        return True


api.add_resource(Ipn, '/ipn')

if __name__ == '__main__':
    app.run(debug=False, port=7771)