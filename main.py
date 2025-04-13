import os
import json
import time
from datetime import datetime, timedelta

from astrbot.api.star import Star, register, Context
from astrbot.api.event import AstrMessageEvent, EventMessageType
from astrbot.api.event import filter as astr_filter

@register("kami_plugin", "YourName", "卡密发放插件", "1.0.0")
class KamiPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.kami_file = os.path.join(self.context.get_plugin_data_dir(), "kami_pool.json")
        self.user_file = os.path.join(self.context.get_plugin_data_dir(), "user_records.json")
        self.load_data()

    def load_data(self):
        self.kami_pool = []
        self.user_records = {}
        if os.path.exists(self.kami_file):
            with open(self.kami_file, "r", encoding="utf-8") as f:
                self.kami_pool = json.load(f)
        if os.path.exists(self.user_file):
            with open(self.user_file, "r", encoding="utf-8") as f:
                self.user_records = json.load(f)

    def save_data(self):
        with open(self.kami_file, "w", encoding="utf-8") as f:
            json.dump(self.kami_pool, f, indent=2, ensure_ascii=False)
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(self.user_records, f, indent=2, ensure_ascii=False)

    def get_unused_kami(self):
        for item in self.kami_pool:
            if not item.get("used", False):
                return item
        return None

    def mark_kami_used(self, code):
        for item in self.kami_pool:
            if item["code"] == code:
                item["used"] = True
                return

    def can_receive(self, user_id):
        record = self.user_records.get(user_id)
        if not record:
            return True
        last_time = datetime.fromtimestamp(record["last_time"])
        return datetime.now() - last_time > timedelta(days=3)

    def update_user_record(self, user_id):
        self.user_records[user_id] = {"last_time": time.time()}

    @astr_filter.message_type(EventMessageType.GROUP_MESSAGE)
    async def handle_group_message(self, event: AstrMessageEvent):
        text = event.message_str.strip()
        user_id = str(event.get_sender_id())

        if "获取卡密" in text:
            if not self.can_receive(user_id):
                yield event.plain_result("您已领取过卡密，请3天后再试")
                return

            kami = self.get_unused_kami()
            if not kami:
                yield event.plain_result("卡密已发放完毕，请稍后再试")
                return

            self.mark_kami_used(kami["code"])
            self.update_user_record(user_id)
            self.save_data()
            yield event.plain_result(f"您的卡密是：{kami['code']}")
