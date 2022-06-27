"""
Copyright (c) 2022 Mozaiku Inc. All Rights Reserved.
"""
from fastapi import Cookie, Response, status

from warehouse.db import get_date, hashpass
from warehouse.lib.payloads import CreateUser, EditUser, Login
from warehouse.lib.users.basic import User


async def create_user(payload: CreateUser, resp: Response):
    user = User(
        email=payload.email,
        password=payload.password,
        username=payload.username,
        joined_at=get_date(),  # type: ignore
        avatar_url='',
        banner_url='',
        flags=1,
        bio='',
        locale='en-US',
    )

    await user.commit()

    transmission = user.for_transmission(False)
    resp.status_code = status.HTTP_201_CREATED
    resp.set_cookie(
        'venera_authorization', user.create_token(), secure=True, httponly=True
    )

    return transmission


async def login(payload: Login, resp: Response):
    u = await User.login(
        email=payload.email,
        password=payload.password
    )

    if u is None:
        resp.status_code = status.HTTP_403_FORBIDDEN
        return {
            'err': 'Invalid email or password'
        }

    resp.set_cookie(
        'venera_authorization',
        u.create_token(),
        secure=True,
        httponly=True
    )

    return {
        'success': True
    }


async def logout(resp: Response):
    try:
        resp.delete_cookie('venera_authorization', secure=True, httponly=True)
    except:
        return {
            'success': True
        }


async def edit_user(
    payload: EditUser, venera_authorization: str = Cookie(default=None)
):
    user = User.from_authorization(token=venera_authorization)

    edited_content = {}

    if payload.username:
        edited_content['username'] = payload.username

    if payload.email:
        edited_content['email'] = payload.email

    if payload.password:
        edited_content['password'] = hashpass(payload.password)

    if payload.avatar_url:
        edited_content['avatar_url'] = payload.avatar_url

    if payload.banner_url:
        edited_content['banner_url'] = payload.banner_url

    if payload.bio:
        edited_content['bio'] = payload.bio

    user.commit_edit(**edited_content)

    return user.for_transmission(False)


async def get_user(
    username: int, resp: Response, venera_authorization: str = Cookie(default=None)
):
    User.from_authorization(token=venera_authorization)

    try:
        user = User.from_username(username=username)
    except:
        resp.status_code = status.HTTP_404_NOT_FOUND
        return {'err_code': 2, 'message': 'User does not exist'}

    return user.for_transmission()
