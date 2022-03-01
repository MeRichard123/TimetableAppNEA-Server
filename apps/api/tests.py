from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth.models import User
from .views import ClassRoutes

user = User.objects.get(username="admin")

class APITest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_fetch_classes(self):
        """
        Ensure we can fetch classes
        """
        request = self.factory.get('/classes/')
        force_authenticate(request, user=user)
        response = ClassRoutes.as_view({'get':'list'})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)