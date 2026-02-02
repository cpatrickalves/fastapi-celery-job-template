"""
Tests for Schema Registry.

Tests the registration and validation of job schemas by job_type.
"""

from typing import Literal

import pytest
from pydantic import Field

from app.workflows.schemas.base import BaseJobSchema
from app.workflows.schemas.registry import (
    _register_schema,
    clear_registry,
    get_all_schemas,
    get_schema,
    list_schemas,
    schema_exists,
    validate_job,
)


class TestSchemaRegistration:
    """Tests for schema registration."""

    def test_register_schema(self) -> None:
        """_register_schema() should register a schema class."""

        class TestSchema(BaseJobSchema):
            job_type: Literal["test_schema"] = "test_schema"
            data: str

        _register_schema("test_schema", TestSchema)

        assert schema_exists("test_schema")

    def test_get_schema_returns_class(self) -> None:
        """get_schema() should return the registered schema class."""

        class MySchema(BaseJobSchema):
            job_type: Literal["my_schema"] = "my_schema"
            value: int

        _register_schema("my_schema", MySchema)

        schema_class = get_schema("my_schema")

        assert schema_class is MySchema

    def test_register_duplicate_raises_error(self) -> None:
        """Registering the same job_type twice should raise ValueError."""

        class FirstSchema(BaseJobSchema):
            job_type: Literal["duplicate_schema"] = "duplicate_schema"

        class SecondSchema(BaseJobSchema):
            job_type: Literal["duplicate_schema"] = "duplicate_schema"

        _register_schema("duplicate_schema", FirstSchema)

        with pytest.raises(ValueError, match="already registered"):
            _register_schema("duplicate_schema", SecondSchema)


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

        class ExistsSchema(BaseJobSchema):
            job_type: Literal["exists_schema"] = "exists_schema"

        _register_schema("exists_schema", ExistsSchema)

        assert schema_exists("exists_schema") is True


class TestSchemaListing:
    """Tests for listing schemas."""

    def test_list_schemas_empty_initially(self) -> None:
        """list_schemas() should return empty list when no schemas registered."""
        assert list_schemas() == []

    def test_list_schemas_returns_registered_types(self) -> None:
        """list_schemas() should return all registered job_types."""

        class SchemaA(BaseJobSchema):
            job_type: Literal["schema_a"] = "schema_a"

        class SchemaB(BaseJobSchema):
            job_type: Literal["schema_b"] = "schema_b"

        _register_schema("schema_a", SchemaA)
        _register_schema("schema_b", SchemaB)

        schemas = list_schemas()

        assert "schema_a" in schemas
        assert "schema_b" in schemas
        assert len(schemas) == 2

    def test_get_all_schemas_returns_dict(self) -> None:
        """get_all_schemas() should return dict mapping job_type to schema class."""

        class AllTestSchema(BaseJobSchema):
            job_type: Literal["all_test"] = "all_test"

        _register_schema("all_test", AllTestSchema)

        all_schemas = get_all_schemas()

        assert "all_test" in all_schemas
        assert all_schemas["all_test"] is AllTestSchema


class TestSchemaValidation:
    """Tests for job data validation."""

    def test_validate_job_returns_validated_instance(self) -> None:
        """validate_job() should return a validated schema instance."""

        class ValidateSchema(BaseJobSchema):
            job_type: Literal["validate_test"] = "validate_test"
            message: str = Field(..., min_length=1)

        _register_schema("validate_test", ValidateSchema)

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

        class ToClearSchema(BaseJobSchema):
            job_type: Literal["to_clear_schema"] = "to_clear_schema"

        _register_schema("to_clear_schema", ToClearSchema)

        assert schema_exists("to_clear_schema")

        clear_registry()

        assert schema_exists("to_clear_schema") is False
        assert list_schemas() == []
