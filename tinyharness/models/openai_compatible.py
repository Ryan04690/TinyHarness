from openai import OpenAI
from tinyharness.models import ModelProvider

class OpenAICompatibleProvider(ModelProvider):
    def __init__(
            self,
            model,
            api_key,
            base_url,
            thinking_enabled=False,
    ):
        self.model = model
        # self.messages = [] 目前先不需要Provider自己维护messages，交给调用者维护 后面会针对这个开发一个State
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.thinking_enabled = thinking_enabled

    def generate(self, messages, tools=None):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream":False,
        }
        if tools is not None:
            kwargs["tools"] = tools
        if not self.thinking_enabled:
            kwargs["extra_body"] = {
                "thinking":{
                    "type":"disabled"
                }
            }
        return self.client.chat.completions.create(**kwargs)