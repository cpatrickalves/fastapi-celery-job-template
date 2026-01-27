"""
Tests for Schema Registry.

Tests the registration and validation of job schemas by job_type.
"""

from typing import Literal

import pytest
from pydantic import Field

from app.workflows.schemas.base import BaseJobSchema
from app.workflows.schemas.registry import (
    clear_registry,
    get_all_schemas,
    get_schema,
    list_schemas,
    register_schema,
    schema_exists,
    validate_job,
)


class TestSchemaRegistration:
    """Tests for schema registration."""

    def test_register_schema_with_decorator(self) -> None:
        """@register_schema decorator should register a schema class."""

        @register_schema("test_schema")
        class TestSchema(BaseJobSchema):
            job_type: Literal["test_schema"] = "test_schema"
            data: str

        assert schema_exists("test_schema")

    def test_get_schema_returns_class(self) -> None:
        """get_schema() should return the registered schema class."""

        @register_schema("my_schema")
        class MySchema(BaseJobSchema):
            job_type: Literal["my_schema"] = "my_schema"
            value: int

        schema_class = get_schema("my_schema")

        assert schema_class is MySchema

    def test_register_duplicate_raises_error(self) -> None:
        """Registering the same job_type twice should raise ValueError."""

        @register_schema("duplicate_schema")
        class FirstSchema(BaseJobSchema):
            job_type: Literal["duplicate_schema"] = "duplicate_schema"

        with pytest.raises(ValueError, match="already registered"):

            @register_schema("duplicate_schema")
            class SecondSchema(BaseJobSchema):
                job_type: Literal["duplicate_schema"] = "duplicate_schema"


class TestSchemaRetrieval:
    """Tests for schema retrieval."""

    def test_get_schema_unknown_raises_keyerror(self) -> None:
        """get_schema() with unknown job_type should raise KeyError."""
        with pytest.raises(KeyError, match="No schema registered"):
            get_schema("unknown_schema")

    def test_schema_exists_returns_false_for_unknown(self) -> None:
        """schema_exists() should return False for unregistered job_type."""
        assert schema_exists("nonexistent") is False

    def test_schema_exists_returns_true_for_registered(self) -> None:
        """schema_exists() should return True for registered job_type."""

        @register_schema("exists_schema")
        class ExistsSchema(BaseJobSchema):
            job_type: Literal["exists_schema"] = "exists_schema"

        assert schema_exists("exists_schema") is True


class TestSchemaListing:
    """Tests for listing schemas."""

    def test_list_schemas_empty_initially(self) -> None:
        """list_schemas() should return empty list when no schemas registered."""
        assert list_schemas() == []

    def test_list_schemas_returns_registered_types(self) -> None:
        """list_schemas() should return all registered job_types."""

        @register_schema("schema_a")
        class SchemaA(BaseJobSchema):
            job_type: Literal["schema_a"] = "schema_a"

        @register_schema("schema_b")
        class SchemaB(BaseJobSchema):
            job_type: Literal["schema_b"] = "schema_b"

        schemas = list_schemas()

        assert "schema_a" in schemas
        assert "schema_b" in schemas
        assert len(schemas) == 2

    def test_get_all_schemas_returns_dict(self) -> None:
        """get_all_schemas() should return dict mapping job_type to schema class."""

        @register_schema("all_test")
        class AllTestSchema(BaseJobSchema):
            job_type: Literal["all_test"] = "all_test"

        all_schemas = get_all_schemas()

        assert "all_test" in all_schemas
        assert all_schemas["all_test"] is AllTestSchema


class TestSchemaValidation:
    """Tests for job data validation."""

    def test_validate_job_returns_validated_instance(self) -> None:
        """validate_job() should return a validated schema instance."""

        @register_schema("validate_test")
        class ValidateSchema(BaseJobSchema):
            job_type: Literal["validate_test"] = "validate_test"
            message: str = Field(..., min_length=1)

        job_data = {"job_type": "validate_test", "message": "Hello"}

        validated = validate_job(job_data)

        assert isinstance(validated, ValidateSchema)
        assert validated.message == "Hello"

    def test_validate_job_missing_job_type_raises_error(self) -> None:
        """validate_job() should raise ValueError if job_type is missing."""
        with pytest.raises(ValueError, match="must contain 'job_type'"):
            validate_job({"message": "no type"})

    def test_validate_job_unknown_type_raises_keyerror(self) -> None:
        """validate_job() should raise KeyError for unknown job_type."""
        with pytest.raises(KeyError, match="No schema registered"):
            validate_job({"job_type": "unknown"})


class TestRegistryClear:
    """Tests for registry clearing."""

    def test_clear_registry_removes_all_schemas(self) -> None:
        """clear_registry() should remove all registered schemas."""

        @register_schema("to_clear_schema")
        class ToClearSchema(BaseJobSchema):
            job_type: Literal["to_clear_schema"] = "to_clear_schema"

        assert schema_exists("to_clear_schema")

        clear_registry()

        assert schema_exists("to_clear_schema") is False
        assert list_schemas() == []
