from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import NormalMessageResponded
from pkg.platform.types.message import MessageChain, Plain
import yaml
import os
import asyncio



class TextSplitterPlugin(BasePlugin):
    default_config = {
        "split_threshold": 500,  # 触发分段的最小字符数
        "segment_size": 500  # 每个分段的字符数
    }

    def __init__(self, host: APIHost):
        super().__init__(host)
        self.config = self.default_config.copy()
        self.config_file = os.path.join(os.dirname(__file__), "config.yaml")
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    if config := yaml.safe_load(f):
                        self.config.update(config)
            except Exception as e:
                self.host.ap.logger.error(f"配置加载失败：{e}")
        else:
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True)
        except Exception as e:
            self.host.ap.logger.error(f"配置保存失败：{e}")

    def split_text(self, text: str) -> list:
        # 核心分段逻辑
        if len(text) <= self.config["split_threshold"]:
            return [text]
        return [
            text[i:i + self.config["segment_size"]]
            for i in range(0, len(text), self.config["segment_size"])
        ]

    @handler(NormalMessageResponded)
    async def on_normal_message_responded(self, ctx: EventContext):
        if not (response_text := ctx.event.response_text):
            return

        segments = self.split_text(response_text)
        if len(segments) <= 1:
            return

        ctx.prevent_default()
        for segment in segments:
            await ctx.reply(MessageChain([Plain(segment)]))