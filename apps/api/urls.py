from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import TeacherRoutes, ClassRoutes, SubjectRoutes, TimeslotRoutes, RoomRoutes, OverviewRoute

router = DefaultRouter() 

router.register("teachers",TeacherRoutes, basename="teachers")
router.register("year",ClassRoutes, basename="classes")
router.register("subjects",SubjectRoutes, basename="subjects")
router.register("timeslots",TimeslotRoutes, basename="timeslots")
router.register("rooms",RoomRoutes, basename="rooms")
router.register("overview", OverviewRoute, basename="overview")

urlpatterns = [
    path("api/",include(router.urls)),
]