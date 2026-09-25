# --- Ingestion errors: something went wrong turning a CSV row into a model ---
class DocumentLoadError(Exception):
    """Something went wrong turning a documents.csv row into a Document."""

class TicketLoadError(Exception):
    """Something went wrong turning a tickets.csv row into a Ticket."""

class CrewLoadError(Exception):
    """Something went wrong turning a crew.csv row into a CrewMember."""


# --- Store lookup errors: something was requested that doesn't exist ---
class DocumentNotFoundError(Exception):
    """Document was not found."""

class TicketNotFoundError(Exception):
    """Ticket was not found."""

class CrewMemberNotFoundError(Exception):
    """Crew member was not found."""