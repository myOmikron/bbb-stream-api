import os

from django.db.models import Count
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.http import urlencode
from rc_protocol import get_checksum

from bbb_common_api.views import PostApiPoint, GetApiPoint
from children.models import BBB, BBBChat, BBBLive, StreamFrontend
from stream.models import Stream


class StartStream(PostApiPoint):

    endpoint = "startStream"
    required_parameters = ["meeting_id"]

    def safe_post(self, request, parameters, *args, **kwargs):
        # TODO: implement optional welcome_msg, redirect_url
        meeting_id = parameters["meeting_id"]

        if Stream.objects.filter(meeting_id=meeting_id).count() > 0:
            return JsonResponse(
                {"success": False, "message": "There is already a stream running"},
                status=304,
                reason="There is already a stream running"
            )

        # Search in bbb instances for meeting id
        for bbb in BBB.objects.all():
            if bbb.api.is_meeting_running(meeting_id).is_meeting_running():
                break
        else:
            return JsonResponse(
                {"success": False, "message": "No matching running meeting found."},
                status=404,
                reason="No matching running meeting found."
            )

        # bbb chat for bbb instance
        bbb_chat = BBBChat.objects.get(bbb=bbb)

        # bbb live with least running streams
        bbb_live = BBBLive.objects.annotate(streams=Count("stream")).earliest("streams")

        # frontend with least running streams
        frontend = StreamFrontend.objects.annotate(streams=Count("stream")).earliest("streams")

        _key = frontend.open_channel(meeting_id).json()["content"]["streaming_key"]
        rtmp_uri = os.path.join(frontend.url, "stream", _key)
        _replace = "http"
        if rtmp_uri.startswith("https"):
            _replace = "https"
        rtmp_uri = rtmp_uri.replace(_replace, "rtmp")

        # new stream to start
        stream = Stream.objects.create(
            meeting_id=meeting_id,
            rtmp_uri=rtmp_uri,
            frontend=frontend,
            bbb_chat=bbb_chat,
            bbb_live=bbb_live,
        )

        stream.bbb_chat.start_chat(
            meeting_id,
            "Stream",
            frontend.api_url,
            frontend.secret
        )

        stream.frontend.start_chat(
            meeting_id,
            bbb_chat.url,
            bbb_chat.secret
        )

        stream.bbb_live.start_stream(
            rtmp_uri,
            meeting_id,
            stream.meeting_password
        )

        return JsonResponse(
            {"success": True, "message": "Stream started successfully."}
        )


class JoinStream(GetApiPoint):

    endpoint = "joinStream"
    required_parameters = ["meeting_id", "user_name"]

    def safe_get(self, request, *args, **kwargs):
        meeting_id = request.GET["meeting_id"]
        user_name = request.GET["user_name"]

        try:
            stream = Stream.objects.get(meeting_id=meeting_id)
        except Stream.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "There is no stream running for this meeting"},
                status=404,
                reason="There is no stream running for this meeting"
            )

        get = {
            "meeting_id": meeting_id,
            "user_name": user_name,
        }
        get["checksum"] = get_checksum(get, stream.frontend.secret, "join")

        return HttpResponseRedirect(
            os.path.join(stream.frontend.url, "/api/v1/join?") + urlencode(get)
        )


class EndStream(PostApiPoint):

    endpoint = "endStream"
    required_parameters = ["meeting_id"]

    def safe_post(self, request, parameters, *args, **kwargs):
        meeting_id = parameters["meeting_id"]

        try:
            stream = Stream.objects.get(meeting_id=meeting_id)
        except Stream.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "There is no stream running for this meeting"},
                status=404,
                reason="There is no stream running for this meeting"
            )

        stream.bbb_chat.end_chat(stream.meeting_id)
        stream.frontend.end_chat(stream.meeting_id)
        stream.bbb_live.stop_stream(stream.meeting_id)
        stream.frontend.close_channel(stream.meeting_id)
        stream.delete()

        return JsonResponse(
            {"success": True, "message": "Stream stopped successfully."}
        )
