"""
api 包初始化：统一将项目根目录和 scripts/ 插入 sys.path，
所有 router 模块导入时会自动完成路径设置，无需重复代码。
"""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
for _p in [str(_ROOT), str(_SCRIPTS)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
