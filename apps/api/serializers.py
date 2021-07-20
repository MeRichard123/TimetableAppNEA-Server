from rest_framework import serializers
from .models import Teacher, Timeslot, Block, YearGroup, Room, Subject, ClassGroup


class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    # Slugs replace the id you would get normally 
    Room = serializers.SlugRelatedField(read_only=True, many=True, slug_field="RoomNumber")
    # SubjectTeach = serializers.SlugRelatedField(read_only=True, many=True, slug_field="name")
    class Meta:
        model = Teacher
        fields = ('id','name','Room')

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'

class YeargroupSerializer(serializers.ModelSerializer):
    classes = serializers.SlugRelatedField(read_only=True, many=True, slug_field="classCode")
    class Meta:
        model = YearGroup
        fields = ('name','classes')

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ('id','RoomNumber','RoomType')

class SubjectSerializer(serializers.ModelSerializer):
    yearGroup = serializers.SlugRelatedField(read_only=True, slug_field='name')
    class Meta:
        model = Subject
        fields = ('name','block','yearGroup','Count')

class ClassGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassGroup
        fields = '__all__'