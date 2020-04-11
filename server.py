from waitress import serve
#from redis_app import server
from dbc_app import server
serve(server)
