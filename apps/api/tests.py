from django.http import request
from django.test import TestCase
from rest_framework.test import APIRequestFactory

# Create your tests here.

factory = APIRequestFactory()

request = factory.get("/api/year", None)

# WRITE TESTS FOR ROOMS