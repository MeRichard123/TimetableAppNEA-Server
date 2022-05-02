from django.contrib import admin
from .models import Timeslot,YearGroup,Teacher,Subject,Room,ClassGroup,Block, SubjectGroup
from django.db.models import Count
from .customFilters import PupilCountFilter,RoomCapacityFilter

"""
- Define how data will be viewed in the admin panel
- Define which fields to display
- Define custom aggregate display values
- Define filters for data

"""
admin.site.register(Block)
admin.site.register(SubjectGroup)

@admin.register(Timeslot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['id','Day','Unit','Subject','Room','Teacher','ClassGroup']
    list_filter = ['Day','Unit']
    list_display_links = ['id','Day']


@admin.register(Teacher)
class TeacherAdminView(admin.ModelAdmin):
    list_display = ['id','name','LessonsWeekly']
    list_filter = ['LessonsWeekly']
    list_display_links = ['name']
    search_fields = ['name']


@admin.register(Room)
class RoomAdminView(admin.ModelAdmin):
    list_display = ['id','RoomNumber','Description','Capacity','Block','RoomType']
    list_filter = ['Block','RoomType','Description', RoomCapacityFilter]
    list_display_links = ['RoomNumber']
    search_fields = ['RoomNumber']

@admin.register(YearGroup)
class YearGroupAdminView(admin.ModelAdmin):
    # aggregate a count of all classes which are related
    def get_queryset(self,request):
        qs = super(YearGroupAdminView,self).get_queryset(request)
        return qs.annotate(class_count = Count('classes'))

    # Create a value to use as a display
    def class_count(self,instance):
        return instance.class_count

    list_display = ['name','class_count']

@admin.register(ClassGroup)
class GroupAdminDisplay(admin.ModelAdmin):
    list_display = ['id','classCode','NumOfPupils']
    list_filter = [PupilCountFilter]
    list_display_links = ['classCode']
    search_fields = ['classCode']

@admin.register(Subject)
class SubjectAdminDisplay(admin.ModelAdmin):
    list_display = ['id','name','yearGroup','Count','block']
    list_filter = ['yearGroup__name']
    list_display_links = ['name']
    search_fields = ['name']