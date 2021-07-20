from django.contrib.admin import SimpleListFilter

class PupilCountFilter(SimpleListFilter):
    """
    This filter is being used in django admin panel in ClassGroup model.
    It will allow you to filter by less than or greater than
    """
    # Displayed in the filter box
    title = 'Number Of Pupils'
    # Url bar text
    parameter_name = 'pupilcount'

    # define values for the filter
    def lookups(self,req,model_admin):
        return (
            ('lte','20 or Less'),
            ('gte','more than 20')
        )

    # return filtered querysets
    def queryset(self,req,queryset):
        if self.value() == "lte":
            return queryset.filter(NumOfPupils__lte = 20)
        elif self.value() == 'gte':
            return queryset.filter(NumOfPupils__gte = 20)
        else:
            return queryset.all()

class RoomCapacityFilter(SimpleListFilter):
    """
    This filter is being used in django admin panel in Room model.
    It will allow you to filter by less than or greater than
    """
    # Displayed in the filter box
    title = 'Capacity'
    # Url bar text
    parameter_name = 'capacity'

    # define values for the filter
    def lookups(self,req,model_admin):
        return (
            ('lte','Less than 30'),
            ('gte','30 or More')
        )

    # return filtered querysets
    def queryset(self,req,queryset):
        if self.value() == "lte":
            return queryset.filter(Capacity__lt = 30)
        elif self.value() == 'gte':
            return queryset.filter(Capacity__gte = 30)
        else:
            return queryset.all()