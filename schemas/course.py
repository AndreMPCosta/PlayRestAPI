from ma import ma
from models.course import CourseModel
from schemas.user import UserSchema


class CourseSchema(ma.ModelSchema):
    users = ma.Nested(UserSchema, many=True)

    class Meta:
        model = CourseModel
        dump_only = ("id",)
        exclude = ("users",)
        include_fk = True
