from django.db import models
from django.utils.functional import cached_property

from children.models import XmppChat, BBBChat, BBBLive, StreamFrontend


class Stream(models.Model):
    meeting_id = models.CharField(default="", max_length=255)
    rtmp_uri = models.CharField(default="", max_length=255)
    bbb_chat = models.ForeignKey(BBBChat, on_delete=models.CASCADE)
    bbb_live = models.ForeignKey(BBBLive, on_delete=models.CASCADE)
    frontend = models.ForeignKey(StreamFrontend, on_delete=models.CASCADE)

    class Meta:
        # Only one meeting id per bbb cluster per time
        unique_together = ("meeting_id", "bbb_chat")

    @cached_property
    def meeting_password(self):
        return str(self.bbb_chat.bbb.api.get_meeting_info(self.meeting_id)["xml"]["attendeePW"])

    def start(self):
        print(self.bbb_chat.start_chat(
            self.meeting_id,
            "Stream",
            self.frontend.api_url,
            self.frontend.secret,
            self.meeting_id
        ).text)

        print(self.frontend.start_chat(
            self.meeting_id,
            self.bbb_chat.url,
            self.bbb_chat.secret
        ).text)

        print(self.bbb_live.start_stream(
            self.rtmp_uri,
            self.meeting_id,
            self.meeting_password
        ).text)

    def end(self):
        print(self.bbb_chat.end_chat(self.meeting_id).text)
        print(self.frontend.end_chat(self.meeting_id).text)
        print(self.bbb_live.stop_stream(self.meeting_id).text)
