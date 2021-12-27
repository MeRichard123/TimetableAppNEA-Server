from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from knox.models import AuthToken
from .serializers import UserSerializer, LoginSerializer, ExtendedUserSerializer
from  .models import ExtendUser
from rest_framework import viewsets

class LoginApi(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, req, *args, **kwargs):
        serializer = self.get_serializer(data=req.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'token': AuthToken.objects.create(user)[1],
        })

class GetUserApi(viewsets.ViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def list(self, request):
        user = ExtendUser.objects.get(user=request.user)
        serializedExtended = ExtendedUserSerializer(user)
        mainUser = UserSerializer(request.user)
        return Response({'user':mainUser.data ,'extended':serializedExtended.data})

@api_view()
def completeTutorial(request):
    user = ExtendUser.objects.get(user=request.user)
    user.finishedTutorial = True
    user.save()
    
    return Response({'finishedTutorial': True})