# XhUtils

```shell
python setup.py bdist_wheel --universal
twine upload dist/*
```

1. 彩色日志

## 示例

### 1.彩色日志

```python
from xh_utils.logger import Logger as logger

logger.init_logger()
logger.debug("debug")
logger.info("info")
logger.warning("warning")
logger.error("error")
```

