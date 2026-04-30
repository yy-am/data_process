from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import AgentRuntimeConfig, TemplateIdentificationClientConfig


class RuntimeConfigRepository(ABC):
    @abstractmethod
    def get_runtime_config(self) -> AgentRuntimeConfig:
        raise NotImplementedError

    @abstractmethod
    def update_template_identification_config(
        self,
        config: TemplateIdentificationClientConfig,
    ) -> AgentRuntimeConfig:
        raise NotImplementedError

    @abstractmethod
    def update_rule_draft_config(
        self,
        config: TemplateIdentificationClientConfig,
    ) -> AgentRuntimeConfig:
        raise NotImplementedError

    @abstractmethod
    def update_image_ocr_config(
        self,
        config: TemplateIdentificationClientConfig,
    ) -> AgentRuntimeConfig:
        raise NotImplementedError


class InMemoryRuntimeConfigRepository(RuntimeConfigRepository):
    def __init__(self, runtime_config: AgentRuntimeConfig | None = None) -> None:
        self._runtime_config = runtime_config or AgentRuntimeConfig()

    def get_runtime_config(self) -> AgentRuntimeConfig:
        return self._runtime_config

    def update_template_identification_config(
        self,
        config: TemplateIdentificationClientConfig,
    ) -> AgentRuntimeConfig:
        self._runtime_config.template_identification_client = config
        return self._runtime_config

    def update_rule_draft_config(
        self,
        config: TemplateIdentificationClientConfig,
    ) -> AgentRuntimeConfig:
        self._runtime_config.rule_draft_client = config
        return self._runtime_config

    def update_image_ocr_config(
        self,
        config: TemplateIdentificationClientConfig,
    ) -> AgentRuntimeConfig:
        self._runtime_config.image_ocr_client = config
        return self._runtime_config
