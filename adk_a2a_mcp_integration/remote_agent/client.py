"""Module to test the remote agent exposed via A2A. Mimic's client side implementation"""
import asyncio
import logging
from typing import Any
from uuid import uuid4
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

logger = logging.getLogger(__name__)

async def client():
    """Test the agent with a simple client"""
    async with httpx.AsyncClient(timeout=120) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url="http://localhost:8090/",
        )
        logger.info("Attempting to fetch agent card...")
        agent_card = await resolver.get_agent_card()
        logger.info('Agent card fetched. Agent card:')
        logger.info(agent_card.model_dump_json(indent=2, exclude_none=True))

        logger.info("Initializing A2A Client")
        client_instance = A2AClient(
            httpx_client=httpx_client, agent_card=agent_card
        )
        logger.info('A2A Client initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'kind': 'text',
                        'text': 'What is model context protocol? Give a brief description.'
                    }
                ],
                'messageId': uuid4().hex,
            },
        }
        logger.info("Sending test message")
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        response = await client_instance.send_message(request)
        logger.info(response.model_dump(mode='json', exclude_none=True))
        response_dict = response.model_dump(mode='json', exclude_none=True)
        agent_response_text = "No text content found in response or an error occurred."
        try:
            agent_response_text = response_dict['result']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            logger.info(f"Error parsing agent response structure: {e}")

        logger.info("\n--- Agent's Final Response ---")
        logger.info(agent_response_text)
        logger.info("----------------------------")

asyncio.run(client())
