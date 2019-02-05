import datetime
import time

from flask import request
from flask_restful import Resource

from models.course import CourseModel
from models.user import UserModel
from schemas.course import CourseSchema
from libs.strings import gettext
from utils.datetime_converter import str_to_time

course_schema = CourseSchema()
course_list_schema = CourseSchema(many=True)
week_list = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']


class Course(Resource):
    @classmethod
    def get(cls, name: str = None, course_id: int = None):
        course = CourseModel.find_by_name(name)
        if course_id:
            course = CourseModel.find_by_id(course_id)
            if course:
                return course_schema.dump(course), 200
        if course:
            return {"course_intances": course_list_schema.dump(course)}, 200

        return {"message": gettext("course_not_found")}, 404

    @classmethod
    def post(cls, name: str):
        data = request.get_json()
        #converted_start_time = str_to_time(data['start_time'])
        # for course in CourseModel.find_by_name(name):
        #     if course.start_time == converted_start_time:
        #         return {"message": gettext("course_already_scheduled").format(name)}, 400
        data["name"] = name
        course = course_schema.load(data)
        try:
            course.save_to_db()
        except:
            return {"message": gettext("course_error_inserting")}, 500

        return course_schema.dump(course), 201

    @classmethod
    def delete(cls, course_id: int = None):
        course = CourseModel.find_by_id(course_id)
        if course:
            course.delete_from_db()
            return {"message": gettext("course_deleted")}, 200

        return {"message": gettext("course_not_found")}, 404


class CourseList(Resource):
    @classmethod
    def get(cls):
        return {"courses": course_list_schema.dump(CourseModel.query.order_by(CourseModel.day_week).all())}, 200


class EnrollUser(Resource):
    @classmethod
    def post(cls):
        data = request.get_json()
        course = CourseModel.find_by_id(data['course_id'])
        user = UserModel.find_by_id(data['user_id'])
        if user:
            if course:
                if user in course.users:
                    return {"message": gettext('user_already_enrolled').format
                            (course.name, week_list[course.day_week].capitalize() +
                             course.start_time.strftime(' - %H:%M'))}, 400
                else:
                    course.enroll_user(user)
            else:
                return {"message": gettext("course_not_found")}, 404
        else:
            return {"message": gettext("user_not_found")}, 404
        return {"message": gettext("user_enrolled").format
                (course.name, week_list[course.day_week].capitalize() +
                 course.start_time.strftime(' - %H:%M'))}, 200


class DisenrollUser(Resource):
    @classmethod
    def post(cls):
        data = request.get_json()
        course = CourseModel.find_by_id(data['course_id'])
        user = UserModel.find_by_id(data['user_id'])
        if user:
            if course:
                if user not in course.users:
                    return {"message": gettext('user_not_enrolled')}, 400
                else:
                    course.disenroll_user(user)
            else:
                return {"message": gettext("course_not_found")}, 404
        else:
            return {"message": gettext("user_not_found")}, 404
        return {"message": gettext("user_disenrolled").format
                (course.name, week_list[course.day_week].capitalize() +
                 course.start_time.strftime(' - %H:%M'))}, 200


class GetEnrolledUsers(Resource):
    @classmethod
    def get(cls, course_id: int):
        course = CourseModel.find_by_id(course_id)
        if course:
            return {"registered users": [{"id": user.id, "name": user.name} for user in course.users]}
        else:
            return {"message": gettext("course_not_found")}, 404
