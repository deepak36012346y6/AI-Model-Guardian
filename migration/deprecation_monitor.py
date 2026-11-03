import csv
import os
import re
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from migration.lifecycle_registry import ModelLifecycleRegistry


SOURCES = {
    "Google Gemini": (
        "https://ai.google.dev/gemini-api/docs/deprecations"
    ),
    "OpenAI": (
        "https://developers.openai.com/api/docs/deprecations"
    ),
}

CHECK_LOG = "logs/deprecation_checks.csv"


class OfficialTableParser(HTMLParser):
    """Extract rows from HTML tables on official documentation pages."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.current_table = None
        self.current_row = None
        self.current_cell = None
        self.table_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag == "table":
            if self.table_depth == 0:
                self.current_table = []
            self.table_depth += 1

        elif tag == "tr" and self.table_depth > 0:
            self.current_row = []

        elif tag in ("td", "th") and self.current_row is not None:
            self.current_cell = []

        elif tag == "br" and self.current_cell is not None:
            self.current_cell.append(" ")

    def handle_data(self, data):
        if self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in ("td", "th") and self.current_cell is not None:
            cell_text = " ".join(
                "".join(self.current_cell).split()
            )
            self.current_row.append(cell_text)
            self.current_cell = None

        elif tag == "tr" and self.current_row is not None:
            if self.current_table is not None:
                self.current_table.append(self.current_row)

            self.current_row = None

        elif tag == "table" and self.table_depth > 0:
            self.table_depth -= 1

            if self.table_depth == 0 and self.current_table is not None:
                self.tables.append(self.current_table)
                self.current_table = None


def fetch_page(url):
    """Download an official documentation page."""

    request = Request(
        url,
        headers={
            "User-Agent": "AI-Model-Guardian/1.0",
        },
    )

    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(
                f"Unexpected HTTP status: {response.status}"
            )

        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def normalize_header(value):
    """Normalize a table heading for comparison."""

    return re.sub(
        r"\s+",
        " ",
        value.strip().lower(),
    )


def parse_shutdown_date(value):
    """Convert common written dates into YYYY-MM-DD."""

    value = value.strip()

    if not value:
        return None

    value = value.replace("\u2011", "-")
    value = value.replace("\u2013", "-")
    value = value.replace("\u2014", "-")

    formats = [
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]

    for date_format in formats:
        try:
            parsed = datetime.strptime(
                value,
                date_format,
            ).date()

            return parsed.isoformat()

        except ValueError:
            continue

    return None


def find_column(headers, keywords):
    """Find a table column by its heading."""

    for index, header in enumerate(headers):
        normalized = normalize_header(header)

        if any(word in normalized for word in keywords):
            return index

    return None


def extract_deprecations(provider, html):
    """
    Extract model names, shutdown dates, and replacement suggestions.

    This parser depends on the structure of the provider's HTML tables.
    Extracted information should be verified against the official page.
    """

    parser = OfficialTableParser()
    parser.feed(html)

    records = []

    for table in parser.tables:
        for header_index, row in enumerate(table):
            headers = [
                normalize_header(cell)
                for cell in row
            ]

            model_index = find_column(
                headers,
                ["model"],
            )

            date_index = find_column(
                headers,
                ["shutdown date", "retirement date"],
            )

            replacement_index = find_column(
                headers,
                ["recommended replacement", "replacement"],
            )

            # Only process tables with recognizable model and date columns.
            if model_index is None or date_index is None:
                continue

            if header_index == len(table) - 1:
                continue

            for data_row in table[header_index + 1:]:
                if len(data_row) <= max(
                    model_index,
                    date_index,
                ):
                    continue

                model_name = data_row[model_index].strip()
                raw_date = data_row[date_index].strip()

                if not model_name:
                    continue

                # Avoid treating headings as model names.
                if normalize_header(model_name) in {
                    "model",
                    "model / system",
                    "deprecated model",
                }:
                    continue

                shutdown_date = parse_shutdown_date(raw_date)

                # Rows without a recognized date are not imported.
                if shutdown_date is None:
                    continue

                replacement = ""

                if (
                    replacement_index is not None
                    and replacement_index < len(data_row)
                ):
                    replacement = data_row[
                        replacement_index
                    ].strip()

                records.append(
                    {
                        "provider": provider,
                        "model_name": model_name,
                        "retirement_date": shutdown_date,
                        "replacement": replacement,
                    }
                )

    # Remove duplicate rows from overlapping documentation tables.
    unique_records = []
    seen = set()

    for record in records:
        key = (
            record["provider"].lower(),
            record["model_name"].lower(),
            record["retirement_date"],
        )

        if key not in seen:
            seen.add(key)
            unique_records.append(record)

    return unique_records


def save_check_results(results):
    """Append official-source check results to a CSV log."""

    os.makedirs("logs", exist_ok=True)

    fields = [
        "provider",
        "url",
        "checked_at",
        "reachable",
        "models_extracted",
        "message",
    ]

    file_exists = (
        os.path.exists(CHECK_LOG)
        and os.path.getsize(CHECK_LOG) > 0
    )

    with open(
        CHECK_LOG,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(results)


def run_check():
    """Check official pages and update the lifecycle registry."""

    registry = ModelLifecycleRegistry()
    check_results = []

    for provider, url in SOURCES.items():
        print(f"\nChecking {provider}...")
        checked_at = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

        try:
            html = fetch_page(url)
            records = extract_deprecations(provider, html)

            print("Official page: reachable")
            print("Model records extracted:", len(records))

            imported = 0

            for record in records:
                retirement_date = record["retirement_date"]
                shutdown = date.fromisoformat(retirement_date)

                if shutdown < date.today():
                    status = "deprecated"
                    notes = (
                        "The announced date has passed. "
                        "Verify the model's actual availability "
                        "on the official page."
                    )
                else:
                    status = "scheduled_for_retirement"
                    notes = "Shutdown date extracted from official documentation."

                if record["replacement"]:
                    notes += (
                        " Suggested replacement: "
                        + record["replacement"]
                    )

                registry.add_or_update_model(
                    provider=provider,
                    model_name=record["model_name"],
                    status=status,
                    retirement_date=retirement_date,
                    official_notice=url,
                    notes=notes,
                )

                imported += 1

            message = (
                f"Page reachable; {imported} model records "
                "saved to the lifecycle registry."
            )

            if imported == 0:
                message += (
                    " No matching model tables were extracted. "
                    "The page structure may have changed."
                )

            print(message)

            check_results.append(
                {
                    "provider": provider,
                    "url": url,
                    "checked_at": checked_at,
                    "reachable": True,
                    "models_extracted": imported,
                    "message": message,
                }
            )

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            RuntimeError,
        ) as error:
            message = f"Could not check source: {error}"

            print(message)

            check_results.append(
                {
                    "provider": provider,
                    "url": url,
                    "checked_at": checked_at,
                    "reachable": False,
                    "models_extracted": 0,
                    "message": message,
                }
            )

    save_check_results(check_results)

    print("\n" + "=" * 50)
    print("MODEL LIFECYCLE CHECK FINISHED")
    print("Registry: logs/model_lifecycle.csv")
    print("Check history:", CHECK_LOG)
    print("=" * 50)

    print(
        "\nImportant: Review extracted records against official "
        "documentation before using them to migrate a production system."
    )


if __name__ == "__main__":
    run_check()