import os
from abc import ABC, abstractmethod
from typing import List

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer
)


class ChatModel(ABC):
    @abstractmethod
    def get_model(cls) -> None:
        pass

    @abstractmethod
    def generate(
        cls,
        messages: list,
        temperature: float = 0.9,
        top_p: float = 0.9,
        n: int = 1,
        stream: bool = False,
        max_tokens: int = 128,
        stop: str = "",
        **kwargs,
    ) -> None:
        pass

    @abstractmethod
    def embeddings(cls, text) -> None:
        pass


class Gorilla(ChatModel):
    model = None
    tokenizer = None 

    @classmethod
    def generate(
        cls,
        messages: list,
        temperature: float = 0.7,
        top_p: float = 0.9,
        n: int = 1,
        stream: bool = False,
        max_tokens: int = 1024,
        stop: str = "",
        **kwargs,
    ) -> List:
        message = f"""
        User: {messages[-1]["content"]}
        Assistant:
        """
        input_ids = cls.tokenizer([message]).input_ids
        output_ids = cls.model.generate(
            torch.as_tensor(input_ids).to('cuda'),
            temperature=temperature,
            top_p=top_p,
            num_return_sequences=n,
            eos_token_id=cls.tokenizer.eos_token_id,
            max_new_tokens=max_tokens,
            do_sample=kwargs.get("do_sample", True),
            **kwargs
        )
        output_ids = output_ids[0][len(input_ids[0]) :]
        return [
            cls.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        ]

    @classmethod
    def get_model(cls) -> AutoModelForCausalLM:
        if cls.model is None:
            cls.tokenizer = AutoTokenizer.from_pretrained(os.getenv("MODEL_ID", 'gorilla-llm/gorilla-falcon-7b-hf-v0'), trust_remote_code=True)
            cls.tokenizer.pad_token = cls.tokenizer.eos_token
            cls.tokenizer.pad_token_id = 11
            cls.model = AutoModelForCausalLM.from_pretrained(
                os.getenv("MODEL_ID", 'gorilla-llm/gorilla-falcon-7b-hf-v0'),
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map=os.getenv("DEVICE", "auto")
        )
        return cls.model