"""
RabbitMQ 客户端封装
"""
import json
import logging
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass

import pika
from pika.adapters.asyncio_connection import AsyncioConnection

logger = logging.getLogger(__name__)


@dataclass
class MQConfig:
    """MQ 配置"""
    url: str
    exchange: str
    command_queue: str
    result_queue: str
    progress_queue: str
    enabled: bool = True


class RabbitMQClient:
    """RabbitMQ 客户端"""

    def __init__(self, config: MQConfig):
        self.config = config
        self.connection: Optional[AsyncioConnection] = None
        self.channel = None

    def connect(self) -> bool:
        """建立连接"""
        if not self.config.enabled:
            logger.warning("RabbitMQ is disabled")
            return False

        try:
            parameters = pika.URLParameters(self.config.url)
            self.connection = AsyncioConnection(parameters)
            self.connection.add_on_open_callback(self._on_connection_open)
            self.connection.add_on_close_callback(self._on_connection_closed)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def _on_connection_open(self, unused_connection):
        """连接成功回调"""
        logger.info("RabbitMQ connection opened")
        self.connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """通道打开回调"""
        self.channel = channel
        self._setup_exchanges_and_queues()

    def _on_connection_closed(self, connection, reason):
        """连接关闭回调"""
        logger.warning(f"RabbitMQ connection closed: {reason}")
        self.channel = None

    def _setup_exchanges_and_queues(self):
        """设置交换机和队列"""
        # 声明交换机
        self.channel.exchange_declare(
            exchange=self.config.exchange,
            exchange_type='topic',
            durable=True
        )

        # 声明并绑定队列
        queues = [
            (self.config.command_queue, 'analysis.command'),
            (self.config.result_queue, 'analysis.result'),
            (self.config.progress_queue, 'analysis.progress'),
        ]

        for queue_name, routing_key in queues:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.queue_bind(
                queue=queue_name,
                exchange=self.config.exchange,
                routing_key=routing_key
            )
            logger.debug(f"Queue {queue_name} declared and bound to {routing_key}")

    def publish_command(self, task_id: int, issue_id: int, payload: Dict[str, Any]):
        """发布分析命令"""
        message = {
            "task_id": task_id,
            "issue_id": issue_id,
            "payload": payload
        }
        self._publish('analysis.command', message, persistent=True)
        logger.info(f"Command published for task {task_id}")

    def publish_result(self, task_id: int, issue_id: int, success: bool,
                       summary: str = "", result: Dict = None, error: str = ""):
        """发布分析结果"""
        message = {
            "task_id": task_id,
            "issue_id": issue_id,
            "success": success,
            "summary": summary,
            "result": result or {},
            "error": error
        }
        self._publish('analysis.result', message, persistent=True)
        logger.info(f"Result published for task {task_id}, success={success}")

    def publish_progress(self, task_id: int, progress: str, current_step: str):
        """发布进度更新"""
        message = {
            "task_id": task_id,
            "progress": progress,
            "current_step": current_step
        }
        self._publish('analysis.progress', message, persistent=False)
        logger.debug(f"Progress published for task {task_id}: {current_step}")

    def _publish(self, routing_key: str, message: Dict, persistent: bool = True):
        """发布消息"""
        if not self.channel:
            logger.error("Channel not available, cannot publish")
            return

        properties = pika.BasicProperties(
            delivery_mode=2 if persistent else 1,
            content_type='application/json'
        )

        self.channel.basic_publish(
            exchange=self.config.exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=properties
        )

    def consume_commands(self, handler: Callable[[Dict], None]):
        """消费命令消息"""
        if not self.channel:
            logger.error("Channel not available, cannot consume")
            return

        def on_message(ch, method, properties, body):
            try:
                message = json.loads(body)
                logger.info(f"Received command message: {message.get('task_id')}")
                handler(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Failed to handle command message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_consume(
            queue=self.config.command_queue,
            on_message_callback=on_message,
            auto_ack=False
        )
        logger.info(f"Started consuming commands from {self.config.command_queue}")

    def close(self):
        """关闭连接"""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()
        logger.info("RabbitMQ connection closed")
