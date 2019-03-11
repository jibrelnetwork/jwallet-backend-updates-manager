import logging
import re

from aiohttp import web


logger = logging.getLogger(__name__)


def check_request(request, entries):
    for pattern in entries:
        if request.method == pattern['method'] and \
                re.match(pattern['path'], request.path):
            return True

    return False


def TokenAuthMiddleware(secret, _list=tuple()):
    async def factory(app, handler):
        async def middleware_handler(request):
            try:
                if not check_request(request, _list):
                    return await handler(request)

                # check auth header
                if 'Authorization' not in request.headers:
                    logger.info('Invalid authorization header')
                    raise web.HTTPForbidden(
                        reason='Invalid authorization header',
                    )

                try:
                    scheme, token = request.headers.get(
                        'Authorization'
                    ).strip().split(' ')
                except ValueError:
                    logger.info('Invalid authorization header')
                    raise web.HTTPForbidden(
                        reason='Invalid authorization header',
                    )

                if not 'Token' == scheme:
                    logger.info('Invalid token scheme')
                    raise web.HTTPForbidden(
                        reason='Invalid token scheme',
                    )

                if not token:
                    logger.info('Missing authorization token')
                    raise web.HTTPUnauthorized(
                        reason='Missing authorization token',
                    )

                if not token == secret:
                    logger.info('Invalid token.')
                    raise web.HTTPForbidden(
                        reason="Invalid token.",
                    )

                # return response
                response = await handler(request)
                return response
            except web.HTTPException:
                raise
        return middleware_handler
    return factory
