import json
import os
from typing import List

import requests
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlencode
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rc_protocol import get_checksum


class Endpoint:
    def __init__(self, method: str, name: str):
        self.method = method
        self.name = name


class Api:
    def __init__(self, name: str, endpoints: List[Endpoint]):
        self.name = name
        self.endpoints = endpoints


apis = list(enumerate([
    Api("Controller",
        [Endpoint("post", "openChannel"),
         Endpoint("post", "startStream"),
         Endpoint("get",  "joinStream"),
         Endpoint("post", "endStream")]),
    Api("Streaming Frontend",
        [Endpoint("get",  "join"),
         Endpoint("post", "openChannel"),
         Endpoint("post", "closeChannel"),
         Endpoint("post", "startChat"),
         Endpoint("post", "sendMessage"),
         Endpoint("post", "closeChat")]),
    Api("Streamer",
        [Endpoint("post", "startStream"),
         Endpoint("post", "stopStream")]),
    Api("BBB Chat",
        [Endpoint("get",  "runningChats"),
         Endpoint("post", "startChat"),
         Endpoint("post", "sendMessage"),
         Endpoint("post", "endChat")]),
]))


class MakeCallsView(LoginRequiredMixin, TemplateView):

    template_name = "calls.html"
    login_url = "/admin/login/"

    def get(self, request, *args, **kwargs):
        method = request.GET.get("method", "post")
        url = request.GET.get("url", None)
        secret = request.GET.get("secret", None)
        parameters = json.loads(request.GET.get("parameters", "{}"))
        redirect = json.loads(request.GET.get("redirect", "false"))

        context = {
            "response": False,
            "method": method,
            "url": url,
            "secret": secret,
            "parameters": json.dumps(parameters, indent=4),
            "redirect": redirect,
            "apis": apis,
        }

        if method not in ("get", "post"):
            pass

        elif url is not None and secret is not None and parameters is not None:
            parameters["checksum"] = get_checksum(parameters, secret, os.path.basename(url))
            if method == "post":
                response = requests.post(url, json=parameters, verify=settings.VERIFY_SSL_CERTS, headers={"user-agent": "bbb-controller"})
            elif not redirect:
                response = requests.get(url, params=parameters, verify=settings.VERIFY_SSL_CERTS, headers={"user-agent": "bbb-controller"})
            else:
                return HttpResponseRedirect(url + "?" + urlencode(parameters))

            try:
                text = json.dumps(response.json(), indent=4)
            except json.decoder.JSONDecodeError:
                text = response.text

            context = {
                **context,
                "response": True,
                "status_code": response.status_code,
                "text": text,
            }

        return render(request, self.template_name, context=context)
