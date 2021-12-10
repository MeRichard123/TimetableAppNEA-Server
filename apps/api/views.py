from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django.db.models.query import QuerySet
from django.http import  HttpRequest
from django.db.models import Q, Case, When
from django.shortcuts import get_object_or_404

from .serializers import *
from .models import Teacher, Timeslot, YearGroup, Room, Subject, ClassGroup
        


class SharedMethods:
    @staticmethod
    def ExtractValuesById(DataCollection):
        '''Without SlugRelatedFields on Serializer IDs are returned in
        ForeignKey field.
        This makes it hard for POST Routes and so...
        To make it more readable this method takes these 
        IDs makes a query and gets the name/title of the Field. 

        Args:
            DataCollection (OrderedDict): serialized data from db

        Returns:
            dict: returns a formatted response object
        '''
        TeacherVal = Teacher.objects.get(id=DataCollection['Teacher']).name
        RoomVal = Room.objects.get(id=DataCollection['Room']).RoomNumber
        SubjectVal = Subject.objects.get(id=DataCollection['Subject']).name
        ClassGroupVal = ClassGroup.objects.get(id=DataCollection['ClassGroup']).classCode
        data = {
                'id': DataCollection['id'],
                'Day': DataCollection['Day'],
                'Unit': DataCollection['Unit'],
                'Teacher': TeacherVal,
                'Room': RoomVal,
                'Subject': SubjectVal,
                'ClassGroup': ClassGroupVal
            }
        return data  


# ============= Timeslot route logic =============


class TimeslotRoutes(viewsets.ViewSet,SharedMethods):
    permission_classes = [IsAuthenticated]

    def list(self, request:HttpRequest) -> 'QuerySet[Timeslot]':
        '''Performs a SELECT * getting all the timeslots which
        exist in the database.

        Returns:
            QuerySet: A list of all the rows returned from database
        '''
        queryset = Timeslot.objects.all()
        serializer = TimeslotSerializer(queryset,many=True)
        res = [self.ExtractValuesById(data) for data in serializer.data]
        return Response(res)

    def create(self,request:HttpRequest) -> 'Response':
        '''POST Route to create an entry in the Timeslots table
        This will create a timeslot / timetable entry

        Args:
            request: data sent

        Returns:
            Response: return the created entry or any errors
        '''
        yearGroup = 'Yr'+request.data['ClassGroup'][0]
        # Convert Passed in Strings to Ids 
        RequestData = {
            'Day': request.data['Day'],
            'Unit': request.data['Unit'],
            'Teacher' : Teacher.objects.get(name=request.data['Teacher']).id,
            'Room': Room.objects.get(RoomNumber=request.data['Room']).id,
            'Subject': Subject.objects.get(name=request.data['Subject'], yearGroup__name=yearGroup).id,
            'ClassGroup': ClassGroup.objects.get(classCode=request.data['ClassGroup']).id,
        }
        if not request.user.is_staff:
            return Response({'msg':'UNAUTHORISED'})

        serializer = TimeslotSerializer(data=RequestData)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request:HttpRequest, pk:str) -> 'QuerySet[Timeslot]':
        '''Filter the timeslot which is for a specific class on a 
        day and unit specified by query parameters:
        /api/timeslots/7B2/?unit=2&day=Mon

        Args:
            pk: ClassCode to filter timeslots
            request: data sent over http

        Returns:
            Response: return the filter values
        '''
        if request.query_params:
            unit = request.query_params.get('unit')
            day = request.query_params.get('day')
            unitName = f'Unit{unit}'
            queryset = get_object_or_404(Timeslot, ClassGroup__classCode=pk, Day=day, Unit=unitName)
            serializer = TimeslotSerializer(queryset)
            data = self.ExtractValuesById(serializer.data)
            return Response(data)
        else:
            return Response({'msg':'Missing Parameters for Day and Unit',
                             'PreferredFormat':'/api/timeslots/7B2/?unit=2&day=Mon'
                            },status=status.HTTP_400_BAD_REQUEST)

    def delete(self, req, pk):
        if not req.user.is_staff:
            return Response({'msg':'UNAUTHORISED'})

        timeslot = Timeslot.objects.get(id=pk)
        timeslot.delete()
        return Response(data={"Deleted Timeslot"}, status=status.HTTP_204_NO_CONTENT)





# ============= SUBJECT API ROUTE LOGIC =============




