import httpx
import asyncio
from typing import Any
from uuid import uuid4
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

async def client():
    async with httpx.AsyncClient(timeout=120) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url="http://localhost:8090/",
        )
        print("Attempting to fetch agent card...")
        agent_card = await resolver.get_agent_card()
        print('Agent card fetched. Agent card:')
        print(agent_card.model_dump_json(indent=2, exclude_none=True))

        print("Initializing A2A Client")
        client = A2AClient(
            httpx_client=httpx_client, agent_card=agent_card
        )
        print('A2A Client initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'What is model context protocol? Give a brief description.'}
                ],
                'messageId': uuid4().hex,
            },
        }
        print("Sending test message")
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        response = await client.send_message(request)
        print(response.model_dump(mode='json', exclude_none=True))
        response_dict = response.model_dump(mode='json', exclude_none=True)
        agent_response_text = "No text content found in response or an error occurred."
        try:
            agent_response_text = response_dict['result']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            print(f"Error parsing agent response structure: {e}")

        print("\n--- Agent's Final Response ---")
        print(agent_response_text)
        print("----------------------------")

asyncio.run(client())
