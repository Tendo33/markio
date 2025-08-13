from pydantic import BaseModel, Field, field_validator, model_validator


class BaseParserConfig(BaseModel):
    # resource_path: str = Field(
    #     default="",
    #     description="The path to the file to be parsed or URL.",
    # )
    save_parsed_content: bool = Field(
        default=False,
        description="If set to true, the parsed content will be saved to a file. Images will be automatically extracted and saved when this is true.",
    )
    output_dir: str = Field(
        default="outputs",
        description="The directory where the parsed content will be saved.",
    )

    @field_validator("save_parsed_content", mode="before")
    @classmethod
    def validate_save_parsed_content(cls, v):
        """Ensure save_parsed_content is a boolean value"""
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ("true", "1", "yes", "on"):
                return True
            elif v_lower in ("false", "0", "no", "off"):
                return False
            else:
                raise ValueError(f"Invalid boolean value: {v}")
        return bool(v)

    @model_validator(mode="before")
    def check_output_dir(cls, values):
        save_parsed_content = values.get("save_parsed_content")
        output_dir = values.get("output_dir")

        if save_parsed_content and not output_dir:
            raise ValueError(
                "output_dir must be provided when save_parsed_content is True."
            )

        return values
