"""Pydantic model for qcsetup configuration in QCTSS Client SDK.
(`mod:`qctss_client.models.configuration`)"""

from typing import (
    Annotated,
    Generic,
    Iterator,
    Literal,
    Optional,
    TypeVar,
    Union,
    TypedDict,
    Any,
)
from pathlib import Path
from datetime import datetime
from abc import abstractmethod
import warnings
import json
import html
from urllib.parse import ParseResult, urlparse, parse_qsl
from pydantic import ConfigDict, Field, TypeAdapter


from .base import BaseModel
from ..exceptions import QCSetupConfigNothingToSaveWarning

ConfigurationCategory = Literal[
    "quantum-machine", "qblox", "quantaser", "keysight", "not-specified"
]
"""Configuration category literal type

Possible values are:

- `quantum-machine <https://www.quantum-machines.co/>`_ 
- `qblox <https://qblox.com/>`_
- `quantaser <https://www.quantaser.com>`_
- `keysight <https://www.keysight.com>`_
- `not-specified`

"""


def esc(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        value = value.strftime("%Y-%m-%d %H:%M:%S")
    return html.escape(str(value))


def table(cells: dict[str, Any]) -> str:
    head = "".join(f"<th>{k}</th>" for k in cells)
    body = "".join(f"<td>{esc(v)}</td>" for v in cells.values())
    return (
        '<table style="border-collapse: collapse; text-align: center; '
        'margin-top: 10px;">'
        f"<thead><tr>{head}</tr></thead><tbody><tr>{body}</tr></tbody></table>"
    )


class QuantumMachine(BaseModel):
    """Quantum machine configuration details"""

    state: dict = Field(description="state.json")
    wiring: dict = Field(description="wiring.json")


class Qblox(BaseModel):
    """Qblox configuration details"""

    state: dict = Field(description="state.json")
    hardware: dict = Field(description="hardware.json")


class General(BaseModel):
    """General configuration details"""

    config: dict = Field(description="config.json")


C = TypeVar("C", QuantumMachine, Qblox, General)
"""Type variable for configuration data models"""


class ConfigurationBase(BaseModel, Generic[C]):
    """QC setup configuration data"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Configuration ID")
    """The configuration ID on QC-Test Space."""
    name: str = Field(description="Configuration name")
    """The configuration name on QC-Test Space."""
    description: Optional[str] = Field(description="Configuration description")
    """The configuration description on QC-Test Space."""

    author_id: int = Field(description="User identifier", alias="user_id")
    """The author user identifier on QC-Test Space.
    Convert from backend variable name 'user_id'."""
    author_name: str = Field(description="Author name")
    """The author name on QC-Test Space."""
    qcsetup_id: int = Field(description="QC setup identifier", alias="qcsetup")
    """The QC setup identifier on QC-Test Space.
    Convert from backend variable name 'qcsetup'."""
    qcsetup_name: str = Field(description="QC setup name")
    """The QC setup name on QC-Test Space."""
    qpu_id: int = Field(description="QPU identifier", alias="qpu")
    """The QPU identifier on QC-Test Space.
    Convert from backend variable name 'qpu'."""
    qpu_name: str = Field(description="QPU name", alias="qpu_chip_id")
    """The QPU chip identifier on QC-Test Space.
    Convert from backend variable name 'qpu_chip_id'"""
    machine_id: int = Field(description="Machine identifier", alias="machine")
    """The machine identifier on QC-Test Space.
    Convert from backend variable name 'machine'."""
    machine_name: str = Field(description="Machine name")
    """The machine name on QC-Test Space."""

    created_at: Optional[datetime] = Field(
        default=None, description="Configuration creation timestamp"
    )
    """The configuration creation timestamp on QC-Test Space."""
    updated_at: Optional[datetime] = Field(
        default=None, description="Configuration last update timestamp"
    )
    """The configuration last update timestamp on QC-Test Space."""

    configuration: Optional[C] = Field(description="Configuration details")
    """The configuration details on QC-Test Space.
    Convert from backend variable name 'configuration'."""

    @abstractmethod
    def save(self, save_dir: Path | str) -> Path:
        """Save the configuration details to the specified directory.

        Args:
            save_dir (Path | str):
                The directory where the configuration JSON files will be saved.

        Returns:
            Path: The directory where the configuration JSON files were saved.
        """
        pass

    def _repr_pretty_(self, p: Any, cycle: bool) -> None:
        """Render a compact multiline representation in IPython/Jupyter."""
        if cycle:
            p.text(f"{self.__class__.__name__}(...)")
            return

        fields = self.model_dump(
            exclude={"configuration", "author_id", "machine_id"}, exclude_none=True
        )
        p.begin_group(2, f"{self.__class__.__name__}(")
        for index, (name, value) in enumerate(fields.items()):
            if index:
                p.text(",")
                p.breakable()
            p.text(f"{name}=")
            p.pretty(value)
        p.text(",")
        p.breakable()
        p.text("configuration={...}")
        p.end_group(2, ")")

    def __repr__(self) -> str:
        """Return a string representation of the configuration object."""
        fields = self.model_dump(
            exclude={"configuration", "author_id", "machine_id"}, exclude_none=True
        )
        field_str = ", ".join(f"{name}={value!r}" for name, value in fields.items())
        if "configuration" not in fields:
            field_str += ", configuration={...}"
        return f"{self.__class__.__name__}({field_str})"

    def _repr_html_(self) -> str:
        """Return an HTML representation of the configuration object
        for IPython/Jupyter."""

        files = ", ".join(
            f"<code>{k}.json</code>"
            for k in (self.configuration.model_fields_set if self.configuration else ())
        )
        files_note = (
            f"Include following configuration files: <br/>{files}"
            "<br/> which can be exported by classmethod"
            '<code>.save("/path/to/save/directory")</code>.'
            if files
            else "No configuration files available."
        )
        description = esc(self.description).strip()

        return (
            f"<div><p><strong>{self.__class__.__name__}</strong> id={self.id}, "
            f"qcsetup_id={self.qcsetup_id}, qpu_id={self.qpu_id}</p>"
            + table(
                {
                    "Configuration Name": self.name,
                    "QC Setup": self.qcsetup_name,
                    "QPU": self.qpu_name,
                }
            )
            + f"<div style='margin-top: 10px;'>{files_note}</div>"
            + table(
                {
                    "Author": self.author_name,
                    "Machine": self.machine_name,
                    "Created At": self.created_at,
                    "Updated At": self.updated_at,
                }
            )
            + (
                "<div style='margin-top: 10px;'><p><strong>Description</strong></p>"
                f"<p>{description}</p></div>"
                if description
                else ""
            )
            + "</div>"
        )

    def save_other_info(
        self, save_dir: Path | str, name_of_other_info: str = "_config_info.json"
    ) -> Path:
        """Save additional configuration information to a JSON file.

        Args:
            save_dir (Path | str):
                The directory where the additional information JSON file will be saved.
            name_of_other_info (str, optional):
                The filename for the additional information JSON file.
                Defaults to `"_config_info.json"`.

        Returns:
            The directory where the additional information JSON file was saved.
        """

        if isinstance(save_dir, str):
            save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        with (save_dir / name_of_other_info).open("w") as f:
            json.dump(
                self.model_dump(
                    mode="json",
                    exclude={"configuration", "author_id", "machine_id"},
                    exclude_none=True,
                ),
                f,
                indent=4,
            )
        return save_dir


class QuantumMachineConfiguration(ConfigurationBase[QuantumMachine]):
    """The configuration for a Quantum Machine device."""

    category: Literal["quantum-machine"]
    """The category of the configuration, 
    which is `"quantum-machine" <https://www.quantum-machines.co/>`_  
    for Quantum Machine devices."""

    def get_state(self) -> dict:
        """Retrieve the state configuration as a dictionary."""
        return self.configuration.state if self.configuration else {}

    def get_wiring(self) -> dict:
        """Retrieve the wiring configuration as a dictionary."""
        return self.configuration.wiring if self.configuration else {}

    def save(
        self,
        save_dir: Path | str,
        name_of_state: str = "state.json",
        name_of_wiring: str = "wiring.json",
        name_of_other_info: str = "_config_info.json",
    ) -> Path:
        """Save the state, wiring for the Quantum Machine devices,
        and additional configuration information to the specified directory.

        Args:
            save_dir (Path | str):
                The directory where the state and wiring JSON files will be saved.
            name_of_state (str, optional):
                The filename for the state JSON file. Defaults to `"state.json"`.
            name_of_wiring (str, optional):
                The filename for the wiring JSON file. Defaults to `"wiring.json"`.
            name_of_other_info (str, optional):
                The filename for the additional configuration information JSON file.
                Defaults to `"_config_info.json"`.

        Returns:
            The directory where the state, wiring for Quantum Machine devices,
            and additional configuration JSON files were saved.
        """
        save_dir = self.save_other_info(save_dir, name_of_other_info=name_of_other_info)
        if not self.configuration:
            warnings.warn(
                "No configuration available to save.", QCSetupConfigNothingToSaveWarning
            )
            return save_dir

        with (save_dir / name_of_state).open("w") as f:
            json.dump(self.configuration.state, f, indent=4)
        with (save_dir / name_of_wiring).open("w") as f:
            json.dump(self.configuration.wiring, f, indent=4)

        return save_dir


class QbloxConfiguration(ConfigurationBase[Qblox]):
    """The configuration for a Qblox device."""

    category: Literal["qblox"]
    """The category of the configuration, 
    which is `"qblox" <https://www.qblox.com/>`_  
    for Qblox devices."""

    def get_state(self) -> dict:
        """Retrieve the state configuration as a dictionary."""
        return self.configuration.state if self.configuration else {}

    def get_hardware(self) -> dict:
        """Retrieve the hardware configuration as a dictionary."""
        return self.configuration.hardware if self.configuration else {}

    def save(
        self,
        save_dir: Path | str,
        name_of_state: str = "state.json",
        name_of_hardware: str = "hw.json",
        name_of_other_info: str = "_config_info.json",
    ) -> Path:
        """Save the state, hardware for the Qblox device,
        and additional configuration information to the specified directory.

        Args:
            save_dir (Path | str):
                The directory where the state and hardware JSON files will be saved.
            name_of_state (str, optional):
                The filename for the state JSON file. Defaults to `"state.json"`.
            name_of_hardware (str, optional):
                The filename for the hardware JSON file. Defaults to `"hw.json"`.
            name_of_other_info (str, optional):
                The filename for the additional configuration information JSON file.
                Defaults to `"_config_info.json"`.

        Returns:
            The directory where the state, hardware for the Qblox device,
            and additional configuration JSON files were saved.
        """
        save_dir = self.save_other_info(save_dir, name_of_other_info=name_of_other_info)
        if not self.configuration:
            warnings.warn(
                "No configuration available to save.", QCSetupConfigNothingToSaveWarning
            )
            return save_dir

        with (save_dir / name_of_state).open("w") as f:
            json.dump(self.configuration.state, f, indent=4)
        with (save_dir / name_of_hardware).open("w") as f:
            json.dump(self.configuration.hardware, f, indent=4)

        return save_dir


class GeneralConfiguration(ConfigurationBase[General]):
    """The configuration for general settings."""

    category: Literal["quantaser", "keysight", "not-specified"]
    """The category of the configuration for other general settings."""

    def get_config(self) -> dict:
        """Retrieve the general configuration as a dictionary."""
        return self.configuration.config if self.configuration else {}

    def save(
        self,
        save_dir: Path | str,
        name_of_config: str = "config.json",
        name_of_other_info: str = "_config_info.json",
    ) -> Path:
        """Save the general configuration and
        additional configuration information to the specified directory.

        Args:
            save_dir (Path | str):
                The directory where the general configuration JSON file will be saved.
            name_of_config (str, optional):
                The filename for the general configuration JSON file.
                Defaults to `"config.json"`.
            name_of_other_info (str, optional):
                The filename for the additional configuration information JSON file.
                Defaults to `"_config_info.json"`.

        Returns:
            The directory where the general configuration and
            additional configuration JSON files were saved.
        """

        save_dir = self.save_other_info(save_dir, name_of_other_info=name_of_other_info)
        if not self.configuration:
            warnings.warn(
                "No configuration available to save.", QCSetupConfigNothingToSaveWarning
            )
            return save_dir

        with (save_dir / name_of_config).open("w") as f:
            json.dump(self.configuration.config, f, indent=4)

        return save_dir


Configuration = Annotated[
    Union[QuantumMachineConfiguration, QbloxConfiguration, GeneralConfiguration],
    Field(discriminator="category"),
]
"""The type representing the union of all possible configuration categories."""

ConfigurationAdapter: TypeAdapter[Configuration] = TypeAdapter(Configuration)
"""Type adapter for the Configuration union.

Examples:
    How to use the ConfigurationAdapter to validate and parse configuration data.

    >>> from qctss_client import Configuration, ConfigurationAdapter
    >>> config_data = {
    ...     "category": "quantum-machine",
    ...     "qcsetup_name": "example_setup",
    ...     "qpu": 1,
    ...     "qpu_chip_id": "chip_123",
    ...     "machine": 2,
    ...     "machine_name": "machine_abc",
    ...     "configuration": {
    ...         "state": {},
    ...         "wiring": {}
    ...     }
    ... }
    >>> qm_config = ConfigurationAdapter.validate_python(config_data)

    With `match` statement:

    >>> match qm_config:
    ...     case QuantumMachineConfiguration():
    ...         state = qm_config.get_state()
    ...         wiring = qm_config.get_wiring()
"""
# Well, who will actually use "match" statements in Python?
# This example made by Claude Opus 5.5 Medium


class PublicConfigResponse(TypedDict):
    """TypedDict representing the public configuration response from
    `/api/public-config/by-qcsetup` or `/api/public-config/by-qpu`.

    """

    results: list[dict[str, Any]]
    count: int
    next: str | None
    previous: str | None
    qpu_id: int
    qpu_name: str


DEFAULT_PAGE_SIZE = 20
"""Default page size for paginated configuration results."""


def handle_url_parse(url: str | None) -> ParseResult | None:
    """Parse a URL and ensure it contains the required query parameters.
    Ensures that the URL contains the required query parameters "page" and "page_size".

    Example:
        >>> handle_url_parse("https://example.com/api/config?page=1&page_size=20")
        ParseResult(
            scheme='https',
            netloc='example.com',
            path='/api/config',
            params='',
            query='page=1&page_size=20',
            fragment='')

    Args:
        url (str | None): The URL to parse.

    Returns:
        ParseResult | None: The parsed URL if valid, otherwise None.

    Raises:
        ValueError: If the URL is missing required query parameters.
    """
    if url is None:
        return None

    parsed_url = urlparse(url)
    query_params = dict(parse_qsl(parsed_url.query))
    missing_params = {"page_size"} - set(query_params.keys())
    if missing_params:
        raise ValueError(
            f"Missing query parameters: {missing_params}. URL provided: {url}"
        )

    return parsed_url


class ConfigurationsResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    count: int = Field(description="Total number of configurations available")
    page: int = Field(
        description="Current page number of the configurations result",
    )
    page_size: int = Field(
        description="Number of configurations per page", default=DEFAULT_PAGE_SIZE
    )
    next_url_parse: ParseResult | None = Field(
        description="URL to the next page of configurations, if any",
    )
    prev_url_parse: ParseResult | None = Field(
        description="URL to the previous page of configurations, if any",
    )

    qpu_id: int | None = Field(
        description="ID of the QPU associated with the configurations"
    )
    qpu_name: str | None = Field(
        description="Name of the QPU associated with the configurations"
    )
    qcsetup_id: int | None = Field(
        description="ID of the QC setup associated with the configurations"
    )
    qcsetup_name: str | None = Field(
        description="Name of the QC setup associated with the configurations"
    )
    configurations: list[Configuration] = Field(description="List of configurations")

    def __getitem__(self, item: int):
        return self.configurations[item]

    def __len__(self):
        return len(self.configurations)

    def __iter__(self) -> Iterator[Configuration]:  # type: ignore[override]
        return iter(self.configurations)

    @classmethod
    def from_response(
        cls, response: PublicConfigResponse, page_size: int | None = None
    ) -> "ConfigurationsResult":
        """Create a ConfigurationsResult instance from a response dictionary.
        Args:
            response (PublicConfigResponse):
                The response dictionary containing configuration data.
            page_size (int | None):
                The number of configurations per page. Defaults to None.

        Returns:
            An instance of ConfigurationsResult populated with the response data.
        """

        next_url_parse = handle_url_parse(response.get("next", None))
        prev_url_parse = handle_url_parse(response.get("previous", None))
        next_query_params = (
            dict(parse_qsl(next_url_parse.query)) if next_url_parse else {}
        )
        prev_query_params = (
            dict(parse_qsl(prev_url_parse.query)) if prev_url_parse else {}
        )

        if prev_url_parse is None:
            page = 1
            page_size = int(next_query_params.get("page_size", DEFAULT_PAGE_SIZE))
        else:
            page = int(prev_query_params.get("page", 1)) + 1
            page_size = int(prev_query_params.get("page_size", DEFAULT_PAGE_SIZE))

        return cls(
            configurations=[
                ConfigurationAdapter.validate_python(config)
                for config in response.get("results", [])
            ],
            count=response.get("count", 0),
            next_url_parse=next_url_parse,
            prev_url_parse=prev_url_parse,
            qpu_id=response.get("qpu_id", None),
            qpu_name=response.get("qpu_name", None),
            qcsetup_id=response.get("qcsetup_id", None),
            qcsetup_name=response.get("qcsetup_name", None),
            page=page,
            page_size=page_size,
        )

    @property
    def next_url(self) -> str | None:
        """Return the next URL if available, otherwise None."""
        return self.next_url_parse.geturl() if self.next_url_parse else None

    @property
    def prev_url(self) -> str | None:
        """Return the previous URL if available, otherwise None."""
        return self.prev_url_parse.geturl() if self.prev_url_parse else None

    def get_configuration(self, configuration_id: int) -> Configuration | None:
        for config in self.configurations:
            if config.id == configuration_id:
                return config
        return None

    def _repr_html_(self) -> str:
        """Render the configurations as an HTML table in Jupyter."""

        columns_dict = {
            "id": "ID",
            "name": "Name",
            "qcsetup_name": "QC Setup",
            # "qpu_name": "QPU",
            "category": "Category",
            # "description": "Description",
            "author_name": "Author",
            "machine_name": "Machine",
            "created_at": "Created",
            "updated_at": "Updated",
        }
        if self.qcsetup_name is not None:
            columns_dict.pop("qcsetup_name", None)

        columns = list(columns_dict.items())

        scope = []
        if self.qcsetup_name is not None or self.qcsetup_id is not None:
            scope_of_id = f"qcsetup_id={esc(self.qcsetup_id)}"
            scope_of_func = "get_config_by_qcsetup"
            scope.append(
                f"<br /><strong>QC setup: {esc(self.qcsetup_name)} "
                f"({scope_of_id})</strong>"
            )
        elif self.qpu_name is not None or self.qpu_id is not None:
            scope_of_id = f"qpu_id={esc(self.qpu_id)}"
            scope_of_func = "get_config_by_qpu"
            scope.append(
                f"<br /><strong>QPU: {esc(self.qpu_name)} ({scope_of_id})</strong>"
            )
        else:
            scope_of_id = ""
            scope_of_func = ""
            scope.append("<em>No specific scope</em>")

        pages = []
        if self.prev_url_parse:
            prev_page_num = self.page - 1
            pages.append(
                f"Use the classmethod of client <code>.{scope_of_func}({scope_of_id}, "
                + (f"page={prev_page_num}, " if prev_page_num > 1 else "")
                + f"page_size={self.page_size})</code> to access the previous page"
            )
        if self.next_url_parse:
            next_page_num = self.page + 1
            pages.append(
                f"Use the classmethod of client <code>.{scope_of_func}({scope_of_id}, "
                + f"page={next_page_num}, "
                + f"page_size={self.page_size})</code> to access the next page"
            )

        caption = (
            f"<strong>ConfigurationsResult</strong>: "
            f"showing {(self.page - 1) * self.page_size + 1} to "
            f"{min(self.page * self.page_size, self.count)} of "
            f"{self.count} configurations"
            f" (page {self.page} of {((self.count - 1) // self.page_size) + 1})"
            if self.page is not None and self.page_size is not None
            else ""
        )
        if scope:
            caption += " &middot; " + " &middot; ".join(scope)
        for page in pages:
            caption += "<br />" + page

        header = "".join(f"<th>{label}</th>" for _, label in columns)
        rows = "".join(
            "<tr>"
            + "".join(
                f"<td>{esc(getattr(config, key, None))}</td>" for key, _ in columns
            )
            + "</tr>"
            for config in sorted(self.configurations, key=lambda c: c.id, reverse=True)
        )
        if not rows:
            rows = (
                f'<tr><td colspan="{len(columns) + 1}">'
                + "<em>No configurations</em></td></tr>"
            )

        return (
            "<div>"
            f'<div style="margin-bottom: 4px;">{caption}</div>'
            '<table style="border-collapse: collapse; text-align: left;">'
            f"<thead><tr>{header}</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
            '<div style="margin-top: 4px;">'
            "The configurations are listed in descending order by their ID. "
            "Largest ID means the most recently added configuration."
            "</div>"
            "</div>"
        )
