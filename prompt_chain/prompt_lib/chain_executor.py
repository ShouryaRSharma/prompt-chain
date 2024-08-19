import json
from typing import Any, cast

from pydantic import ValidationError

from prompt_chain.prompt_lib.db_manager import DatabaseManager
from prompt_chain.prompt_lib.models import ChainConfig, DynamicModel, PromptModel
from prompt_chain.prompt_lib.web_client import WebClient


class ChainExecutor:
    def __init__(
        self, db_manager: DatabaseManager, web_client: WebClient, openai_api_key: str | None
    ) -> None:
        self.db_manager = db_manager
        self.web_client = web_client
        self._openai_api_key = openai_api_key

    def execute_chain(
        self, chain_config: ChainConfig, initial_input: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a chain of AI models as defined in the chain_config.

        Args:
            chain_config (ChainConfig): Configuration defining the chain of models to execute.
            initial_input (dict[str, Any]): Initial input data for the chain.

        Returns:
            dict[str, Any]: The final output of the chain after all steps have been executed.

        Raises:
            ValueError: If a model in the chain is not found.
        """
        current_output = initial_input
        step_outputs: list[dict[str, Any]] = []

        for i, step in enumerate(chain_config.steps):
            model = self.db_manager.get_prompt_model(step.name)
            if not model:
                raise ValueError(f"Model not found: {step.name}")

            step_input = self._map_input(current_output, step.input_mapping, step_outputs)
            validated_input = self._validate_input(model, step_input)
            step_output = self._execute_step(model, validated_input)
            validated_output = self._validate_output(model, step_output)
            step_outputs.append(validated_output)
            current_output = {**current_output, **validated_output}

        return self._map_input(current_output, chain_config.final_output_mapping, step_outputs)

    def _map_input(
        self, data: dict[str, Any], mapping: dict[str, str], step_outputs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Map input data according to the provided mapping configuration.

        Args:
            data (dict[str, Any]): Current data available for mapping.
            mapping (dict[str, str]): Mapping configuration.
            step_outputs (list[dict[str, Any]]): Outputs from previous steps in the chain.

        Returns:
            dict[str, Any]: Mapped input data for the next step in the chain.

        Raises:
            ValueError: If an invalid mapping is encountered.
        """
        result: dict[str, Any] = {}
        for key, value in mapping.items():
            if value.startswith("initial_input."):
                result[key] = data[value.split(".", 1)[1]]
            elif value.startswith("previous_step."):
                result[key] = step_outputs[-1][value.split(".", 1)[1]]
            elif value.startswith("step_"):
                step_parts = value.split(".", 1)
                if len(step_parts) != 2:
                    raise ValueError(f"Invalid mapping: {value}")
                step_index_str, output_key = step_parts
                step_index = int(step_index_str.split("_")[1])
                result[key] = step_outputs[step_index][output_key]
            else:
                raise ValueError(f"Invalid mapping: {value}")
        return result

    def _validate_input(self, model: PromptModel, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate input data against the model's input schema.

        Args:
            model (PromptModel): The model whose input schema will be used for validation.
            input_data (dict[str, Any]): Input data to be validated.

        Returns:
            dict[str, Any]: Validated input data.

        Raises:
            ValueError: If input validation fails.
        """
        input_model = DynamicModel.create_from_schema(
            model.user_prompt, model_name=f"{model.name}_Input"
        )
        try:
            validated_data = input_model(**input_data)
            return validated_data.model_dump()
        except ValidationError as e:
            raise ValueError(f"Input validation failed for model {model.name}: {str(e)}")

    def _validate_output(self, model: PromptModel, output_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate output data against the model's output schema.

        Args:
            model (PromptModel): The model whose output schema will be used for validation.
            output_data (dict[str, Any]): Output data to be validated.

        Returns:
            dict[str, Any]: Validated output data.

        Raises:
            ValueError: If output validation fails.
        """
        output_model = DynamicModel.create_from_schema(
            model.response, model_name=f"{model.name}_Output"
        )
        try:
            validated_data = output_model(**output_data)
            return validated_data.model_dump()
        except ValidationError as e:
            raise ValueError(f"Output validation failed for model {model.name}: {str(e)}")

    def _execute_step(self, model: PromptModel, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single step in the chain by calling the OpenAI API.

        Args:
            model (PromptModel): The model to be executed.
            input_data (dict[str, Any]): Validated input data for the model.

        Returns:
            dict[str, Any]: The output from the OpenAI API call.
        """
        headers = {
            "Authorization": f"Bearer {self._openai_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": model.system_prompt},
                {"role": "user", "content": json.dumps(input_data)},
            ],
        }

        response = self.web_client.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=data
        )

        return cast(dict[str, Any], json.loads(response["choices"][0]["message"]["content"]))
