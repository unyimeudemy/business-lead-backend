from flask import Flask, jsonify
from flask_restful import Api, Resource, reqparse, fields, marshal_with, abort,request
from flask_sqlalchemy import SQLAlchemy
from scraper import scrap
from flask_cors import CORS
from sqlalchemy import func
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy import func, Column
from logging.config import dictConfig
from logging.handlers import SysLogHandler
import logging


app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)

PAPERTRAIL_HOST = "logs2.papertrailapp.com"
PAPERTRAIL_PORT = 20720 

def setup_logging():
    handler = SysLogHandler(address=(PAPERTRAIL_HOST, PAPERTRAIL_PORT))
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  
    logger.addHandler(handler)

    app.logger.addHandler(handler)

setup_logging()

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flask_app_db:Cr1UPlUtgm9gvLO00V4oDGEKwOxakwD4@dpg-ct26k8i3esus73d4nl0g-a.oregon-postgres.render.com:5432/flask_app_db_u2cx'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db.init_app(app)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "https://business-leads-frontend.onrender.com", "https://business-leads-frontend.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"]
    }
})


class TSVector(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            return func.to_tsvector('english', value) 
        return value

    def process_result_value(self, value, dialect):
        return value


class BusinessModel(db.Model):
    __tablename__ = 'business'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    hours = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.String(500), nullable=True)
    reviews = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    industry = db.Column(db.String(500), nullable=True)
    searchable = db.Column(TSVector(), nullable=False) 

    def __init__(self, id=None, name=None, address=None, hours=None, phone=None, rating=None, reviews=None, website=None, industry=None, searchable=None):
        self.id = id
        self.name = name
        self.address = address
        self.hours = hours
        self.phone = phone
        self.rating = rating
        self.reviews = reviews
        self.website = website
        self.industry = industry
        self.searchable = searchable


class IndustryModel(db.Model):
    __tablename__ = 'industries'
    id = db.Column(db.Integer, primary_key=True)
    industry = db.Column(db.String(500), unique=True, nullable=True)

    def __init__(self, id=None, industry=None):
        self.id = id
        self.industry = industry



with app.app_context():
    db.create_all()


business_put_args = reqparse.RequestParser()
business_put_args.add_argument("name", type=str, help="name of business if required", required=False)
business_put_args.add_argument("address", type=str, help="address of business is required", required=False)
business_put_args.add_argument("hours", type=str, help="operating hours of business", required=False)
business_put_args.add_argument("phone", type=str, help="contact phone number of business", required=False)
business_put_args.add_argument("rating", type=str, help="rating of the business", required=False)
business_put_args.add_argument("reviews", type=str, help="reviews for the business", required=False)
business_put_args.add_argument("website", type=str, help="website of the business", required=False)
business_put_args.add_argument("industry", type=str, help="industry of the business", required=False)

industry_put_args = reqparse.RequestParser()
industry_put_args.add_argument("industry", type=str, help="name of business if required", required=False)

business_field = {
    "id": fields.Integer,
    "name": fields.String,
    "address": fields.String,
    "hours": fields.String,
    "phone": fields.String,
    "rating": fields.String,
    "reviews": fields.String,
    "website": fields.String,
    "industry": fields.String
}

industry_field = {
    "id": fields.Integer,
    "industry": fields.String,
}

class Scraper(Resource):

    @marshal_with(business_field)
    def get(self, query):
        result = scrap(query)
        print("------------------", result)
        return result

        # business_objects = []
        # for item in result:
        #     #args = business_put_args.parse_args(req=jsonify(item))

        #     business = BusinessModel()
        #     setattr(business, "industry", query)
        #     for key, value in item.items():
        #         if hasattr(business, key):
        #             setattr(business, key, value)
            
        #     # db.session.add(business)
        #     business_objects.append(business)

        # # db.session.commit()
        # return business_objects, 201


class Search(Resource):
    @marshal_with(business_field)
    def get(self, query):

        search_query = func.websearch_to_tsquery('english', query)  # Or func.websearch_to_tsquery
        result = BusinessModel.query.filter(BusinessModel.searchable.op('@@')(search_query)).all()

        if not result:
            abort(404, message="Business not found")
            app.logger.warning("A search was NOT sucessful")
        app.logger.info("A search was sucessful")
        return result


class GetAll(Resource):
    @marshal_with(business_field)
    def get(self):
        page = int(request.args.get('page', 1)) 
        per_page = int(request.args.get('per_page', 12)) 
        industry = request.args.get('industry')

        paginated_results = None
        if industry:
            paginated_results = BusinessModel.query.filter_by(industry=industry).paginate(page=page, per_page=per_page, error_out=False)
        else:
            paginated_results = BusinessModel.query.paginate(page=page, per_page=per_page, error_out=False)

        if not paginated_results.items:
            app.logger.warning("List of businesses NOT successfully retrieved")
            abort(404, message="List of businesses NOT successfully retrieved")

        app.logger.info("List of businesses successfully retrieved")
        return paginated_results.items 

class GetIndustries(Resource):
    @marshal_with(industry_field)
    def get(self):
        results = IndustryModel.query.all()

        if not results:
            app.logger.warning("List of industries NOT successfully retrieved")
            abort(404, message="No industry found on this page")

        app.logger.info("List of industry successfully retrieved")
        return results


api.add_resource(Scraper, "/scrap/<string:query>")
api.add_resource(Search, "/search/<string:query>")
api.add_resource(GetAll, "/businesses")
api.add_resource(GetIndustries, "/industries")


if __name__ == "__main__":
    # app.run(debug=True)
    app.run()