
from click import Choice
from fuzzywuzzy import fuzz, process
from pathlib import Path
import click
import json
import os
import subprocess
import tempfile

DOC_PATH = Path('/home/bob/repos/devdocs/public/docs')


def available_languages():
    return [path.name for path in DOC_PATH.iterdir() if path.is_dir()]


@click.command()
@click.argument('language', type=Choice(available_languages()))
@click.argument('search_term')
def doctor(language, search_term):
    language_docs = DOC_PATH.joinpath(language)

    index_file = language_docs.joinpath('index.json')
    with index_file.open() as f:
        index = json.load(f)

    index_entries = {
        entry['name']: entry for entry in index['entries']
    }

    matches = process.extract(
        search_term,
        index_entries.keys(),
        scorer=fuzz.token_sort_ratio,
        limit=5,
    )
    print("matches:", matches)
    match_name, _ = matches[0]
    match = index_entries[match_name]

    entry_path = match['path'].split('#')[0]
    doc_path = language_docs.joinpath(entry_path).with_suffix('.html')
    with doc_path.open() as doc:
        completed_process = subprocess.run(
            ['./to-markdown'],
            stdin=doc,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
    markdown_doc = completed_process.stdout

    _, temp = tempfile.mkstemp(prefix=match['name'] + '.', suffix='.md')
    with open(temp, 'w+') as f:
        f.write(markdown_doc)
    subprocess.run(['vim', temp])
    os.remove(temp)
