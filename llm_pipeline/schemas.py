from pydantic import BaseModel


class QAGroup(BaseModel):
    question: str
    client_message_indices: list[int]
    advisor_message_indices: list[int]
    tags: list[str]


class ExtractionResult(BaseModel):
    qa_groups: list[QAGroup]
    skipped_indices: list[int]


class QAGroupFull(BaseModel):
    question: str
    tags: list[str]
    client_messages: list[str]
    advisor_messages: list[str]


class ProcessedChat(BaseModel):
    client: str
    thread_subject: str
    source_file: str
    filter_stats: dict
    qa_groups: list[QAGroupFull]
