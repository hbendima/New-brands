import os
from dotenv import load_dotenv

load_dotenv()

print('DB_USER:', os.getenv('DB_USER'))
print('DB_PASS:', os.getenv('DB_PASS'))
print('DB_NAME:', os.getenv('DB_NAME'))
print('DB_HOST:', os.getenv('DB_HOST'))
print('DB_PORT:', os.getenv('DB_PORT'))