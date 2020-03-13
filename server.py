from waitress import serve
from redis_app import server

serve(server)
