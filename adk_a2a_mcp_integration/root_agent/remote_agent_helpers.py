"""Helper functions to interact with other agents exposed via A2A"""
import httpx
import logging
from typing import Any
from uuid import uuid4
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

logger = logging.getLogger(__name__)

remote_agent_cards_cache = []

remote_agent_url = "http://localhost:8090/"

async def list_remote_agents() -> list[dict]:
    """Fetches the capabilities of all available remote agents"""
    
    if remote_agent_cards_cache:
        logger.info("Remote agents card cache exists, using cache")
        return remote_agent_cards_cache
    logger.info("Agent card cache empty, fetching...")
    try:
        async with httpx.AsyncClient(timeout=120) as httpx_client:
            # get only one agent url for now
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=remote_agent_url,
            )
            logger.info("Attempting to fetch agent card...")
            agent_card = await resolver.get_agent_card()
            logger.info('Agent card fetched. Agent card:')
            logger.info(agent_card.model_dump_json(indent=2, exclude_none=True))
        
        remote_agent_cards_cache.append({
            "agent_name": agent_card.name,
            "agent_card": agent_card
        })
        logger.info("Adding data to cache...")
        return remote_agent_cards_cache
    except Exception as e:
        logger.error("Failed to fetch agent card.")
        raise RuntimeError("Failed to fetch the agent card. Unable to proceed") from e

async def call_remote_agent(query: str, agent_name: str) -> str:
    """Call the remote agent with appropriate query"""
    
    agent_cards = await list_remote_agents()
    
    agent_card_to_use = None
    
    for card in agent_cards:
        if card.get("agent_name") == agent_name:
            agent_card_to_use = card.get("agent_card")
            break
    if agent_card_to_use is None:
        raise ValueError(f"Agent with name '{agent_name}' not found in available agents.")
    logger.info("Initializing A2A Client...")
    async with httpx.AsyncClient(timeout=120) as httpx_client:

        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card_to_use
        )
        logger.info("A2A Client Initialized.")

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': query}
                ],
                'messageId': uuid4().hex,
            },
        }
        logger.info("Sending query to remote agent...")
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        try:
            response = await client.send_message(request)
            response_dict = response.model_dump(mode='json', exclude_none=True)
            logger.info(f"Response received from remote agent: {response_dict}")
        except Exception as e:
            logger.error("Failed to send message to remote agent.")
            raise RuntimeError("Remote agent call failed.") from e
    
    agent_response_text = "No text content found in response or an error occurred."
    try:
        agent_response_text = response_dict['result']['parts'][0]['text']
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing agent response structure: {e}")

    return agent_response_text
