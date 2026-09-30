"""
Conversation memory for the /ask endpoint.

Owns per-session chat history as a list of LangChain BaseMessage objects, so
ask_question() (a stateless function in chains.py) can be handed the right
history for a given session, and the caller appends the new turn back in
afterward -- same "caller owns and appends to a plain list" pattern chains.py
was built around. Same "in-memory, no persistence, single shared instance"
shape as core/store.py: history lives for the life of the process and resets
on restart, consistent with the rest of LineMate not using a real database.
"""
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class ConversationMemory:
    def __init__(self) -> None:
        self._sessions: dict[str, list[BaseMessage]] = {}

    def get_history(self, session_id: str) -> list[BaseMessage]:
        """
        Returns this session's history, creating an empty one on first use.
        The list returned is the live one this instance holds -- callers pass
        it straight into ask_question() to read, but should go through
        add_turn() (not append to this list directly) to write new turns.
        """
        return self._sessions.setdefault(session_id, [])

    def add_turn(self, session_id: str, question: str, answer: str) -> None:
        """Appends one question/answer exchange to the session's history."""
        history = self.get_history(session_id)
        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=answer))

    def clear(self, session_id: str) -> None:
        """Drops a session's history entirely -- e.g. a 'start over' request."""
        self._sessions.pop(session_id, None)


# Single shared instance, imported everywhere -- same pattern as core/store.store
memory = ConversationMemory()