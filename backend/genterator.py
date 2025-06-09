import os
from openai import OpenAI
import threading


class GeneratorService:
    def __init__(self):
        """
        初始化生成器服务
        """
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
            base_url=os.getenv(
                "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        )
        self.model = os.getenv("OPENAI_MODEL", "deepseek-r1-distill-llama-8b")
        self.prompt_data = {}

        self.summary_health_message = ""

    def update_data(self, data):
        """
        更新健康状态数据
        """
        self.prompt_data = data

    ai_summary_prompt = """你是一个世界级超级智能语言处理模型。用户在工位上，你需要总结以下一系列关于这个人（即用户）的健康相关的状态数据，主要包含关键信息解读，50字以内。
注意：
- 语言以第二人称“你”来表达，不要直呼用户。
- 你需要纯中文响应，不能带Markdown语法，不能使用Emoji，不能带状态原始JSON字段。
- 响应内容不需要标题，自然的方式表达。
- 以下用户的健康状态数据以JSON形式提供，你需要回复纯文本的响应：
"""

    def refresh_summary_health(self):
        """
        根据最新的健康指标，在后台更新 summary_health_message
        使用流式API实时累积响应
        """
        if not self.prompt_data:
            return "[GeneratorService] 没有可用的健康数据"

        def stream_worker():
            try:
                self.summary_health_message = ""  # 重置消息

                # 创建流式响应
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.ai_summary_prompt
                        },
                        {
                            "role": "user",
                            "content": str(self.prompt_data)
                        }
                    ],
                    stream=True
                )

                # 处理流式响应，实时累积消息
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        self.summary_health_message += content  # 实时累积消息

                print(
                    f"[GeneratorService] Streaming completed, total message: {len(self.summary_health_message)} characters")

            except Exception as e:
                error_msg = f"[GeneratorService] Streaming Error: {str(e)}"
                print(error_msg)
                self.summary_health_message = error_msg

        # 在新线程中启动流式处理
        thread = threading.Thread(target=stream_worker)
        thread.daemon = True
        thread.start()

        return "[GeneratorService] 开始生成流式健康摘要"
