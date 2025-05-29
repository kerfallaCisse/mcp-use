from mcp_use import MCPAgent, MCPClient
import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class MCPUSE_CLIENT:
    def __init__(self, config: dict = None):
        # self.client = MCPClient.from_config_file(
        #     os.path.join(os.path.dirname(__file__), "config.json"))
        self.client = MCPClient.from_dict(config=config)
        self.llm = ChatOpenAI(
            model_name="gpt-4o", temperature=0, api_key=OPENAI_API_KEY
        )
        self.agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=30,
            use_server_manager=True,
            verbose=True,
        )

    async def process_query(self, query: str, access_token) -> str:
        result = await self.agent.run(query=query, access_token=access_token)
        return result
