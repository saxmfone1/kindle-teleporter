import time
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler
from os import environ
import stkclient
from ebooklib import epub
from pprint import pprint as pp
from pathlib import Path

def get_metadata(book: str):
    print(f"Getting metadata for {book}")
    metadata = epub.read_epub(book)
    author = metadata.get_metadata(namespace="DC", name="creator")[0][0]
    title = metadata.get_metadata(namespace="DC", name="title")[0][0]
    print(f"Found book metadata:")
    pp(metadata.metadata)
    return {"author": author, "title": title}

def send_to_kindle(book: str, metadata: dict):
    CLIENT_JSON = environ["CLIENT_JSON"]
    with open(CLIENT_JSON, "r") as f:
        client = stkclient.Client.load(f)
    devices = client.get_owned_devices()
    destinations = [d.device_serial_number for d in devices]
    author = metadata["author"]
    title = metadata["title"]
        
    print("Sending book to kindle")
    try:
        client.send_file(file_path=Path(book), target_device_serial_numbers=destinations, author=author, title=title, format="epub")
    except Exception as e:
        print("Could not send to kindle")
        print(e)

def on_created(event):
    book = event.src_path
    print(f"New book: {book} has been added.")
    time.sleep(3)
    try:
        metadata = get_metadata(book)
    except Exception as e:
        print("Could not get book metadata. Bailing out.")
        print(e)
        return
    try:
        send_to_kindle(book, metadata)
    except Exception as e:
        print(f"Could not send to kindle: {e}")
    print("Sent to kindle")

def run(path: str, recursive: bool=False):
    print(f"Starting up Kindle-Teleporter, watching {path} for books")
    patterns = ["*.epub"]
    ignore_patterns = None
    ignore_directories = None
    case_sensitive = True
    event_handler = PatternMatchingEventHandler(patterns=patterns, ignore_patterns=ignore_patterns, ignore_directories=ignore_directories, case_sensitive=case_sensitive)
    event_handler.on_created = on_created
    observer = PollingObserver()
    observer.schedule(event_handler=event_handler, path=path, recursive=recursive)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        print("Shutting down")

def cmd():
    import fire
    fire.Fire(run)