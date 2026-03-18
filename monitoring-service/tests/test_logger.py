import pytest
import logging
from src.middleware.logger import log_requests, log_exceptions


def test_logger_imports():
    """测试日志中间件导入"""
    assert log_requests is not None
    assert log_exceptions is not None


def test_logger_initialization():
    """测试日志记录器初始化"""
    import src.middleware.logger
    assert src.middleware.logger.logger is not None
    assert isinstance(src.middleware.logger.logger, logging.Logger)
