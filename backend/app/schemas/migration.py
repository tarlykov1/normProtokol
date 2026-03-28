from typing import Any

from pydantic import BaseModel, Field


class CreateRunResponse(BaseModel):
    run_id: int
    status: str


class UsersSyncRequest(BaseModel):
    run_id: int
    source_users: list[dict[str, Any]]
    target_users: list[dict[str, Any]]


class UsersOverrideRequest(BaseModel):
    run_id: int
    source_id: str
    target_id: str


class DomainSyncRequest(BaseModel):
    run_id: int
    source_items: list[dict[str, Any]]
    target_items: list[dict[str, Any]] = Field(default_factory=list)


class TasksMigrateRequest(BaseModel):
    run_id: int
    tasks: list[dict[str, Any]]


class CommentsMigrateRequest(BaseModel):
    run_id: int
    comments: list[dict[str, Any]]


class FileRefsMigrateRequest(BaseModel):
    run_id: int
    file_refs: list[dict[str, Any]]


class VerifyCountsRequest(BaseModel):
    run_id: int
    source_counts: dict[str, int]


class ExecutePipelineRequest(BaseModel):
    run_id: int
    source_users: list[dict[str, Any]]
    target_users: list[dict[str, Any]]
    source_groups: list[dict[str, Any]] = Field(default_factory=list)
    target_groups: list[dict[str, Any]] = Field(default_factory=list)
    source_projects: list[dict[str, Any]] = Field(default_factory=list)
    target_projects: list[dict[str, Any]] = Field(default_factory=list)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    comments: list[dict[str, Any]] = Field(default_factory=list)
    file_refs: list[dict[str, Any]] = Field(default_factory=list)
