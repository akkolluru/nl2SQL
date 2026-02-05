
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Set, Any

class BaseAdapter(ABC):
    """
    Abstract base class for all database adapters.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    def get_schema_summary(self) -> str:
        """
        Return a compact string representation of the schema for the LLM.
        Format: "Tables: t1(c1, c2); t2(c3, c4)"
        """
        pass

    @abstractmethod
    def get_allowed_sets(self) -> Tuple[Set[str], Dict[str, Set[str]]]:
        """
        Return (set_of_table_names, dict_of_table_to_columns) for validation.
        """
        pass

    @abstractmethod
    def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Execute a SELECT query and return (columns, rows).
        rows should be a list of dictionaries.
        """
        pass
