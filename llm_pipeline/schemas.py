from pydantic import BaseModel


class QAGroup(BaseModel):
    question: str
    client_message_indices: list[int]
    advisor_message_indices: list[int]
    tags: list[str]
    reasoning: str
    answer: str


class ExtractionResult(BaseModel):
    qa_groups: list[QAGroup]
    skipped_indices: list[int] = []


class QAGroupFull(BaseModel):
    question: str
    tags: list[str]
    reasoning: str
    answer: str
    advisor_message_indices: list[int]


class ProcessedChat(BaseModel):
    client: str
    thread_subject: str
    source_file: str
    filter_stats: dict
    qa_groups: list[QAGroupFull]
