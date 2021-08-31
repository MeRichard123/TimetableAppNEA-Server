from django.db import models

class Timeslot(models.Model):
    # ENUM Choices
    DayChoices = [
        ('Mon','Monday'),
        ('Tue','Tuesday'),
        ('Wed','Wednesday'),
        ('Thu','Thursday'),
        ('Fri','Friday')
    ]
    UnitChoices = [
        ('Unit1', 'Unit 1'),
        ('Unit2', 'Unit 2'),
        ('Form','Form'),
        ('Unit3','Unit 3'),
        ('Unit4','Unit 4'),
        ('Unit5','Unit 5'),
    ]
    # db fields
    Day = models.CharField(max_length=3, choices=DayChoices)
    Unit = models.CharField(max_length=6, choices=UnitChoices)
    Teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    Room = models.ForeignKey('Room', on_delete=models.CASCADE)
    Subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    ClassGroup = models.ForeignKey('ClassGroup',on_delete=models.CASCADE)

class Teacher(models.Model):
    name = models.CharField(max_length=50,default="Mrs Jones")
    LessonsWeekly = models.IntegerField(default=0)
    Room = models.ManyToManyField("Room", blank=True)
    SubjectTeach = models.ManyToManyField("Subject", blank=True)

    def __str__(self):
        return self.name

class Block(models.Model):
    name = models.IntegerField(default=0)

    def __str__(self):
        return f'Block {self.name}'

class Room(models.Model):
    RoomChoices = [
        ('ClassRoom','Class Room'),
        ('ComputerRoom','Computer Room')
    ]
    DescriptionChoices = [
        ('Science','Science'),
        ('Computing','Computing'),
        ('Food','Food'),
        ('Art','Art'),
        ('Construction','Construction'),
        ('English','English'),
        ('Hums','Hums'),
        ('ICT','ICT'),
        ('P16','P16'),
        ('Maths','Maths'),
        ('PE','PE'),
        ('BSt','BSt'),
        ('MFL','MFL'),
        ('Music', 'Music'),
        ('Sp Hall','Sp Hall'),
        ('Nurture','Nurture'),
        ('Dr St','Dr St'),
        ('Da St', 'Da St')
    ]
    RoomNumber = models.CharField(max_length=4)
    Description = models.CharField(max_length=50,choices=DescriptionChoices,null=True)
    Capacity = models.IntegerField(default=0)
    Block = models.ForeignKey(Block,on_delete=models.SET_NULL, blank=True,null=True)
    RoomType = models.CharField(choices=RoomChoices,max_length=len('ComputerRoom'))

    def __str__(self):
        return f"{self.RoomType} - {self.RoomNumber}"

class YearGroup(models.Model):
    # Max Length = 3; e.g Yr8
    name = models.CharField(max_length=4)
    classes = models.ManyToManyField('ClassGroup',blank=True) 

    def __str__(self):
        return self.name

class ClassGroup(models.Model):
    classCode = models.CharField(max_length=10)
    NumOfPupils = models.IntegerField(default=0)
    Subjects = models.ManyToManyField('Subject',blank=True)

    def __str__(self):
        return self.classCode

class Subject(models.Model):
    name = models.CharField(max_length=50)
    block = models.ForeignKey(Block,on_delete=models.SET_NULL, blank=True, null=True)
    yearGroup = models.ForeignKey(YearGroup,
        on_delete=models.CASCADE,
        blank=True,
        related_name='yeargroups')
    Count = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.name} - {self.yearGroup}' 




