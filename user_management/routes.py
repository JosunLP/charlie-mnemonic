from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from fastapi.responses import (
    Response,
)
from fastapi.templating import Jinja2Templates

from authentication import Authentication
from classes import (
    LoginUser,
    User,
    UserCheckToken,
)
from config import STATIC, LOGIN_REQUIRED, PRODUCTION, origins
from configuration_page.middleware import set_user_as_logged_in
from simple_utils import get_root

templates = Jinja2Templates(directory=get_root(STATIC))
router = APIRouter()


# login route
@router.post(
    "/login/",
    tags=["Authentication"],
    summary="Login a user",
    description="This endpoint allows you to login a user by providing a username and password. If the login is successful, a session token and username will be set in cookies which expire after 90 days. The cookies' secure attribute is set to True, httponly is set to False, and samesite is set to 'None'. If the login fails, an HTTP 401 error will be returned.",
    response_description="Returns a success message if the user is logged in successfully, else returns an HTTPException with status code 401.",
    responses={
        200: {
            "description": "User logged in successfully",
            "content": {
                "application/json": {
                    "example": {"message": "User logged in successfully"}
                }
            },
        },
        401: {
            "description": "User login failed",
            "content": {
                "application/json": {"example": {"detail": "User login failed"}}
            },
        },
    },
)
async def login(request: Request, user: LoginUser, response: Response):
    auth = Authentication()
    session_token = auth.login(user.username, user.password)
    if session_token:
        set_login_cookies(session_token, user.username, response)
        set_user_as_logged_in(session_token, user.username, request)
        return {"message": "User logged in successfully"}
    else:
        raise HTTPException(status_code=401, detail="User login failed")


def set_login_cookies(
    session_token: str, username: str, response: Response, duration_days: int = 90
) -> None:
    expiracy_date = datetime.now(timezone.utc) + timedelta(days=duration_days)
    cookie_params = {
        "secure": PRODUCTION,
        "httponly": False,
        "samesite": "None",
        "expires": expiracy_date,
    }

    if PRODUCTION:
        cookie_params["domain"] = origins()

    response.set_cookie(key="session_token", value=session_token, **cookie_params)

    response.set_cookie(key="username", value=username, **cookie_params)


# logout route
@router.post(
    "/logout/",
    tags=["Authentication", LOGIN_REQUIRED],
    summary="Logout a user",
    description="This endpoint allows you to logout a user by providing a username and session token. If the logout is successful, the session token and username cookies will be deleted. If the logout fails, an HTTP 401 error will be returned.",
    response_description="Returns a success message if the user is logged out successfully, else returns an HTTPException with status code 401.",
    responses={
        200: {
            "description": "User logged out successfully",
            "content": {
                "application/json": {
                    "example": {"message": "User logged out successfully"}
                }
            },
        },
        401: {
            "description": "User logout failed",
            "content": {
                "application/json": {"example": {"detail": "User logout failed"}}
            },
        },
    },
)
async def logout(request: Request):
    auth = Authentication()
    success = auth.logout(request.state.user.username)
    request.cookies["session_token"] = ""
    request.cookies["username"] = ""
    if success:
        return {"message": "User logged out successfully"}
    else:
        raise HTTPException(status_code=401, detail="User logout failed")


@router.post(
    "/register/",
    tags=["Authentication"],
    summary="Register a new user",
    description="This endpoint allows you to register a new user by providing a username and password. If the registration is successful, a session token and username will be set in cookies which expire after 90 days. The cookies' secure attribute is set to True, httponly is set to False, and samesite is set to 'None'. If the registration fails, an HTTP 400 error will be returned.",
    response_description="Returns a success message if the user is registered successfully, else returns an HTTPException with status code 400.",
    responses={
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {"message": "User registered successfully"}
                }
            },
        },
        400: {
            "description": "User registration failed",
            "content": {
                "application/json": {"example": {"detail": "User registration failed"}}
            },
        },
    },
)
async def register(user: User, response: Response):
    auth = Authentication()
    session_token = auth.register(user.username, user.password, user.display_name)
    if session_token:
        set_login_cookies(session_token, user.username, response)
        return {
            "message": "User registered successfully",
            "display_name": user.display_name,
        }
    else:
        raise HTTPException(status_code=400, detail="User registration failed")


@router.post(
    "/check_token/",
    tags=["Authentication"],
    summary="Check if a token is valid",
    description="This endpoint allows you to check if a token is valid by providing a username and session token. If the token is valid, a success message will be returned. If the token is invalid, an HTTP 401 error will be returned.",
    response_description="Returns a success message if the token is valid, else returns an HTTPException with status code 401.",
    responses={
        200: {
            "description": "Token is valid",
            "content": {"application/json": {"example": {"message": "Token is valid"}}},
        },
        401: {
            "description": "Token is invalid",
            "content": {
                "application/json": {"example": {"detail": "Token is invalid"}}
            },
        },
    },
)
async def check_token(user: UserCheckToken):
    auth = Authentication()
    success = auth.check_token(user.username, user.session_token)
    if success:
        return {"message": "Token is valid"}
    else:
        raise HTTPException(status_code=401, detail="Token is invalid")
