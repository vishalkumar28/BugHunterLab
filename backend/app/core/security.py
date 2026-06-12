from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates JWT token and extracts user/tenant context.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        tenant_id: str = payload.get("tenant_id")
        user_id: str = payload.get("sub")
        if tenant_id is None or user_id is None:
            raise credentials_exception
            
        return {"user_id": user_id, "tenant_id": tenant_id}
    except JWTError:
        raise credentials_exception