class SubjectRoutes(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def __CheckBlockedSubjects(day:str, unit:str, class_:str)->str:
        '''Check the yeargroup the user chose, of a class has a blocked subject
        return it and allow only that to be chosen as they should all have  the 
        same if it is blocked.

        Args:
            day (str): Day on which to check block subject
            unit (str): The unit of the day to check
            class_ (str): The you are filtering for

        Returns:
            [str|None]: return the subject of there is one.  
        '''
        yearHalf = class_[:2]
        blockedSubjects = ['Maths','English','PE','PSHE']
        # get all the subjects of the yeargroup half
        yearSubjects = Timeslot.objects.filter(Day=day,Unit=unit,ClassGroup__classCode__contains=yearHalf)
        serializer = TimeslotSerializer(yearSubjects,many=True)
        # get ids of all subjects
        subjectIds = {timeslot['Subject'] for timeslot in serializer.data}
        # check if it should be a blocked/grouped subject
        for id_ in subjectIds:
            qs = Subject.objects.get(id=id_)
            subject = SubjectSerializer(qs).data['name']
            if subject in blockedSubjects:
                return subject
            else: 
                return None

    @staticmethod
    def __getCurrentSubjectTotals(class_:str, allSubjects:'QuerySet[Subject]')->dict:
        """Create a hash map of the totals of subjects the class has currently
        on their timetable

        Args:
            class_ (str): ClassCode
            allSubjects (querySet): a list of all subjects for the yeargroup

        Returns:
            [dict]: a dictionary holding the subject and amount the class has
       """
        currentAmounts = dict()
        for subject in allSubjects:
            subjectName = subject['name']
            amountHave = Timeslot.objects.filter(
                 ClassGroup__classCode=class_,
                 Subject__name = subjectName).count()
            currentAmounts[subjectName] = amountHave
        return currentAmounts

    @staticmethod
    def __getMissingSubjectAmounts(currentAmounts:dict, yearGroup:int)->list:
        """Create a list of id of all the subjects a yeargroup is missing on their 
        timetable.

        Args:
            currentAmounts (dict): the number of each lessons they already have on the timetable
            yearGroup (int): the yeargroup the the class

        Returns:
            list: a list of ids of all the database entries which match the filter
        """
        subjectsMissingWeights = dict()
        for subject in currentAmounts.keys():
            queryset = Subject.objects.get(yearGroup__name = f'Yr{yearGroup}',name=subject)
            subjectData = SubjectSerializer(queryset).data
            amountMissing =subjectData['Count'] - currentAmounts[subject]
            if amountMissing != 0:
                subjectsMissingWeights[queryset.id] = amountMissing
        
        # Sort by how much they are missing so the one they are missing most is on top.
        subjectMissingIds = sorted(subjectsMissingWeights,
                                    key=lambda k: subjectsMissingWeights[k],
                                    reverse=True
                                    )
        return subjectMissingIds

    def list(self , request:HttpRequest) -> 'QuerySet[Subject]':
        '''Get the names of all the unique subjects which exist:
        SELECT DISTINCT name FROM Subjects

        Returns:
            [JSON Response]: a set of subjects converted to JSON
        '''
        qs = Subject.objects.all()
        data = SubjectSerializer(qs, many=True).data
        return Response(set([subject['name'] for subject in data]))
    

    def retrieve(self, request:HttpRequest, pk:int) -> 'QuerySet[Subject]':
        '''
        GET /api/subjects/7/?day=Mon&unit=5&class=7B2
        Otherwise return any block based subject if the class should have a 
        subject which should run in blocks.

        Returns:
            [JSON Response]: return a set of subjects
        '''
        # Extract Parameters from http request
        day = request.query_params.get('day')
        unit = request.query_params.get('unit')
        class_ = request.query_params.get('class')

        if any(param == None for param in [day,unit,class_]):
            return Response({'msg':'Missing Query for Unit, Day and Class',
                             'format':'/api/subjects/7/?day=Mon&unit=5&class=7B2'})

        # Check for group and return the grouped if any
        blockedSubject = self.__CheckBlockedSubjects(day,f'Unit{unit}',class_)
        if blockedSubject != None: # if there is a blocked subject
            queryset = Subject.objects.get(yearGroup__name = f'Yr{pk}',name=blockedSubject)
            serializer = SubjectSerializer(queryset)
            return Response(serializer.data)
       
        # get all the subjects for a year group
        queryset = Subject.objects.filter(yearGroup__name = f'Yr{pk}')
        serializer = SubjectSerializer(queryset, many=True)
        allSubjects = serializer.data
        removeBlocked = False

        # Remove blocked subjects if a class already has a non blocked subject
        if blockedSubject == None:
            yearHalf = class_[:2]
            yearSubjects = Timeslot.objects.filter(Day=day,Unit=f'Unit{unit}', ClassGroup__classCode__contains=yearHalf)
            classSubjectData = TimeslotSerializer(yearSubjects,many=True).data
            blockedSubjects = ['Maths','English','PE','PSHE']
            subjectNames = [Subject.objects.get(id=item['Subject']).name for item in classSubjectData]

            if any(not subject in blockedSubjects for subject in subjectNames):
                removeBlocked = True
                
        # find current amount of each subject a yeargroup has on their timetable
        currentAmounts = self.__getCurrentSubjectTotals(class_, allSubjects)
        # the subjects the yeargroup is missing most of in their timetable
        subjectMissingIds = self.__getMissingSubjectAmounts(currentAmounts, pk)

        preserveOrder = Case(*[When(pk=pk, then=pos) for pos,pk in enumerate(subjectMissingIds)])

        if removeBlocked:
            subjectFrequencyQueryset = Subject.objects.filter(
                yearGroup__name = f'Yr{pk}',
                id__in=subjectMissingIds,
            ).exclude(
                name__in=['Maths','PSHE','PE','English']
            ).order_by(preserveOrder)
        else:
            subjectFrequencyQueryset = Subject.objects.filter(
                yearGroup__name = f'Yr{pk}',
                id__in=subjectMissingIds).order_by(preserveOrder)
        
        serializedSubjects = SubjectSerializer(subjectFrequencyQueryset, many=True)
        return Response(serializedSubjects.data)







# ============= Yeargroup Api route logic =============






class ClassRoutes(viewsets.ViewSet,SharedMethods):
    permission_classes = [IsAuthenticated]
    # API Routes for the ClassGroups
    def list(self , request:HttpRequest) -> 'QuerySet[YearGroup]':
        '''Performs a: 
        SELECT ClassName from YearGroup
        This will return all the classes for the specified yeargroup.

        Returns:
            [JSON Response]: Sends back JSON for the YearGroup Objects.
        '''
        queryset = YearGroup.objects.all()
        return Response([ClassObject.name for ClassObject in queryset])


    def retrieve(self, request:HttpRequest, pk:int) -> 'QuerySet[YearGroup]':
        '''Perform:
        SELECT * FROM YearGroup WHERE name = Yr{pk}

        Args:
            request (object): holds info about the http request
            pk (int): year group from url i.e /api/year/7

        Returns:
            [JSON Response]: return one yeargroups data based.
        '''
        try:
            queryset = YearGroup.objects.get(name = f'Yr{pk}')
            serializer = YeargroupSerializer(queryset)
            yearGroupData = serializer.data

            classTimeslots = Timeslot.objects.filter(ClassGroup__classCode__contains = pk)
            serializedTimeslots = TimeslotSerializer(classTimeslots,many=True)

            returnObject = {
                'name': yearGroupData['name'],
                'classes': yearGroupData['classes'],
                'timeslots': [self.ExtractValuesById(data) for data in serializedTimeslots.data]
            }
        except:
            return Response('No Classes Found', status=status.HTTP_204_NO_CONTENT)
        return Response(returnObject)






# ============= Teacher Route Logic =============


# GET /api/teachers/

# GET /api/teachers/?Unit=1&Day=Mon&subject=subject/


class TeacherRoutes(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self , request:HttpRequest) -> 'QuerySet[Teacher]':
        """Get all the free teachers who do not have lessons on
        the specified day. Then look at their teaching hours and
        return those who have the most missing. Finally filter 
        them for the specific subject and sort by missing hours. 

        Query Params:
            - subject: the subject you need teachers for
            - day: the week day on the timetable
            - unit: the unit of the day

        Returns:
            [queryset]: the free subject teachers ordered by missing hours.
        """
        subject = request.query_params.get('subject')
        day = request.query_params.get('day')
        unit = request.query_params.get('unit')

        # make sure all params are passed in
        if any(param == None for param in [subject,day,unit]):
            return Response({'msg':"A Parameter is missing. Required:",
                            'params':['subject','day','unit','class']},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get Ids of all teachers who are busy on the selected timeslot
        currentOccupiedTeachers = Timeslot.objects.filter(Day=day, Unit=f'Unit{unit}')
        currentTeacherData = TimeslotSerializer(currentOccupiedTeachers,many=True).data
        occupiedTeacherIds = set([timeslot['Teacher'] for timeslot in currentTeacherData])

        # Get Ids of all teachers
        allTeachers = Teacher.objects.all()
        allTeacherData = TeacherSerializer(allTeachers, many=True).data
        allTeacherIds = set([teacher['id'] for teacher in allTeacherData])

        # Find the difference between the two sets to get all the free teachers
        freeTeachers = allTeacherIds - occupiedTeacherIds
        
        # Hash table of teacher hours missing
        teacherHours = dict()
        # calculate missing hours
        for teacherId in freeTeachers:
            teacherCurrentHours = Timeslot.objects.filter(Teacher=teacherId).count()
            teacher = Teacher.objects.get(id=teacherId)
            weeklyLessons = teacher.LessonsWeekly
            remainingHours = weeklyLessons - teacherCurrentHours
            teacherHours[teacherId] = remainingHours
        # Filter out teachers who have no free hours
        teachersWithFreeHours = list(filter(lambda id_: teacherHours[id_] != 0, teacherHours))
        # Order by from most missing hours to least
        teachersWithFreeHours.sort(reverse=True)
        
      
        #NOTE: pk and index of the sorted teachersWithFreeHours 
        '''
        SELECT DISTINCT id, name, LessonsWeekly
        FROM api_teacher
        INNER JOIN teacher_SubjectTeach
        ON teacher.id = teacher_SubjectTeach.teacher_id
        INNER JOIN subject
        ON teacher_SubjectTeach.subject_id = subject.id
        WHERE subject.name IN (subject) AND teacher.id IN (teacherWithFreeHours)
        ORDER BY CASE WHEN api_teacher.id = pk THEN index ELSE NULL END ASC
        '''
        # make sure the order of the original array stays when I return.
        preserveOrder = Case(*[When(pk=pk, then=pos) for pos,pk in enumerate(teachersWithFreeHours)])

        freeTeachersQuery = Teacher.objects.filter(
                        id__in=teachersWithFreeHours,
                         SubjectTeach__name__in=[subject]
                        ).distinct().order_by(preserveOrder)
        freeTeachersData = TeacherSerializer(freeTeachersQuery, many=True)
        return Response(freeTeachersData.data)
    





# ============= Room Route Logic =============






class RoomRoutes(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @staticmethod
    def __convertRoomsToIds(queryset):
        """Convert a set of rooms returned from db
        to a list of ids for easier comparison.

        Args:
            queryset (QuerySet): result from db query

        Returns:
            [set]: ids of entities in the queryset
        """
        allRooms = RoomSerializer(queryset, many=True).data
        return set([room['id'] for room in allRooms])

    def list(self, request:HttpRequest) -> 'QuerySet[Room]':
        """Filtered Endpoint for returning rooms
        /api/rooms/?class=class&Subject=subject&day=day&unit=unit&teacher=teacher 
        Query Params:
            - class (str) :
            - subject (str) :
            - day (str) :
            - unit (int) :
            - teacher (str) : 

        Returns:
            [type]: [description]
        """
        # Extract Params
        subject = request.query_params.get('subject')
        day = request.query_params.get('day')
        unit = request.query_params.get('unit')
        teacher = request.query_params.get('teacher')
        class_ = request.query_params.get('class')

        # Make sure all parameters are passed in
        if any(param == None for param in [subject,day,unit,teacher,class_]):
            return Response({'msg':"A Parameter is missing. Required:",
                            'params':['subject','day','unit','teacher','class']},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get ids of all rooms being used on a specific day
        currentLessons = Timeslot.objects.filter(Day=day, Unit=f'Unit{unit}')
        currentLessonsData = TimeslotSerializer(currentLessons,many=True).data
        usedRoomIds = set([timeslot['Room'] for timeslot in currentLessonsData])

        # Get the number of pupils in the class
        PupilsInClass = ClassGroup.objects.get(classCode=class_).NumOfPupils
        
        # Get ids of all rooms making sure there is enough space in the room
        allRooms = Room.objects.filter(Capacity__gte=PupilsInClass)
        allRoomIds = self.__convertRoomsToIds(allRooms)
 
        # Set Difference for all free rooms - remove used rooms from all rooms set
        freeRooms = allRoomIds - usedRoomIds

        try:
            # Get all the rooms a teacher usually teaches in
            teacherSubjects = Teacher.objects.get(name=teacher)
            teacherData = TeacherSerializer(teacherSubjects).data
            teacherRooms = teacherData['Room']
        except:
            teacherRooms = []

        # get all the ids of rooms of the teacher from query so that we can
        # prioritize the room of the teacher if it's free
        RoomDataOfTeacher = Room.objects.filter(RoomNumber__in=teacherRooms)
        teacherRoomIds = self.__convertRoomsToIds(RoomDataOfTeacher)
        
        # Filter rooms and only return the teacher rooms which are free
        prioritizeRooms = list(filter(lambda roomId: roomId in teacherRoomIds, freeRooms))

        outPutFilteredRooms = None
        # check of there are any rooms of teachers free and return them of yes
        # AP is excluded as there are no specific rooms for that.
        if len(prioritizeRooms) >= 1 and subject != "AP":
            outPutFilteredRooms = prioritizeRooms
        else:
            # return all of not
            outPutFilteredRooms = freeRooms

        # Allow to return both computing and ICT rooms because they are
        # Differentiated. This is because some rooms are for IT and Computer Science
        # Others are just there available for booking 
        if subject == "ICT" or subject == "Computing":
            # Q gives me the ability to perform or operations: Computing OR ICT Room
            query = Q(Description='ICT') | Q(Description='Computing')
            queryset = Room.objects.filter(query, id__in=outPutFilteredRooms)
        else:
            queryset = Room.objects.filter(Description=subject, id__in=outPutFilteredRooms)
            # Append the rest of the rooms on the list
            currentFilteredData = set(self.__convertRoomsToIds(queryset))
            allRoomsUnique = set(freeRooms) - currentFilteredData
            querysetIds =  list(currentFilteredData) + list(allRoomsUnique)
            preserveOrder = Case(*[When(pk=pk, then=pos) for pos,pk in enumerate(querysetIds)])
            queryset = Room.objects.filter(id__in=querysetIds).order_by(preserveOrder)
  
        # Return all if no filtered rooms are found
        if len(queryset) == 0:
            queryset = Room.objects.filter(id__in=outPutFilteredRooms)
        
        serializer = RoomSerializer(queryset, many=True)
        return Response(serializer.data)





# Overview route






class OverviewRoute(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        day = request.query_params.get('day')
        unit = request.query_params.get('unit')
        # Optional
        subject = request.query_params.get('subject')

        if any(param == None for param in [day,unit]):
            return Response({'msg':"A Parameter is missing. Required:",
                            'params':['day','unit']},
                            status=status.HTTP_400_BAD_REQUEST)

        currentLessons = Timeslot.objects.filter(Day=day, Unit=f'Unit{unit}')
        currentLessonsData = TimeslotSerializer(currentLessons,many=True).data
        usedRoomIds = set([timeslot['Room'] for timeslot in currentLessonsData])

        allRooms = Room.objects.all()
        allRoomData = RoomSerializer(allRooms, many=True).data
        allRoomIds = set([room['id'] for room in allRoomData])

        freeRooms = allRoomIds - usedRoomIds

        query = Q(Description='ICT') | Q(Description='Computing')
        queryset = Room.objects.filter(query, id__in=freeRooms)
        
        teacherOutput = {}

        if subject:
            currentOccupiedTeachers = Timeslot.objects.filter(Day=day, Unit=f'Unit{unit}')
            currentTeacherData = TimeslotSerializer(currentOccupiedTeachers,many=True).data
            occupiedTeacherIds = set([timeslot['Teacher'] for timeslot in currentTeacherData])

            allTeachers = Teacher.objects.all()
            allTeacherData = TeacherSerializer(allTeachers, many=True).data
            allTeacherIds = set([teacher['id'] for teacher in allTeacherData])

            freeTeachers = allTeacherIds - occupiedTeacherIds
            teacherQuery = Teacher.objects.filter(id__in=freeTeachers, SubjectTeach__name__in=[subject]).distinct()
            teacherOutput = TeacherSerializer(teacherQuery, many=True).data


        roomsOutput = RoomSerializer(queryset, many=True).data
        response = {
            'rooms': roomsOutput,
            'teachers': teacherOutput
        }
        return Response(response)