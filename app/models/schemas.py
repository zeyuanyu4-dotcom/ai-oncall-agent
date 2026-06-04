"""
Request and Response Models
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IssueAnalysisRequest(BaseModel):
    """问题分析请求"""
    issue_id: int = Field(..., description="问题ID")
    issue_no: str = Field(..., description="问题编号")
    title: str = Field(..., description="问题标题")
    description: Optional[str] = Field(default="", description="问题描述")
    error_message: Optional[str] = Field(default="", description="错误信息")
    log_excerpt: Optional[str] = Field(default="", description="日志片段")
    environment: Optional[str] = Field(default="", description="环境")
    project_name: Optional[str] = Field(default="", description="项目名称")
    service_name: Optional[str] = Field(default="", description="服务名称")
    impact_scope: Optional[str] = Field(default="", description="影响范围")


class AgentAnalysisRequest(BaseModel):
    """Agent 深度分析请求"""
    task_id: int = Field(default=0, description="任务ID")
    issue_id: int = Field(..., description="问题ID")
    issue_no: str = Field(..., description="问题编号")
    title: str = Field(..., description="问题标题")
    description: Optional[str] = Field(default="", description="问题描述")
    error_message: Optional[str] = Field(default="", description="错误信息")
    log_excerpt: Optional[str] = Field(default="", description="日志片段")
    environment: Optional[str] = Field(default="", description="环境")
    project_id: int = Field(default=0, description="项目ID")
    project_name: Optional[str] = Field(default="", description="项目名称")
    service_name: Optional[str] = Field(default="", description="服务名称")
    impact_scope: Optional[str] = Field(default="", description="影响范围")


class KeyInfo(BaseModel):
    """关键信息"""
    error_code: Optional[str] = Field(default=None, description="错误码")
    error_type: Optional[str] = Field(default=None, description="错误类型")
    affected_endpoint: Optional[str] = Field(default=None, description="受影响的接口")
    error_time: Optional[str] = Field(default=None, description="错误发生时间")
    trace_id: Optional[str] = Field(default=None, description="Trace ID")
    additional_info: Optional[Dict[str, Any]] = Field(default=None, description="其他关键信息")


class AnalysisResult(BaseModel):
    """分析结果"""
    summary: str = Field(..., description="问题摘要")
    issue_type: str = Field(..., description="问题类型")
    environment: Optional[str] = Field(default=None, description="识别的环境")
    related_services: List[str] = Field(default_factory=list, description="关联服务")
    priority: str = Field(..., description="建议优先级")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    key_info: Optional[KeyInfo] = Field(default=None, description="关键信息")
    missing_info: List[str] = Field(default_factory=list, description="缺失信息")
    suggestions: List[str] = Field(default_factory=list, description="排查建议")


class AnalysisResponse(BaseModel):
    """分析响应"""
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[AnalysisResult] = Field(default=None, description="分析结果")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="ok")
    version: str
    llm_provider: str
