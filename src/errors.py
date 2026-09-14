"""System-wide custom exceptions for the Football AI Intelligence System."""


class FootballAIError(Exception):
    """Base exception for all system errors."""
    pass


class ValidationError(FootballAIError):
    """Raised when data validation fails."""
    pass


class DataIntegrityError(FootballAIError):
    """Raised when data contracts or required fields are violated."""
    pass


class RiskEngineError(FootballAIError):
    """Raised when risk assessment encounters invalid configurations or states."""
    pass
