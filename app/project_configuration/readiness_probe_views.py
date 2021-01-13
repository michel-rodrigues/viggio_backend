from django.db import connection
from django.http import HttpResponse, HttpResponseServerError


def readiness_probe(request, k8s_key):
    if not str(k8s_key) == '453a9f60-5851-4b40-a5a1-1e875e108d79':
        return HttpResponseServerError()
    connection.ensure_connection()
    return HttpResponse()
