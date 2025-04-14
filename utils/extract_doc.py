import csv
from typing import Iterator


def prepare_documents_from_csv_stream(
    file_path: str,
    include_columns: list[str] = None,
    batch_size: int = 100,
    skip_empty: bool = True
) -> Iterator[list[dict]]:
    """
    Stream a large CSV file and yield batches of documents.

    :param file_path: Path to the CSV file.
    :param include_columns: List of column names to include in the document payload. If None, include all columns.
    :param batch_size: Number of documents to yield per batch.
    :param skip_empty: If True, skip rows with empty values in the specified columns.
    :return: Yields batches of documents (list of dicts).
    """
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        batch = []
        for row in reader:
            if include_columns:
                document = {col: row[col]
                            for col in include_columns if col in row}
                if skip_empty and any(not row[col] for col in include_columns):
                    continue
            else:
                document = dict(row)
                if skip_empty and any(not value for value in row.values()):
                    continue

            batch.append(document)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield any remaining documents
        if batch:
            yield batch
