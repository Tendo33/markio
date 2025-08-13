from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware


def add_gzip_middleware(app: FastAPI):
    """
    Add gzip compression middleware

    :param app: FastAPI object
    :return:
    """
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)
