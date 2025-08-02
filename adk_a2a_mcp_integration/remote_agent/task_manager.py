"""Module that handles the invocation of agent"""
import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_task

from remote_agent.agent import BasicSearchAgent

logger = logging.getLogger(__name__)

class BasicSearchAgentExecutor(AgentExecutor):
    """Agent executor that invokes the agent"""

    def __init__(self):
        super().__init__()
        self._agent = BasicSearchAgent()

    async def execute(self, request_context: RequestContext, event_queue: EventQueue) -> None:
        """Invokes the agent with the request context"""
        query = request_context.get_user_input()
        task = request_context.current_task
        if not task:
            task = new_task(request_context.message)
            await event_queue.enqueue_event(task)
            logger.info(f"Creating new task with id: {task.id}.")

        session_id = task.contextId
        logger.info(f"Using session id: {session_id}.")
        async for event in self._agent.invoke(
            session_id=session_id,
            query=query
            # user_id=request_context.user_id,
        ):
            if event.get("status") == "success":
                await event_queue.enqueue_event(
                    new_agent_text_message(text=event.get("result"))
                )
            elif event.get("status") == "error":
                await event_queue.enqueue_event(
                    new_agent_text_message(text=f"Error: {event.get('error_message')}")
                )
            else:
                await event_queue.enqueue_event(
                    new_agent_text_message(text=event.get("result"))
                )

    async def cancel(self, request_context: RequestContext, event_queue: EventQueue) -> None:
        """To cancel an ongoing agent execution"""
        raise ValueError('cancel not supported at this moment!')
