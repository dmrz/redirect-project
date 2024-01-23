import os

import multiprocessing

_host = os.getenv("REDIRECT_SERVER_HOST", "0.0.0.0")
_port = os.getenv("REDIRECT_SERVER_PORT", 8080)

bind = f"{_host}:{_port}"
workers = multiprocessing.cpu_count()
worker_class = "aiohttp.GunicornWebWorker"
accesslog = "-"
access_log_format = '%a %t "%r" %s %D μs %b "%{Referer}i" "%{User-Agent}i" "%{X-Redirect-Pool-ID}i" "%{Location}o"'
