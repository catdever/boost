from termcolor import colored

import functools
import asyncio
from aiohttp import web
from ..clients import clients
from ..models import models
from ..cli import set_logger

STATUS = {
    200: lambda x: web.json_response(x, status=200),
    500: lambda x: web.json_response(dict(error=str(x), type=type(x).__name__), status=500)
}


class RankProxy:
    def __init__(self, args):
        self.args = args

    @property
    def status(self):
        return dict(res='Chillin')

    def create_site(self):
        logger = set_logger(self.__class__.__name__)
        # query_id = itertools.count()
        # train_id = itertools.count()
        loop = asyncio.get_event_loop()
        model = getattr(models, self.args.model)(self.args)
        client = getattr(clients, self.args.client)(self.args)

        async def route_handler(f):
            @functools.wraps(f)
            def decorator(*args, **kwargs):
                try:
                    logger.info('new %s request' % f.__name__)
                    return STATUS[200](f(*args, **kwargs))
                except Exception as ex:
                    logger.error('Error on %s request' % f.__name__, exc_info=True)
                    return STATUS[500](ex)
            return decorator

        @route_handler
        async def status():
            return self.status

        @route_handler
        async def query(request):
            response, q, candidates = await client.query(request)
            ranks = model.rank(q, candidates)
            return client.reorder(response, ranks)

        @route_handler
        async def train(request):
            return model.train(request)

        async def main():
            app = web.Application()
            app.add_routes([
                web.get('/status', status),
                web.get('/query', query),
                web.post('/train', train),
            ])
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.args.proxy_host, self.args.proxy_port)
            await site.start()

            logger.info('proxy forwarding %s:%d to %s:%d' % (
                self.args.proxy_host, self.args.proxy_port,
                self.args.server_host, self.args.server_port))

        loop.run_until_complete(main())
        loop.run_forever()

    def run(self):
        self.create_site()
