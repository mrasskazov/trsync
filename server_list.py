import os

servers = [_.strip() for _ in os.environ.get('LOCATIONS').split()]
