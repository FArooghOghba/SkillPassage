"""Auth token service module for managing token-related business logic.

This module provides core functionality for generating, parsing, and verifying
tokens for authentication and authorization purposes.
"""
import logging
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID

from jose import jwt
from jose.exceptions import (
    ExpiredSignatureError,
    JWTClaimsError,
    JWTError,
)

from src.auth.exceptions import (
    NotAuthorizedError,
    TokenError,
)
from src.auth.schemas import TokenPayload
from src.core.config import auth_settings


logger = logging.getLogger(__name__)


def create_access_token(
    user_id: UUID,
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token for the given user.

    Args:
        user_id: The UUID of the user
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token

    Note:
        Token includes:
        - Subject claim (sub): User's UUID
        - Issued at (iat): Current UTC timestamp
        - Expiration (exp): UTC timestamp
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + auth_settings.access_token_expire_delta

    claims = {
        "sub": str(user_id),
        'iat': now,
        "exp": expire,
    }

    encoded_jwt: str = jwt.encode(
        claims=claims,
        key=auth_settings.JWT_SECRET_KEY,
        algorithm=auth_settings.JWT_ALGORITHM
    )

    logger.info(
        msg="Access token created",
        extra={
            "user_id": str(user_id),
            "expires_at": expire.isoformat()
        }
    )
    return encoded_jwt


async def verify_access_token(token: str) -> TokenPayload:
    """Verify and decode a JWT access token.

    Args:
        token: JWT token to verify and decode

    Returns:
        dict[str, str]: Verified token payload containing user_id

    Raises:
        TokenError: If token is malformed or has invalid signature
        NotAuthorizedError: If token is expired or has invalid claims

    Note:
        Performs multiple validations:
        - Token signature verification
        - Expiration check
        - Required claims presence
        - Claims format validation
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.JWT_SECRET_KEY,
            algorithms=[auth_settings.JWT_ALGORITHM]
        )

        user_id = payload.get('sub')
        token_issued_at_in_sec = payload.get('iat')
        token_expiration_in_sec = payload.get('exp')

        token_issued_at = datetime.fromtimestamp(
            token_issued_at_in_sec, tz=timezone.utc
        ) if token_issued_at_in_sec else None

        token_expiration = datetime.fromtimestamp(
            token_expiration_in_sec, tz=timezone.utc
        ) if token_expiration_in_sec else None

        if not user_id:
            logger.warning("Token missing required 'sub' claim")
            raise TokenError('Invalid token format')

        return TokenPayload(
            sub=UUID(user_id),
            iat=token_issued_at,
            exp=token_expiration
        )

    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise NotAuthorizedError('Token has expired')
    except JWTClaimsError:
        logger.warning("Token has invalid claims")
        raise TokenError('Invalid token claims')
    except JWTError as e:
        logger.warning(
            msg="Token verification failed",
            extra={"error": str(e)}
        )
        raise TokenError('Invalid token')
