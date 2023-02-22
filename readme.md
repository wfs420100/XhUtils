# XhUtils

```shell
python setup.py bdist_wheel --universal
twine upload dist/*  # pip install twine

pip install xh_utils -i https://www.pypi.org/simple/
```

1. 彩色日志

## 示例

### 1.彩色日志

```python
from xh_utils.logger import Logger as logger

logger.init_logger()
# logger.init_logger(log_pathdir="./log/",is_split_logfile=True) # 日志同步写入文件，并按天进行文件分割写入
logger.debug("debug")
logger.info("info")
logger.warning("warning")
logger.error("error")
```

