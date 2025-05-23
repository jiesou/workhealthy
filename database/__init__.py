from .models import create_tables, get_db, Base, engine
from . import crud

# 初始化数据库
create_tables() 